"""
MCP tool definitions and execution logic for Neo4j memory operations.
"""

import json
import logging
from typing import Any, Dict, List

import mcp.types as types

from .models import Entity, Relation, ObservationAddition, ObservationDeletion
from .memory import Neo4jMemory

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory.core.tools')


def get_mcp_tools() -> List[types.Tool]:
    """Get the list of available MCP tools."""
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
                                "observations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of observation contents associated with the entity"
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
                                "contents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of observation contents to add"
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
                        "description": "An array of entity names to delete"
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
                                "entityName": {"type": "string", "description": "The name of the entity containing the observations"},
                                "observations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of observations to delete"
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
                    "query": {"type": "string", "description": "The search query to match against entity names, types, and observation content"},
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


async def execute_tool(
    memory: Neo4jMemory,
    name: str,
    arguments: Dict[str, Any] | None
) -> List[types.TextContent | types.ImageContent]:
    """
    Execute a tool and return MCP-formatted response.

    Args:
        memory: Neo4jMemory instance
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of MCP content objects
    """
    try:
        if name == "read_graph":
            result = await memory.read_graph()
            return [types.TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

        if not arguments:
            raise ValueError(f"No arguments provided for tool: {name}")

        if name == "create_entities":
            entities_data = arguments.get("entities", [])

            # Handle case where entities is sent as JSON string
            if isinstance(entities_data, str):
                try:
                    entities_data = json.loads(entities_data)
                    logger.warning(f"Parsed entities from JSON string: {entities_data}")
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON string for entities: {e}")

            entities = [Entity(**entity) for entity in entities_data]
            result = await memory.create_entities(entities)
            return [types.TextContent(type="text", text=json.dumps([e.model_dump() for e in result], indent=2))]

        elif name == "create_relations":
            relations_data = arguments.get("relations", [])

            # Handle case where relations is sent as JSON string
            if isinstance(relations_data, str):
                try:
                    relations_data = json.loads(relations_data)
                    logger.warning(f"Parsed relations from JSON string: {relations_data}")
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON string for relations: {e}")

            relations = [Relation(**relation) for relation in relations_data]
            result = await memory.create_relations(relations)
            return [types.TextContent(type="text", text=json.dumps([r.model_dump() for r in result], indent=2))]

        elif name == "add_observations":
            observations = [ObservationAddition(**obs) for obs in arguments.get("observations", [])]
            result = await memory.add_observations(observations)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "delete_entities":
            await memory.delete_entities(arguments.get("entityNames", []))
            return [types.TextContent(type="text", text="Entities deleted successfully")]

        elif name == "delete_observations":
            deletions = [ObservationDeletion(**deletion) for deletion in arguments.get("deletions", [])]
            await memory.delete_observations(deletions)
            return [types.TextContent(type="text", text="Observations deleted successfully")]

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



