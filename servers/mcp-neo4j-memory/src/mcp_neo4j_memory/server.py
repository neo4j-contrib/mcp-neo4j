import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
import neo4j
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from neo4j import GraphDatabase
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger("mcp_neo4j_memory")
logger.setLevel(logging.INFO)


# Models for our knowledge graph
class TimestampedObservation(BaseModel):
    content: str
    created_at: datetime


class Entity(BaseModel):
    name: str
    type: str
    observations: List[str]  # Keep for backward compatibility
    timestamped_observations: Optional[List[TimestampedObservation]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def model_dump_json_safe(self):
        """Return a JSON-safe dict representation"""
        data = self.model_dump()
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        if self.timestamped_observations:
            data["timestamped_observations"] = [
                {
                    "content": obs.content,
                    "created_at": obs.created_at.isoformat()
                }
                for obs in self.timestamped_observations
            ]
        return data


class Relation(BaseModel):
    source: str
    target: str
    relationType: str


class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]
    
    def model_dump_json_safe(self):
        """Return a JSON-safe dict representation"""
        return {
            "entities": [entity.model_dump_json_safe() for entity in self.entities],
            "relations": [relation.model_dump() for relation in self.relations]
        }


class ObservationAddition(BaseModel):
    entityName: str
    contents: List[str]


class ObservationDeletion(BaseModel):
    entityName: str
    observations: List[str]


class Neo4jMemory:
    def __init__(self, neo4j_driver):
        self.neo4j_driver = neo4j_driver
        self.create_fulltext_index()

    def create_fulltext_index(self):
        try:
            # Create fulltext index for traditional search
            query = """
            CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) ON EACH [m.name, m.type, m.observations];
            """
            self.neo4j_driver.execute_query(query)
            logger.info("Created fulltext search index")

            # Create indexes for temporal queries
            temporal_indexes = [
                "CREATE INDEX memory_created_at IF NOT EXISTS FOR (m:Memory) ON (m.created_at)",
                "CREATE INDEX memory_updated_at IF NOT EXISTS FOR (m:Memory) ON (m.updated_at)",
            ]

            for idx_query in temporal_indexes:
                self.neo4j_driver.execute_query(idx_query)

            logger.info("Created temporal indexes")

        except neo4j.exceptions.ClientError as e:
            if "An index with this name already exists" in str(
                e
            ) or "equivalent index already exists" in str(e):
                logger.info("Indexes already exist")
            else:
                raise e

    async def load_graph(self, filter_query="*"):
        query = """
            CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct {
                name: entity.name, 
                type: entity.type, 
                observations: entity.observations,
                created_at: entity.created_at,
                updated_at: entity.updated_at,
                timestamped_observations: entity.timestamped_observations
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
        nodes = record.get("nodes")
        rels = record.get("relations")

        entities = [
            Entity(
                name=node.get("name"),
                type=node.get("type"),
                observations=node.get("observations", []),
                created_at=node.get("created_at"),
                updated_at=node.get("updated_at"),
                timestamped_observations=node.get("timestamped_observations", []),
            )
            for node in nodes
            if node.get("name")
        ]

        relations = [
            Relation(
                source=rel.get("source"),
                target=rel.get("target"),
                relationType=rel.get("relationType"),
            )
            for rel in rels
            if rel.get("source") and rel.get("target") and rel.get("relationType")
        ]

        logger.debug(f"Loaded entities: {entities}")
        logger.debug(f"Loaded relations: {relations}")

        return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        current_time = datetime.utcnow().isoformat()

        # Prepare entities with timestamps
        entities_data = []
        for entity in entities:
            entity_dict = entity.model_dump_json_safe()
            entity_dict["created_at"] = current_time
            entity_dict["updated_at"] = current_time

            # Convert timestamped observations to the format Neo4j expects
            if entity.timestamped_observations:
                timestamped_obs = []
                for obs in entity.timestamped_observations:
                    timestamped_obs.append(
                        {
                            "content": obs.content,
                            "created_at": obs.created_at.isoformat(),
                        }
                    )
                entity_dict["timestamped_observations"] = timestamped_obs

            entities_data.append(entity_dict)

        query = """
        UNWIND $entities as entity
        MERGE (e:Memory { name: entity.name })
        SET e += entity {.type, .observations, .created_at, .updated_at, .timestamped_observations}
        RETURN count(*)
        """

        self.neo4j_driver.execute_query(query, {"entities": entities_data})
        
        # Return entities with updated timestamps by reloading them
        entity_names = [entity.name for entity in entities]
        updated_graph = await self.find_nodes(entity_names)
        return updated_graph.entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        # Group relations by type for batch processing
        relations_by_type = {}

        for relation in relations:
            relation_type = relation.relationType

            # Validate relation type to prevent Cypher injection
            if not re.match(r"^[A-Z_][A-Z0-9_]*$", relation_type, re.IGNORECASE):
                raise ValueError(f"Invalid relation type: {relation_type}")

            if relation_type not in relations_by_type:
                relations_by_type[relation_type] = []

            relations_by_type[relation_type].append(
                {"from_name": relation.source, "to_name": relation.target}
            )

        # Process each relationship type in batch
        for relation_type, relations_batch in relations_by_type.items():
            query = f"""
                    UNWIND $relations_batch AS rel
                    MATCH (from:Memory), (to:Memory)
                    WHERE from.name = rel.from_name AND to.name = rel.to_name
                    MERGE (from)-[r:{relation_type}]->(to)
                """

            self.neo4j_driver.execute_query(query, {"relations_batch": relations_batch})

        return relations

    async def add_observations(
        self, observations: List[ObservationAddition]
    ) -> List[Dict[str, Any]]:
        current_time = datetime.utcnow().isoformat()

        query = """
        UNWIND $observations as obs  
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.contents WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new,
            e.updated_at = $current_time
        RETURN e.name as name, new
        """

        result = self.neo4j_driver.execute_query(
            query,
            {
                "observations": [obs.model_dump() for obs in observations],
                "current_time": current_time,
            },
        )

        results = [
            {"entityName": record.get("name"), "addedObservations": record.get("new")}
            for record in result.records
        ]
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """

        self.neo4j_driver.execute_query(query, {"entities": entity_names})

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        query = """
        UNWIND $deletions as d  
        MATCH (e:Memory { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations,[]) WHERE NOT o IN d.observations]
        """
        self.neo4j_driver.execute_query(
            query, {"deletions": [deletion.model_dump() for deletion in deletions]}
        )

    async def delete_relations(self, relations: List[Relation]) -> None:
        # Group relations by type for batch processing
        relations_by_type = {}

        for relation in relations:
            relation_type = relation.relationType

            # Validate relation type to prevent Cypher injection
            if not re.match(r"^[A-Z_][A-Z0-9_]*$", relation_type, re.IGNORECASE):
                raise ValueError(f"Invalid relation type: {relation_type}")

            if relation_type not in relations_by_type:
                relations_by_type[relation_type] = []

            relations_by_type[relation_type].append(
                {"source_name": relation.source, "target_name": relation.target}
            )

        # Delete each relationship type in batch
        for relation_type, relations_batch in relations_by_type.items():
            query = f"""
              UNWIND $relations_batch AS rel
              MATCH (source_node:Memory)-[r:{relation_type}]->(target_node:Memory)
              WHERE source_node.name = rel.source_name
                AND target_node.name = rel.target_name
              DELETE r
          """

            self.neo4j_driver.execute_query(query, {"relations_batch": relations_batch})

    async def read_graph(self) -> KnowledgeGraph:
        return await self.load_graph()

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        return await self.load_graph(query)

    async def find_nodes(self, names: List[str]) -> KnowledgeGraph:
        return await self.load_graph("name: (" + " ".join(names) + ")")

    async def get_memories_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> KnowledgeGraph:
        """Get memories created within a specific time range"""
        query = """
        MATCH (entity:Memory)
        WHERE datetime(entity.created_at) >= datetime($start_time) 
          AND datetime(entity.created_at) <= datetime($end_time)
        OPTIONAL MATCH (entity)-[r]-(other)
        RETURN collect(distinct {
            name: entity.name, 
            type: entity.type, 
            observations: entity.observations,
            created_at: entity.created_at,
            updated_at: entity.updated_at
        }) as nodes,
        collect(distinct {
            source: startNode(r).name, 
            target: endNode(r).name, 
            relationType: type(r)
        }) as relations
        """

        result = self.neo4j_driver.execute_query(
            query,
            {"start_time": start_time.isoformat(), "end_time": end_time.isoformat()},
        )

        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])

        record = result.records[0]
        nodes = record.get("nodes")
        rels = record.get("relations")

        entities = [
            Entity(
                name=node.get("name"),
                type=node.get("type"),
                observations=node.get("observations", []),
                created_at=datetime.fromisoformat(node.get("created_at"))
                if node.get("created_at")
                else None,
                updated_at=datetime.fromisoformat(node.get("updated_at"))
                if node.get("updated_at")
                else None,
            )
            for node in nodes
            if node.get("name")
        ]

        relations = [
            Relation(
                source=rel.get("source"),
                target=rel.get("target"),
                relationType=rel.get("relationType"),
            )
            for rel in rels
            if rel.get("source") and rel.get("target") and rel.get("relationType")
        ]

        return KnowledgeGraph(entities=entities, relations=relations)

    async def get_recent_memories(self, days: int = 7) -> KnowledgeGraph:
        """Get memories from the last N days"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        return await self.get_memories_by_time_range(start_time, end_time)

    async def search_with_temporal_decay(
        self, query: str, decay_days: int = 30
    ) -> KnowledgeGraph:
        """Search with temporal decay - newer memories get higher scores"""
        cypher_query = """
        CALL db.index.fulltext.queryNodes('search', $query) yield node as entity, score
        WITH entity, score,
             CASE 
                WHEN entity.created_at IS NOT NULL 
                THEN duration.between(datetime(entity.created_at), datetime()).days
                ELSE $decay_days
             END as days_old
        WITH entity, score * (1.0 - (toFloat(days_old) / $decay_days)) as temporal_score
        WHERE temporal_score > 0
        ORDER BY temporal_score DESC
        OPTIONAL MATCH (entity)-[r]-(other)
        RETURN collect(distinct {
            name: entity.name, 
            type: entity.type, 
            observations: entity.observations,
            created_at: entity.created_at,
            updated_at: entity.updated_at,
            temporal_score: temporal_score
        }) as nodes,
        collect(distinct {
            source: startNode(r).name, 
            target: endNode(r).name, 
            relationType: type(r)
        }) as relations
        """

        result = self.neo4j_driver.execute_query(
            cypher_query, {"query": query, "decay_days": decay_days}
        )

        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])

        record = result.records[0]
        nodes = record.get("nodes")
        rels = record.get("relations")

        entities = [
            Entity(
                name=node.get("name"),
                type=node.get("type"),
                observations=node.get("observations", []),
                created_at=datetime.fromisoformat(node.get("created_at"))
                if node.get("created_at")
                else None,
                updated_at=datetime.fromisoformat(node.get("updated_at"))
                if node.get("updated_at")
                else None,
            )
            for node in nodes
            if node.get("name")
        ]

        relations = [
            Relation(
                source=rel.get("source"),
                target=rel.get("target"),
                relationType=rel.get("relationType"),
            )
            for rel in rels
            if rel.get("source") and rel.get("target") and rel.get("relationType")
        ]

        return KnowledgeGraph(entities=entities, relations=relations)


async def main(
    neo4j_uri: str, neo4j_user: str, neo4j_password: str, neo4j_database: str
):
    logger.info(f"Connecting to neo4j MCP Server with DB URL: {neo4j_uri}")

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(
        neo4j_uri, auth=(neo4j_user, neo4j_password), database=neo4j_database
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
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the entity",
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "The type of the entity",
                                    },
                                    "observations": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "An array of observation contents associated with the entity",
                                    },
                                },
                                "required": ["name", "type", "observations"],
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
                                    "source": {
                                        "type": "string",
                                        "description": "The name of the entity where the relation starts",
                                    },
                                    "target": {
                                        "type": "string",
                                        "description": "The name of the entity where the relation ends",
                                    },
                                    "relationType": {
                                        "type": "string",
                                        "description": "The type of the relation",
                                    },
                                },
                                "required": ["source", "target", "relationType"],
                            },
                        },
                    },
                    "required": ["relations"],
                },
            ),
            types.Tool(
                name="add_observations",
                description="Add new observations to existing entities in the knowledge graph",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "observations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "entityName": {
                                        "type": "string",
                                        "description": "The name of the entity to add the observations to",
                                    },
                                    "contents": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "An array of observation contents to add",
                                    },
                                },
                                "required": ["entityName", "contents"],
                            },
                        },
                    },
                    "required": ["observations"],
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
                            "description": "An array of entity names to delete",
                        },
                    },
                    "required": ["entityNames"],
                },
            ),
            types.Tool(
                name="delete_observations",
                description="Delete specific observations from entities in the knowledge graph",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deletions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "entityName": {
                                        "type": "string",
                                        "description": "The name of the entity containing the observations",
                                    },
                                    "observations": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "An array of observations to delete",
                                    },
                                },
                                "required": ["entityName", "observations"],
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
                                    "source": {
                                        "type": "string",
                                        "description": "The name of the entity where the relation starts",
                                    },
                                    "target": {
                                        "type": "string",
                                        "description": "The name of the entity where the relation ends",
                                    },
                                    "relationType": {
                                        "type": "string",
                                        "description": "The type of the relation",
                                    },
                                },
                                "required": ["source", "target", "relationType"],
                            },
                            "description": "An array of relations to delete",
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
                        "query": {
                            "type": "string",
                            "description": "The search query to match against entity names, types, and observation content",
                        },
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
            types.Tool(
                name="get_recent_memories",
                description="Get memories from the last N days (default 7 days)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 7)",
                            "default": 7,
                        },
                    },
                },
            ),
            types.Tool(
                name="get_memories_by_date_range",
                description="Get memories created within a specific date range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
                        },
                    },
                    "required": ["start_date", "end_date"],
                },
            ),
            types.Tool(
                name="search_with_temporal_decay",
                description="Search memories with temporal decay - newer memories get higher priority",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to match against entity names, types, and observations",
                        },
                        "decay_days": {
                            "type": "integer",
                            "description": "Number of days for full decay (default: 30)",
                            "default": 30,
                        },
                    },
                    "required": ["query"],
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
                return [
                    types.TextContent(
                        type="text", text=json.dumps(result.model_dump_json_safe(), indent=2)
                    )
                ]

            if not arguments:
                raise ValueError(f"No arguments provided for tool: {name}")

            if name == "create_entities":
                entities = []
                for entity_data in arguments.get("entities", []):
                    # Filter out datetime fields that shouldn't come from user input
                    filtered_data = {k: v for k, v in entity_data.items() 
                                   if k not in ['created_at', 'updated_at']}
                    entities.append(Entity(**filtered_data))
                result = await memory.create_entities(entities)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps([e.model_dump_json_safe() for e in result], indent=2),
                    )
                ]

            elif name == "create_relations":
                relations = [
                    Relation(**relation) for relation in arguments.get("relations", [])
                ]
                result = await memory.create_relations(relations)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps([r.model_dump() for r in result], indent=2),
                    )
                ]

            elif name == "add_observations":
                observations = [
                    ObservationAddition(**obs)
                    for obs in arguments.get("observations", [])
                ]
                result = await memory.add_observations(observations)
                return [
                    types.TextContent(type="text", text=json.dumps(result, indent=2))
                ]

            elif name == "delete_entities":
                await memory.delete_entities(arguments.get("entityNames", []))
                return [
                    types.TextContent(type="text", text="Entities deleted successfully")
                ]

            elif name == "delete_observations":
                deletions = [
                    ObservationDeletion(**deletion)
                    for deletion in arguments.get("deletions", [])
                ]
                await memory.delete_observations(deletions)
                return [
                    types.TextContent(
                        type="text", text="Observations deleted successfully"
                    )
                ]

            elif name == "delete_relations":
                relations = [
                    Relation(**relation) for relation in arguments.get("relations", [])
                ]
                await memory.delete_relations(relations)
                return [
                    types.TextContent(
                        type="text", text="Relations deleted successfully"
                    )
                ]

            elif name == "search_nodes":
                result = await memory.search_nodes(arguments.get("query", ""))
                return [
                    types.TextContent(
                        type="text", text=json.dumps(result.model_dump_json_safe(), indent=2)
                    )
                ]

            elif name == "find_nodes" or name == "open_nodes":
                result = await memory.find_nodes(arguments.get("names", []))
                return [
                    types.TextContent(
                        type="text", text=json.dumps(result.model_dump_json_safe(), indent=2)
                    )
                ]

            elif name == "get_recent_memories":
                days = arguments.get("days", 7)
                result = await memory.get_recent_memories(days)
                return [
                    types.TextContent(
                        type="text", text=json.dumps(result.model_dump_json_safe(), indent=2)
                    )
                ]

            elif name == "get_memories_by_date_range":
                start_date = datetime.fromisoformat(arguments.get("start_date"))
                end_date = datetime.fromisoformat(arguments.get("end_date"))
                result = await memory.get_memories_by_time_range(start_date, end_date)
                return [
                    types.TextContent(
                        type="text", text=json.dumps(result.model_dump_json_safe(), indent=2)
                    )
                ]

            elif name == "search_with_temporal_decay":
                query = arguments.get("query", "")
                decay_days = arguments.get("decay_days", 30)
                result = await memory.search_with_temporal_decay(query, decay_days)
                return [
                    types.TextContent(
                        type="text", text=json.dumps(result.model_dump_json_safe(), indent=2)
                    )
                ]

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
