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
    
    yield driver
    
    # Clean up test data after tests
    driver.execute_query("MATCH (n:Memory) DETACH DELETE n")
    
    driver.close()

@pytest.fixture(scope="function")
def memory(neo4j_driver):
    """Create a Neo4jMemory instance with the Neo4j driver."""
    return Neo4jMemory(neo4j_driver)

@pytest.mark.asyncio
async def test_create_and_read_entities(memory):
    # Create test entities
    test_entities = [
        Entity(name="Alice", type="Person", properties={"hobby": "reading", "workplace": "Company X"}),
        Entity(name="Bob", type="Person", properties={"hobby": "hiking"})
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
    assert entities_by_name["Alice"].properties.get("hobby") == "reading"
    assert entities_by_name["Alice"].properties.get("workplace") == "Company X"
    assert entities_by_name["Bob"].properties.get("hobby") == "hiking"

@pytest.mark.asyncio
async def test_create_and_read_relations(memory):
    # Create test entities
    test_entities = [
        Entity(name="Alice", type="Person", properties={}),
        Entity(name="Bob", type="Person", properties={})
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
    graph = await memory.read_graph()
    
    # Verify relation was created
    assert len(graph.relations) == 1
    relation = graph.relations[0]
    assert relation.source == "Alice"
    assert relation.target == "Bob"
    assert relation.relationType == "KNOWS"
    assert relation.properties == {}  # Default empty properties


@pytest.mark.asyncio
async def test_create_relations_with_properties(memory):
    # Create test entities
    test_entities = [
        Entity(name="Document", type="Document", properties={"version": "1.0"}),
        Entity(name="Section", type="Section", properties={"title": "Introduction"})
    ]
    await memory.create_entities(test_entities)
    
    # Create test relation with properties
    test_relations = [
        Relation(
            source="Document", 
            target="Section", 
            relationType="hasPart",
            properties={
                "dateCreated": "2025-01-16T10:31:02",
                "order": 1,
                "required": True
            }
        )
    ]
    
    # Create relation in the graph
    created_relations = await memory.create_relations(test_relations)
    assert len(created_relations) == 1
    assert created_relations[0].properties["dateCreated"] == "2025-01-16T10:31:02"
    
    # Read the graph
    graph = await memory.read_graph()
    
    # Verify relation was created with properties
    assert len(graph.relations) == 1
    relation = graph.relations[0]
    assert relation.source == "Document"
    assert relation.target == "Section"
    assert relation.relationType == "hasPart"
    assert relation.properties["dateCreated"] == "2025-01-16T10:31:02"
    assert relation.properties["order"] == 1
    assert relation.properties["required"] == True

@pytest.mark.asyncio
async def test_update_properties(memory):
    # Create test entity
    test_entity = Entity(name="Charlie", type="Person", properties={"status": "active"})
    await memory.create_entities([test_entity])
    
    # Update properties
    property_updates = [
        PropertyUpdate(entityName="Charlie", properties={"age": 30, "city": "NYC"})
    ]
    
    result = await memory.update_properties(property_updates)
    assert len(result) == 1
    
    # Read the graph
    graph = await memory.read_graph()
    
    # Find Charlie
    charlie = next((e for e in graph.entities if e.name == "Charlie"), None)
    assert charlie is not None
    
    # Verify properties were added/updated
    assert charlie.properties.get("status") == "active"
    assert charlie.properties.get("age") == 30
    assert charlie.properties.get("city") == "NYC"

@pytest.mark.asyncio
async def test_delete_properties(memory):
    # Create test entity with properties
    test_entity = Entity(
        name="Dave", 
        type="Person", 
        properties={"prop1": "value1", "prop2": "value2", "prop3": "value3"}
    )
    await memory.create_entities([test_entity])
    
    # Delete specific properties
    property_deletions = [
        PropertyDeletion(entityName="Dave", propertyKeys=["prop2"])
    ]
    
    await memory.delete_properties(property_deletions)
    
    # Read the graph
    graph = await memory.read_graph()
    
    # Find Dave
    dave = next((e for e in graph.entities if e.name == "Dave"), None)
    assert dave is not None
    
    # Verify property was deleted
    assert dave.properties.get("prop1") == "value1"
    assert "prop2" not in dave.properties
    assert dave.properties.get("prop3") == "value3"

@pytest.mark.asyncio
async def test_delete_entities(memory):
    # Create test entities
    test_entities = [
        Entity(name="Eve", type="Person", properties={}),
        Entity(name="Frank", type="Person", properties={})
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
async def test_delete_relations(memory):
    # Create test entities
    test_entities = [
        Entity(name="Grace", type="Person", properties={}),
        Entity(name="Hank", type="Person", properties={})
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
    graph = await memory.read_graph()
    
    # Verify only the WORKS_WITH relation remains
    assert len(graph.relations) == 1
    assert graph.relations[0].relationType == "WORKS_WITH"

@pytest.mark.asyncio
async def test_search_nodes(memory):
    # Create test entities
    test_entities = [
        Entity(name="Ian", type="Person", properties={"preference": "coffee"}),
        Entity(name="Jane", type="Person", properties={"preference": "tea"}),
        Entity(name="Coffee", type="Beverage", properties={"temperature": "hot"})
    ]
    await memory.create_entities(test_entities)
    
    # Search for coffee-related nodes by name/type
    result = await memory.search_nodes("coffee")
    
    # Verify search results
    entity_names = [e.name for e in result.entities]
    assert "Coffee" in entity_names
    
    # Search by property
    result2 = await memory.search_nodes("entity.preference = 'coffee'")
    entity_names2 = [e.name for e in result2.entities]
    assert "Ian" in entity_names2
    assert "Jane" not in entity_names2

@pytest.mark.asyncio
async def test_find_nodes(memory):
    # Create test entities
    test_entities = [
        Entity(name="Kevin", type="Person", properties={}),
        Entity(name="Laura", type="Person", properties={}),
        Entity(name="Mike", type="Person", properties={})
    ]
    await memory.create_entities(test_entities)
    
    # Open specific nodes
    result = await memory.find_nodes(["Kevin", "Laura"])
    
    # Verify only requested nodes are returned
    entity_names = [e.name for e in result.entities]
    assert "Kevin" in entity_names
    assert "Laura" in entity_names
    assert "Mike" not in entity_names 