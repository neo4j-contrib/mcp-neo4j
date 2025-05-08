from fastapi import FastAPI
from src.mcp_neo4j_memory.transport import TransportLayer
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport


class SSETransport(TransportLayer):
    """Implementation of SSE transport for MCP server"""

    def __init__(self):
        super().__init__()
        self.app = FastAPI(
            title="Neo4j MCP Memory Server",
            description="MCP server for Neo4j knowledge graph memory",
        )

    async def create_app(self, mcp_server):
        """Create and return a FastAPI app with the SSE transport configured"""
        # Create the SSE transport
        transport = SseServerTransport("/messages/")

        # Create the SSE handler
        async def handle_sse(request):
            async with transport.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await mcp_server.run(
                    streams[0],
                    streams[1],
                    InitializationOptions(
                        server_name="mcp-neo4j-memory",
                        server_version="1.1",
                        capabilities=mcp_server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )

        # Create the Starlette routes
        routes = [
            Route("/sse", endpoint=handle_sse),
            Mount("/messages", app=transport.handle_post_message),
        ]

        # Create Starlette app and mount it
        sse_app = Starlette(routes=routes)
        self.app.mount("/", sse_app)

        return self.app

    async def run_server(self, mcp_server):
        """Run the server with the given MCP server"""
        self.logger.info("Starting MCP server with SSE transport")
        app = await self.create_app(mcp_server)

        # In production, app will be run by uvicorn
        return app
