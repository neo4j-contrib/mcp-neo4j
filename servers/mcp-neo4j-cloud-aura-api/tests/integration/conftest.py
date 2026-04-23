import os
import pytest
import asyncio
import threading
import time
from typing import Dict, AsyncGenerator

# Skip only tests that require real Aura credentials
def pytest_collection_modifyitems(config, items):
    skip_marker = pytest.mark.skip(reason="NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET environment variables are required for integration tests")

    for item in items:
        # Skip only TestAuraManagerRealAPI class tests if credentials are missing
        if (not os.environ.get("NEO4J_AURA_CLIENT_ID") or not os.environ.get("NEO4J_AURA_CLIENT_SECRET")):
            # Check if this test is in the TestAuraManagerRealAPI class
            if hasattr(item, 'parent') and hasattr(item.parent, 'name'):
                if "TestAuraManagerRealAPI" in item.parent.name:
                    item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def aura_credentials() -> Dict[str, str]:
    """Get Aura API credentials from environment variables."""
    client_id = os.environ.get("NEO4J_AURA_CLIENT_ID")
    client_secret = os.environ.get("NEO4J_AURA_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        pytest.skip("NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET environment variables are required")
    
    return {
        "client_id": client_id,
        "client_secret": client_secret
    }


@pytest.fixture(scope="session")
def test_tenant_id(aura_credentials) -> str:
    """Get a test tenant ID for integration tests."""
    from mcp_neo4j_aura_manager.server import AuraAPIClient
    
    client = AuraAPIClient(aura_credentials["client_id"], aura_credentials["client_secret"])
    tenants = client.list_tenants()
    
    if len(tenants) == 0:
        pytest.skip("No tenants available for testing")
    
    # Look for a test tenant or use the first one
    for tenant in tenants:
        if "test" in tenant.get("name", "").lower():
            return tenant["id"]
    
    # Return the first tenant if no test tenant found
    return tenants[0]["id"]


@pytest.fixture(scope="session")
def test_instance_id(aura_credentials) -> str:
    """Get a test instance ID for integration tests."""
    from mcp_neo4j_aura_manager.server import AuraAPIClient
    
    client = AuraAPIClient(aura_credentials["client_id"], aura_credentials["client_secret"])
    instances = client.list_instances()
    
    if len(instances) == 0:
        pytest.skip("No instances available for testing")
    
    # Look for a test instance or use the first one
    for instance in instances:
        if "test" in instance.get("name", "").lower():
            return instance["id"]
    
    # Return the first instance if no test instance found
    return instances[0]["id"]


# Middleware test fixtures (independent of Aura credentials)

@pytest.fixture(scope="session")
def middleware_test_server() -> Dict[str, str]:
    """Start the Aura Manager MCP server for middleware testing with dummy credentials."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

    from mcp_neo4j_aura_manager.server import main

    server_url = "http://127.0.0.1:8005/mcp/"

    try:
        def run_server():
            asyncio.run(main(
                client_id="test-client-id",  # Dummy credentials for middleware testing
                client_secret="test-client-secret",
                transport="http",
                host="127.0.0.1",
                port=8005,
                path="/mcp/",
                allow_origins=[],  # Empty by default for security testing
                allowed_hosts=["localhost", "127.0.0.1"],
                namespace=""  # Add namespace parameter
            ))

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Wait for server to start
        time.sleep(3)

        return {"url": server_url}

    finally:
        # Thread will be cleaned up automatically as it's a daemon thread
        pass


@pytest.fixture(scope="session")
def middleware_test_server_restricted_cors() -> Dict[str, str]:
    """Start the Aura Manager MCP server with restricted CORS for testing."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

    from mcp_neo4j_aura_manager.server import main

    server_url = "http://127.0.0.1:8006/mcp/"

    try:
        def run_server():
            asyncio.run(main(
                client_id="test-client-id",  # Dummy credentials
                client_secret="test-client-secret",
                transport="http",
                host="127.0.0.1",
                port=8006,
                path="/mcp/",
                allow_origins=["http://localhost:3000", "https://trusted-site.com"],
                allowed_hosts=["localhost", "127.0.0.1"],
                namespace=""  # Add namespace parameter
            ))

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Wait for server to start
        time.sleep(3)

        return {"url": server_url}

    finally:
        # Thread will be cleaned up automatically as it's a daemon thread
        pass 