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
        
        # Verify we have the expected number of tools (12 tools based on the server implementation)
        assert len(default_tools) == 12
        assert len(namespaced_tools) == 12
