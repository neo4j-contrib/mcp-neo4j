"""
Neo4j 3.5 Compatible Memory Module

Synchronous version of the Neo4j Memory knowledge graph storage.
Key changes from 5.x:
- All methods are synchronous (no async/await)
- Fulltext index creation uses 3.5 procedure syntax
- No multi-database support
"""

import logging
from typing import Any

from neo4j import GraphDatabase
from pydantic import BaseModel, Field

logger = logging.getLogger("mcp_neo4j_memory")
logger.setLevel(logging.INFO)


class Entity(BaseModel):
    """Represents a memory entity in the knowledge graph."""

    name: str = Field(
        description="Unique identifier/name for the entity.",
        min_length=1,
        examples=["John Smith", "Neo4j Inc", "San Francisco"],
    )
    type: str = Field(
        description="Category or classification of the entity.",
        min_length=1,
        examples=["person", "company", "location"],
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    )
    observations: list[str] = Field(
        description="List of facts or observations about this entity.",
        examples=[["Works at Neo4j", "Lives in San Francisco"]],
    )


class Relation(BaseModel):
    """Represents a relationship between two entities."""

    source: str = Field(
        description="Name of the source entity.",
        min_length=1,
    )
    target: str = Field(
        description="Name of the target entity.",
        min_length=1,
    )
    relationType: str = Field(
        description="Type of relationship (SCREAMING_SNAKE_CASE).",
        min_length=1,
        examples=["WORKS_AT", "LIVES_IN", "MANAGES"],
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    )


class KnowledgeGraph(BaseModel):
    """Complete knowledge graph with entities and relationships."""

    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)


class ObservationAddition(BaseModel):
    """Request to add observations to an entity."""

    entityName: str = Field(min_length=1)
    observations: list[str] = Field(min_length=1)


class ObservationDeletion(BaseModel):
    """Request to delete observations from an entity."""

    entityName: str = Field(min_length=1)
    observations: list[str] = Field(min_length=1)


class Neo4j35Driver:
    """Neo4j 3.5 compatible driver wrapper."""

    def __init__(self, uri: str, auth: tuple[str, str]):
        self._driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self._driver.close()

    def verify_connectivity(self):
        with self._driver.session() as session:
            session.run("RETURN 1").consume()

    def read(self, query: str, params: dict | None = None) -> list[dict]:
        params = params or {}
        with self._driver.session() as session:
            result = session.read_transaction(lambda tx: tx.run(query, params).data())
            return result

    def write(self, query: str, params: dict | None = None) -> None:
        params = params or {}
        with self._driver.session() as session:
            session.write_transaction(lambda tx: tx.run(query, params).consume())


class Neo4jMemory35:
    """
    Neo4j 3.5 compatible memory storage.
    
    All operations are synchronous.
    """

    def __init__(self, driver: Neo4j35Driver):
        self.driver = driver

    def create_fulltext_index(self) -> None:
        """
        Create fulltext search index for Memory nodes.
        
        Neo4j 3.5 uses a different syntax for fulltext indexes.
        Note: May fail if index already exists - this is expected.
        """
        try:
            # Neo4j 3.5 fulltext index creation syntax
            query = """
            CALL db.index.fulltext.createNodeIndex(
                'search',
                ['Memory'],
                ['name', 'type', 'observations']
            )
            """
            self.driver.write(query)
            logger.info("Created fulltext search index")
        except Exception as e:
            # Index might already exist, which is fine
            if "already exists" in str(e).lower():
                logger.debug("Fulltext index already exists")
            else:
                logger.warning(f"Fulltext index creation: {e}")

    def load_graph(self, filter_query: str = "*") -> KnowledgeGraph:
        """Load knowledge graph using fulltext search."""
        logger.info("Loading knowledge graph from Neo4j")

        query = """
            CALL db.index.fulltext.queryNodes('search', $filter) YIELD node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct {
                name: entity.name, 
                type: entity.type, 
                observations: entity.observations
            }) as nodes,
            collect(distinct {
                source: startNode(r).name, 
                target: endNode(r).name, 
                relationType: type(r)
            }) as relations
        """

        results = self.driver.read(query, {"filter": filter_query})

        if not results:
            return KnowledgeGraph(entities=[], relations=[])

        record = results[0]
        nodes = record.get("nodes", [])
        rels = record.get("relations", [])

        entities = [
            Entity(
                name=node["name"],
                type=node["type"],
                observations=node.get("observations", []),
            )
            for node in nodes
            if node.get("name")
        ]

        relations = [
            Relation(
                source=rel["source"],
                target=rel["target"],
                relationType=rel["relationType"],
            )
            for rel in rels
            if rel.get("relationType")
        ]

        return KnowledgeGraph(entities=entities, relations=relations)

    def create_entities(self, entities: list[Entity]) -> list[Entity]:
        """Create multiple new entities in the knowledge graph."""
        logger.info(f"Creating {len(entities)} entities")

        for entity in entities:
            query = f"""
            WITH $entity as entity
            MERGE (e:Memory {{ name: entity.name }})
            SET e += entity {{ .type, .observations }}
            SET e:`{entity.type}`
            """
            self.driver.write(query, {"entity": entity.model_dump()})

        return entities

    def create_relations(self, relations: list[Relation]) -> list[Relation]:
        """Create multiple new relations between entities."""
        logger.info(f"Creating {len(relations)} relations")

        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (from:Memory),(to:Memory)
            WHERE from.name = relation.source
            AND to.name = relation.target
            MERGE (from)-[r:`{relation.relationType}`]->(to)
            """
            self.driver.write(query, {"relation": relation.model_dump()})

        return relations

    def add_observations(
        self, observations: list[ObservationAddition]
    ) -> list[dict[str, Any]]:
        """Add new observations to existing entities."""
        logger.info(f"Adding observations to {len(observations)} entities")

        query = """
        UNWIND $observations as obs  
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.observations WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new
        RETURN e.name as name, new
        """

        # Use write transaction since we're modifying data
        with self.driver._driver.session() as session:
            result = session.write_transaction(
                lambda tx: tx.run(
                    query, {"observations": [obs.model_dump() for obs in observations]}
                ).data()
            )

        return [
            {"entityName": record.get("name"), "addedObservations": record.get("new")}
            for record in result
        ]

    def delete_entities(self, entity_names: list[str]) -> None:
        """Delete multiple entities and their associated relations."""
        logger.info(f"Deleting {len(entity_names)} entities")

        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """
        self.driver.write(query, {"entities": entity_names})
        logger.info(f"Successfully deleted {len(entity_names)} entities")

    def delete_observations(self, deletions: list[ObservationDeletion]) -> None:
        """Delete specific observations from entities."""
        logger.info(f"Deleting observations from {len(deletions)} entities")

        query = """
        UNWIND $deletions as d  
        MATCH (e:Memory { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations,[]) WHERE NOT o IN d.observations]
        """
        self.driver.write(
            query, {"deletions": [deletion.model_dump() for deletion in deletions]}
        )
        logger.info(f"Successfully deleted observations from {len(deletions)} entities")

    def delete_relations(self, relations: list[Relation]) -> None:
        """Delete multiple relations from the graph."""
        logger.info(f"Deleting {len(relations)} relations")

        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (source:Memory)-[r:`{relation.relationType}`]->(target:Memory)
            WHERE source.name = relation.source
            AND target.name = relation.target
            DELETE r
            """
            self.driver.write(query, {"relation": relation.model_dump()})

        logger.info(f"Successfully deleted {len(relations)} relations")

    def read_graph(self) -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        return self.load_graph()

    def search_memories(self, query: str) -> KnowledgeGraph:
        """Search for memories based on a query with Fulltext Search."""
        logger.info(f"Searching for memories with query: '{query}'")
        return self.load_graph(query)

    def find_memories_by_name(self, names: list[str]) -> KnowledgeGraph:
        """Find specific memories by their names."""
        logger.info(f"Finding {len(names)} memories by name")

        query = """
        MATCH (e:Memory)
        WHERE e.name IN $names
        RETURN e.name as name, e.type as type, e.observations as observations
        """
        result_nodes = self.driver.read(query, {"names": names})

        entities = [
            Entity(
                name=record["name"],
                type=record["type"],
                observations=record.get("observations", []),
            )
            for record in result_nodes
        ]

        # Get relations for found entities
        relations = []
        if entities:
            rel_query = """
            MATCH (source:Memory)-[r]->(target:Memory)
            WHERE source.name IN $names OR target.name IN $names
            RETURN source.name as source, target.name as target, type(r) as relationType
            """
            result_relations = self.driver.read(rel_query, {"names": names})

            relations = [
                Relation(
                    source=record["source"],
                    target=record["target"],
                    relationType=record["relationType"],
                )
                for record in result_relations
            ]

        logger.info(f"Found {len(entities)} entities and {len(relations)} relations")
        return KnowledgeGraph(entities=entities, relations=relations)


def create_driver(uri: str, username: str, password: str) -> Neo4j35Driver:
    """Create a Neo4j 3.5 compatible driver."""
    return Neo4j35Driver(uri, auth=(username, password))
