import json
import uuid

import aiohttp
import pytest


async def parse_sse_response(response: aiohttp.ClientResponse) -> dict:
    """Parse Server-Sent Events response from FastMCP 2.0."""
    content = await response.text()
    lines = content.strip().split("\n")

    # Find the data line that contains the JSON
    for line in lines:
        if line.startswith("data: "):
            json_str = line[6:]  # Remove 'data: ' prefix
            return json.loads(json_str)

    raise ValueError("No data line found in SSE response")


@pytest.mark.asyncio
async def test_http_tools_list(http_server):
    """Test that tools/list endpoint works over HTTP."""
    session_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": session_id,
            },
        ) as response:
            print(f"Response status: {response.status}")
            print(f"Response headers: {dict(response.headers)}")
            response_text = await response.text()
            print(f"Response text: {response_text}")

            assert response.status == 200
            result = await parse_sse_response(response)
            assert "result" in result
            assert "tools" in result["result"]
            tools = result["result"]["tools"]
            assert len(tools) > 0
            tool_names = [tool["name"] for tool in tools]
            assert "get_neo4j_schema" in tool_names
            assert "read_neo4j_cypher" in tool_names
            assert "write_neo4j_cypher" in tool_names


@pytest.mark.asyncio
async def test_http_get_schema(http_server):
    """Test that get_neo4j_schema works over HTTP."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_neo4j_schema", "arguments": {}},
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": "test-session",
            },
        ) as response:
            result = await parse_sse_response(response)
            assert response.status == 200
            assert "result" in result
            assert "content" in result["result"]
            assert len(result["result"]["content"]) > 0


@pytest.mark.asyncio
async def test_http_write_query(http_server):
    """Test that write_neo4j_cypher works over HTTP."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "write_neo4j_cypher",
                    "arguments": {"query": "CREATE (n:Test {name: 'http_test'})"},
                },
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": "test-session",
            },
        ) as response:
            result = await parse_sse_response(response)
            assert response.status == 200
            assert "result" in result
            assert "content" in result["result"]


@pytest.mark.asyncio
async def test_http_read_query(http_server):
    """Test that read_neo4j_cypher works over HTTP."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "read_neo4j_cypher",
                    "arguments": {"query": "MATCH (n:Test) RETURN n.name as name"},
                },
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": "test-session",
            },
        ) as response:
            result = await parse_sse_response(response)
            assert response.status == 200
            assert "result" in result
            assert "content" in result["result"]


@pytest.mark.asyncio
async def test_http_invalid_method(http_server):
    """Test handling of invalid method over HTTP."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "invalid_method"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": "test-session",
            },
        ) as response:
            result = await parse_sse_response(response)
            assert response.status == 200
            # Accept either JSON-RPC error or result with isError
            assert ("result" in result and result["result"].get("isError", False)) or (
                "error" in result
            )


@pytest.mark.asyncio
async def test_http_invalid_tool(http_server):
    """Test handling of invalid tool over HTTP."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "invalid_tool", "arguments": {}},
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": "test-session",
            },
        ) as response:
            result = await parse_sse_response(response)
            assert response.status == 200
            # FastMCP returns errors in result field with isError: True
            assert "result" in result
            assert result["result"].get("isError", False)


@pytest.mark.asyncio
async def test_http_full_workflow(http_server):
    """Test complete workflow over HTTP transport."""

    async with aiohttp.ClientSession() as session:
        # 1. List tools
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": "test-session",
            },
        ) as response:
            result = await parse_sse_response(response)
            assert response.status == 200
            assert "result" in result

        # 2. Write data
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "write_neo4j_cypher",
                    "arguments": {
                        "query": "CREATE (n:IntegrationTest {name: 'workflow_test'})"
                    },
                },
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": "test-session",
            },
        ) as response:
            result = await parse_sse_response(response)
            assert response.status == 200
            assert "result" in result

        # 3. Read data
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "read_neo4j_cypher",
                    "arguments": {
                        "query": "MATCH (n:IntegrationTest) RETURN n.name as name"
                    },
                },
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": "test-session",
            },
        ) as response:
            result = await parse_sse_response(response)
            assert response.status == 200
            assert "result" in result
