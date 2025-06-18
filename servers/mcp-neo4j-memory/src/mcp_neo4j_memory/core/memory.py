"""
Neo4j memory management for the knowledge graph.
"""

import logging
import re
from typing import Any, Dict, List

import neo4j
from neo4j import GraphDatabase

from .models import Entity, Relation, KnowledgeGraph, ObservationAddition, ObservationDeletion

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory.core.memory')


class Neo4jMemory:
    """Manages knowledge graph storage and retrieval using Neo4j."""
    
    def __init__(self, neo4j_driver):
        self.neo4j_driver = neo4j_driver
        self.create_fulltext_index()

    def create_fulltext_index(self):
        """Create a fulltext search index for Memory nodes."""
        try:
            query = """
            CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) ON EACH [m.name, m.type, m.observations];
            """
            self.neo4j_driver.execute_query(query)
            logger.info("Created fulltext search index")
        except neo4j.exceptions.ClientError as e:
            if "An index with this name already exists" in str(e):
                logger.info("Fulltext search index already exists")
            else:
                raise e

    async def load_graph(self, filter_query="*"):
        """Load knowledge graph based on a filter query."""
        query = """
            CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
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

        result = self.neo4j_driver.execute_query(query, {"filter": filter_query})

        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])

        record = result.records[0]
        nodes = record.get('nodes')
        rels = record.get('relations')

        entities = [
            Entity(
                name=node.get('name'),
                type=node.get('type'),
                observations=node.get('observations', [])
            )
            for node in nodes if node.get('name')
        ]

        relations = [
            Relation(
                source=rel.get('source'),
                target=rel.get('target'),
                relationType=rel.get('relationType')
            )
            for rel in rels if rel.get('source') and rel.get('target') and rel.get('relationType')
        ]

        logger.debug(f"Loaded entities: {entities}")
        logger.debug(f"Loaded relations: {relations}")

        return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        """Create multiple entities in the knowledge graph."""
        query = """
        UNWIND $entities as entity
        MERGE (e:Memory { name: entity.name })
        SET e += entity {.type, .observations}
        SET e:$(entity.type)
        """

        entities_data = [entity.model_dump() for entity in entities]
        self.neo4j_driver.execute_query(query, {"entities": entities_data})
        return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        """Create multiple relations between entities in the knowledge graph."""
        # Group relations by type for batch processing
        relations_by_type = {}

        for relation in relations:
            relation_type = relation.relationType

            # Validate relation type to prevent Cypher injection
            if not re.match(r"^[A-Z_][A-Z0-9_]*$", relation_type, re.IGNORECASE):
                raise ValueError(f"Invalid relation type: {relation_type}")

            if relation_type not in relations_by_type:
                relations_by_type[relation_type] = []

            relations_by_type[relation_type].append({
                'from_name': relation.source,
                'to_name': relation.target
            })

        # Process each relationship type in batch
        for relation_type, relations_batch in relations_by_type.items():
            query = f"""
                    UNWIND $relations_batch AS rel
                    MATCH (from:Memory), (to:Memory)
                    WHERE from.name = rel.from_name AND to.name = rel.to_name
                    MERGE (from)-[r:{relation_type}]->(to)
                """

            self.neo4j_driver.execute_query(
                query,
                {"relations_batch": relations_batch}
            )

        return relations

    async def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
        """Add new observations to existing entities."""
        query = """
        UNWIND $observations as obs
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.contents WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new
        RETURN e.name as name, new
        """

        result = self.neo4j_driver.execute_query(
            query,
            {"observations": [obs.model_dump() for obs in observations]}
        )

        results = [{"entityName": record.get("name"), "addedObservations": record.get("new")} for record in result.records]
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        """Delete multiple entities and their associated relations."""
        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """

        self.neo4j_driver.execute_query(query, {"entities": entity_names})

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        """Delete specific observations from entities."""
        query = """
        UNWIND $deletions as d
        MATCH (e:Memory { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations,[]) WHERE NOT o IN d.observations]
        """
        self.neo4j_driver.execute_query(
            query,
            {
                "deletions": [deletion.model_dump() for deletion in deletions]
            }
        )

    async def delete_relations(self, relations: List[Relation]) -> None:
        """Delete multiple relations from the knowledge graph."""
        # Group relations by type for batch processing
        relations_by_type = {}

        for relation in relations:
            relation_type = relation.relationType

            # Validate relation type to prevent Cypher injection
            if not re.match(r"^[A-Z_][A-Z0-9_]*$", relation_type, re.IGNORECASE):
                raise ValueError(f"Invalid relation type: {relation_type}")

            if relation_type not in relations_by_type:
                relations_by_type[relation_type] = []

            relations_by_type[relation_type].append({
                'source_name': relation.source,
                'target_name': relation.target
            })

        # Delete each relationship type in batch
        for relation_type, relations_batch in relations_by_type.items():
            query = f"""
                  UNWIND $relations_batch AS rel
                  MATCH (source_node:Memory)-[r:{relation_type}]->(target_node:Memory)
                  WHERE source_node.name = rel.source_name
                    AND target_node.name = rel.target_name
                  DELETE r
              """

            self.neo4j_driver.execute_query(
                query,
                {"relations_batch": relations_batch}
            )

    async def read_graph(self) -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        return await self.load_graph()

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        """Search for nodes in the knowledge graph based on a query."""
        return await self.load_graph(query)

    async def find_nodes(self, names: List[str]) -> KnowledgeGraph:
        """Find specific nodes in the knowledge graph by their names."""
        return await self.load_graph("name: (" + " ".join(names) + ")")
