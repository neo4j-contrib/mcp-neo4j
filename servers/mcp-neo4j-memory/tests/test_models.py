import pytest
from mcp_neo4j_memory.server import Entity, Relation, ObservationAddition, ObservationDeletion, KnowledgeGraph


def test_entity_model():
    """Test Entity model creation and validation."""
    entity = Entity(
        name="Alice", 
        type="Person", 
        observations=["Likes reading", "Works at Company X"]
    )
    
    assert entity.name == "Alice"
    assert entity.type == "Person"
    assert len(entity.observations) == 2
    assert "Likes reading" in entity.observations
    assert "Works at Company X" in entity.observations


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


def test_knowledge_graph_model():
    """Test KnowledgeGraph model with entities and relations."""
    entities = [
        Entity(name="Alice", type="Person", observations=["Developer"]),
        Entity(name="Bob", type="Person", observations=["Manager"])
    ]
    relations = [
        Relation(source="Alice", target="Bob", relationType="REPORTS_TO")
    ]
    
    graph = KnowledgeGraph(entities=entities, relations=relations)
    
    assert len(graph.entities) == 2
    assert len(graph.relations) == 1
    assert graph.entities[0].name == "Alice"
    assert graph.relations[0].relationType == "REPORTS_TO"


def test_observation_addition_model():
    """Test ObservationAddition model."""
    obs_addition = ObservationAddition(
        entityName="Alice",
        contents=["New observation 1", "New observation 2"]
    )
    
    assert obs_addition.entityName == "Alice"
    assert len(obs_addition.contents) == 2
    assert "New observation 1" in obs_addition.contents


def test_observation_deletion_model():
    """Test ObservationDeletion model."""
    obs_deletion = ObservationDeletion(
        entityName="Alice",
        observations=["Old observation"]
    )
    
    assert obs_deletion.entityName == "Alice"
    assert len(obs_deletion.observations) == 1
    assert "Old observation" in obs_deletion.observations