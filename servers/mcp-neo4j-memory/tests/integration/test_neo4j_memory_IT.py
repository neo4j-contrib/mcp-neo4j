import os
import pytest
import pytest_asyncio

from neo4j import AsyncGraphDatabase
from mcp_neo4j_memory.server import Neo4jMemory, Entity, Relation, ObservationAddition, ObservationDeletion, KnowledgeGraph

def get_neo4j_driver():
    uri = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    return AsyncGraphDatabase.driver(uri, auth=(user, password))

@pytest_asyncio.fixture(scope="function")
async def neo4j_driver():
    driver = get_neo4j_driver()
    # Verify connection
    try:
        await driver.verify_connectivity()
    except Exception as e:
        pytest.skip(f"Could not connect to Neo4j: {e}")
    yield driver
    async with driver.session() as session:
        await session.run("MATCH (n:Memory) DETACH DELETE n")
    await driver.close()

@pytest_asyncio.fixture(scope="function")
async def memory(neo4j_driver) -> Neo4jMemory:
    """Create a Neo4jMemory instance with the Neo4j driver."""
    mem = Neo4jMemory(neo4j_driver)
    await mem.create_fulltext_index()
    return mem

@pytest.mark.asyncio
async def test_create_and_read_entities(memory: Neo4jMemory):
    # Create test entities
    test_entities = [
        Entity(name="Alice", type="Person", observations=["Likes reading", "Works at Company X"]),
        Entity(name="Bob", type="Person", observations=["Enjoys hiking"])
    ]
    # Create entities in the graph
    created_entities = await memory.create_entities(test_entities)
    assert len(created_entities) == 2
    
    # Read the graph
    graph = await memory.read_graph()
    
    # Verify entities were created
    assert len(graph.entities) == 2
    
    # Check if entities have correct data
    entities_by_name = {entity.name: entity for entity in graph.entities}
    assert "Alice" in entities_by_name
    assert "Bob" in entities_by_name
    assert entities_by_name["Alice"].type == "Person"
    assert "Likes reading" in entities_by_name["Alice"].observations
    assert "Enjoys hiking" in entities_by_name["Bob"].observations

@pytest.mark.asyncio
async def test_create_and_read_relations(memory: Neo4jMemory):
    # Create test entities
    test_entities = [
        Entity(name="Alice", type="Person", observations=[]),
        Entity(name="Bob", type="Person", observations=[])
    ]
    await memory.create_entities(test_entities)
    
    # Create test relation
    test_relations = [
        Relation(source="Alice", target="Bob", relationType="KNOWS")
    ]
    
    # Create relation in the graph
    created_relations = await memory.create_relations(test_relations)
    assert len(created_relations) == 1
    
    # Read the graph
    graph: KnowledgeGraph = await memory.read_graph()
    
    # Verify relation was created
    assert len(graph.relations) == 1
    relation = graph.relations[0]
    assert relation.source == "Alice"
    assert relation.target == "Bob"
    assert relation.relationType == "KNOWS"

@pytest.mark.asyncio
async def test_add_observations(memory: Neo4jMemory):
    # Create test entity
    test_entity = Entity(name="Charlie", type="Person", observations=["Initial observation"])
    await memory.create_entities([test_entity])
    
    # Add observations
    observation_additions = [
        ObservationAddition(entityName="Charlie", observations=["New observation 1", "New observation 2"])
    ]
    
    result = await memory.add_observations(observation_additions)
    assert len(result) == 1
    
    # Read the graph
    graph = await memory.read_graph()
    
    # Find Charlie
    charlie = next((e for e in graph.entities if e.name == "Charlie"), None)
    assert charlie is not None
    
    # Verify observations were added
    assert "Initial observation" in charlie.observations
    assert "New observation 1" in charlie.observations
    assert "New observation 2" in charlie.observations

@pytest.mark.asyncio
async def test_delete_observations(memory: Neo4jMemory):
    # Create test entity with observations
    test_entity = Entity(
        name="Dave", 
        type="Person", 
        observations=["Observation 1", "Observation 2", "Observation 3"]
    )
    await memory.create_entities([test_entity])
    
    # Delete specific observations
    observation_deletions = [
        ObservationDeletion(entityName="Dave", observations=["Observation 2"])
    ]
    
    await memory.delete_observations(observation_deletions)
    
    # Read the graph
    graph = await memory.read_graph()
    
    # Find Dave
    dave = next((e for e in graph.entities if e.name == "Dave"), None)
    assert dave is not None
    
    # Verify observation was deleted
    assert "Observation 1" in dave.observations
    assert "Observation 2" not in dave.observations
    assert "Observation 3" in dave.observations

@pytest.mark.asyncio
async def test_delete_entities(memory: Neo4jMemory):
    # Create test entities
    test_entities = [
        Entity(name="Eve", type="Person", observations=[]),
        Entity(name="Frank", type="Person", observations=[])
    ]
    await memory.create_entities(test_entities)
    
    # Delete one entity
    await memory.delete_entities(["Eve"])
    
    # Read the graph
    graph = await memory.read_graph()
    
    # Verify Eve was deleted but Frank remains
    entity_names = [e.name for e in graph.entities]
    assert "Eve" not in entity_names
    assert "Frank" in entity_names

@pytest.mark.asyncio
async def test_delete_relations(memory: Neo4jMemory):
    # Create test entities
    test_entities = [
        Entity(name="Grace", type="Person", observations=[]),
        Entity(name="Hank", type="Person", observations=[])
    ]
    await memory.create_entities(test_entities)
    
    # Create test relations
    test_relations = [
        Relation(source="Grace", target="Hank", relationType="KNOWS"),
        Relation(source="Grace", target="Hank", relationType="WORKS_WITH")
    ]
    await memory.create_relations(test_relations)
    
    # Delete one relation
    relations_to_delete = [
        Relation(source="Grace", target="Hank", relationType="KNOWS")
    ]
    await memory.delete_relations(relations_to_delete)
    
    # Read the graph
    graph: KnowledgeGraph = await memory.read_graph()
    
    # Verify only the WORKS_WITH relation remains
    assert len(graph.relations) == 1
    assert graph.relations[0].relationType == "WORKS_WITH"

@pytest.mark.asyncio
async def test_search_nodes(memory: Neo4jMemory):
    # Create test entities
    test_entities = [
        Entity(name="Ian", type="Person", observations=["Likes coffee"]),
        Entity(name="Jane", type="Person", observations=["Likes tea"]),
        Entity(name="coffee", type="Beverage", observations=["Hot drink"])
    ]
    await memory.create_entities(test_entities)
    
    # Search for coffee-related nodes
    result = await memory.search_memories("coffee")
    
    # Verify search results
    entity_names = [e.name for e in result.entities]
    assert "Ian" in entity_names
    assert "coffee" in entity_names
    assert "Jane" not in entity_names

@pytest.mark.asyncio
async def test_find_nodes(memory: Neo4jMemory):
    # Create test entities
    test_entities = [
        Entity(name="Kevin", type="Person", observations=[]),
        Entity(name="Laura", type="Person", observations=[]),
        Entity(name="Mike", type="Person", observations=[])
    ]
    await memory.create_entities(test_entities)


    # Open specific nodes
    result = await memory.find_memories_by_name(["Kevin", "Laura"])

    # Verify only requested nodes are returned
    entity_names = [e.name for e in result.entities]
    assert "Kevin" in entity_names
    assert "Laura" in entity_names
    assert "Mike" not in entity_names 