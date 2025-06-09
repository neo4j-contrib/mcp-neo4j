"""
Server-Sent Events (SSE) protocol implementation for MCP Neo4j Memory server.
Fully compliant with MCP SSE specification using a simplified approach.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import mcp.types as types

from ..core import Neo4jMemory, get_mcp_tools, execute_tool

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory.protocols.sse')


class MCPSSEServer:
    """
    MCP-compliant Server-Sent Events server for Neo4j Memory.
    
    Implements the MCP SSE transport specification with:
    - GET /sse - SSE endpoint for server-to-client streaming
    - POST /messages - JSON-RPC endpoint for client-to-server messages
    - Session management with session IDs
    - Full MCP protocol support (initialize, tools, etc.)
    """

    def __init__(self, memory: Neo4jMemory):
        self.memory = memory
        self.app = self._create_app()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        app = FastAPI(
            title="MCP Neo4j Memory SSE Server",
            description="MCP-compliant Server-Sent Events server for Neo4j knowledge graph memory",
            version="1.1"
        )

        # Add CORS middleware - required for cross-origin SSE connections
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow cross-origin requests
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )

        # Register routes
        self._register_routes(app)

        return app

    def _register_routes(self, app: FastAPI):
        """Register HTTP routes."""

        @app.get("/")
        async def root():
            """Root endpoint with server info."""
            return {
                "service": "MCP Neo4j Memory SSE Server",
                "version": "1.1",
                "protocol": "mcp-sse",
                "description": "MCP-compliant Server-Sent Events server for Neo4j knowledge graph memory",
                "endpoints": {
                    "health": "/health",
                    "sse": "/sse",
                    "messages": "/messages"
                }
            }

        @app.get("/health")
        async def health_check():
            """Lightweight health check endpoint."""
            try:
                # Simple connection test - just verify driver connectivity
                self.memory.neo4j_driver.execute_query("RETURN 1")
                return {"status": "healthy", "neo4j": "connected"}
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail="Neo4j unavailable")

        @app.get("/sse")
        async def sse_endpoint(request: Request):
            """
            SSE endpoint for MCP client connections.
            
            This implements the MCP SSE specification:
            1. Creates a new session
            2. Sends endpoint event with messages URL
            3. Maintains connection for server-to-client streaming
            """
            try:
                # Create new session
                session_id = str(uuid.uuid4()).replace("-", "")
                session_data = {
                    "id": session_id,
                    "created_at": asyncio.get_event_loop().time(),
                    "initialized": False
                }
                self.active_sessions[session_id] = session_data
                
                logger.info(f"New SSE connection, session: {session_id}")

                # Messages endpoint URL with session ID
                messages_endpoint = f"/messages?session_id={session_id}"

                async def event_generator():
                    try:
                        # Send endpoint event (required by MCP SSE spec)
                        yield f"event: endpoint\ndata: {messages_endpoint}\n\n"
                        
                        # Keep connection alive and send responses
                        while session_id in self.active_sessions:
                            # Check for pending responses in session
                            session = self.active_sessions[session_id]
                            
                            # Send any pending responses
                            if "pending_responses" in session:
                                while session["pending_responses"]:
                                    response = session["pending_responses"].pop(0)
                                    yield f"event: message\ndata: {json.dumps(response)}\n\n"
                            
                            # Heartbeat to keep connection alive
                            await asyncio.sleep(5)
                            
                    except asyncio.CancelledError:
                        logger.info(f"SSE connection cancelled for session {session_id}")
                    except Exception as e:
                        logger.error(f"SSE error for session {session_id}: {e}")
                    finally:
                        # Clean up session
                        if session_id in self.active_sessions:
                            del self.active_sessions[session_id]
                        logger.info(f"SSE session {session_id} cleaned up")

                return StreamingResponse(
                    event_generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",  # Disable nginx buffering
                    }
                )

            except Exception as e:
                logger.error(f"Error creating SSE connection: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/messages")
        async def handle_messages(request: Request):
            """
            Messages endpoint for MCP JSON-RPC communication.
            
            This handles POST requests from MCP clients with JSON-RPC messages.
            Requires session_id parameter to identify the SSE session.
            """
            try:
                # Get session ID from query parameters
                session_id = request.query_params.get("session_id")
                if not session_id:
                    raise HTTPException(status_code=400, detail="session_id parameter required")

                # Check if session exists
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session_data = self.active_sessions[session_id]
                
                # Initialize pending responses list if not exists
                if "pending_responses" not in session_data:
                    session_data["pending_responses"] = []

                # Parse JSON-RPC request
                json_rpc_request = await request.json()
                logger.debug(f"Received JSON-RPC request: {json_rpc_request}")

                # Handle the JSON-RPC request
                response = await self._handle_json_rpc(json_rpc_request, session_data)
                
                if response:
                    # Add response to pending responses queue for SSE transmission
                    session_data["pending_responses"].append(response)
                
                # Return 202 Accepted for notifications/responses (MCP spec)
                return JSONResponse(
                    {"status": "accepted"},
                    status_code=202
                )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.options("/messages")
        async def options_messages():
            """Handle CORS preflight requests for messages endpoint."""
            return JSONResponse({}, headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Mcp-Session-Id",
            })

    async def _handle_json_rpc(self, request: dict, session_data: dict) -> Optional[dict]:
        """
        Handle JSON-RPC 2.0 requests according to MCP specification.
        
        Args:
            request: JSON-RPC request object
            session_data: Session information
            
        Returns:
            JSON-RPC response or None for notifications
        """
        try:
            jsonrpc = request.get("jsonrpc")
            if jsonrpc != "2.0":
                return self._create_error_response(
                    request.get("id"), -32600, "Invalid JSON-RPC version"
                )

            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            logger.debug(f"Handling method: {method}")

            # Handle initialize
            if method == "initialize":
                session_data["initialized"] = True
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                        },
                        "serverInfo": {
                            "name": "mcp-neo4j-memory",
                            "version": "1.1"
                        }
                    }
                }

            # Handle initialized notification
            elif method == "initialized":
                # No response needed for notifications
                return None

            # Handle tools/list
            elif method == "tools/list":
                self._ensure_initialized(session_data)
                
                tools = get_mcp_tools()
                tools_data = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in tools
                ]
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools_data
                    }
                }

            # Handle tools/call
            elif method == "tools/call":
                self._ensure_initialized(session_data)
                
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if not tool_name:
                    return self._create_error_response(
                        request_id, -32602, "Missing tool name"
                    )
                
                try:
                    # Execute the tool
                    result_content = await execute_tool(self.memory, tool_name, arguments)
                    
                    # Convert to MCP format
                    content = []
                    for item in result_content:
                        if hasattr(item, 'type') and hasattr(item, 'text'):
                            content.append({
                                "type": item.type,
                                "text": item.text
                            })
                        else:
                            # Fallback for simple string results
                            content.append({
                                "type": "text",
                                "text": str(item)
                            })
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": content,
                            "isError": False
                        }
                    }
                    
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{
                                "type": "text",
                                "text": f"Error executing tool: {str(e)}"
                            }],
                            "isError": True
                        }
                    }

            # Handle ping
            elif method == "ping":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {}
                }

            # Unknown method
            else:
                return self._create_error_response(
                    request_id, -32601, f"Method '{method}' not found"
                )

        except Exception as e:
            logger.error(f"Error processing JSON-RPC request: {e}")
            return self._create_error_response(
                request.get("id"), -32603, f"Internal error: {str(e)}"
            )

    def _ensure_initialized(self, session_data: dict) -> None:
        """Ensure session is initialized, auto-initialize if needed."""
        if not session_data.get("initialized"):
            session_data["initialized"] = True
            logger.warning(f"Auto-initializing session {session_data.get('id', 'unknown')}")

    def _create_error_response(self, request_id: Any, code: int, message: str) -> dict:
        """Create a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


async def run_sse_server(memory: Neo4jMemory, host: str = "0.0.0.0", port: int = 3001):
    """
    Run the MCP-compliant SSE server.

    Args:
        memory: Neo4jMemory instance
        host: Host to bind to
        port: Port to bind to
    """
    logger.info(f"Starting MCP SSE server on {host}:{port}")

    sse_server = MCPSSEServer(memory)
    config = uvicorn.Config(sse_server.app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
