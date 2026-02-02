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


@pytest.mark.asyncio
async def test_calculate_database_sizing_basic(mock_client):
    """Test calculate_database_sizing with basic parameters."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.calculate_database_sizing(
        num_nodes=100000,
        num_relationships=500000,
        avg_properties_per_node=5,
        avg_properties_per_relationship=2,
    )
    
    # Should return a dict with calculations and metadata
    assert isinstance(result, dict)
    assert "calculations" in result
    assert "metadata" in result
    assert result["calculations"]["total_size_with_indexes_gb"] > 0
    assert result["metadata"]["calculator_type"] == "Neo4jSizingCalculator"
    assert "recommended_memory_gb" in result["calculations"]
    assert "recommended_vcpus" in result["calculations"]


@pytest.mark.asyncio
async def test_calculate_database_sizing_with_all_params(mock_client):
    """Test calculate_database_sizing with all optional parameters."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.calculate_database_sizing(
        num_nodes=100000,
        num_relationships=500000,
        avg_properties_per_node=5,
        avg_properties_per_relationship=2,
        total_num_large_node_properties=1000,
        total_num_large_reltype_properties=500,
        vector_index_dimensions=768,
        percentage_nodes_with_vector_properties=50.0,
        number_of_vector_indexes=1,
        quantization_enabled=True,
        memory_to_storage_ratio=2.0,
        concurrent_end_users=10,
    )
    
    assert isinstance(result, dict)
    assert "calculations" in result
    assert "metadata" in result
    assert result["calculations"]["size_of_vector_indexes_gb"] > 0
    assert result["metadata"]["calculation_config"]["quantization_enabled"] is True
    assert result["metadata"]["calculation_config"]["vector_index_dimensions"] == 768
    # With memory_to_storage_ratio=2.0, memory should be calculated
    assert result["calculations"]["recommended_memory_gb"] > 0
    # With concurrent_end_users=10, vCPUs should be 20 (2 per user)
    assert result["calculations"]["recommended_vcpus"] == 20


@pytest.mark.asyncio
async def test_calculate_database_sizing_error_handling(mock_client):
    """Test calculate_database_sizing error handling."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Should raise ValueError for negative nodes
    with pytest.raises(ValueError, match="num_nodes must be non-negative"):
        await manager.calculate_database_sizing(
            num_nodes=-1,
            num_relationships=100,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
        )


@pytest.mark.asyncio
async def test_calculate_database_sizing_returns_dict(mock_client):
    """Test that calculate_database_sizing returns a dict (not Pydantic model)."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.calculate_database_sizing(
        num_nodes=1000,
        num_relationships=5000,
        avg_properties_per_node=5,
        avg_properties_per_relationship=2,
    )
    
    # Should be a dict, not a Pydantic model
    assert isinstance(result, dict)
    # Should be JSON serializable
    import json
    json_str = json.dumps(result)
    assert json_str is not None


@pytest.mark.asyncio
async def test_forecast_database_size_basic(mock_client):
    """Test forecast_database_size with basic parameters."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.forecast_database_size(
        base_size_gb=100.0,
        base_memory_gb=64,
        base_cores=8,
        domain="customer",
    )
    
    # Should return a dict with projections
    assert isinstance(result, dict)
    assert "base_size_gb" in result
    assert "base_memory_gb" in result
    assert "base_cores" in result
    assert "projections" in result
    assert "growth_model_used" in result
    assert len(result["projections"]) == 3  # Default projection_years
    assert result["base_size_gb"] == 100.0
    assert result["base_memory_gb"] == 64
    assert result["base_cores"] == 8


@pytest.mark.asyncio
async def test_forecast_database_size_with_all_params(mock_client):
    """Test forecast_database_size with all optional parameters."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.forecast_database_size(
        base_size_gb=100.0,
        base_memory_gb=64,
        base_cores=8,
        annual_growth_rate=15.0,
        projection_years=5,
        workloads=["transactional", "agentic"],
        domain="customer",
        memory_to_storage_ratio=4.0,
    )
    
    assert isinstance(result, dict)
    assert len(result["projections"]) == 5
    assert result["growth_model_used"] is not None
    # Projections should show growth
    assert result["projections"][0]["total_size_gb"] > result["base_size_gb"]
    assert result["projections"][1]["total_size_gb"] > result["projections"][0]["total_size_gb"]


@pytest.mark.asyncio
async def test_forecast_database_size_with_workloads(mock_client):
    """Test forecast_database_size with workload types."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.forecast_database_size(
        base_size_gb=100.0,
        base_memory_gb=64,
        base_cores=8,
        domain="generic",
        workloads=["transactional"],
    )
    
    # Transactional should use LogLinearGrowthModel
    assert "LogLinear" in result["growth_model_used"]


@pytest.mark.asyncio
async def test_forecast_database_size_with_domain(mock_client):
    """Test forecast_database_size with domain."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.forecast_database_size(
        base_size_gb=100.0,
        base_memory_gb=64,
        base_cores=8,
        domain="customer",
    )
    
    # Customer domain defaults to transactional + analytical -> LogLinear
    assert "LogLinear" in result["growth_model_used"]


@pytest.mark.asyncio
async def test_forecast_database_size_error_handling(mock_client):
    """Test forecast_database_size error handling."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    # Should raise ValueError for negative base_size_gb
    with pytest.raises(ValueError, match="base_size_gb must be non-negative"):
        await manager.forecast_database_size(
            base_size_gb=-1.0,
            base_memory_gb=64,
            base_cores=8,
            domain="customer",
        )
    
    # Should raise ValueError for invalid projection_years
    with pytest.raises(ValueError, match="projection_years must be at least 1"):
        await manager.forecast_database_size(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            domain="customer",
            projection_years=0,
        )


@pytest.mark.asyncio
async def test_forecast_database_size_returns_dict(mock_client):
    """Test that forecast_database_size returns a dict (not Pydantic model)."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.forecast_database_size(
        base_size_gb=100.0,
        base_memory_gb=64,
        base_cores=8,
        domain="customer",
    )
    
    # Should be a dict, not a Pydantic model
    assert isinstance(result, dict)
    # Should be JSON serializable
    import json
    json_str = json.dumps(result)
    assert json_str is not None


@pytest.mark.asyncio
async def test_forecast_database_size_memory_scaling(mock_client):
    """Test that forecast_database_size scales memory with storage ratio."""
    manager = AuraManager("fake-id", "fake-secret")
    manager.client = mock_client
    
    result = await manager.forecast_database_size(
        base_size_gb=100.0,
        base_memory_gb=64,
        base_cores=8,
        domain="customer",
        annual_growth_rate=10.0,
        projection_years=3,
        memory_to_storage_ratio=2,  # 1:2 ratio (integer)
    )
    
    # Memory should scale with projected size
    # First projection should have memory >= base_memory_gb
    assert result["projections"][0]["recommended_memory_gb"] >= result["base_memory_gb"]
    # As size grows, memory should increase
    if result["projections"][2]["total_size_gb"] > result["projections"][0]["total_size_gb"]:
        assert result["projections"][2]["recommended_memory_gb"] >= result["projections"][0]["recommended_memory_gb"]
