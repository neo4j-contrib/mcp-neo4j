import asyncio
import json
import subprocess

import aiohttp
import pytest
import pytest_asyncio


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
async def test_http_transport_creation(mcp_server):
    """Test that HTTP transport can be created."""
    # Test that the server can be created
    tools = await mcp_server.get_tools()
    assert len(tools) > 0


class TestHTTPEndpoints:
    """Test HTTP endpoints work correctly."""

    @pytest_asyncio.fixture
    async def http_server(self):
        """Start the server in HTTP mode."""
        import os

        # Get the current directory - we're already in the server directory
        server_dir = os.getcwd()

        # Start server process from the correct directory
        process = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "mcp-neo4j-data-modeling",
            "--transport",
            "http",
            "--server-host",
            "127.0.0.1",
            "--server-port",
            "8007",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=server_dir,
        )

        # Wait for server to start
        await asyncio.sleep(3)

        yield process

        # Cleanup
        try:
            process.terminate()
            await process.wait()
        except ProcessLookupError:
            pass  # Process already terminated

    @pytest.mark.asyncio
    async def test_http_tools_list(self, http_server):
        """Test that tools/list endpoint works."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8007/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)
                assert "result" in result
                assert "tools" in result["result"]
                tools = result["result"]["tools"]
                assert len(tools) > 0
                tool_names = [tool["name"] for tool in tools]
                assert "validate_node" in tool_names

    @pytest.mark.asyncio
    async def test_http_validate_node(self, http_server):
        """Test that validate_node endpoint works."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8007/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "validate_node",
                        "arguments": {
                            "node": {
                                "label": "Person",
                                "key_property": {"name": "name", "type": "STRING"},
                                "properties": [],
                            }
                        },
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)
                assert "result" in result
                assert "content" in result["result"]

    @pytest.mark.asyncio
    async def test_http_validate_data_model(self, http_server):
        """Test that validate_data_model endpoint works."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8007/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "validate_data_model",
                        "arguments": {
                            "data_model": {
                                "nodes": [
                                    {
                                        "label": "Person",
                                        "key_property": {
                                            "name": "name",
                                            "type": "STRING",
                                        },
                                        "properties": [],
                                    }
                                ],
                                "relationships": [],
                            }
                        },
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)
                assert "result" in result
                assert "content" in result["result"]

    @pytest.mark.asyncio
    async def test_http_get_mermaid_config(self, http_server):
        """Test that get_mermaid_config_str endpoint works."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8007/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_mermaid_config_str",
                        "arguments": {
                            "data_model": {
                                "nodes": [
                                    {
                                        "label": "Person",
                                        "key_property": {
                                            "name": "name",
                                            "type": "STRING",
                                        },
                                        "properties": [],
                                    }
                                ],
                                "relationships": [],
                            }
                        },
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)
                assert "result" in result
                assert "content" in result["result"]

    @pytest.mark.asyncio
    async def test_http_resources(self, http_server):
        """Test that resource endpoints work."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8007/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "resources/list"},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)
                assert "result" in result
                assert "resources" in result["result"]


class TestErrorHandling:
    """Test error handling in HTTP transport."""

    @pytest_asyncio.fixture
    async def http_server(self):
        """Start the server in HTTP mode."""
        import os

        # Get the current directory - we're already in the server directory
        server_dir = os.getcwd()

        process = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "mcp-neo4j-data-modeling",
            "--transport",
            "http",
            "--server-host",
            "127.0.0.1",
            "--server-port",
            "8008",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=server_dir,
        )

        await asyncio.sleep(3)
        yield process
        process.terminate()
        await process.wait()

    @pytest.mark.asyncio
    async def test_invalid_json(self, http_server):
        """Test handling of invalid JSON."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8008/mcp/",
                data="invalid json",
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                # FastMCP returns 406 for missing Accept header, but with proper headers it should handle invalid JSON
                assert response.status in [400, 406]

    @pytest.mark.asyncio
    async def test_invalid_method(self, http_server):
        """Test handling of invalid method."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8008/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "invalid_method"},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                # Accept either JSON-RPC error or result with isError
                assert (
                    "result" in result and result["result"].get("isError", False)
                ) or ("error" in result)

    @pytest.mark.asyncio
    async def test_invalid_tool_call(self, http_server):
        """Test handling of invalid tool call."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8008/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "nonexistent_tool", "arguments": {}},
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                # FastMCP returns errors in result field with isError: True
                assert "result" in result
                assert result["result"].get("isError", False)

    @pytest.mark.asyncio
    async def test_invalid_node_data(self, http_server):
        """Test handling of invalid node data."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8008/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "validate_node",
                        "arguments": {"node": {"invalid_field": "invalid_value"}},
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                # Should return an error or handle gracefully
                assert "result" in result

    @pytest.mark.asyncio
    async def test_invalid_data_model(self, http_server):
        """Test handling of invalid data model."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8008/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "validate_data_model",
                        "arguments": {"data_model": {"invalid_field": "invalid_value"}},
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                # Should return an error or handle gracefully
                assert "result" in result


class TestHTTPTransportIntegration:
    """Integration tests for HTTP transport."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test a complete workflow over HTTP transport."""
        import os

        # Get the current directory - we're already in the server directory
        server_dir = os.getcwd()

        process = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "mcp-neo4j-data-modeling",
            "--transport",
            "http",
            "--server-host",
            "127.0.0.1",
            "--server-port",
            "8009",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=server_dir,
        )

        await asyncio.sleep(3)

        try:
            async with aiohttp.ClientSession() as session:
                # 1. List tools
                async with session.post(
                    "http://127.0.0.1:8009/mcp/",
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    result = await parse_sse_response(response)
                    assert response.status == 200
                    assert "result" in result

                # 2. List resources
                async with session.post(
                    "http://127.0.0.1:8009/mcp/",
                    json={"jsonrpc": "2.0", "id": 2, "method": "resources/list"},
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    result = await parse_sse_response(response)
                    assert response.status == 200
                    assert "result" in result

                # 3. Validate a node
                async with session.post(
                    "http://127.0.0.1:8009/mcp/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "validate_node",
                            "arguments": {
                                "node": {
                                    "label": "IntegrationTest",
                                    "properties": [
                                        {
                                            "name": "test_field",
                                            "type": "string",
                                            "required": True,
                                        }
                                    ],
                                }
                            },
                        },
                    },
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    result = await parse_sse_response(response)
                    assert response.status == 200
                    assert "result" in result

                # 4. Validate a data model
                async with session.post(
                    "http://127.0.0.1:8009/mcp/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {
                            "name": "validate_data_model",
                            "arguments": {
                                "data_model": {
                                    "nodes": [
                                        {
                                            "label": "IntegrationTest",
                                            "properties": [
                                                {
                                                    "name": "test_field",
                                                    "type": "string",
                                                    "required": True,
                                                }
                                            ],
                                        }
                                    ],
                                    "relationships": [],
                                }
                            },
                        },
                    },
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    result = await parse_sse_response(response)
                    assert response.status == 200
                    assert "result" in result

        finally:
            process.terminate()
            await process.wait()


class TestMiddleware:
    """Test middleware functionality in HTTP transport."""

    @pytest_asyncio.fixture
    async def http_server_with_middleware(self):
        """Start the server in HTTP mode with middleware configuration."""
        import os

        server_dir = os.getcwd()

        process = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "mcp-neo4j-data-modeling",
            "--transport",
            "http",
            "--server-host",
            "127.0.0.1",
            "--server-port",
            "8010",
            "--allow-origins",
            "https://example.com,https://test.com",
            "--allowed-hosts",
            "localhost,127.0.0.1,example.com",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=server_dir,
        )

        await asyncio.sleep(3)
        yield process
        process.terminate()
        await process.wait()

    @pytest.mark.asyncio
    async def test_cors_headers(self, http_server_with_middleware):
        """Test CORS middleware is working."""
        async with aiohttp.ClientSession() as session:
            async with session.options(
                "http://127.0.0.1:8010/mcp/",
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            ) as response:
                # CORS preflight should return 200 with appropriate headers
                assert response.status == 200
                assert "access-control-allow-origin" in response.headers
                assert "access-control-allow-methods" in response.headers

    @pytest.mark.asyncio
    async def test_trusted_host_security(self, http_server_with_middleware):
        """Test TrustedHost middleware blocks invalid hosts."""
        async with aiohttp.ClientSession() as session:
            # This should work with valid host
            async with session.post(
                "http://127.0.0.1:8010/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "Host": "127.0.0.1:8010",
                },
            ) as response:
                assert response.status == 200

            # This should be blocked by TrustedHost middleware
            try:
                async with session.post(
                    "http://127.0.0.1:8010/mcp/",
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json",
                        "Host": "malicious.com",
                    },
                ) as response:
                    # Should return 400 status for invalid host
                    assert response.status == 400
            except aiohttp.ClientConnectorError:
                # Connection might be dropped entirely, which is also valid
                pass
