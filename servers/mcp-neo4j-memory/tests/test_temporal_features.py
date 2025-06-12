import os
import pytest
import asyncio
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from mcp_neo4j_memory.server import Neo4jMemory, Entity

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
    
    yield driver
    
    # Clean up test data after tests
    driver.execute_query("MATCH (n:Memory) DETACH DELETE n")
    
    driver.close()

@pytest.fixture(scope="function")
def memory(neo4j_driver):
    """Create a Neo4jMemory instance with the Neo4j driver."""
    return Neo4jMemory(neo4j_driver)

@pytest.mark.asyncio
async def test_create_entities_with_timestamps(memory):
    """Test the create_entities function with timestamp functionality"""
    # Create test entities
    test_entities = [
        Entity(name="TimestampedTask", type="Task", observations=["Task with timestamps"]),
        Entity(name="TimestampedProject", type="Project", observations=["Project with timestamps"])
    ]
    
    # Create entities in the graph
    created_entities = await memory.create_entities(test_entities)
    
    # Verify that entities were created and have timestamps
    assert len(created_entities) == 2
    
    # Check that timestamps were added
    for entity in created_entities:
        assert entity.created_at is not None
        assert entity.updated_at is not None
        assert entity.created_at == entity.updated_at  # Should be same on creation
    
    # Verify entity names and types are preserved
    entity_names = [e.name for e in created_entities]
    assert "TimestampedTask" in entity_names
    assert "TimestampedProject" in entity_names
    
    # Check that we can retrieve them
    found_entities = await memory.find_nodes(["TimestampedTask", "TimestampedProject"])
    assert len(found_entities.entities) == 2

@pytest.mark.asyncio
async def test_get_recent_memories(memory):
    """Test the get_recent_memories function"""
    # Create test entities
    test_entities = [
        Entity(name="RecentTask", type="Task", observations=["This task was created recently"]),
        Entity(name="RecentProject", type="Project", observations=["New project started today"])
    ]
    
    # Create entities in the graph
    await memory.create_entities(test_entities)
    
    # Test get_recent_memories with 7 days
    recent_memories = await memory.get_recent_memories(days=7)
    
    # Verify that recent memories were found
    assert len(recent_memories.entities) >= 2
    
    # Check that our test entities are in the results
    entity_names = [e.name for e in recent_memories.entities]
    assert "RecentTask" in entity_names
    assert "RecentProject" in entity_names

@pytest.mark.asyncio
async def test_get_memories_by_date_range(memory):
    """Test the get_memories_by_time_range function"""
    # Create test entities
    test_entities = [
        Entity(name="RangeTask1", type="Task", observations=["Task in date range"]),
        Entity(name="RangeTask2", type="Task", observations=["Another task in range"])
    ]
    
    # Create entities in the graph
    await memory.create_entities(test_entities)
    
    # Test get_memories_by_time_range
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    
    range_memories = await memory.get_memories_by_time_range(
        start_time=yesterday,
        end_time=tomorrow
    )
    
    # Verify that memories in range were found
    assert len(range_memories.entities) >= 2
    
    # Check that our test entities are in the results
    entity_names = [e.name for e in range_memories.entities]
    assert "RangeTask1" in entity_names
    assert "RangeTask2" in entity_names

@pytest.mark.asyncio
async def test_search_with_temporal_decay(memory):
    """Test the search_with_temporal_decay function"""
    # Create test entities
    test_entities = [
        Entity(name="DecayProject", type="Project", observations=["This is a project with temporal decay"]),
        Entity(name="DecayTask", type="Task", observations=["Task that should be found in decay search"])
    ]
    
    # Create entities in the graph
    await memory.create_entities(test_entities)
    
    # Test search_with_temporal_decay
    decay_results = await memory.search_with_temporal_decay(
        query="decay",
        decay_days=30
    )
    
    # Verify that search found results
    assert len(decay_results.entities) >= 2
    
    # Check that our test entities are in the results
    entity_names = [e.name for e in decay_results.entities]
    assert "DecayProject" in entity_names
    assert "DecayTask" in entity_names

@pytest.mark.asyncio
async def test_temporal_features_integration(memory):
    """Integration test for all temporal features"""
    # Create test entities
    test_entities = [
        Entity(name="IntegrationTest1", type="Test", observations=["First integration test entity"]),
        Entity(name="IntegrationTest2", type="Test", observations=["Second integration test entity"])
    ]
    
    # Create entities
    await memory.create_entities(test_entities)
    
    # Test all three temporal functions work together
    recent = await memory.get_recent_memories(days=1)
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    range_result = await memory.get_memories_by_time_range(
        start_time=today_start,
        end_time=today_end
    )
    decay_result = await memory.search_with_temporal_decay(query="integration", decay_days=30)
    
    # All should find our test entities
    assert len(recent.entities) >= 2
    assert len(range_result.entities) >= 2
    assert len(decay_result.entities) >= 2