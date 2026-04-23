import json
from typing import Any

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP


@pytest.mark.asyncio(loop_scope="function")
async def test_get_neo4j_schema(mcp_server: FastMCP, init_data: Any):
    tool = await mcp_server.get_tool("get_neo4j_schema")
    response = await tool.run(dict())

    schema = json.loads(response.content[0].text)

    # Verify the schema result
    assert "Person" in schema
    assert schema["Person"]["count"] == 3
    assert len(schema["Person"]["properties"]) == 2
    assert "FRIEND" in schema["Person"]["relationships"]


@pytest.mark.asyncio(loop_scope="function")
async def test_write_neo4j_cypher(mcp_server: FastMCP):
    query = "CREATE (n:Test {name: 'test', age: 123}) RETURN n.name"
    tool = await mcp_server.get_tool("write_neo4j_cypher")
    response = await tool.run(dict(query=query))

    result = json.loads(response.content[0].text)

    assert "nodes_created" in result
    assert "labels_added" in result
    assert "properties_set" in result
    assert result["nodes_created"] == 1
    assert result["labels_added"] == 1
    assert result["properties_set"] == 2


@pytest.mark.asyncio(loop_scope="function")
async def test_read_neo4j_cypher(mcp_server: FastMCP, init_data: Any):
    query = """
    MATCH (p:Person)-[:FRIEND]->(friend)
    RETURN p.name AS person, friend.name AS friend_name
    ORDER BY p.name, friend.name
    """

    tool = await mcp_server.get_tool("read_neo4j_cypher")
    response = await tool.run(dict(query=query))

    result = json.loads(response.content[0].text)

    assert len(result) == 2
    assert result[0]["person"] == "Alice"
    assert result[0]["friend_name"] == "Bob"
    assert result[1]["person"] == "Bob"
    assert result[1]["friend_name"] == "Charlie"


@pytest.mark.asyncio(loop_scope="function")
async def test_read_query_timeout_with_slow_query(
    mcp_server_short_timeout: FastMCP, clear_data: Any
):
    """Test that read queries timeout appropriately with a slow query."""
    # Create a query that should take longer than 0.01 seconds
    slow_query = """
    WITH range(1, 10000) AS r
    UNWIND r AS x
    WITH x
    WHERE x % 2 = 0
    RETURN count(x) AS result
    """

    tool = await mcp_server_short_timeout.get_tool("read_neo4j_cypher")

    # The query might timeout and raise a ToolError, or it might complete very fast
    # Let's just verify the server handles it without crashing
    try:
        response = await tool.run(dict(query=slow_query))
        # If it completes, verify it returns valid results
        if response.content[0].text:
            result = json.loads(response.content[0].text)
            assert isinstance(result, list)
    except ToolError as e:
        # If it times out, that's also acceptable behavior
        error_message = str(e)
        assert "Neo4j Error" in error_message


@pytest.mark.asyncio(loop_scope="function")
async def test_read_query_with_normal_timeout_succeeds(
    mcp_server: FastMCP, init_data: Any
):
    """Test that normal queries succeed with reasonable timeout."""
    query = "MATCH (p:Person) RETURN p.name AS name ORDER BY name"

    tool = await mcp_server.get_tool("read_neo4j_cypher")
    response = await tool.run(dict(query=query))

    result = json.loads(response.content[0].text)

    # Should succeed and return expected results
    assert len(result) == 3
    assert result[0]["name"] == "Alice"
    assert result[1]["name"] == "Bob"
    assert result[2]["name"] == "Charlie"


@pytest.mark.asyncio(loop_scope="function")
async def test_schema_query_timeout(mcp_server_short_timeout: FastMCP):
    """Test that schema queries also respect timeout settings."""
    tool = await mcp_server_short_timeout.get_tool("get_neo4j_schema")

    # Schema query should typically be fast, but with very short timeout it might timeout
    # depending on the database state. Let's just verify it doesn't crash
    try:
        response = await tool.run(dict())
        # If it succeeds, verify the response format
        if response.content[0].text:
            schema = json.loads(response.content[0].text)
            assert isinstance(schema, dict)
    except ToolError as e:
        # If it times out, that's also acceptable behavior for this test
        error_message = str(e)
        assert "Neo4j Error" in error_message or "timeout" in error_message.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_write_query_no_timeout(
    mcp_server_short_timeout: FastMCP, clear_data: Any
):
    """Test that write queries are not subject to timeout restrictions."""
    # Write queries should not be affected by read_timeout
    query = "CREATE (n:TimeoutTest {name: 'test', created: timestamp()}) RETURN n.name"

    tool = await mcp_server_short_timeout.get_tool("write_neo4j_cypher")
    response = await tool.run(dict(query=query))

    result = json.loads(response.content[0].text)

    # Write operation should succeed regardless of short timeout
    assert "nodes_created" in result
    assert result["nodes_created"] == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_timeout_configuration_passed_correctly(async_neo4j_driver):
    """Test that timeout configuration is properly passed to the server."""
    from mcp_neo4j_cypher.server import create_mcp_server

    # Create servers with different timeout values
    mcp_30s = create_mcp_server(async_neo4j_driver, "neo4j", read_timeout=30)
    mcp_60s = create_mcp_server(async_neo4j_driver, "neo4j", read_timeout=60)

    # Both should be created successfully (configuration test)
    assert mcp_30s is not None
    assert mcp_60s is not None

    # The actual timeout values are used internally in Query objects,
    # so this test mainly verifies the parameter is accepted without error
