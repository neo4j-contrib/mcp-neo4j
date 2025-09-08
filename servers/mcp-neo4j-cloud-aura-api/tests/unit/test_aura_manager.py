import os
import pytest
from unittest.mock import patch, MagicMock

from mcp_neo4j_aura_manager.aura_api_client import AuraAPIClient
from mcp_neo4j_aura_manager.aura_manager import AuraManager

# Mock responses for testing
MOCK_INSTANCES = {
    "data": [
        {
            "id": "instance-1",
            "name": "Test Instance 1",
            "memory": 4,
            "status": "running",
            "region": "us-east-1",
            "version": "5.15",
            "type": "enterprise",
            "vector_optimized": False
        },
        {
            "id": "instance-2",
            "name": "Test Instance 2",
            "memory": 8,
            "status": "paused",
            "region": "eu-west-1",
            "version": "5.15",
            "type": "enterprise",
            "vector_optimized": True
        }
    ]
}

MOCK_TENANTS = {
    "data": [
        {
            "id": "tenant-1",
            "name": "Test Tenant 1",
            "type": "free"
        },
        {
            "id": "tenant-2",
            "name": "Test Tenant 2",
            "type": "professional"
        }
    ]
}

MOCK_TENANT_DETAILS = {
    "data": {
        "id": "tenant-1",
        "name": "Test Tenant 1",
        "instance_configurations": [
            {
                "cloud_provider": "gcp",
                "memory": "8GB",
                "region": "europe-west1",
                "region_name": "Belgium (europe-west1)",
                "storage": "16GB",
                "type": "professional-ds",
                "version": "5"
            }
        ]
    }
}


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        
    def json(self):
        return self.json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


@pytest.fixture
def mock_client():
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.patch') as mock_patch:
                
        # Set up different responses based on URL
        def get_side_effect(url, headers=None, **kwargs):
            if "/instances" in url and not url.split("/instances")[1]:
                return MockResponse(MOCK_INSTANCES)
            elif "/instances/instance-1" in url:
                return MockResponse({"data":MOCK_INSTANCES["data"][0]})
            elif "/instances/instance-2" in url:
                return MockResponse({"data":MOCK_INSTANCES["data"][1]})
            elif "/tenants" in url and not url.split("/tenants")[1]:
                return MockResponse(MOCK_TENANTS)
            elif "/tenants/tenant-1" in url:
                return MockResponse(MOCK_TENANT_DETAILS)
            else:
                return MockResponse({"error": "Not found"}, 404)
        
        mock_get.side_effect = get_side_effect
        
        # Set up different responses based on URL for POST requests
        def post_side_effect(url, headers=None, **kwargs):
            if "/oauth/token" in url:
                return MockResponse({
                    "access_token": "fake-token",
                    "token_type": "bearer", 
                    "expires_in": 3600,
                })
            elif "/instances" in url and not url.split("/instances")[1]:
                # Creating new instance
                return MockResponse({"data": MOCK_INSTANCES["data"][0]})
            elif "/pause" in url:
                return MockResponse({"data": {"status": "paused"}})
            elif "/resume" in url:
                return MockResponse({"data": {"status": "running"}})
            else:
                return MockResponse({"error": "Not found"}, 404)
                
        mock_post.side_effect = post_side_effect
        mock_patch.return_value = MockResponse({"status": "updated"})
        
        client = AuraAPIClient("fake-id", "fake-secret")
        yield client


@pytest.mark.asyncio
async def test_list_instances(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.list_instances()
    assert "instances" in result
    assert len(result["instances"]) == 2
    assert result["count"] == 2


@pytest.mark.asyncio
async def test_get_instance_details(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    mock_client.get_instance_details = MagicMock(return_value=[
        MOCK_INSTANCES["data"][0]
    ])
    manager.client = mock_client
    
    result = await manager.get_instance_details(["instance-1"])
    assert result["count"] == 1

    assert result["instances"][0]["id"] == "instance-1"
    assert result["instances"][0]["name"] == "Test Instance 1"


@pytest.mark.asyncio
async def test_get_instance_details_multiple(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the get_instance_details method to return a list
    mock_client.get_instance_details = MagicMock(return_value=[
        MOCK_INSTANCES["data"][0],
        MOCK_INSTANCES["data"][1]
    ])
    
    result = await manager.get_instance_details(["instance-1", "instance-2"])
    assert "instances" in result
    assert result["count"] == 2
    assert result["instances"][0]["id"] == "instance-1"
    assert result["instances"][1]["id"] == "instance-2"


@pytest.mark.asyncio
async def test_get_instance_by_name(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the get_instance_by_name method
    mock_client.get_instance_by_name = MagicMock(return_value=MOCK_INSTANCES["data"][0])
    
    result = await manager.get_instance_by_name("Test Instance 1")
    assert result["id"] == "instance-1"
    assert result["name"] == "Test Instance 1"

@pytest.mark.asyncio
async def test_get_instance_by_name_substring(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the get_instance_by_name method
    mock_client.get_instance_by_name = MagicMock(return_value=MOCK_INSTANCES["data"][0])
    
    result = await manager.get_instance_by_name("Instance 1")
    assert result["id"] == "instance-1"
    assert result["name"] == "Test Instance 1"

@pytest.mark.asyncio
async def test_get_instance_by_name_lower(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the get_instance_by_name method
    mock_client.get_instance_by_name = MagicMock(return_value=MOCK_INSTANCES["data"][0])
    
    result = await manager.get_instance_by_name("test instance")
    assert result["id"] == "instance-1"
    assert result["name"] == "Test Instance 1"


@pytest.mark.asyncio
async def test_list_tenants(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.list_tenants()
    assert "tenants" in result
    assert len(result["tenants"]) == 2
    assert result["count"] == 2


@pytest.mark.asyncio
async def test_error_handling(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock an error
    mock_client.get_instance_details = MagicMock(side_effect=Exception("Test error"))
    
    result = await manager.get_instance_details(["non-existent"])
    assert "error" in result
    assert "Test error" in result["error"]


@pytest.mark.asyncio
async def test_get_tenant_details(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.get_tenant_details("tenant-1")
    print(result)
    assert result["id"] == "tenant-1"
    assert "instance_configurations" in result
    assert len(result["instance_configurations"]) > 0


@pytest.mark.asyncio
async def test_pause_instance(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the pause_instance method
    mock_client.pause_instance = MagicMock(return_value={"status": "paused"})
    
    result = await manager.pause_instance("instance-1")
    assert result["status"] == "paused"

@pytest.mark.asyncio
async def test_update_instance_name(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the update_instance method
    mock_client.update_instance = MagicMock(return_value={"name": "New Name", "id": "instance-1"})
    
    result = await manager.update_instance_name("instance-1", "New Name")
    assert result["name"] == "New Name"
    assert result["id"] == "instance-1"

@pytest.mark.asyncio
async def test_create_instance(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the create_instance method
    mock_client.create_instance = MagicMock(return_value={
        "id": "new-instance-1",
        "name": "New Test Instance",
        "status": "creating"
    })
    
    result = await manager.create_instance(
        tenant_id="tenant-1",
        name="New Test Instance",
        memory=1,
        region="us-central1",
        type="free-db"
    )
    
    assert result["id"] == "new-instance-1"
    assert result["name"] == "New Test Instance"
    assert result["status"] == "creating"
    
    # Verify the mock was called with the correct parameters
    mock_client.create_instance.assert_called_once_with(
        tenant_id="tenant-1",
        name="New Test Instance",
        memory=1,
        region="us-central1",
        version="5",
        type="free-db",
        vector_optimized=False,
        cloud_provider="gcp",
        graph_analytics_plugin=False,
        source_instance_id=None
    )


@pytest.mark.asyncio
async def test_delete_instance(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the delete_instance method
    mock_client.delete_instance = MagicMock(return_value={"status": "deleted", "id": "instance-1"})
    
    result = await manager.delete_instance(instance_id="instance-1")
    assert result["id"] == "instance-1"
    
    # Verify the mock was called with the correct parameters
    mock_client.delete_instance.assert_called_once_with("instance-1")


@pytest.mark.asyncio
async def test_update_instance_name(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the update_instance method
    mock_client.update_instance = MagicMock(return_value={"name": "New Name", "id": "instance-1"})
    
    result = await manager.update_instance_name("instance-1", "New Name")
    assert result["name"] == "New Name"
    assert result["id"] == "instance-1"
    
    # Verify the mock was called with the correct parameters
    mock_client.update_instance.assert_called_once_with(instance_id="instance-1", name="New Name")


@pytest.mark.asyncio
async def test_pause_instance(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the pause_instance method
    mock_client.pause_instance = MagicMock(return_value={"status": "paused"})
    
    result = await manager.pause_instance("instance-1")
    assert result["status"] == "paused"
    
    # Verify the mock was called with the correct parameters
    mock_client.pause_instance.assert_called_once_with("instance-1")


@pytest.mark.asyncio
async def test_resume_instance(mock_client):
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Mock the resume_instance method
    mock_client.resume_instance = MagicMock(return_value={"status": "running"})
    
    result = await manager.resume_instance("instance-1")
    assert result["status"] == "running"
    
    # Verify the mock was called with the correct parameters
    mock_client.resume_instance.assert_called_once_with("instance-1")
