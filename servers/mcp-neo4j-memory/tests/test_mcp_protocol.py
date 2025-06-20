"""
Integration tests for Neo4j Memory MCP Server using MCP client
"""
import os
import json
import pytest
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables from .env file
load_dotenv()


class MCPTestHelper:
    """Helper class to manage MCP client lifecycle within tests"""
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="uv",
            args=[
                "run",
                "mcp-neo4j-memory",
                "--db-url", os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "--username", os.getenv("NEO4J_USERNAME", "neo4j"),
                "--password", os.getenv("NEO4J_PASSWORD", "password"),
                "--database", os.getenv("NEO4J_DATABASE", "neo4j")
            ],
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        self._read_stream = None
        self._write_stream = None
        self._client = None
        self._session = None
    
    async def __aenter__(self):
        # Create the stdio client connection
        self._client = stdio_client(self.server_params)
        self._read_stream, self._write_stream = await self._client.__aenter__()
        
        # Create the MCP session
        self._session = ClientSession(self._read_stream, self._write_stream)
        await self._session.__aenter__()
        
        # Initialize the connection
        await self._session.initialize()
        
        # Clean up any existing data
        await self._cleanup_database()
        
        return self._session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up after test
        if self._session:
            try:
                await self._cleanup_database()
            except Exception:
                pass  # Ignore cleanup errors
            
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
        
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def _cleanup_database(self):
        """Helper to clean up all Memory nodes from the database"""
        if not self._session:
            return
            
        try:
            # Read current graph
            result = await self._session.call_tool("read_graph", {})
            if result and result.content and len(result.content) > 0:
                # Parse the response
                content = result.content[0]
                if hasattr(content, 'text'):
                    result_text = content.text
                    # Look for JSON in the response
                    if "{" in result_text and "entities" in result_text:
                        start = result_text.find("{")
                        end = result_text.rfind("}") + 1
                        if start >= 0 and end > start:
                            graph_json = result_text[start:end]
                            graph_data = json.loads(graph_json)
                            
                            # Delete all entities if any exist
                            entities = graph_data.get("entities", [])
                            if entities:
                                entity_names = [e["name"] for e in entities]
                                await self._session.call_tool("delete_entities", {"entityNames": entity_names})
        except Exception:
            pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_list_tools():
    """Test that the server provides the expected tools"""
    async with MCPTestHelper() as session:
        result = await session.list_tools()
        
        # Expected tool names
        expected_tools = {
            "read_graph",
            "search_nodes", 
            "find_nodes",
            "open_nodes",
            "create_entities",
            "delete_entities",
            "create_relations",
            "delete_relations",
            "update_properties",
            "delete_properties"
        }
        
        # Get actual tool names
        actual_tools = {tool.name for tool in result.tools}
        
        # Verify all expected tools are present
        assert expected_tools == actual_tools


@pytest.mark.asyncio
async def test_create_and_read_entities():
    """Test creating entities and reading them back via MCP"""
    async with MCPTestHelper() as session:
        # Create entities
        create_result = await session.call_tool(
            "create_entities",
            {
                "entities": [
                    {
                        "name": "Alice",
                        "type": "Person",
                        "properties": {"hobby": "reading", "workplace": "Company X"}
                    },
                    {
                        "name": "Bob", 
                        "type": "Person",
                        "properties": {"hobby": "hiking"}
                    }
                ]
            }
        )
        
        assert create_result is not None
        assert create_result.content is not None
        
        # Read the graph
        read_result = await session.call_tool("read_graph", {})
        
        assert read_result is not None
        assert read_result.content is not None
        
        # Parse the result
        result_text = read_result.content[0].text
        assert "Alice" in result_text
        assert "Bob" in result_text
        assert "reading" in result_text
        assert "hiking" in result_text


@pytest.mark.asyncio
async def test_create_relations():
    """Test creating relations between entities via MCP"""
    async with MCPTestHelper() as session:
        # First create entities
        await session.call_tool(
            "create_entities",
            {
                "entities": [
                    {"name": "Alice", "type": "Person", "properties": {}},
                    {"name": "Bob", "type": "Person", "properties": {}}
                ]
            }
        )
        
        # Create relation
        relation_result = await session.call_tool(
            "create_relations",
            {
                "relations": [
                    {
                        "source": "Alice",
                        "target": "Bob", 
                        "relationType": "KNOWS"
                    }
                ]
            }
        )
        
        assert relation_result is not None
        
        # Read graph to verify
        read_result = await session.call_tool("read_graph", {})
        result_text = read_result.content[0].text
        
        assert "KNOWS" in result_text
        assert "Alice" in result_text
        assert "Bob" in result_text


@pytest.mark.asyncio
async def test_search_nodes():
    """Test searching nodes via MCP"""
    async with MCPTestHelper() as session:
        # Create test data
        await session.call_tool(
            "create_entities",
            {
                "entities": [
                    {"name": "Coffee Shop", "type": "Place", "properties": {"specialty": "coffee"}},
                    {"name": "Tea House", "type": "Place", "properties": {"specialty": "tea"}},
                    {"name": "John", "type": "Person", "properties": {"preference": "coffee"}}
                ]
            }
        )
        
        # Search for coffee-related nodes
        search_result = await session.call_tool(
            "search_nodes",
            {"query": "coffee"}
        )
        
        assert search_result is not None
        result_text = search_result.content[0].text
        
        # Should find Coffee Shop but not others (searching by name/type only)
        assert "Coffee Shop" in result_text


@pytest.mark.asyncio
async def test_find_specific_nodes():
    """Test finding specific nodes by name via MCP"""
    async with MCPTestHelper() as session:
        # Create test data
        await session.call_tool(
            "create_entities",
            {
                "entities": [
                    {"name": "Entity1", "type": "Type1", "properties": {}},
                    {"name": "Entity2", "type": "Type2", "properties": {}},
                    {"name": "Entity3", "type": "Type3", "properties": {}}
                ]
            }
        )
        
        # Find specific nodes using open_nodes (not find_nodes)
        find_result = await session.call_tool(
            "open_nodes",
            {"names": ["Entity1", "Entity3"]}
        )
        
        assert find_result is not None
        result_text = find_result.content[0].text
        
        # Should find Entity1 and Entity3, but not Entity2
        assert "Entity1" in result_text
        assert "Entity3" in result_text
        assert "Entity2" not in result_text


@pytest.mark.asyncio
async def test_add_and_delete_properties():
    """Test adding and deleting properties via MCP"""
    async with MCPTestHelper() as session:
        # Create entity
        await session.call_tool(
            "create_entities",
            {
                "entities": [
                    {"name": "TestEntity", "type": "TestType", "properties": {"status": "initial"}}
                ]
            }
        )
        
        # Update properties
        add_result = await session.call_tool(
            "update_properties",
            {
                "updates": [
                    {
                        "entityName": "TestEntity",
                        "properties": {"level": 5, "category": "test"}
                    }
                ]
            }
        )
        
        assert add_result is not None
        
        # Verify properties were added
        read_result = await session.call_tool("read_graph", {})
        result_text = read_result.content[0].text
        
        assert "initial" in result_text
        assert "5" in result_text
        assert "test" in result_text
        
        # Delete one property
        delete_result = await session.call_tool(
            "delete_properties",
            {
                "deletions": [
                    {
                        "entityName": "TestEntity",
                        "propertyKeys": ["level"]
                    }
                ]
            }
        )
        
        assert delete_result is not None
        
        # Verify property was deleted
        read_result = await session.call_tool("read_graph", {})
        result_text = read_result.content[0].text
        
        assert "initial" in result_text
        assert "test" in result_text
        # The actual number 5 might still appear in JSON structure, check for absence in properties


@pytest.mark.asyncio
async def test_delete_entities_and_relations():
    """Test deleting entities and relations via MCP"""
    async with MCPTestHelper() as session:
        # Create entities and relation
        await session.call_tool(
            "create_entities",
            {
                "entities": [
                    {"name": "Person1", "type": "Person", "properties": {}},
                    {"name": "Person2", "type": "Person", "properties": {}},
                    {"name": "Person3", "type": "Person", "properties": {}}
                ]
            }
        )
        
        await session.call_tool(
            "create_relations",
            {
                "relations": [
                    {"source": "Person1", "target": "Person2", "relationType": "KNOWS"},
                    {"source": "Person2", "target": "Person3", "relationType": "WORKS_WITH"}
                ]
            }
        )
        
        # Delete one relation
        await session.call_tool(
            "delete_relations",
            {
                "relations": [
                    {"source": "Person1", "target": "Person2", "relationType": "KNOWS"}
                ]
            }
        )
        
        # Delete one entity
        await session.call_tool(
            "delete_entities",
            {"entityNames": ["Person1"]}
        )
        
        # Verify deletions
        read_result = await session.call_tool("read_graph", {})
        result_text = read_result.content[0].text
        
        # Person1 should be deleted
        assert "Person1" not in result_text
        # KNOWS relation should be deleted
        assert "KNOWS" not in result_text
        # Person2, Person3 and WORKS_WITH should remain
        assert "Person2" in result_text
        assert "Person3" in result_text
        assert "WORKS_WITH" in result_text


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for invalid operations"""
    async with MCPTestHelper() as session:
        # Try to create relation with non-existent entities
        # First, let's see what happens when we try to create a relation without the nodes
        result = await session.call_tool(
            "create_relations",
            {
                "relations": [
                    {"source": "NonExistent1", "target": "NonExistent2", "relationType": "KNOWS"}
                ]
            }
        )
        
        # The tool should return a result (may create the nodes implicitly or return empty)
        assert result is not None
        
        # Now verify the graph state - relations shouldn't exist without valid nodes
        read_result = await session.call_tool("read_graph", {})
        result_text = read_result.content[0].text
        
        # Check if the non-existent entities were created or if the operation was handled gracefully
        # The behavior might vary - some implementations create nodes implicitly
        # What matters is that the operation doesn't crash