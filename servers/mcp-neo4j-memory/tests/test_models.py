import pytest
from mcp_neo4j_memory.server import Entity, Relation, PropertyUpdate, PropertyDeletion, KnowledgeGraph


def test_entity_model():
    """Test Entity model creation and validation."""
    entity = Entity(
        name="Alice", 
        type="Person", 
        properties={"hobby": "reading", "workplace": "Company X"}
    )
    
    assert entity.name == "Alice"
    assert entity.type == "Person"
    assert len(entity.properties) == 2
    assert entity.properties["hobby"] == "reading"
    assert entity.properties["workplace"] == "Company X"


def test_relation_model():
    """Test Relation model creation and validation."""
    relation = Relation(
        source="Alice",
        target="Bob", 
        relationType="KNOWS"
    )
    
    assert relation.source == "Alice"
    assert relation.target == "Bob"
    assert relation.relationType == "KNOWS"
    assert relation.properties == {}  # Default empty dict


def test_relation_model_with_properties():
    """Test Relation model with properties."""
    relation = Relation(
        source="Document",
        target="Section",
        relationType="hasPart",
        properties={
            "dateCreated": "2025-01-16T10:31:02",
            "order": 1
        }
    )
    
    assert relation.source == "Document"
    assert relation.target == "Section"
    assert relation.relationType == "hasPart"
    assert relation.properties["dateCreated"] == "2025-01-16T10:31:02"
    assert relation.properties["order"] == 1


def test_knowledge_graph_model():
    """Test KnowledgeGraph model with entities and relations."""
    entities = [
        Entity(name="Alice", type="Person", properties={"role": "Developer"}),
        Entity(name="Bob", type="Person", properties={"role": "Manager"})
    ]
    relations = [
        Relation(source="Alice", target="Bob", relationType="REPORTS_TO")
    ]
    
    graph = KnowledgeGraph(entities=entities, relations=relations)
    
    assert len(graph.entities) == 2
    assert len(graph.relations) == 1
    assert graph.entities[0].name == "Alice"
    assert graph.relations[0].relationType == "REPORTS_TO"


def test_property_update_model():
    """Test PropertyUpdate model."""
    prop_update = PropertyUpdate(
        entityName="Alice",
        properties={"status": "active", "level": 5}
    )
    
    assert prop_update.entityName == "Alice"
    assert len(prop_update.properties) == 2
    assert prop_update.properties["status"] == "active"
    assert prop_update.properties["level"] == 5


def test_property_deletion_model():
    """Test PropertyDeletion model."""
    prop_deletion = PropertyDeletion(
        entityName="Alice",
        propertyKeys=["old_property"]
    )
    
    assert prop_deletion.entityName == "Alice"
    assert len(prop_deletion.propertyKeys) == 1
    assert "old_property" in prop_deletion.propertyKeys