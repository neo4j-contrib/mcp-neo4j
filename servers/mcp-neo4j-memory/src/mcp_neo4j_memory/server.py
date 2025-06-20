import os
import logging
import json
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import neo4j
from neo4j import GraphDatabase
from pydantic import BaseModel

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory')
logger.setLevel(logging.INFO)

# Models for our knowledge graph
class Entity(BaseModel):
    name: str
    type: str
    properties: Dict[str, Any] = {}

class Relation(BaseModel):
    source: str
    target: str
    relationType: str

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]

class PropertyUpdate(BaseModel):
    entityName: str
    properties: Dict[str, Any]

class PropertyDeletion(BaseModel):
    entityName: str
    propertyKeys: List[str]

class Neo4jMemory:
    def __init__(self, neo4j_driver):
        self.neo4j_driver = neo4j_driver
        self.create_fulltext_index()

    def create_fulltext_index(self):
        try:
            # Create index on name and type only, as properties is a complex object
            query = """
            CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) ON EACH [m.name, m.type];
            """
            self.neo4j_driver.execute_query(query)
            logger.info("Created fulltext search index")
        except neo4j.exceptions.ClientError as e:
            if "An index with this name already exists" in str(e):
                logger.info("Fulltext search index already exists")
            else:
                raise e

    async def load_graph(self, filter_query="*"):
        query = """
            CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct entity {.*, properties: properties(entity)}) as nodes,
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
        
        entities = []
        for node in nodes:
            if node and node.get('name'):
                # Get all properties except name and type
                all_props = node.get('properties', {})
                filtered_props = {k: v for k, v in all_props.items() if k not in ['name', 'type']}
                
                entities.append(Entity(
                    name=node.get('name'),
                    type=node.get('type'),
                    properties=filtered_props
                ))
        
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
        for entity in entities:
            query = f"""
            WITH $entity as entity
            MERGE (e:Memory {{ name: entity.name }})
            SET e.type = entity.type
            SET e += entity.properties
            SET e:{entity.type}
            """
            self.neo4j_driver.execute_query(query, {"entity": entity.model_dump()})

        return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (from:Memory),(to:Memory)
            WHERE from.name = relation.source
            AND  to.name = relation.target
            MERGE (from)-[r:{relation.relationType}]->(to)
            """
            
            self.neo4j_driver.execute_query(
                query, 
                {"relation": relation.model_dump()}
            )

        return relations

    async def update_properties(self, updates: List[PropertyUpdate]) -> List[Dict[str, Any]]:
        results = []
        for update in updates:
            query = """
            MATCH (e:Memory { name: $entityName })
            SET e += $properties
            RETURN e.name as name, $properties as updatedProperties
            """
            
            result = self.neo4j_driver.execute_query(
                query, 
                {"entityName": update.entityName, "properties": update.properties}
            )
            
            if result.records:
                record = result.records[0]
                results.append({
                    "entityName": record.get("name"), 
                    "updatedProperties": record.get("updatedProperties")
                })
        
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """
        
        self.neo4j_driver.execute_query(query, {"entities": entity_names})

    async def delete_properties(self, deletions: List[PropertyDeletion]) -> None:
        for deletion in deletions:
            for key in deletion.propertyKeys:
                query = """
                MATCH (e:Memory { name: $entityName })
                REMOVE e[$key]
                """
                self.neo4j_driver.execute_query(
                    query, 
                    {"entityName": deletion.entityName, "key": key}
                )

    async def delete_relations(self, relations: List[Relation]) -> None:
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (source:Memory)-[r:{relation.relationType}]->(target:Memory)
            WHERE source.name = relation.source
            AND target.name = relation.target
            DELETE r
            """
            self.neo4j_driver.execute_query(
                query, 
                {"relation": relation.model_dump()}
            )

    async def read_graph(self) -> KnowledgeGraph:
        return await self.load_graph()

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        # For simple queries, use the fulltext index
        if not any(op in query for op in [':', '=', 'AND', 'OR', 'WHERE']):
            return await self.load_graph(query)
        
        # For complex queries with property searches, use a custom query
        cypher_query = """
            MATCH (entity:Memory)
            WHERE """ + query + """
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct entity {.*, properties: properties(entity)}) as nodes,
            collect(distinct {
                source: startNode(r).name, 
                target: endNode(r).name, 
                relationType: type(r)
            }) as relations
        """
        
        result = self.neo4j_driver.execute_query(cypher_query)
        
        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])
        
        record = result.records[0]
        nodes = record.get('nodes')
        rels = record.get('relations')
        
        entities = []
        for node in nodes:
            if node and node.get('name'):
                # Get all properties except name and type
                all_props = node.get('properties', {})
                filtered_props = {k: v for k, v in all_props.items() if k not in ['name', 'type']}
                
                entities.append(Entity(
                    name=node.get('name'),
                    type=node.get('type'),
                    properties=filtered_props
                ))
        
        relations = [
            Relation(
                source=rel.get('source'),
                target=rel.get('target'),
                relationType=rel.get('relationType')
            )
            for rel in rels if rel.get('source') and rel.get('target') and rel.get('relationType')
        ]
        
        return KnowledgeGraph(entities=entities, relations=relations)

    async def find_nodes(self, names: List[str]) -> KnowledgeGraph:
        return await self.load_graph("name: (" + " ".join(names) + ")")

async def main(neo4j_uri: str, neo4j_user: str, neo4j_password: str, neo4j_database: str):
    logger.info(f"Connecting to neo4j MCP Server with DB URL: {neo4j_uri}")

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(
        neo4j_uri,
        auth=(neo4j_user, neo4j_password), 
        database=neo4j_database
    )
    
    # Verify connection
    try:
        neo4j_driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {neo4j_uri}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        exit(1)

    # Initialize memory
    memory = Neo4jMemory(neo4j_driver)
    
    # Create MCP server
    server = Server("mcp-neo4j-memory")

    # Register handlers
    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="create_entities",
                description="Create multiple new entities in the knowledge graph",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "The name of the entity"},
                                    "type": {"type": "string", "description": "The type of the entity"},
                                    "properties": {
                                        "type": "object",
                                        "description": "A dictionary of key-value properties for the entity",
                                        "additionalProperties": True
                                    },
                                },
                                "required": ["name", "type"],
                            },
                        },
                    },
                    "required": ["entities"],
                },
            ),
            types.Tool(
                name="create_relations",
                description="Create multiple new relations between entities in the knowledge graph. Relations should be in active voice",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "relations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string", "description": "The name of the entity where the relation starts"},
                                    "target": {"type": "string", "description": "The name of the entity where the relation ends"},
                                    "relationType": {"type": "string", "description": "The type of the relation"},
                                },
                                "required": ["source", "target", "relationType"],
                            },
                        },
                    },
                    "required": ["relations"],
                },
            ),
            types.Tool(
                name="update_properties",
                description="Update properties on existing entities in the knowledge graph",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "updates": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "entityName": {"type": "string", "description": "The name of the entity to update"},
                                    "properties": {
                                        "type": "object",
                                        "description": "Properties to add or update on the entity",
                                        "additionalProperties": True
                                    },
                                },
                                "required": ["entityName", "properties"],
                            },
                        },
                    },
                    "required": ["updates"],
                },
            ),
            types.Tool(
                name="delete_entities",
                description="Delete multiple entities and their associated relations from the knowledge graph",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entityNames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "An array of entity names to delete"
                        },
                    },
                    "required": ["entityNames"],
                },
            ),
            types.Tool(
                name="delete_properties",
                description="Delete specific properties from entities in the knowledge graph",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deletions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "entityName": {"type": "string", "description": "The name of the entity containing the properties"},
                                    "propertyKeys": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "An array of property keys to delete"
                                    },
                                },
                                "required": ["entityName", "propertyKeys"],
                            },
                        },
                    },
                    "required": ["deletions"],
                },
            ),
            types.Tool(
                name="delete_relations",
                description="Delete multiple relations from the knowledge graph",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "relations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string", "description": "The name of the entity where the relation starts"},
                                    "target": {"type": "string", "description": "The name of the entity where the relation ends"},
                                    "relationType": {"type": "string", "description": "The type of the relation"},
                                },
                                "required": ["source", "target", "relationType"],
                            },
                            "description": "An array of relations to delete"
                        },
                    },
                    "required": ["relations"],
                },
            ),
            types.Tool(
                name="read_graph",
                description="Read the entire knowledge graph",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="search_nodes",
                description="Search for nodes in the knowledge graph based on a query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query. For simple searches: text to match against names/types. For property searches: Cypher WHERE clause (e.g., 'entity.age > 30', 'entity.city = \"NYC\"', 'entity.status = \"active\" AND entity.priority = \"high\"')"},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="find_nodes",
                description="Find specific nodes in the knowledge graph by their names",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "An array of entity names to retrieve",
                        },
                    },
                    "required": ["names"],
                },
            ),
            types.Tool(
                name="open_nodes",
                description="Open specific nodes in the knowledge graph by their names",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "An array of entity names to retrieve",
                        },
                    },
                    "required": ["names"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Dict[str, Any] | None
    ) -> List[types.TextContent | types.ImageContent]:
        try:
            if name == "read_graph":
                result = await memory.read_graph()
                return [types.TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

            if not arguments:
                raise ValueError(f"No arguments provided for tool: {name}")

            if name == "create_entities":
                entities = [Entity(**entity) for entity in arguments.get("entities", [])]
                result = await memory.create_entities(entities)
                return [types.TextContent(type="text", text=json.dumps([e.model_dump() for e in result], indent=2))]
                
            elif name == "create_relations":
                relations = [Relation(**relation) for relation in arguments.get("relations", [])]
                result = await memory.create_relations(relations)
                return [types.TextContent(type="text", text=json.dumps([r.model_dump() for r in result], indent=2))]
                
            elif name == "update_properties":
                updates = [PropertyUpdate(**update) for update in arguments.get("updates", [])]
                result = await memory.update_properties(updates)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "delete_entities":
                await memory.delete_entities(arguments.get("entityNames", []))
                return [types.TextContent(type="text", text="Entities deleted successfully")]
                
            elif name == "delete_properties":
                deletions = [PropertyDeletion(**deletion) for deletion in arguments.get("deletions", [])]
                await memory.delete_properties(deletions)
                return [types.TextContent(type="text", text="Properties deleted successfully")]
                
            elif name == "delete_relations":
                relations = [Relation(**relation) for relation in arguments.get("relations", [])]
                await memory.delete_relations(relations)
                return [types.TextContent(type="text", text="Relations deleted successfully")]
                
            elif name == "search_nodes":
                result = await memory.search_nodes(arguments.get("query", ""))
                return [types.TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]
                
            elif name == "find_nodes" or name == "open_nodes":
                result = await memory.find_nodes(arguments.get("names", []))
                return [types.TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]
                
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # Start the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP Knowledge Graph Memory using Neo4j running on stdio")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-neo4j-memory",
                server_version="1.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
