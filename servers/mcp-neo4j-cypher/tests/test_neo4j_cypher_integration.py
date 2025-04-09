import os
import pytest
import asyncio
from mcp_neo4j_cypher.server import neo4jDatabase


@pytest.fixture(scope="function")
def neo4j():
    """Create a Neo4j driver using environment variables for connection details."""
    uri = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")

    neo4j = neo4jDatabase(uri, user, password)

    neo4j._execute_query("MATCH (n) DETACH DELETE n")

    yield neo4j

    neo4j.close()


# Clean up test data after tests
@pytest.mark.asyncio
async def test_execute_cypher_update_query(neo4j):
    # Execute a Cypher query to create a node
    query = "CREATE (n:Person {name: 'Alice', age: 30}) RETURN n.name"
    result = neo4j._execute_query(query)

    # Verify the node creation
    assert len(result) == 1
    print(result)
    assert result[0]["nodes_created"] == 1
    assert result[0]["labels_added"] == 1
    assert result[0]["properties_set"] == 2


@pytest.mark.asyncio
async def test_retrieve_schema(neo4j):
    # Execute a Cypher query to retrieve schema information
    query = "CALL db.schema.visualization()"
    result = neo4j._execute_query(query)

    # Verify the schema result
    assert "nodes" in result[0]
    assert "relationships" in result[0]


@pytest.mark.asyncio
async def test_execute_complex_read_query(neo4j):
    # Prepare test data
    neo4j._execute_query("CREATE (a:Person {name: 'Alice', age: 30})")
    neo4j._execute_query("CREATE (b:Person {name: 'Bob', age: 25})")
    neo4j._execute_query("CREATE (c:Person {name: 'Charlie', age: 35})")
    neo4j._execute_query(
        "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:FRIEND]->(b)"
    )
    neo4j._execute_query(
        "MATCH (b:Person {name: 'Bob'}), (c:Person {name: 'Charlie'}) CREATE (b)-[:FRIEND]->(c)"
    )

    # Execute a complex read query
    query = """
    MATCH (p:Person)-[:FRIEND]->(friend)
    RETURN p.name AS person, friend.name AS friend_name
    ORDER BY p.name, friend.name
    """
    result = neo4j._execute_query(query)

    # Verify the query result
    assert len(result) == 2
    assert result[0]["person"] == "Alice"
    assert result[0]["friend_name"] == "Bob"
    assert result[1]["person"] == "Bob"
    assert result[1]["friend_name"] == "Charlie"
