"""
Neo4j 3.5 Compatible Memory MCP Server

Synchronous version of the Memory MCP server for Neo4j 3.5.
"""

import json
import logging
from typing import Literal

from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import ToolAnnotations, TextContent
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .neo4j_memory_35 import (
    Entity,
    KnowledgeGraph,
    Neo4jMemory35,
    ObservationAddition,
    ObservationDeletion,
    Relation,
    create_driver,
)
from .utils import format_namespace

logger = logging.getLogger("mcp_neo4j_memory")
logger.setLevel(logging.INFO)


def create_mcp_server(memory: Neo4jMemory35, namespace: str = "") -> FastMCP:
    """Create an MCP server instance for Neo4j 3.5 memory management."""

    namespace_prefix = format_namespace(namespace)
    mcp: FastMCP = FastMCP("mcp-neo4j-memory", stateless_http=True)

    @mcp.tool(
        name=namespace_prefix + "read_graph",
        annotations=ToolAnnotations(
            title="Read Graph",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def read_graph() -> ToolResult:
        """Read the entire knowledge graph with all entities and relationships."""
        logger.info("MCP tool: read_graph")
        try:
            result = memory.read_graph()
            return ToolResult(
                content=[TextContent(type="text", text=result.model_dump_json())],
                structured_content=result,
            )
        except Exception as e:
            logger.error(f"Error reading knowledge graph: {e}")
            raise ToolError(f"Error reading knowledge graph: {e}")

    @mcp.tool(
        name=namespace_prefix + "create_entities",
        annotations=ToolAnnotations(
            title="Create Entities",
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def create_entities(
        entities: list[Entity] = Field(
            ..., description="List of entities to create with name, type, and observations"
        )
    ) -> ToolResult:
        """Create multiple new entities in the knowledge graph."""
        logger.info(f"MCP tool: create_entities ({len(entities)} entities)")
        try:
            entity_objects = [Entity.model_validate(entity) for entity in entities]
            result = memory.create_entities(entity_objects)
            return ToolResult(
                content=[
                    TextContent(
                        type="text", text=json.dumps([e.model_dump() for e in result])
                    )
                ],
                structured_content={"result": result},
            )
        except Exception as e:
            logger.error(f"Error creating entities: {e}")
            raise ToolError(f"Error creating entities: {e}")

    @mcp.tool(
        name=namespace_prefix + "create_relations",
        annotations=ToolAnnotations(
            title="Create Relations",
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def create_relations(
        relations: list[Relation] = Field(
            ..., description="List of relations to create between existing entities"
        )
    ) -> ToolResult:
        """Create multiple new relationships between existing entities."""
        logger.info(f"MCP tool: create_relations ({len(relations)} relations)")
        try:
            relation_objects = [Relation.model_validate(relation) for relation in relations]
            result = memory.create_relations(relation_objects)
            return ToolResult(
                content=[
                    TextContent(
                        type="text", text=json.dumps([r.model_dump() for r in result])
                    )
                ],
                structured_content={"result": result},
            )
        except Exception as e:
            logger.error(f"Error creating relations: {e}")
            raise ToolError(f"Error creating relations: {e}")

    @mcp.tool(
        name=namespace_prefix + "add_observations",
        annotations=ToolAnnotations(
            title="Add Observations",
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def add_observations(
        observations: list[ObservationAddition] = Field(
            ..., description="List of observations to add to existing entities"
        )
    ) -> ToolResult:
        """Add new observations/facts to existing entities."""
        logger.info(f"MCP tool: add_observations ({len(observations)} additions)")
        try:
            observation_objects = [
                ObservationAddition.model_validate(obs) for obs in observations
            ]
            result = memory.add_observations(observation_objects)
            return ToolResult(
                content=[TextContent(type="text", text=json.dumps(result))],
                structured_content={"result": result},
            )
        except Exception as e:
            logger.error(f"Error adding observations: {e}")
            raise ToolError(f"Error adding observations: {e}")

    @mcp.tool(
        name=namespace_prefix + "delete_entities",
        annotations=ToolAnnotations(
            title="Delete Entities",
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def delete_entities(
        entityNames: list[str] = Field(
            ..., description="List of exact entity names to delete permanently"
        )
    ) -> ToolResult:
        """Delete entities and all their associated relationships."""
        logger.info(f"MCP tool: delete_entities ({len(entityNames)} entities)")
        try:
            memory.delete_entities(entityNames)
            return ToolResult(
                content=[TextContent(type="text", text="Entities deleted successfully")],
                structured_content={"result": "Entities deleted successfully"},
            )
        except Exception as e:
            logger.error(f"Error deleting entities: {e}")
            raise ToolError(f"Error deleting entities: {e}")

    @mcp.tool(
        name=namespace_prefix + "delete_observations",
        annotations=ToolAnnotations(
            title="Delete Observations",
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def delete_observations(
        deletions: list[ObservationDeletion] = Field(
            ..., description="List of specific observations to remove from entities"
        )
    ) -> ToolResult:
        """Delete specific observations from existing entities."""
        logger.info(f"MCP tool: delete_observations ({len(deletions)} deletions)")
        try:
            deletion_objects = [
                ObservationDeletion.model_validate(deletion) for deletion in deletions
            ]
            memory.delete_observations(deletion_objects)
            return ToolResult(
                content=[
                    TextContent(type="text", text="Observations deleted successfully")
                ],
                structured_content={"result": "Observations deleted successfully"},
            )
        except Exception as e:
            logger.error(f"Error deleting observations: {e}")
            raise ToolError(f"Error deleting observations: {e}")

    @mcp.tool(
        name=namespace_prefix + "delete_relations",
        annotations=ToolAnnotations(
            title="Delete Relations",
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def delete_relations(
        relations: list[Relation] = Field(
            ..., description="List of specific relationships to delete"
        )
    ) -> ToolResult:
        """Delete specific relationships between entities."""
        logger.info(f"MCP tool: delete_relations ({len(relations)} relations)")
        try:
            relation_objects = [Relation.model_validate(relation) for relation in relations]
            memory.delete_relations(relation_objects)
            return ToolResult(
                content=[TextContent(type="text", text="Relations deleted successfully")],
                structured_content={"result": "Relations deleted successfully"},
            )
        except Exception as e:
            logger.error(f"Error deleting relations: {e}")
            raise ToolError(f"Error deleting relations: {e}")

    @mcp.tool(
        name=namespace_prefix + "search_memories",
        annotations=ToolAnnotations(
            title="Search Memories",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def search_memories(
        query: str = Field(
            ...,
            description="Fulltext search query to find entities by name, type, or observations",
        )
    ) -> ToolResult:
        """Search for entities using fulltext search."""
        logger.info(f"MCP tool: search_memories ('{query}')")
        try:
            result = memory.search_memories(query)
            return ToolResult(
                content=[TextContent(type="text", text=result.model_dump_json())],
                structured_content=result,
            )
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise ToolError(f"Error searching memories: {e}")

    @mcp.tool(
        name=namespace_prefix + "find_memories_by_name",
        annotations=ToolAnnotations(
            title="Find Memories by Name",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def find_memories_by_name(
        names: list[str] = Field(..., description="List of exact entity names to retrieve")
    ) -> ToolResult:
        """Find specific entities by their exact names."""
        logger.info(f"MCP tool: find_memories_by_name ({len(names)} names)")
        try:
            result = memory.find_memories_by_name(names)
            return ToolResult(
                content=[TextContent(type="text", text=result.model_dump_json())],
                structured_content=result,
            )
        except Exception as e:
            logger.error(f"Error finding memories by name: {e}")
            raise ToolError(f"Error finding memories by name: {e}")

    return mcp


def main(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_database: str = "neo4j",  # Ignored in 3.5
    transport: Literal["stdio", "sse", "http"] = "stdio",
    namespace: str = "",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
    allow_origins: list[str] = None,
    allowed_hosts: list[str] = None,
) -> None:
    """Main entry point for Neo4j 3.5 compatible Memory MCP Server."""
    logger.info("Starting Neo4j MCP Memory Server (3.5 Compatible)")
    logger.info(f"Connecting to Neo4j at: {neo4j_uri}")

    if neo4j_database != "neo4j":
        logger.warning(
            f"Neo4j 3.5 does not support multi-database. Ignoring: {neo4j_database}"
        )

    allow_origins = allow_origins or []
    allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1"]

    # Create 3.5 compatible driver
    neo4j_driver = create_driver(neo4j_uri, neo4j_user, neo4j_password)

    # Verify connection
    try:
        neo4j_driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {neo4j_uri}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        exit(1)

    # Initialize memory
    memory = Neo4jMemory35(neo4j_driver)
    logger.info("Neo4jMemory35 initialized")

    # Create fulltext index (3.5 syntax)
    memory.create_fulltext_index()

    # Configure security middleware
    custom_middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        ),
        Middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts),
    ]

    # Create MCP server
    mcp = create_mcp_server(memory, namespace)
    logger.info("MCP server created")

    # Run the server with the specified transport
    logger.info(f"Starting server with transport: {transport}")
    if transport == "http":
        logger.info(f"HTTP server starting on {host}:{port}{path}")
        mcp.run_http(host=host, port=port, path=path, middleware=custom_middleware)
    elif transport == "stdio":
        logger.info("STDIO server starting")
        mcp.run_stdio()
    elif transport == "sse":
        logger.info(f"SSE server starting on {host}:{port}{path}")
        mcp.run_http(
            host=host, port=port, path=path, middleware=custom_middleware, transport="sse"
        )
    else:
        raise ValueError(f"Unsupported transport: {transport}")
