"""
Unit tests for core data models in the refactored MCP Neo4j Memory server.
"""

import pytest
from pydantic import ValidationError

from mcp_neo4j_memory.core.models import (
    Entity, 
    Relation, 
    KnowledgeGraph, 
    ObservationAddition, 
    ObservationDeletion
)


class TestEntity:
    """Test Entity model."""
    
    def test_entity_creation(self):
        """Test creating a valid entity."""
        entity = Entity(
            name="Test Person",
            type="Person",
            observations=["Observation 1", "Observation 2"]
        )
        
        assert entity.name == "Test Person"
        assert entity.type == "Person"
        assert len(entity.observations) == 2
        assert "Observation 1" in entity.observations
    
    def test_entity_empty_observations(self):
        """Test creating entity with empty observations."""
        entity = Entity(
            name="Empty Person",
            type="Person", 
            observations=[]
        )
        
        assert entity.name == "Empty Person"
        assert len(entity.observations) == 0
    
    def test_entity_validation_error(self):
        """Test that invalid entity data raises validation error."""
        with pytest.raises(ValidationError):
            Entity(
                # Missing required name field
                type="Person",
                observations=[]
            )


class TestRelation:
    """Test Relation model."""
    
    def test_relation_creation(self):
        """Test creating a valid relation."""
        relation = Relation(
            source="Person A",
            target="Person B",
            relationType="KNOWS"
        )
        
        assert relation.source == "Person A"
        assert relation.target == "Person B"
        assert relation.relationType == "KNOWS"
    
    def test_relation_validation_error(self):
        """Test that invalid relation data raises validation error."""
        with pytest.raises(ValidationError):
            Relation(
                source="Person A",
                # Missing target and relationType
            )


class TestKnowledgeGraph:
    """Test KnowledgeGraph model."""
    
    def test_knowledge_graph_creation(self):
        """Test creating a knowledge graph with entities and relations."""
        entities = [
            Entity(name="Alice", type="Person", observations=["Likes coding"]),
            Entity(name="Bob", type="Person", observations=["Enjoys reading"])
        ]
        
        relations = [
            Relation(source="Alice", target="Bob", relationType="FRIENDS_WITH")
        ]
        
        graph = KnowledgeGraph(entities=entities, relations=relations)
        
        assert len(graph.entities) == 2
        assert len(graph.relations) == 1
        assert graph.entities[0].name == "Alice"
        assert graph.relations[0].relationType == "FRIENDS_WITH"
    
    def test_empty_knowledge_graph(self):
        """Test creating an empty knowledge graph."""
        graph = KnowledgeGraph(entities=[], relations=[])
        
        assert len(graph.entities) == 0
        assert len(graph.relations) == 0


class TestObservationAddition:
    """Test ObservationAddition model."""
    
    def test_observation_addition_creation(self):
        """Test creating observation addition."""
        addition = ObservationAddition(
            entityName="Test Entity",
            contents=["New observation 1", "New observation 2"]
        )
        
        assert addition.entityName == "Test Entity"
        assert len(addition.contents) == 2
        assert "New observation 1" in addition.contents
    
    def test_empty_contents(self):
        """Test observation addition with empty contents."""
        addition = ObservationAddition(
            entityName="Test Entity",
            contents=[]
        )
        
        assert addition.entityName == "Test Entity"
        assert len(addition.contents) == 0


class TestObservationDeletion:
    """Test ObservationDeletion model."""
    
    def test_observation_deletion_creation(self):
        """Test creating observation deletion."""
        deletion = ObservationDeletion(
            entityName="Test Entity",
            observations=["Old observation 1", "Old observation 2"]
        )
        
        assert deletion.entityName == "Test Entity"
        assert len(deletion.observations) == 2
        assert "Old observation 1" in deletion.observations
    
    def test_single_observation_deletion(self):
        """Test deleting single observation."""
        deletion = ObservationDeletion(
            entityName="Test Entity",
            observations=["Single observation"]
        )
        
        assert deletion.entityName == "Test Entity"
        assert len(deletion.observations) == 1
        assert deletion.observations[0] == "Single observation"


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_entity_dict_conversion(self):
        """Test converting entity to/from dict."""
        entity = Entity(
            name="Test Person",
            type="Person",
            observations=["Test observation"]
        )
        
        # Convert to dict
        entity_dict = entity.model_dump()
        
        assert entity_dict["name"] == "Test Person"
        assert entity_dict["type"] == "Person"
        assert len(entity_dict["observations"]) == 1
        
        # Convert back from dict
        new_entity = Entity(**entity_dict)
        
        assert new_entity.name == entity.name
        assert new_entity.type == entity.type
        assert new_entity.observations == entity.observations
    
    def test_knowledge_graph_dict_conversion(self):
        """Test converting knowledge graph to/from dict."""
        entities = [
            Entity(name="Alice", type="Person", observations=["Coder"]),
            Entity(name="Bob", type="Person", observations=["Reader"])
        ]
        
        relations = [
            Relation(source="Alice", target="Bob", relationType="KNOWS")
        ]
        
        graph = KnowledgeGraph(entities=entities, relations=relations)
        
        # Convert to dict
        graph_dict = graph.model_dump()
        
        assert len(graph_dict["entities"]) == 2
        assert len(graph_dict["relations"]) == 1
        assert graph_dict["entities"][0]["name"] == "Alice"
        assert graph_dict["relations"][0]["relationType"] == "KNOWS"
        
        # Convert back from dict
        new_graph = KnowledgeGraph(**graph_dict)
        
        assert len(new_graph.entities) == len(graph.entities)
        assert len(new_graph.relations) == len(graph.relations)
        assert new_graph.entities[0].name == graph.entities[0].name


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_core_models.py -v
    pytest.main([__file__, "-v"])
