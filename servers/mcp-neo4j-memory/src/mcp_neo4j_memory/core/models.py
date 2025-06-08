"""
Data models for the MCP Neo4j Memory knowledge graph.
"""

from typing import List
from pydantic import BaseModel


class Entity(BaseModel):
    """Represents an entity in the knowledge graph."""
    name: str
    type: str
    observations: List[str]


class Relation(BaseModel):
    """Represents a relation between entities in the knowledge graph."""
    source: str
    target: str
    relationType: str


class KnowledgeGraph(BaseModel):
    """Represents a complete knowledge graph with entities and relations."""
    entities: List[Entity]
    relations: List[Relation]


class ObservationAddition(BaseModel):
    """Represents observations to be added to an entity."""
    entityName: str
    contents: List[str]


class ObservationDeletion(BaseModel):
    """Represents observations to be deleted from an entity."""
    entityName: str
    observations: List[str]
