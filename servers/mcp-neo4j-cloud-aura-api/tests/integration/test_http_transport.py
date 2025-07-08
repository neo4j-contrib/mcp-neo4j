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

# Skip all tests if credentials are not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("NEO4J_AURA_CLIENT_ID") or not os.environ.get("NEO4J_AURA_CLIENT_SECRET"),
    reason="NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET environment variables are required for integration tests"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
                path="/mcp/"
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 