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
logger = logging.getLogger("mcp_neo4j_memory")
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
    self.neo4j_driver = neo4j_driver
    self.create_fulltext_index()

  def create_fulltext_index(self):
    """Create fulltext indexes for nodes and relationships in the Neo4j graph."""
    index_config = {
      "indexConfig": {
        "fulltext.analyzer": "cjk",
        "fulltext.eventually_consistent": True,  # Use async indexing
      }
    }

    # Node index: name, type, and observations
    node_query = """
      CREATE FULLTEXT INDEX node_search IF NOT EXISTS
      FOR (n:Memory)
      ON EACH [n.name, n.type, n.observations]
      OPTIONS $config
      """

    try:
      self.neo4j_driver.execute_query(node_query, {"config": index_config})
      logger.info("Full text indexes created successfully.")
    except neo4j.exceptions.ClientError as e:
      logger.error(f"Indexing failed with: {str(e)}")
      raise

  async def check_index_status(self):
      query = """
      CALL db.index.fulltext.list()
      YIELD name, state, populationPercent, type
      WHERE name IN ['node_search', 'rel_search']
      RETURN name, state, populationPercent, type
      ORDER BY name
      """

      result = self.neo4j_driver.execute_query(query)
      status = {}

      for record in result.records:
          status[record["name"]] = {
              "state": record["state"],
              "progress": f"{record['populationPercent']}%",
              "type": record["type"]
          }

      return {
          "node_index": status.get("node_search", "not found"),
      }

  async def fuzzy_search(
      self,
      search_term: str,
      target_type: Optional[str] = None,  # 'node'/'relationship'/None
      limit: int = 50
  ) -> Dict[str, List]:
      """
      Fuzzy search for nodes and relationships in the knowledge graph using fulltext indexing.
      :param search_term: keyword or phrase to search for in the knowledge graph (with Lucene query syntax support)
      :param target_type: type to search: node/relationship
      :param limit: maximum number of results to return for each type
      """
      queries = []

      # Dynamically build queries based on target_type
      if not target_type or target_type == "node":
          queries.append({
              "type": "node",
              "query": """
              CALL db.index.fulltext.queryNodes('node_search', $term)
              YIELD node, score
              RETURN 'node' AS type,
                     node.name AS name,
                     node.type AS entityType,
                     node.observations AS observations,
                     score
              ORDER BY score DESC
              LIMIT $limit
              """
          })

      if not target_type or target_type == "relationship":
          queries.append({
              "type": "relationship",
              "query": """
              CALL db.index.fulltext.queryRelationships('node_search', $term)
              YIELD relationship, score
              RETURN 'relationship' AS type,
                     type(relationship) AS relationType,
                     startNode(relationship).name AS source,
                     endNode(relationship).name AS target,
                     score
              ORDER BY score DESC
              LIMIT $limit
              """
          })

      # Parallelized execution of queries
      results = {"nodes": [], "relationships": []}
      params = {"term": search_term, "limit": limit}

      for q in queries:
          result = self.neo4j_driver.execute_query(q["query"], params)

          for record in result.records:
              item = {key: record[key] for key in record.keys()}
              if q["type"] == "node":
                  results["nodes"].append({
                      "name": item["name"],
                      "type": item["entityType"],
                      "observations": item.get("observations", []),
                      "score": item["score"]
                  })
              else:
                  results["relationships"].append({
                      "type": item["relationType"],
                      "source": item["source"],
                      "target": item["target"],
                      "score": item["score"]
                  })

      return results


  async def load_graph(self, filter_query="*"):
    query = """
            CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            WITH entity, collect(DISTINCT {
                source: startNode(r).name,
                target: endNode(r).name,
                relationType: type(r)
            }) as distinctRelations
            RETURN collect(distinct {
                name: entity.name,
                type: entity.type,
                observations: entity.observations
            }) as nodes,
            distinctRelations as relations
        """

    result = self.neo4j_driver.execute_query(query, {"filter": filter_query})

    if not result.records:
      return KnowledgeGraph(entities=[], relations=[])

    record = result.records[0]
    nodes = record.get("nodes")
    rels = record.get("relations")

    entities = [Entity(name=node.get("name"), type=node.get("type"), observations=node.get("observations", [])) for node in nodes if node.get("name")]

    relations = [
      Relation(source=rel.get("source"), target=rel.get("target"), relationType=rel.get("relationType"))
      for rel in rels
      if rel.get("source") and rel.get("target") and rel.get("relationType")
    ]

    logger.debug(f"Loaded entities: {entities}")
    logger.debug(f"Loaded relations: {relations}")

    return KnowledgeGraph(entities=entities, relations=relations)

  async def create_entities(self, entities: List[Entity]) -> List[Entity]:
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
    for relation in relations:
      query = f"""
          UNWIND $relations as relation
          MATCH (from:Memory),(to:Memory)
          WHERE from.name = relation.source
            AND to.name = relation.target
          MERGE (from)-[r:{relation.relationType}]->(to)
        """

      self.neo4j_driver.execute_query(
        query,
        {"relations": [relation.model_dump()]},
      )

    return relations

  async def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
    query = """
        UNWIND $observations as obs
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.contents WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new
        RETURN e.name as name, new
        """

    result = self.neo4j_driver.execute_query(query, {"observations": [obs.model_dump() for obs in observations]})

    results = [{"entityName": record.get("name"), "addedObservations": record.get("new")} for record in result.records]
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
    self.neo4j_driver.execute_query(query, {"deletions": [deletion.model_dump() for deletion in deletions]})

  async def delete_relations(self, relations: List[Relation]) -> None:
    query = """
        UNWIND $relations as relation
        MATCH (source:Memory)-[r:$(relation.relationType)]->(target:Memory)
        WHERE source.name = relation.source
        AND target.name = relation.target
        DELETE r
        """
    self.neo4j_driver.execute_query(query, {"relations": [relation.model_dump() for relation in relations]})

  async def read_graph(self) -> KnowledgeGraph:
    return await self.load_graph()

  async def search_nodes(self, query: str) -> KnowledgeGraph:
    return await self.load_graph(query)

  async def find_nodes(self, names: List[str]) -> KnowledgeGraph:
    return await self.load_graph("name: (" + " ".join(names) + ")")


async def main(neo4j_uri: str, neo4j_user: str, neo4j_password: str):
  logger.info(f"Connecting to neo4j MCP Server with DB URL: {neo4j_uri}")

  # Connect to Neo4j
  neo4j_driver: neo4j.Driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

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

  # 在类或模块级别定义工具处理映射表
  tool_handlers = {
    "create_entities": {
      "model": Entity,
      "param_key": "entities",
      "handler": lambda memory, args: memory.create_entities(args),
    },
    "create_relations": {
      "model": Relation,
      "param_key": "relations",
      "handler": lambda memory, args: memory.create_relations(args),
    },
    "add_observations": {
      "model": ObservationAddition,
      "param_key": "observations",
      "handler": lambda memory, args: memory.add_observations(args),
    },
    "delete_entities": {
      "model": None,
      "param_key": "entityNames",
      "handler": lambda memory, args: memory.delete_entities(args),
    },
    "delete_observations": {
      "model": ObservationDeletion,
      "param_key": "deletions",
      "handler": lambda memory, args: memory.delete_observations(args),
    },
    "delete_relations": {
      "model": Relation,
      "param_key": "relations",
      "handler": lambda memory, args: memory.delete_relations(args),
    },
    "read_graph": {
      "model": None,
      "param_key": None,
      "handler": lambda memory, _: memory.read_graph(),
    },
    "search_nodes": {
      "model": None,
      "param_key": "query",
      "handler": lambda memory, args: memory.search_nodes(args),
    },
    "find_nodes": {
      "model": None,
      "param_key": "names",
      "handler": lambda memory, args: memory.find_nodes(args),
    },
  }

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
                  "observations": {"type": "array", "items": {"type": "string"}, "description": "An array of observation contents associated with the entity"},
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
                  "entityName": {"type": "string", "description": "The name of the entity to add the observations to"},
                  "contents": {"type": "array", "items": {"type": "string"}, "description": "An array of observation contents to add"},
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
            "entityNames": {"type": "array", "items": {"type": "string"}, "description": "An array of entity names to delete"},
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
                  "entityName": {"type": "string", "description": "The name of the entity containing the observations"},
                  "observations": {"type": "array", "items": {"type": "string"}, "description": "An array of observations to delete"},
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
                  "source": {"type": "string", "description": "The name of the entity where the relation starts"},
                  "target": {"type": "string", "description": "The name of the entity where the relation ends"},
                  "relationType": {"type": "string", "description": "The type of the relation"},
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
            "query": {"type": "string", "description": "The search query to match against entity names, types, and observation content"},
          },
          "required": ["query"],
        },
      ),
      types.Tool(
        name="find_nodes",
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
  async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[types.TextContent | types.ImageContent]:
    try:
      if name not in tool_handlers:
        raise ValueError(f"Unknown tool: {name}")
      handler_config = tool_handlers[name]
      param_key = handler_config["param_key"]
      model_cls = handler_config["model"]
      handler = handler_config["handler"]

      if param_key is None:
        result = await handler(memory, None)
        return [types.TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]
      if not arguments or param_key not in arguments:
        raise ValueError(f"Missing required parameter: {param_key}")

      raw_params = arguments.get(param_key, [])

      params = [model_cls(**item) for item in raw_params] if model_cls else raw_params

      result = await handler(memory, params)

      if isinstance(result, BaseModel):
        return [types.TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]
      elif isinstance(result, list):
        return [types.TextContent(type="text", text=json.dumps([r.model_dump() for r in result], indent=2))]
      else:
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
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
