import os
import logging
import json
from typing import Any, Dict, List, Optional, Literal
from contextlib import asynccontextmanager

import neo4j
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel, Field

from fastmcp.resources.types import TextResource
from fastmcp.server import FastMCP

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory')
logger.setLevel(logging.INFO)

# Models for our knowledge graph
class Entity(BaseModel):
    name: str
    type: str
    observations: List[str]

class Relation(BaseModel):
    source: str
    target: str
    relationType: str

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]

class ObservationAddition(BaseModel):
    entityName: str
    contents: List[str]

class ObservationDeletion(BaseModel):
    entityName: str
    observations: List[str]

class Neo4jMemory:
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver

    async def create_fulltext_index(self):
        """Create a fulltext search index for entities if it doesn't exist."""
        async with self.driver.session() as session:
            try:
                await session.run("""
                    CALL db.index.fulltext.createNodeIndex("entity_search", ["Entity"], ["name", "type", "observations"])
                """)
            except Exception as e:
                # Index might already exist, which is fine
                logger.debug(f"Fulltext index creation: {e}")

    async def load_graph(self, filter_query="*"):
        """Load the entire knowledge graph from Neo4j."""
        async with self.driver.session() as session:
            # Load all entities
            entity_result = await session.run("""
                MATCH (e:Entity)
                RETURN e.name as name, e.type as type, e.observations as observations
            """)
            
            entities = []
            async for record in entity_result:
                entities.append(Entity(
                    name=record["name"],
                    type=record["type"],
                    observations=record["observations"] if record["observations"] else []
                ))
            
            # Load all relations
            relation_result = await session.run("""
                MATCH (source:Entity)-[r:RELATION]->(target:Entity)
                RETURN source.name as source, target.name as target, type(r) as relationType
            """)
            
            relations = []
            async for record in relation_result:
                relations.append(Relation(
                    source=record["source"],
                    target=record["target"],
                    relationType=record["relationType"]
                ))
            
            return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        """Create multiple new entities in the knowledge graph."""
        async with self.driver.session() as session:
            for entity in entities:
                await session.run("""
                    MERGE (e:Entity {name: $name})
                    SET e.type = $type, e.observations = $observations
                """, name=entity.name, type=entity.type, observations=entity.observations)
            return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        """Create multiple new relations between entities."""
        async with self.driver.session() as session:
            for relation in relations:
                await session.run("""
                    MATCH (source:Entity {name: $source})
                    MATCH (target:Entity {name: $target})
                    MERGE (source)-[r:RELATION]->(target)
                    SET r.relationType = $relationType
                """, source=relation.source, target=relation.target, relationType=relation.relationType)
            return relations

    async def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
        """Add new observations to existing entities."""
        results = []
        async with self.driver.session() as session:
            for obs in observations:
                await session.run("""
                    MATCH (e:Entity {name: $entityName})
                    SET e.observations = CASE 
                        WHEN e.observations IS NULL THEN $contents
                        ELSE e.observations + $contents
                    END
                """, entityName=obs.entityName, contents=obs.contents)
                results.append({"entity": obs.entityName, "added_observations": obs.contents})
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        """Delete multiple entities and their associated relations."""
        async with self.driver.session() as session:
            await session.run("""
                MATCH (e:Entity)
                WHERE e.name IN $entityNames
                DETACH DELETE e
            """, entityNames=entity_names)

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        """Delete specific observations from entities."""
        async with self.driver.session() as session:
            for deletion in deletions:
                await session.run("""
                    MATCH (e:Entity {name: $entityName})
                    SET e.observations = [obs IN e.observations WHERE NOT obs IN $observations]
                """, entityName=deletion.entityName, observations=deletion.observations)

    async def delete_relations(self, relations: List[Relation]) -> None:
        """Delete multiple relations from the graph."""
        async with self.driver.session() as session:
            for relation in relations:
                await session.run("""
                    MATCH (source:Entity {name: $source})-[r:RELATION]->(target:Entity {name: $target})
                    DELETE r
                """, source=relation.source, target=relation.target)

    async def read_graph(self) -> KnowledgeGraph:
        """Read the entire knowledge graph."""
        return await self.load_graph()

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        """Search for nodes based on a query."""
        async with self.driver.session() as session:
            # Use fulltext search if available, otherwise fallback to simple text search
            try:
                result = await session.run("""
                    CALL db.index.fulltext.queryNodes("entity_search", $query)
                    YIELD node
                    RETURN node.name as name, node.type as type, node.observations as observations
                """, query=query)
            except:
                # Fallback to simple text search
                result = await session.run("""
                    MATCH (e:Entity)
                    WHERE e.name CONTAINS $query OR e.type CONTAINS $query OR ANY(obs IN e.observations WHERE obs CONTAINS $query)
                    RETURN e.name as name, e.type as type, e.observations as observations
                """, query=query)
            
            entities = []
            async for record in result:
                entities.append(Entity(
                    name=record["name"],
                    type=record["type"],
                    observations=record["observations"] if record["observations"] else []
                ))
            
            # Get relations for found entities
            if entities:
                entity_names = [e.name for e in entities]
                relation_result = await session.run("""
                    MATCH (source:Entity)-[r:RELATION]->(target:Entity)
                    WHERE source.name IN $entityNames OR target.name IN $entityNames
                    RETURN source.name as source, target.name as target, type(r) as relationType
                """, entityNames=entity_names)
                
                relations = []
                async for record in relation_result:
                    relations.append(Relation(
                        source=record["source"],
                        target=record["target"],
                        relationType=record["relationType"]
                    ))
            else:
                relations = []
            
            return KnowledgeGraph(entities=entities, relations=relations)

    async def find_nodes(self, names: List[str]) -> KnowledgeGraph:
        """Find specific nodes by their names."""
        async with self.driver.session() as session:
            # Load specified entities
            entity_result = await session.run("""
                MATCH (e:Entity)
                WHERE e.name IN $names
                RETURN e.name as name, e.type as type, e.observations as observations
            """, names=names)
            
            entities = []
            async for record in entity_result:
                entities.append(Entity(
                    name=record["name"],
                    type=record["type"],
                    observations=record["observations"] if record["observations"] else []
                ))
            
            # Get relations for found entities
            if entities:
                relation_result = await session.run("""
                    MATCH (source:Entity)-[r:RELATION]->(target:Entity)
                    WHERE source.name IN $names OR target.name IN $names
                    RETURN source.name as source, target.name as target, type(r) as relationType
                """, names=names)
                
                relations = []
                async for record in relation_result:
                    relations.append(Relation(
                        source=record["source"],
                        target=record["target"],
                        relationType=record["relationType"]
                    ))
            else:
                relations = []
            
            return KnowledgeGraph(entities=entities, relations=relations)


def create_mcp_server(neo4j_driver, memory: Neo4jMemory) -> FastMCP:
    """Create an MCP server instance for memory management."""
    
    mcp: FastMCP = FastMCP("mcp-neo4j-memory", dependencies=["neo4j", "pydantic"], stateless_http=True)

    @mcp.tool()
    async def read_graph() -> list[TextResource]:
        """Read the entire knowledge graph."""
        result = await memory.read_graph()
        return [TextResource(uri="neo4j://graph", text=json.dumps(result.model_dump(), indent=2))]

    @mcp.tool()
    async def create_entities(entities: List[Dict[str, Any]] = Field(..., description="List of entities to create")) -> list[TextResource]:
        """Create multiple new entities in the knowledge graph."""
        entity_objects = [Entity(**entity) for entity in entities]
        result = await memory.create_entities(entity_objects)
        return [TextResource(uri="neo4j://entities", text=json.dumps([e.model_dump() for e in result], indent=2))]

    @mcp.tool()
    async def create_relations(relations: List[Dict[str, Any]] = Field(..., description="List of relations to create")) -> list[TextResource]:
        """Create multiple new relations between entities."""
        relation_objects = [Relation(**relation) for relation in relations]
        result = await memory.create_relations(relation_objects)
        return [TextResource(uri="neo4j://relations", text=json.dumps([r.model_dump() for r in result], indent=2))]

    @mcp.tool()
    async def add_observations(observations: List[Dict[str, Any]] = Field(..., description="List of observations to add")) -> list[TextResource]:
        """Add new observations to existing entities."""
        observation_objects = [ObservationAddition(**obs) for obs in observations]
        result = await memory.add_observations(observation_objects)
        return [TextResource(uri="neo4j://observations", text=json.dumps(result, indent=2))]

    @mcp.tool()
    async def delete_entities(entityNames: List[str] = Field(..., description="List of entity names to delete")) -> list[TextResource]:
        """Delete multiple entities and their associated relations."""
        await memory.delete_entities(entityNames)
        return [TextResource(uri="neo4j://deleted", text="Entities deleted successfully")]

    @mcp.tool()
    async def delete_observations(deletions: List[Dict[str, Any]] = Field(..., description="List of observations to delete")) -> list[TextResource]:
        """Delete specific observations from entities."""
        deletion_objects = [ObservationDeletion(**deletion) for deletion in deletions]
        await memory.delete_observations(deletion_objects)
        return [TextResource(uri="neo4j://deleted", text="Observations deleted successfully")]

    @mcp.tool()
    async def delete_relations(relations: List[Dict[str, Any]] = Field(..., description="List of relations to delete")) -> list[TextResource]:
        """Delete multiple relations from the graph."""
        relation_objects = [Relation(**relation) for relation in relations]
        await memory.delete_relations(relation_objects)
        return [TextResource(uri="neo4j://deleted", text="Relations deleted successfully")]

    @mcp.tool()
    async def search_nodes(query: str = Field(..., description="Search query for nodes")) -> list[TextResource]:
        """Search for nodes based on a query."""
        result = await memory.search_nodes(query)
        return [TextResource(uri="neo4j://search", text=json.dumps(result.model_dump(), indent=2))]

    @mcp.tool()
    async def find_nodes(names: List[str] = Field(..., description="List of node names to find")) -> list[TextResource]:
        """Find specific nodes by name."""
        result = await memory.find_nodes(names)
        return [TextResource(uri="neo4j://nodes", text=json.dumps(result.model_dump(), indent=2))]

    @mcp.tool()
    async def open_nodes(names: List[str] = Field(..., description="List of node names to open")) -> list[TextResource]:
        """Open specific nodes by name (alias for find_nodes)."""
        result = await memory.find_nodes(names)
        return [TextResource(uri="neo4j://nodes", text=json.dumps(result.model_dump(), indent=2))]

    return mcp


async def main(
    neo4j_uri: str, 
    neo4j_user: str, 
    neo4j_password: str, 
    neo4j_database: str,
    transport: Literal["stdio", "sse", "http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
) -> None:
    logger.info(f"Connecting to neo4j MCP Server with DB URL: {neo4j_uri}")

    # Connect to Neo4j
    neo4j_driver = AsyncGraphDatabase.driver(
        neo4j_uri,
        auth=(neo4j_user, neo4j_password), 
        database=neo4j_database
    )
    
    # Verify connection
    try:
        await neo4j_driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {neo4j_uri}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        exit(1)

    # Initialize memory
    memory = Neo4jMemory(neo4j_driver)
    
    # Create fulltext index
    await memory.create_fulltext_index()
    
    # Create MCP server
    mcp = create_mcp_server(neo4j_driver, memory)

    # Run the server with the specified transport
    if transport == "http":
        await mcp.run_http_async(host=host, port=port, path=path)
    elif transport == "stdio":
        await mcp.run_stdio_async()
    elif transport == "sse":
        await mcp.run_sse_async(host=host, port=port, path=path)
    else:
        raise ValueError(f"Unsupported transport: {transport}")
