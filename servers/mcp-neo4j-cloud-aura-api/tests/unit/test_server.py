import pytest
from unittest.mock import Mock, AsyncMock

from mcp_neo4j_aura_manager.server import format_namespace, create_mcp_server
from mcp_neo4j_aura_manager.aura_manager import AuraManager


class TestFormatNamespace:
    """Test the format_namespace function behavior."""

    def testformat_namespace_empty_string(self):
        """Test format_namespace with empty string returns empty string."""
        assert format_namespace("") == ""

    def testformat_namespace_no_hyphen(self):
        """Test format_namespace adds hyphen when not present."""
        assert format_namespace("myapp") == "myapp-"

    def testformat_namespace_with_hyphen(self):
        """Test format_namespace returns string as-is when hyphen already present."""
        assert format_namespace("myapp-") == "myapp-"

    def testformat_namespace_complex_name(self):
        """Test format_namespace with complex namespace names."""
        assert format_namespace("company.product") == "company.product-"
        assert format_namespace("app_v2") == "app_v2-"


class TestNamespacing:
    """Test namespacing functionality."""

    @pytest.fixture
    def mock_aura_manager(self):
        """Create a mock AuraManager for testing."""
        manager = Mock(spec=AuraManager)
        # Mock all the async methods that the tools will call
        manager.list_instances = AsyncMock(return_value={"instances": []})
        manager.get_instance_details = AsyncMock(return_value={"details": []})
        manager.get_instance_by_name = AsyncMock(return_value={"instance": None})
        manager.create_instance = AsyncMock(return_value={"instance_id": "test-id"})
        manager.update_instance_name = AsyncMock(return_value={"success": True})
        manager.update_instance_memory = AsyncMock(return_value={"success": True})
        manager.update_instance_vector_optimization = AsyncMock(return_value={"success": True})
        manager.pause_instance = AsyncMock(return_value={"success": True})
        manager.resume_instance = AsyncMock(return_value={"success": True})
        manager.list_tenants = AsyncMock(return_value={"tenants": []})
        manager.get_tenant_details = AsyncMock(return_value={"tenant": {}})
        manager.delete_instance = AsyncMock(return_value={"success": True})
        return manager

    @pytest.mark.asyncio
    async def test_namespace_tool_prefixes(self, mock_aura_manager):
        """Test that tools are correctly prefixed with namespace."""
        # Test with namespace
        namespaced_server = create_mcp_server(mock_aura_manager, namespace="test-ns")
        tools = await namespaced_server.get_tools()
        
        expected_tools = [
            "test-ns-list_instances",
            "test-ns-get_instance_details", 
            "test-ns-get_instance_by_name",
            "test-ns-create_instance",
            "test-ns-update_instance_name",
            "test-ns-update_instance_memory",
            "test-ns-update_instance_vector_optimization",
            "test-ns-pause_instance",
            "test-ns-resume_instance",
            "test-ns-list_tenants",
            "test-ns-get_tenant_details",
            "test-ns-delete_instance"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tools.keys(), f"Tool {expected_tool} not found in tools"

        # Test without namespace (default tools)
        default_server = create_mcp_server(mock_aura_manager)
        default_tools = await default_server.get_tools()
        
        expected_default_tools = [
            "list_instances",
            "get_instance_details",
            "get_instance_by_name", 
            "create_instance",
            "update_instance_name",
            "update_instance_memory",
            "update_instance_vector_optimization",
            "pause_instance",
            "resume_instance",
            "list_tenants",
            "get_tenant_details",
            "delete_instance"
        ]
        
        for expected_tool in expected_default_tools:
            assert expected_tool in default_tools.keys(), f"Default tool {expected_tool} not found"

    @pytest.mark.asyncio
    async def test_namespace_tool_functionality(self, mock_aura_manager):
        """Test that namespaced tools function correctly."""
        namespaced_server = create_mcp_server(mock_aura_manager, namespace="test")
        tools = await namespaced_server.get_tools()
        
        # Test that a namespaced tool exists and works
        list_tool = tools.get("test-list_instances")
        assert list_tool is not None
        
        # Call the tool function and verify it works
        result = await list_tool.fn()
        assert result == {"instances": []}
        mock_aura_manager.list_instances.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_namespace_isolation(self, mock_aura_manager):
        """Test that different namespaces create isolated tool sets."""
        server_a = create_mcp_server(mock_aura_manager, namespace="app-a")
        server_b = create_mcp_server(mock_aura_manager, namespace="app-b")
        
        tools_a = await server_a.get_tools()
        tools_b = await server_b.get_tools()
        
        # Verify app-a tools exist in server_a but not server_b
        assert "app-a-list_instances" in tools_a.keys()
        assert "app-a-list_instances" not in tools_b.keys()
        
        # Verify app-b tools exist in server_b but not server_a
        assert "app-b-list_instances" in tools_b.keys()
        assert "app-b-list_instances" not in tools_a.keys()
        
        # Verify both servers have the same number of tools
        assert len(tools_a) == len(tools_b)

    @pytest.mark.asyncio
    async def test_namespace_hyphen_handling(self, mock_aura_manager):
        """Test namespace hyphen handling edge cases."""
        # Namespace already ending with hyphen
        server_with_hyphen = create_mcp_server(mock_aura_manager, namespace="myapp-")
        tools_with_hyphen = await server_with_hyphen.get_tools()
        assert "myapp-list_instances" in tools_with_hyphen.keys()
        
        # Namespace without hyphen
        server_without_hyphen = create_mcp_server(mock_aura_manager, namespace="myapp")
        tools_without_hyphen = await server_without_hyphen.get_tools()
        assert "myapp-list_instances" in tools_without_hyphen.keys()
        
        # Both should result in identical tool names
        assert set(tools_with_hyphen.keys()) == set(tools_without_hyphen.keys())

    @pytest.mark.asyncio
    async def test_complex_namespace_names(self, mock_aura_manager):
        """Test complex namespace naming scenarios."""
        complex_namespaces = [
            "company.product",
            "app_v2", 
            "client-123",
            "test.env.staging"
        ]
        
        for namespace in complex_namespaces:
            server = create_mcp_server(mock_aura_manager, namespace=namespace)
            tools = await server.get_tools()
            
            # Verify tools are properly prefixed
            expected_tool = f"{namespace}-list_instances"
            assert expected_tool in tools.keys(), f"Tool {expected_tool} not found for namespace '{namespace}'"

    @pytest.mark.asyncio
    async def test_namespace_tool_count_consistency(self, mock_aura_manager):
        """Test that namespaced and default servers have the same number of tools."""
        default_server = create_mcp_server(mock_aura_manager)
        namespaced_server = create_mcp_server(mock_aura_manager, namespace="test")
        
        default_tools = await default_server.get_tools()
        namespaced_tools = await namespaced_server.get_tools()
        
        # Should have the same number of tools
        assert len(default_tools) == len(namespaced_tools)
        
        # Verify we have the expected number of tools (14 tools: 12 instance management + 2 sizing tools)
        assert len(default_tools) == 14
        assert len(namespaced_tools) == 14


class TestPrompts:
    """Test prompt functions for database sizing and forecasting."""

    @pytest.fixture
    def mock_aura_manager(self):
        """Create a mock AuraManager for testing."""
        manager = Mock(spec=AuraManager)
        # Mock all the async methods that the tools will call
        manager.list_instances = AsyncMock(return_value={"instances": []})
        manager.get_instance_details = AsyncMock(return_value={"details": []})
        manager.get_instance_by_name = AsyncMock(return_value={"instance": None})
        manager.create_instance = AsyncMock(return_value={"instance_id": "test-id"})
        manager.update_instance_name = AsyncMock(return_value={"success": True})
        manager.update_instance_memory = AsyncMock(return_value={"success": True})
        manager.update_instance_vector_optimization = AsyncMock(return_value={"success": True})
        manager.pause_instance = AsyncMock(return_value={"success": True})
        manager.resume_instance = AsyncMock(return_value={"success": True})
        manager.list_tenants = AsyncMock(return_value={"tenants": []})
        manager.get_tenant_details = AsyncMock(return_value={"tenant": {}})
        manager.delete_instance = AsyncMock(return_value={"success": True})
        return manager

    # Calculate Database Sizing Prompt Tests
    @pytest.mark.asyncio
    async def test_calculate_database_sizing_prompt_exists(self, mock_aura_manager):
        """Test that the calculate_database_sizing prompt exists."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        
        assert "calculate_database_sizing_prompt" in prompts.keys()
        prompt = prompts["calculate_database_sizing_prompt"]
        assert prompt is not None

    @pytest.mark.asyncio
    async def test_calculate_database_sizing_prompt_no_params(self, mock_aura_manager):
        """Test prompt with no parameters provided."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        prompt = prompts.get("calculate_database_sizing_prompt")
        assert prompt is not None
        
        # Call the prompt function with no arguments (all None)
        result = prompt.fn(
            num_nodes=None,
            num_relationships=None,
            avg_properties_per_node=None,
            avg_properties_per_relationship=None
        )
        
        # Should be a string
        assert isinstance(result, str)
        # Should mention missing required parameters
        assert "Missing required parameters" in result
        assert "num_nodes" in result
        assert "num_relationships" in result
        assert "avg_properties_per_node" in result
        assert "avg_properties_per_relationship" in result
        # Should say none provided yet or show all parameters as missing
        assert "None provided yet" in result or "num_nodes" in result

    @pytest.mark.asyncio
    async def test_calculate_database_sizing_prompt_some_params(self, mock_aura_manager):
        """Test prompt with some parameters provided."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        prompt = prompts.get("calculate_database_sizing_prompt")
        assert prompt is not None
        
        result = prompt.fn(
            num_nodes=1000,
            num_relationships=5000,
            avg_properties_per_node=5
        )
        
        # Should be a string
        assert isinstance(result, str)
        # Should show provided parameters
        assert "num_nodes: 1000" in result
        assert "num_relationships: 5000" in result
        assert "avg_properties_per_node: 5" in result
        # Should still mention missing avg_properties_per_relationship
        assert "avg_properties_per_relationship" in result

    @pytest.mark.asyncio
    async def test_calculate_database_sizing_prompt_all_required(self, mock_aura_manager):
        """Test prompt with all required parameters provided."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        prompt = prompts.get("calculate_database_sizing_prompt")
        assert prompt is not None
        
        result = prompt.fn(
            num_nodes=1000,
            num_relationships=5000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2
        )
        
        # Should be a string
        assert isinstance(result, str)
        # Should show all provided parameters
        assert "num_nodes: 1000" in result
        assert "num_relationships: 5000" in result
        assert "avg_properties_per_node: 5" in result
        assert "avg_properties_per_relationship: 2" in result
        # Should say all required parameters are provided
        assert "None - all required parameters are provided" in result or "all required parameters" in result.lower()

    @pytest.mark.asyncio
    async def test_calculate_database_sizing_prompt_with_optional_params(self, mock_aura_manager):
        """Test prompt with optional parameters provided."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        prompt = prompts.get("calculate_database_sizing_prompt")
        assert prompt is not None
        
        result = prompt.fn(
            num_nodes=1000,
            num_relationships=5000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
            vector_index_dimensions=768,
            percentage_nodes_with_vector_properties=50.0,
            memory_to_storage_ratio=2
        )
        
        # Should be a string
        assert isinstance(result, str)
        # Should show optional parameters
        assert "vector_index_dimensions: 768" in result
        assert "percentage_nodes_with_vector_properties: 50.0" in result
        assert "memory_to_storage_ratio: 2" in result

    # Forecast Database Size Prompt Tests
    @pytest.mark.asyncio
    async def test_forecast_database_size_prompt_exists(self, mock_aura_manager):
        """Test that the forecast_database_size prompt exists."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        
        assert "forecast_database_size_prompt" in prompts.keys()
        prompt = prompts["forecast_database_size_prompt"]
        assert prompt is not None

    @pytest.mark.asyncio
    async def test_forecast_database_size_prompt_no_params(self, mock_aura_manager):
        """Test prompt with no parameters provided."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        prompt = prompts.get("forecast_database_size_prompt")
        assert prompt is not None
        
        # Call the prompt function with no arguments (all None)
        result = prompt.fn(
            base_size_gb=None,
            base_memory_gb=None,
            base_cores=None
        )
        
        # Should be a string
        assert isinstance(result, str)
        # Should mention missing required parameters
        assert "Missing required parameters" in result
        assert "base_size_gb" in result
        assert "base_memory_gb" in result
        assert "base_cores" in result
        # Should say none provided yet or show all parameters as missing
        assert "None provided yet" in result or "base_size_gb" in result

    @pytest.mark.asyncio
    async def test_forecast_database_size_prompt_some_params(self, mock_aura_manager):
        """Test prompt with some parameters provided."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        prompt = prompts.get("forecast_database_size_prompt")
        assert prompt is not None
        
        result = prompt.fn(
            base_size_gb=100.0,
            base_memory_gb=50
        )
        
        # Should be a string
        assert isinstance(result, str)
        # Should show provided parameters
        assert "base_size_gb: 100.0" in result
        assert "base_memory_gb: 50" in result
        # Should still mention missing base_cores
        assert "base_cores" in result

    @pytest.mark.asyncio
    async def test_forecast_database_size_prompt_all_required(self, mock_aura_manager):
        """Test prompt with all required parameters provided."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        prompt = prompts.get("forecast_database_size_prompt")
        assert prompt is not None
        
        result = prompt.fn(
            base_size_gb=100.0,
            base_memory_gb=50,
            base_cores=4
        )
        
        # Should be a string
        assert isinstance(result, str)
        # Should show all provided parameters
        assert "base_size_gb: 100.0" in result
        assert "base_memory_gb: 50" in result
        assert "base_cores: 4" in result
        # Should say all required parameters are provided
        assert "None - all required parameters are provided" in result or "all required parameters" in result.lower()

    @pytest.mark.asyncio
    async def test_forecast_database_size_prompt_with_optional_params(self, mock_aura_manager):
        """Test prompt with optional parameters provided."""
        server = create_mcp_server(mock_aura_manager)
        prompts = await server.get_prompts()
        prompt = prompts.get("forecast_database_size_prompt")
        assert prompt is not None
        
        result = prompt.fn(
            base_size_gb=100.0,
            base_memory_gb=50,
            base_cores=4,
            annual_growth_rate=15.0,
            projection_years=5,
            domain="customer",
            workloads="transactional, analytical",
            memory_to_storage_ratio=2
        )
        
        # Should be a string
        assert isinstance(result, str)
        # Should show optional parameters
        assert "annual_growth_rate: 15.0%" in result
        assert "projection_years: 5" in result
        assert "domain: customer" in result
        assert "workloads: transactional, analytical" in result
        assert "memory_to_storage_ratio: 2" in result
