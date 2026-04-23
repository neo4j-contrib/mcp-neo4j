import pytest
from unittest.mock import Mock, AsyncMock

from mcp_neo4j_memory.server import format_namespace, create_mcp_server
from mcp_neo4j_memory.neo4j_memory import Neo4jMemory, KnowledgeGraph


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
    def mock_memory(self):
        """Create a mock Neo4jMemory for testing."""
        memory = Mock(spec=Neo4jMemory)
        # Mock all the async methods that the tools will call
        knowledge_graph = KnowledgeGraph(entities=[], relations=[])
        memory.read_graph = AsyncMock(return_value=knowledge_graph)
        memory.create_entities = AsyncMock(return_value=[])
        memory.create_relations = AsyncMock(return_value=[])
        memory.add_observations = AsyncMock(return_value=[])
        memory.delete_entities = AsyncMock(return_value=None)
        memory.delete_observations = AsyncMock(return_value=None)
        memory.delete_relations = AsyncMock(return_value=None)
        memory.search_memories = AsyncMock(return_value=knowledge_graph)
        memory.find_memories_by_name = AsyncMock(return_value=knowledge_graph)
        return memory

    @pytest.mark.asyncio
    async def test_namespace_tool_prefixes(self, mock_memory):
        """Test that tools are correctly prefixed with namespace."""
        # Test with namespace
        namespaced_server = create_mcp_server(mock_memory, namespace="test-ns")
        tools = await namespaced_server.get_tools()
        
        expected_tools = [
            "test-ns-read_graph",
            "test-ns-create_entities",
            "test-ns-create_relations",
            "test-ns-add_observations",
            "test-ns-delete_entities",
            "test-ns-delete_observations",
            "test-ns-delete_relations",
            "test-ns-search_memories",
            "test-ns-find_memories_by_name"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tools.keys(), f"Tool {expected_tool} not found in tools"

        # Test without namespace (default tools)
        default_server = create_mcp_server(mock_memory)
        default_tools = await default_server.get_tools()
        
        expected_default_tools = [
            "read_graph",
            "create_entities",
            "create_relations",
            "add_observations",
            "delete_entities",
            "delete_observations",
            "delete_relations",
            "search_memories",
            "find_memories_by_name"
        ]
        
        for expected_tool in expected_default_tools:
            assert expected_tool in default_tools.keys(), f"Default tool {expected_tool} not found"

    @pytest.mark.asyncio
    async def test_namespace_tool_functionality(self, mock_memory):
        """Test that namespaced tools function correctly."""
        namespaced_server = create_mcp_server(mock_memory, namespace="test")
        tools = await namespaced_server.get_tools()
        
        # Test that a namespaced tool exists and works
        read_tool = tools.get("test-read_graph")
        assert read_tool is not None
        
        # Call the tool function and verify it works
        result = await read_tool.fn()
        mock_memory.read_graph.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_namespace_isolation(self, mock_memory):
        """Test that different namespaces create isolated tool sets."""
        server_a = create_mcp_server(mock_memory, namespace="app-a")
        server_b = create_mcp_server(mock_memory, namespace="app-b")
        
        tools_a = await server_a.get_tools()
        tools_b = await server_b.get_tools()
        
        # Verify app-a tools exist in server_a but not server_b
        assert "app-a-read_graph" in tools_a.keys()
        assert "app-a-read_graph" not in tools_b.keys()
        
        # Verify app-b tools exist in server_b but not server_a
        assert "app-b-read_graph" in tools_b.keys()
        assert "app-b-read_graph" not in tools_a.keys()
        
        # Verify both servers have the same number of tools
        assert len(tools_a) == len(tools_b)

    @pytest.mark.asyncio
    async def test_namespace_hyphen_handling(self, mock_memory):
        """Test namespace hyphen handling edge cases."""
        # Namespace already ending with hyphen
        server_with_hyphen = create_mcp_server(mock_memory, namespace="myapp-")
        tools_with_hyphen = await server_with_hyphen.get_tools()
        assert "myapp-read_graph" in tools_with_hyphen.keys()
        
        # Namespace without hyphen
        server_without_hyphen = create_mcp_server(mock_memory, namespace="myapp")
        tools_without_hyphen = await server_without_hyphen.get_tools()
        assert "myapp-read_graph" in tools_without_hyphen.keys()
        
        # Both should result in identical tool names
        assert set(tools_with_hyphen.keys()) == set(tools_without_hyphen.keys())

    @pytest.mark.asyncio
    async def test_complex_namespace_names(self, mock_memory):
        """Test complex namespace naming scenarios."""
        complex_namespaces = [
            "company.product",
            "app_v2", 
            "client-123",
            "test.env.staging"
        ]
        
        for namespace in complex_namespaces:
            server = create_mcp_server(mock_memory, namespace=namespace)
            tools = await server.get_tools()
            
            # Verify tools are properly prefixed
            expected_tool = f"{namespace}-read_graph"
            assert expected_tool in tools.keys(), f"Tool {expected_tool} not found for namespace '{namespace}'"

    @pytest.mark.asyncio
    async def test_namespace_tool_count_consistency(self, mock_memory):
        """Test that namespaced and default servers have the same number of tools."""
        default_server = create_mcp_server(mock_memory)
        namespaced_server = create_mcp_server(mock_memory, namespace="test")
        
        default_tools = await default_server.get_tools()
        namespaced_tools = await namespaced_server.get_tools()
        
        # Should have the same number of tools
        assert len(default_tools) == len(namespaced_tools)
        
        # Verify we have the expected number of tools (9 tools based on the server implementation)
        assert len(default_tools) == 9
        assert len(namespaced_tools) == 9
