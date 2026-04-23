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
async def test_http_tools_list_read_only_mode(http_server_read_only):
    """Test that tools/list endpoint excludes write tools when read-only is enabled."""
    session_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8005/mcp/",
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

            # Read tools should be available
            assert "get_neo4j_schema" in tool_names
            assert "read_neo4j_cypher" in tool_names

            # Write tools should NOT be available in read-only mode
            assert "write_neo4j_cypher" not in tool_names


@pytest.mark.asyncio
async def test_http_write_tool_call_read_only_mode(http_server_read_only):
    """Test that attempting to call write tools fails when read-only is enabled."""
    session_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8005/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "write_neo4j_cypher",
                    "arguments": {"query": "CREATE (n:Test {name: 'test'}) RETURN n"},
                },
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": session_id,
            },
        ) as response:
            print(f"Response status: {response.status}")
            response_text = await response.text()
            print(f"Response text: {response_text}")

            assert response.status == 200
            result = await parse_sse_response(response)

            # Should get an error because the tool doesn't exist in read-only mode
            assert "result" in result
            assert result["result"]["isError"] is True
            assert "Unknown tool" in result["result"]["content"][0]["text"]


@pytest.mark.asyncio
async def test_http_read_tool_call_read_only_mode(http_server_read_only):
    """Test that read tools still work when read-only is enabled."""
    session_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8005/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "read_neo4j_cypher",
                    "arguments": {"query": "MATCH (n) RETURN count(n) as total"},
                },
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "mcp-session-id": session_id,
            },
        ) as response:
            print(f"Response status: {response.status}")
            response_text = await response.text()
            print(f"Response text: {response_text}")

            assert response.status == 200
            result = await parse_sse_response(response)

            # Should succeed - read tools should work in read-only mode
            assert "result" in result
            assert "content" in result["result"]


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


# CORS Middleware Tests


@pytest.mark.asyncio
async def test_cors_preflight_empty_default_origins(http_server):
    """Test CORS preflight request with empty default allowed origins."""
    async with aiohttp.ClientSession() as session:
        async with session.options(
            "http://127.0.0.1:8001/mcp/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        ) as response:
            print(f"CORS preflight response status: {response.status}")
            print(f"CORS preflight response headers: {dict(response.headers)}")

            # Should return 400 when origin is not in allow_origins (empty list blocks all)
            assert response.status == 400
            # Should NOT allow any origin with empty default
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            assert cors_origin is None


@pytest.mark.asyncio
async def test_cors_preflight_any_origin_blocked(http_server):
    """Test CORS preflight request - all origins should be blocked with empty default."""
    async with aiohttp.ClientSession() as session:
        async with session.options(
            "http://127.0.0.1:8001/mcp/",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        ) as response:
            # Should return 400 when origin is blocked by empty allow_origins
            assert response.status == 400
            # Should not include CORS allow origin header for any origin
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            assert cors_origin is None


@pytest.mark.asyncio
async def test_cors_preflight_malicious_origin_blocked(http_server):
    """Test CORS preflight request with malicious origin (should be blocked)."""
    async with aiohttp.ClientSession() as session:
        async with session.options(
            "http://127.0.0.1:8001/mcp/",
            headers={
                "Origin": "http://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        ) as response:
            print(f"Malicious origin response status: {response.status}")
            print(f"Malicious origin response headers: {dict(response.headers)}")

            # Should return 400 when malicious origin is blocked
            assert response.status == 400
            # Should not include CORS headers for any origins (empty default)
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            assert cors_origin is None


@pytest.mark.asyncio
async def test_cors_actual_request_no_cors_headers(http_server):
    """Test actual request without Origin header (should work - not CORS)."""
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
            assert response.status == 200
            # No Origin header means no CORS, request should work
            result = await parse_sse_response(response)
            assert "result" in result
            assert "tools" in result["result"]


@pytest.mark.asyncio
async def test_cors_actual_request_with_origin_blocked(http_server):
    """Test actual CORS request with origin header (should work but no CORS headers)."""
    session_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Origin": "http://localhost:3000",
                "mcp-session-id": session_id,
            },
        ) as response:
            # Request should still work (server processes it) but no CORS headers
            assert response.status == 200
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            assert cors_origin is None

            result = await parse_sse_response(response)
            assert "result" in result
            assert "tools" in result["result"]


@pytest.mark.asyncio
async def test_cors_restricted_server_allowed_origin(http_server_restricted_cors):
    """Test CORS with restricted server and allowed origin."""
    async with aiohttp.ClientSession() as session:
        async with session.options(
            "http://127.0.0.1:8003/mcp/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        ) as response:
            print(
                f"Restricted server allowed origin response status: {response.status}"
            )
            print(
                f"Restricted server allowed origin response headers: {dict(response.headers)}"
            )

            assert response.status == 200
            assert "Access-Control-Allow-Origin" in response.headers
            assert (
                response.headers["Access-Control-Allow-Origin"]
                == "http://localhost:3000"
            )


@pytest.mark.asyncio
async def test_cors_restricted_server_disallowed_origin(http_server_restricted_cors):
    """Test CORS with restricted server and disallowed origin."""
    async with aiohttp.ClientSession() as session:
        async with (
            session.options(
                "http://127.0.0.1:8003/mcp/",
                headers={
                    "Origin": "http://127.0.0.1:3000",  # This should be disallowed on restricted server
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            ) as response
        ):
            print(
                f"Restricted server disallowed origin response status: {response.status}"
            )
            print(
                f"Restricted server disallowed origin response headers: {dict(response.headers)}"
            )

            # Should return 400 when origin is not in restricted allow_origins list
            assert response.status == 400
            # Should not allow 127.0.0.1 on restricted server
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            assert cors_origin is None


@pytest.mark.asyncio
async def test_cors_restricted_server_trusted_site(http_server_restricted_cors):
    """Test CORS with restricted server and trusted site origin."""
    async with aiohttp.ClientSession() as session:
        async with session.options(
            "http://127.0.0.1:8003/mcp/",
            headers={
                "Origin": "https://trusted-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        ) as response:
            assert response.status == 200
            assert "Access-Control-Allow-Origin" in response.headers
            assert (
                response.headers["Access-Control-Allow-Origin"]
                == "https://trusted-site.com"
            )


@pytest.mark.asyncio
async def test_dns_rebinding_protection_trusted_hosts(http_server):
    """Test DNS rebinding protection with TrustedHostMiddleware - allowed hosts."""
    session_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        # Test with localhost - should be allowed (in default allowed_hosts)
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Host": "localhost:8001",
                "mcp-session-id": session_id,
            },
        ) as response:
            print(f"Trusted host (localhost) response status: {response.status}")
            print(
                f"Trusted host (localhost) response headers: {dict(response.headers)}"
            )

            # Should work with trusted host
            assert response.status == 200
            result = await parse_sse_response(response)
            assert "result" in result
            assert "tools" in result["result"]


@pytest.mark.asyncio
async def test_dns_rebinding_protection_untrusted_hosts(http_server):
    """Test DNS rebinding protection with TrustedHostMiddleware - untrusted hosts."""
    session_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        # Test with malicious host - should be blocked
        async with session.post(
            "http://127.0.0.1:8001/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Host": "malicious-site.evil",
                "mcp-session-id": session_id,
            },
        ) as response:
            print(f"Untrusted host response status: {response.status}")
            print(f"Untrusted host response headers: {dict(response.headers)}")

            # Should block untrusted host (DNS rebinding protection)
            assert response.status == 400


@pytest.mark.asyncio
async def test_dns_rebinding_custom_allowed_hosts(http_server_custom_hosts):
    """Test DNS rebinding protection with custom allowed hosts configuration."""
    session_id = str(uuid.uuid4())
    async with aiohttp.ClientSession() as session:
        # Test with custom allowed host - should work
        async with session.post(
            "http://127.0.0.1:8004/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Host": "example.com",
                "mcp-session-id": session_id,
            },
        ) as response:
            print(
                f"Custom allowed host (example.com) response status: {response.status}"
            )
            print(f"Custom allowed host response headers: {dict(response.headers)}")

            # Should work with custom allowed host
            assert response.status == 200
            result = await parse_sse_response(response)
            assert "result" in result
            assert "tools" in result["result"]

        # Test with another custom allowed host with port - should work
        async with session.post(
            "http://127.0.0.1:8004/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Host": "test.local:8004",
                "mcp-session-id": session_id,
            },
        ) as response:
            print(
                f"Custom allowed host (test.local:8004) response status: {response.status}"
            )
            print(f"Custom allowed host response headers: {dict(response.headers)}")

            # Should work with custom allowed host
            assert response.status == 200
            result = await parse_sse_response(response)
            assert "result" in result
            assert "tools" in result["result"]

        # Test with localhost (not in custom allowed list) - should be blocked
        async with session.post(
            "http://127.0.0.1:8004/mcp/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Host": "localhost:8004",
                "mcp-session-id": session_id,
            },
        ) as response:
            print(
                f"Localhost (not in custom allowed) response status: {response.status}"
            )
            print(f"Localhost response headers: {dict(response.headers)}")

            # Should block localhost when not in custom allowed hosts
            assert response.status == 400
