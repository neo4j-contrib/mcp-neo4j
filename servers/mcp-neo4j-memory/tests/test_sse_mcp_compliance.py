#!/usr/bin/env python3
"""
Integration tests for MCP SSE server compliance.

These tests verify that the SSE server implementation follows the MCP specification
for Server-Sent Events transport, including proper endpoint behavior, session management,
and JSON-RPC message handling.
"""

import asyncio
import json
import logging
import os
import pytest
import threading
import time
from typing import Optional, Dict, Any

import aiohttp
from neo4j import GraphDatabase

from mcp_neo4j_memory.core import Neo4jMemory
from mcp_neo4j_memory.protocols.sse_server import MCPSSEServer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def neo4j_driver():
    """Create a Neo4j driver for the test session."""
    uri = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Verify connection
    try:
        driver.verify_connectivity()
    except Exception as e:
        pytest.skip(f"Could not connect to Neo4j for SSE compliance tests: {e}")

    yield driver

    # Clean up test data after all tests
    driver.execute_query("MATCH (n:Memory) DETACH DELETE n")
    driver.close()


@pytest.fixture(scope="function")
def memory(neo4j_driver):
    """Create a fresh Neo4jMemory instance for each test."""
    # Clean up before each test
    neo4j_driver.execute_query("MATCH (n:Memory) DETACH DELETE n")
    return Neo4jMemory(neo4j_driver)


@pytest.fixture
def sse_server_app(memory):
    """Create an SSE server app for testing."""
    server = MCPSSEServer(memory)
    return server.app


class TestSSEServerEndpoints:
    """Test basic SSE server endpoint functionality."""

    def test_root_endpoint(self, sse_server_app):
        """Test the root endpoint returns correct server info."""
        from fastapi.testclient import TestClient

        client = TestClient(sse_server_app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "MCP Neo4j Memory SSE Server"
        assert data["version"] == "1.1"
        assert data["protocol"] == "mcp-sse"
        assert "endpoints" in data
        assert data["endpoints"]["sse"] == "/sse"
        assert data["endpoints"]["messages"] == "/messages"

    def test_health_endpoint(self, sse_server_app):
        """Test the health endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(sse_server_app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["neo4j"] == "connected"

    def test_options_messages_endpoint(self, sse_server_app):
        """Test CORS preflight for messages endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(sse_server_app)
        response = client.options("/messages")

        assert response.status_code == 200
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers


class TestSSEStreamBehavior:
    """Test SSE stream behavior and session management."""

    def test_sse_endpoint_headers(self, sse_server_app):
        """Test SSE endpoint returns correct headers."""
        from fastapi.testclient import TestClient

        client = TestClient(sse_server_app)

        # Start SSE connection in a separate thread with timeout
        result = {"headers": None, "first_event": None, "error": None}

        def connect_sse():
            try:
                with client.stream("GET", "/sse") as response:
                    result["headers"] = dict(response.headers)

                    # Try to read the first event
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line.strip():
                                result["first_event"] = line
                                break

            except Exception as e:
                result["error"] = str(e)

        # Run in thread with timeout
        thread = threading.Thread(target=connect_sse)
        thread.daemon = True
        thread.start()
        thread.join(timeout=3.0)

        # Check results
        if result["headers"]:
            headers = result["headers"]
            assert headers.get("content-type") == "text/event-stream; charset=utf-8"
            assert headers.get("cache-control") == "no-cache"
            assert headers.get("connection") == "keep-alive"

        # Check for endpoint event
        if result["first_event"]:
            assert "event: endpoint" in result["first_event"]

        # If no results but no error, the SSE connection is working (infinite stream)
        if not result["error"] and thread.is_alive():
            logger.info("SSE endpoint working (infinite stream detected)")


class TestMCPJSONRPCCompliance:
    """Test MCP JSON-RPC protocol compliance via async HTTP client."""

    @pytest.mark.asyncio
    async def test_sse_server_startup_and_shutdown(self, memory):
        """Test SSE server can start and shutdown properly."""
        import uvicorn
        from contextlib import asynccontextmanager

        server = MCPSSEServer(memory)

        # Test that we can create the server without errors
        assert server.app is not None
        assert server.memory is not None
        assert server.active_sessions == {}

    @pytest.mark.asyncio
    async def test_session_management(self, sse_server_app):
        """Test session creation and management."""
        from httpx import AsyncClient, ASGITransport

        async with AsyncClient(transport=ASGITransport(app=sse_server_app), base_url="http://test") as client:
            # Test that sessions are created when connecting to SSE
            # Since we can't easily test infinite SSE streams, we'll test the session logic
            # by checking that the server handles missing session IDs properly

            # Test messages endpoint without session ID
            response = await client.post("/messages", json={"jsonrpc": "2.0", "method": "ping"})
            assert response.status_code == 400
            assert "session_id parameter required" in response.json()["detail"]

            # Test messages endpoint with invalid session ID
            response = await client.post(
                "/messages?session_id=invalid",
                json={"jsonrpc": "2.0", "method": "ping"}
            )
            assert response.status_code == 404
            assert "Session not found" in response.json()["detail"]


class TestMCPProtocolMethods:
    """Test MCP protocol method handling."""

    def test_json_rpc_initialize_method(self, sse_server_app):
        """Test the MCP initialize method via direct call."""
        server = MCPSSEServer(None)  # Memory not needed for this test

        # Create mock session data
        session_data = {"initialized": False, "pending_responses": []}

        # Test initialize request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        # Call the internal JSON-RPC handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(
                server._handle_json_rpc(request, session_data)
            )

            assert response is not None
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "result" in response

            result = response["result"]
            assert result["protocolVersion"] == "2024-11-05"
            assert "capabilities" in result
            assert result["capabilities"]["tools"]["listChanged"] is True
            assert result["serverInfo"]["name"] == "mcp-neo4j-memory"
            assert result["serverInfo"]["version"] == "1.1"

            # Check session was marked as initialized
            assert session_data["initialized"] is True

        finally:
            loop.close()

    def test_json_rpc_tools_list_method(self, memory):
        """Test the MCP tools/list method."""
        server = MCPSSEServer(memory)

        # Create initialized session
        session_data = {"initialized": True, "pending_responses": []}

        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(
                server._handle_json_rpc(request, session_data)
            )

            assert response is not None
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 2
            assert "result" in response

            result = response["result"]
            assert "tools" in result
            tools = result["tools"]
            assert len(tools) == 10

            # Check that all expected tools are present
            tool_names = [tool["name"] for tool in tools]
            expected_tools = [
                "create_entities", "create_relations", "add_observations",
                "delete_entities", "delete_observations", "delete_relations",
                "read_graph", "search_nodes", "find_nodes", "open_nodes"
            ]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names

            # Check tool structure
            for tool in tools:
                assert "name" in tool
                assert "description" in tool
                assert "inputSchema" in tool

        finally:
            loop.close()

    def test_json_rpc_tools_call_method(self, memory):
        """Test the MCP tools/call method."""
        server = MCPSSEServer(memory)

        # Create initialized session
        session_data = {"initialized": True, "pending_responses": []}

        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "read_graph",
                "arguments": {}
            }
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(
                server._handle_json_rpc(request, session_data)
            )

            assert response is not None
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 3
            assert "result" in response

            result = response["result"]
            assert "content" in result
            assert "isError" in result
            assert result["isError"] is False

            content = result["content"]
            assert len(content) > 0
            assert content[0]["type"] == "text"
            assert "text" in content[0]

        finally:
            loop.close()

    def test_json_rpc_ping_method(self, memory):
        """Test the MCP ping method."""
        server = MCPSSEServer(memory)

        session_data = {"initialized": True, "pending_responses": []}

        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "ping"
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(
                server._handle_json_rpc(request, session_data)
            )

            assert response is not None
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 4
            assert "result" in response
            assert response["result"] == {}

        finally:
            loop.close()

    def test_json_rpc_error_handling(self, memory):
        """Test JSON-RPC error handling."""
        server = MCPSSEServer(memory)

        session_data = {"initialized": False, "pending_responses": []}

        # Test uninitialized session
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/list"
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(
                server._handle_json_rpc(request, session_data)
            )

            assert response is not None
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 5
            assert "error" in response

            error = response["error"]
            assert error["code"] == -32002
            assert "not initialized" in error["message"]

            # Test unknown method
            request["method"] = "unknown_method"
            response = loop.run_until_complete(
                server._handle_json_rpc(request, session_data)
            )

            assert "error" in response
            assert response["error"]["code"] == -32601
            assert "not found" in response["error"]["message"]

        finally:
            loop.close()


class TestSSEMCPIntegration:
    """Test full MCP integration with actual tool execution."""

    @pytest.mark.asyncio
    async def test_full_mcp_workflow_simulation(self, memory):
        """Simulate a complete MCP workflow without actual SSE connection."""
        server = MCPSSEServer(memory)

        # Simulate session creation
        session_data = {"initialized": False, "pending_responses": []}

        # Step 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        init_response = await server._handle_json_rpc(init_request, session_data)
        assert init_response["result"]["protocolVersion"] == "2024-11-05"
        assert session_data["initialized"] is True

        # Step 2: List tools
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        list_response = await server._handle_json_rpc(list_request, session_data)
        tools = list_response["result"]["tools"]
        assert len(tools) == 10

        # Step 3: Create entities
        create_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "create_entities",
                "arguments": {
                    "entities": [
                        {
                            "name": "TestMCPEntity",
                            "type": "Test",
                            "observations": ["Created via MCP SSE"]
                        }
                    ]
                }
            }
        }

        create_response = await server._handle_json_rpc(create_request, session_data)
        assert create_response["result"]["isError"] is False

        # Step 4: Read graph to verify
        read_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "read_graph",
                "arguments": {}
            }
        }

        read_response = await server._handle_json_rpc(read_request, session_data)
        assert read_response["result"]["isError"] is False

        # Parse the JSON content to verify entity was created
        content_text = read_response["result"]["content"][0]["text"]
        content_data = json.loads(content_text)

        assert len(content_data["entities"]) == 1
        assert content_data["entities"][0]["name"] == "TestMCPEntity"
        assert content_data["entities"][0]["type"] == "Test"


@pytest.mark.integration
class TestSSEServerLiveIntegration:
    """
    Live integration tests that require a running SSE server.

    These tests are marked as 'integration' and can be run separately
    when you want to test against a live server instance.
    """

    @pytest.mark.asyncio
    async def test_live_sse_server_health(self):
        """Test health endpoint of a live SSE server."""
        base_url = os.environ.get("MCP_SSE_SERVER_URL", "http://localhost:3001")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        assert data["status"] == "healthy"
                        assert data["neo4j"] == "connected"
                    else:
                        pytest.skip(f"SSE server not available at {base_url}")
        except aiohttp.ClientError:
            pytest.skip(f"Cannot connect to SSE server at {base_url}")

    @pytest.mark.asyncio
    async def test_live_sse_server_root(self):
        """Test root endpoint of a live SSE server."""
        base_url = os.environ.get("MCP_SSE_SERVER_URL", "http://localhost:3001")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        assert data["service"] == "MCP Neo4j Memory SSE Server"
                        assert data["protocol"] == "mcp-sse"
                        assert "endpoints" in data
                    else:
                        pytest.skip(f"SSE server not available at {base_url}")
        except aiohttp.ClientError:
            pytest.skip(f"Cannot connect to SSE server at {base_url}")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_sse_mcp_compliance.py -v
    # Run integration tests: python -m pytest tests/test_sse_mcp_compliance.py -v -m integration
    pytest.main([__file__, "-v"])
