import pytest
import asyncio
from unittest.mock import Mock
from mcp_neo4j_memory.server import Neo4jMemory
import mcp.types as types


class TestServerTools:
    """Test MCP tool definitions without requiring Neo4j connection."""
    
    def test_neo4j_memory_class_exists(self):
        """Test that Neo4jMemory class can be instantiated."""
        mock_driver = Mock()
        mock_driver.execute_query = Mock()
        
        memory = Neo4jMemory(mock_driver)
        assert memory is not None
        assert memory.neo4j_driver == mock_driver
    
    @pytest.mark.asyncio
    async def test_tool_list_structure(self):
        """Test that all expected tools are defined with correct structure."""
        from mcp_neo4j_memory.server import main
        from mcp.server import Server
        
        # Create a mock server to test tool registration
        server = Server("test-server")
        
        # Import the handler to get the tools list
        
        # We can't easily test the actual handler without mocking more,
        # but we can verify the tool names we expect exist in the code
        expected_tools = [
            "create_entities",
            "create_relations", 
            "update_properties",
            "delete_entities",
            "delete_properties",
            "delete_relations",
            "read_graph",
            "search_nodes",
            "find_nodes",
            "open_nodes"
        ]
        
        # Read the server code to verify tools are defined
        import inspect
        source = inspect.getsource(main)
        
        for tool_name in expected_tools:
            assert tool_name in source, f"Tool {tool_name} not found in server code"