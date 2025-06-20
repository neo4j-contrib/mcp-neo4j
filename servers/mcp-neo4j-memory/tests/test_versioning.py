import os
import pytest
import asyncio
from dotenv import load_dotenv
from neo4j import GraphDatabase
from mcp_neo4j_memory.server import Neo4jMemory, Entity, Relation, PropertyUpdate, PropertyDeletion

# Load environment variables from .env file
load_dotenv()

@pytest.fixture(scope="function")
def neo4j_driver():
    """Create a Neo4j driver using environment variables for connection details."""
    uri = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # Verify connection
    try:
        driver.verify_connectivity()
    except Exception as e:
        pytest.skip(f"Could not connect to Neo4j: {e}")
    
    # Clean up test data before tests
    driver.execute_query("MATCH (n:Memory) DETACH DELETE n")
    
    yield driver
    
    # Clean up test data after tests
    driver.execute_query("MATCH (n:Memory) DETACH DELETE n")
    
    driver.close()

@pytest.fixture(scope="function")
def memory(neo4j_driver):
    """Create a Neo4jMemory instance with the Neo4j driver."""
    return Neo4jMemory(neo4j_driver)

@pytest.mark.asyncio
async def test_versioning_chain(memory, neo4j_driver):
    """Test that updates create a proper version chain."""
    # Create entity
    await memory.create_entities([
        Entity(name="Product", type="Item", properties={"price": 100, "stock": 10})
    ])
    
    # Update 1: Change price
    await memory.update_properties([
        PropertyUpdate(entityName="Product", properties={"price": 120})
    ])
    
    # Update 2: Change stock
    await memory.update_properties([
        PropertyUpdate(entityName="Product", properties={"stock": 5})
    ])
    
    # Check version chain
    result = neo4j_driver.execute_query("""
        MATCH path = (v1:Memory {name: 'Product'})-[:NEXT_VERSION*]->(v2:Memory)
        RETURN length(path) as chain_length, v1.endedAt as v1_ended, v2.endedAt as v2_ended
        ORDER BY length(path) DESC
        LIMIT 1
    """)
    
    if result.records:
        record = result.records[0]
        assert record['chain_length'] == 2  # Two hops: v1 -> v2 -> v3
        assert record['v1_ended'] is not None  # First version is ended
        assert record['v2_ended'] is None  # Last version is current
    
    # Check total versions
    result = neo4j_driver.execute_query("""
        MATCH (n:Memory {name: 'Product'})
        RETURN count(n) as version_count
    """)
    assert result.records[0]['version_count'] == 3  # Original + 2 updates

@pytest.mark.asyncio
async def test_soft_delete_preserves_history(memory, neo4j_driver):
    """Test that soft deletes preserve entity history."""
    # Create entity
    await memory.create_entities([
        Entity(name="User", type="Person", properties={"email": "user@example.com"})
    ])
    
    # Update it
    await memory.update_properties([
        PropertyUpdate(entityName="User", properties={"email": "newemail@example.com"})
    ])
    
    # Soft delete it
    await memory.delete_entities(["User"])
    
    # Check that all versions exist but are ended
    result = neo4j_driver.execute_query("""
        MATCH (n:Memory {name: 'User'})
        RETURN count(n) as total_versions, 
               count(CASE WHEN n.endedAt IS NOT NULL THEN 1 END) as ended_versions
    """)
    
    record = result.records[0]
    assert record['total_versions'] == 2  # Original + 1 update
    assert record['ended_versions'] == 2  # All versions are ended after soft delete
    
    # Current query should not find it
    graph = await memory.read_graph()
    entity_names = [e.name for e in graph.entities]
    assert "User" not in entity_names

@pytest.mark.asyncio
async def test_property_deletion_creates_version(memory, neo4j_driver):
    """Test that property deletions create new versions."""
    # Create entity with properties
    await memory.create_entities([
        Entity(name="Config", type="Setting", properties={"debug": True, "timeout": 30, "retries": 3})
    ])
    
    # Delete one property
    await memory.delete_properties([
        PropertyDeletion(entityName="Config", propertyKeys=["debug"])
    ])
    
    # Check versions
    result = neo4j_driver.execute_query("""
        MATCH (n:Memory {name: 'Config'})
        RETURN n.endedAt as endedAt, 
               'debug' IN keys(n) as has_debug,
               'timeout' IN keys(n) as has_timeout
        ORDER BY n.createdAt
    """)
    
    records = result.records
    assert len(records) == 2  # Original + new version
    
    # First version (ended)
    assert records[0]['endedAt'] is not None
    assert records[0]['has_debug'] == True
    assert records[0]['has_timeout'] == True
    
    # Second version (current)
    assert records[1]['endedAt'] is None
    assert records[1]['has_debug'] == False
    assert records[1]['has_timeout'] == True

@pytest.mark.asyncio 
async def test_concurrent_updates_maintain_consistency(memory, neo4j_driver):
    """Test that concurrent updates to the same entity maintain version consistency."""
    # Create entity
    await memory.create_entities([
        Entity(name="Counter", type="Metric", properties={"value": 0})
    ])
    
    # Perform multiple updates
    for i in range(3):
        await memory.update_properties([
            PropertyUpdate(entityName="Counter", properties={"value": i + 1})
        ])
    
    # Check that we have a proper chain
    result = neo4j_driver.execute_query("""
        MATCH (n:Memory {name: 'Counter'})
        WHERE n.endedAt IS NULL
        RETURN n.value as current_value
    """)
    
    assert result.records[0]['current_value'] == 3
    
    # Check total versions
    result = neo4j_driver.execute_query("""
        MATCH (n:Memory {name: 'Counter'})
        RETURN count(n) as version_count
    """)
    assert result.records[0]['version_count'] == 4  # Original + 3 updates

@pytest.mark.asyncio
async def test_relationship_soft_delete(memory, neo4j_driver):
    """Test that relationships can be soft deleted."""
    # Create entities
    await memory.create_entities([
        Entity(name="Author", type="Person", properties={}),
        Entity(name="Book", type="Document", properties={})
    ])
    
    # Create relationship
    await memory.create_relations([
        Relation(source="Author", target="Book", relationType="WROTE")
    ])
    
    # Delete relationship
    await memory.delete_relations([
        Relation(source="Author", target="Book", relationType="WROTE")
    ])
    
    # Check that relationship is soft deleted
    result = neo4j_driver.execute_query("""
        MATCH (a:Memory {name: 'Author'})-[r:WROTE]-(b:Memory {name: 'Book'})
        RETURN r.endedAt as endedAt
    """)
    
    if result.records:
        assert result.records[0]['endedAt'] is not None
    
    # Current graph should not show the relationship
    graph = await memory.read_graph()
    assert len(graph.relations) == 0

@pytest.mark.asyncio
async def test_version_chain_traversal(memory, neo4j_driver):
    """Test traversing the version chain to get entity history."""
    # Create entity
    await memory.create_entities([
        Entity(name="Document", type="File", properties={"content": "v1"})
    ])
    
    # Multiple updates
    await memory.update_properties([
        PropertyUpdate(entityName="Document", properties={"content": "v2"})
    ])
    await memory.update_properties([
        PropertyUpdate(entityName="Document", properties={"content": "v3"})
    ])
    
    # Get version history
    result = neo4j_driver.execute_query("""
        MATCH (n:Memory {name: 'Document'})
        RETURN n.content as content, n.createdAt as createdAt
        ORDER BY n.createdAt
    """)
    
    versions = [r['content'] for r in result.records]
    assert versions == ['v1', 'v2', 'v3']