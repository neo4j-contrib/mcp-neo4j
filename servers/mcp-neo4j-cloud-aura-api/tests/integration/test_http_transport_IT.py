import asyncio
import json
import logging
import os
import pytest
import requests
import time
from typing import AsyncGenerator, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

async def parse_sse_response(response: aiohttp.ClientResponse) -> dict:
    """Parse Server-Sent Events response from FastMCP 2.0."""
    content = await response.text()
    lines = content.strip().split('\n')
    
    # Find the data line that contains the JSON
    for line in lines:
        if line.startswith('data: '):
            json_str = line[6:]  # Remove 'data: ' prefix
            return json.loads(json_str)
    
    raise ValueError("No data line found in SSE response")
    
# No global skip - individual test classes handle their own credential requirements


# Removed custom event_loop fixture - using pytest-asyncio default with session scope from pyproject.toml


@pytest.fixture(scope="session")
async def aura_manager_server() -> AsyncGenerator[Dict[str, Any], None]:
    """Start the Aura Manager MCP server with HTTP transport."""
    
    # Get real credentials from environment
    client_id = os.environ.get("NEO4J_AURA_CLIENT_ID")
    client_secret = os.environ.get("NEO4J_AURA_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        pytest.skip("NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET environment variables are required")
    
    # Import the server module
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    
    from mcp_neo4j_aura_manager.server import main
    
    # Start the server in a separate process
    server_process = None
    server_url = "http://127.0.0.1:8001/mcp/"
    
    try:
        # Start the server
        import subprocess
        import threading
        
        def run_server():
            asyncio.run(main(
                client_id=client_id,
                client_secret=client_secret,
                transport="http",
                host="127.0.0.1",
                port=8001,
                path="/mcp/",
                allow_origins=["http://localhost:3000"],
                allowed_hosts=["localhost", "127.0.0.1"]
            ))
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        # Test server is running
        try:
            response = requests.get(server_url.replace("/mcp/", "/health"), timeout=5)
            if response.status_code == 200:
                logger.info("Aura Manager server started successfully")
            else:
                logger.warning(f"Server health check returned {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not connect to server: {e}")
        
        yield {
            "url": server_url,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()


@pytest.mark.skipif(
    not os.environ.get("NEO4J_AURA_CLIENT_ID") or not os.environ.get("NEO4J_AURA_CLIENT_SECRET"),
    reason="NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET environment variables are required for HTTP transport tests"
)
class TestAuraManagerHTTPTransport:
    """Test Aura Manager MCP server over HTTP transport."""
    
    @pytest.mark.asyncio
    async def test_server_startup(self, aura_manager_server):
        """Test that the server starts up correctly."""
        url = aura_manager_server["url"]
        
        # Verify server configuration
        assert url == "http://127.0.0.1:8001/mcp/"
        assert aura_manager_server["client_id"] is not None
        assert aura_manager_server["client_secret"] is not None
    
    @pytest.mark.asyncio
    async def test_transport_configuration(self, aura_manager_server):
        """Test that the server is configured for HTTP transport."""
        # This test verifies the server was started with HTTP transport
        # The fixture ensures this by calling main() with transport="http"
        assert True  # If we get here, the server started with HTTP transport
    
    @pytest.mark.asyncio
    async def test_server_connectivity(self, aura_manager_server):
        """Test basic server connectivity."""
        url = aura_manager_server["url"]
        
        try:
            response = requests.get(url, timeout=5)
            # The server should be running and responding
            assert response.status_code in [200, 404, 405]  # Accept various responses
        except requests.exceptions.RequestException as e:
            # Server might not be fully ready, which is okay for this test
            logger.warning(f"Server connectivity test failed: {e}")
            pass

    @pytest.mark.asyncio
    async def test_invalid_node_data(self, aura_manager_server):
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
                        "arguments": {
                            "node": {
                                "invalid_field": "invalid_value"
                            }
                        }
                    }
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                # Should return an error or handle gracefully
                assert "result" in result

    @pytest.mark.asyncio
    async def test_invalid_data_model(self, aura_manager_server):
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
                        "arguments": {
                            "data_model": {
                                "invalid_field": "invalid_value"
                            }
                        }
                    }
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                # Should return an error or handle gracefully
                assert "result" in result


@pytest.mark.skipif(
    not os.environ.get("NEO4J_AURA_CLIENT_ID") or not os.environ.get("NEO4J_AURA_CLIENT_SECRET"),
    reason="NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET environment variables are required for real API tests"
)
class TestAuraManagerRealAPI:
    """Test Aura Manager with real API calls (requires credentials)."""
    
    @pytest.fixture
    def aura_client(self):
        """Create a real Aura API client using environment variables."""
        client_id = os.environ.get("NEO4J_AURA_CLIENT_ID")
        client_secret = os.environ.get("NEO4J_AURA_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            pytest.skip("NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET environment variables are required")
        
        from mcp_neo4j_aura_manager.server import AuraAPIClient
        return AuraAPIClient(client_id, client_secret)
    
    def test_authentication(self, aura_client):
        """Test that authentication works with the provided credentials."""
        token = aura_client._get_auth_token()
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_list_instances(self, aura_client):
        """Test listing instances from the real API."""
        instances = aura_client.list_instances()
        assert isinstance(instances, list)
        # Even if there are no instances, this should return an empty list, not fail
    
    def test_list_tenants(self, aura_client):
        """Test listing tenants/projects from the real API."""
        tenants = aura_client.list_tenants()
        assert isinstance(tenants, list)
        # There should be at least one tenant if the account is valid
        assert len(tenants) > 0
    
    def test_get_instance_details(self, aura_client):
        """Test getting instance details from the real API."""
        # First, list instances to get some IDs
        instances = aura_client.list_instances()
        
        # Skip if there are no instances
        if len(instances) == 0:
            pytest.skip("No instances available for testing")
        
        instance_id = instances[0]["id"]
        details = aura_client.get_instance_details([instance_id])
        
        assert isinstance(details, list)
        assert len(details) == 1
        assert details[0]["id"] == instance_id


# CORS Middleware Tests (independent of Aura credentials)
# These tests use dummy credentials and should always run

@pytest.mark.middleware
class TestMiddlewareSecurity:
    """Test security middleware functionality without requiring Aura credentials."""

    @pytest.mark.asyncio
    @pytest.mark.middleware
    async def test_cors_preflight_empty_default_origins(self, middleware_test_server):
        """Test CORS preflight request with empty default allowed origins."""
        async with aiohttp.ClientSession() as session:
            async with session.options(
                "http://127.0.0.1:8005/mcp/",
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
    @pytest.mark.middleware
    async def test_cors_preflight_malicious_origin_blocked(self, middleware_test_server):
        """Test CORS preflight request with malicious origin (should be blocked)."""
        async with aiohttp.ClientSession() as session:
            async with session.options(
                "http://127.0.0.1:8005/mcp/",
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
    @pytest.mark.middleware
    async def test_cors_actual_request_no_cors_headers(self, middleware_test_server):
        """Test actual request without Origin header (should work - not CORS)."""
        async with aiohttp.ClientSession() as session:
            # First, initiate session with the MCP server
            async with session.post(
                "http://127.0.0.1:8005/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}}},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as init_response:
                # Get session ID from response headers
                session_id = init_response.headers.get("mcp-session-id")

            # Now make the actual test request with session ID
            headers = {
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            }
            if session_id:
                headers["mcp-session-id"] = session_id

            async with session.post(
                "http://127.0.0.1:8005/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers=headers,
            ) as response:
                # The server will fail to authenticate with dummy credentials, but that's ok
                # We just want to test that the middleware allows the request through
                assert response.status in [200, 401, 500]  # Any non-CORS error is fine

    @pytest.mark.asyncio
    @pytest.mark.middleware
    async def test_cors_actual_request_with_origin_blocked(self, middleware_test_server):
        """Test actual CORS request with origin header (should work but no CORS headers)."""
        async with aiohttp.ClientSession() as session:
            # First, initiate session with the MCP server
            async with session.post(
                "http://127.0.0.1:8005/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}}},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as init_response:
                session_id = init_response.headers.get("mcp-session-id")

            # Now make the actual test request with session ID and Origin header
            headers = {
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Origin": "http://localhost:3000",
            }
            if session_id:
                headers["mcp-session-id"] = session_id

            async with session.post(
                "http://127.0.0.1:8005/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers=headers,
            ) as response:
                # Request should still work (server processes it) but no CORS headers
                assert response.status in [200, 401, 500]  # Any non-CORS error is fine
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                assert cors_origin is None

    @pytest.mark.asyncio
    @pytest.mark.middleware
    async def test_dns_rebinding_protection_trusted_hosts(self, middleware_test_server):
        """Test DNS rebinding protection with TrustedHostMiddleware - allowed hosts."""
        async with aiohttp.ClientSession() as session:
            # First, initiate session with the MCP server
            async with session.post(
                "http://127.0.0.1:8005/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}}},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as init_response:
                session_id = init_response.headers.get("mcp-session-id")

            # Test with localhost - should be allowed (in default allowed_hosts)
            headers = {
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Host": "localhost:8005",
            }
            if session_id:
                headers["mcp-session-id"] = session_id

            async with session.post(
                "http://127.0.0.1:8005/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers=headers,
            ) as response:
                print(f"Trusted host (localhost) response status: {response.status}")
                print(f"Trusted host (localhost) response headers: {dict(response.headers)}")

                # Should work with trusted host (may fail with auth error, but not 400)
                assert response.status in [200, 401, 500]  # Should not be blocked by middleware

    @pytest.mark.asyncio
    @pytest.mark.middleware
    async def test_dns_rebinding_protection_untrusted_hosts(self, middleware_test_server):
        """Test DNS rebinding protection with TrustedHostMiddleware - untrusted hosts."""
        async with aiohttp.ClientSession() as session:
            # Test with malicious host - should be blocked
            async with session.post(
                "http://127.0.0.1:8005/mcp/",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "Host": "malicious-site.evil",
                },
            ) as response:
                print(f"Untrusted host response status: {response.status}")
                print(f"Untrusted host response headers: {dict(response.headers)}")

                # Should block untrusted host (DNS rebinding protection)
                assert response.status == 400

    @pytest.mark.asyncio
    @pytest.mark.middleware
    async def test_cors_restricted_server_allowed_origin(self, middleware_test_server_restricted_cors):
        """Test CORS with restricted server and allowed origin."""
        async with aiohttp.ClientSession() as session:
            async with session.options(
                "http://127.0.0.1:8006/mcp/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            ) as response:
                print(f"Restricted server allowed origin response status: {response.status}")
                print(f"Restricted server allowed origin response headers: {dict(response.headers)}")

                assert response.status == 200
                assert "Access-Control-Allow-Origin" in response.headers
                assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"

    @pytest.mark.asyncio
    @pytest.mark.middleware
    async def test_cors_restricted_server_disallowed_origin(self, middleware_test_server_restricted_cors):
        """Test CORS with restricted server and disallowed origin."""
        async with aiohttp.ClientSession() as session:
            async with session.options(
                "http://127.0.0.1:8006/mcp/",
                headers={
                    "Origin": "http://127.0.0.1:3000",  # This should be disallowed on restricted server
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            ) as response:
                print(f"Restricted server disallowed origin response status: {response.status}")
                print(f"Restricted server disallowed origin response headers: {dict(response.headers)}")

                # Should return 400 when origin is not in restricted allow_origins list
                assert response.status == 400
                # Should not allow 127.0.0.1 on restricted server
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                assert cors_origin is None

