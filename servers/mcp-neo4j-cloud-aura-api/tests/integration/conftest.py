import os
import pytest
from typing import Dict, Any

# Skip all tests if credentials are not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("NEO4J_AURA_CLIENT_ID") or not os.environ.get("NEO4J_AURA_CLIENT_SECRET"),
    reason="NEO4J_AURA_CLIENT_ID and NEO4J_AURA_CLIENT_SECRET environment variables are required for integration tests"
)


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