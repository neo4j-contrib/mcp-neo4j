"""
Servidor MCP optimizado para producción con multi-tenancy, paginación y límites
"""
import json
import logging
from typing import Literal, Optional, List

from neo4j import AsyncGraphDatabase
from pydantic import Field

from fastmcp.server import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult, TextContent
from neo4j.exceptions import Neo4jError
from mcp.types import ToolAnnotations

from .neo4j_memory_optimized import (
    Neo4jMemoryOptimized, 
    EntityOptimized, 
    RelationOptimized, 
    KnowledgeGraphOptimized,
    ObservationAdditionOptimized, 
    ObservationDeletionOptimized
)
from .config import config

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory_optimized')
logger.setLevel(logging.INFO)


def create_optimized_mcp_server(memory: Neo4jMemoryOptimized) -> FastMCP:
    """Create an optimized MCP server instance for memory management."""
    
    mcp: FastMCP = FastMCP("mcp-neo4j-memory-optimized", dependencies=["neo4j", "pydantic"], stateless_http=True)

    @mcp.tool(annotations=ToolAnnotations(title="Read Graph Optimized", 
                                          readOnlyHint=True, 
                                          destructiveHint=False, 
                                          idempotentHint=True, 
                                          openWorldHint=True))
    async def read_graph(
        tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy"),
        limit: Optional[int] = Field(None, description="Maximum number of entities to return")
    ) -> KnowledgeGraphOptimized:
        """Read the knowledge graph with tenant support and limits."""
        logger.info(f"MCP tool: read_graph (tenant={tenant_id}, limit={limit})")
        try:
            result = await memory.read_graph_optimized(tenant_id=tenant_id, limit=limit)
            return ToolResult(
                content=[TextContent(type="text", text=result.model_dump_json())],
                structured_content=result
            )
        except Neo4jError as e:
            logger.error(f"Neo4j error reading graph: {e}")
            raise ToolError(f"Neo4j error reading graph: {e}")
        except Exception as e:
            logger.error(f"Error reading graph: {e}")
            raise ToolError(f"Error reading graph: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Create Entities Optimized", 
                                          readOnlyHint=False, 
                                          destructiveHint=False, 
                                          idempotentHint=True, 
                                          openWorldHint=True))
    async def create_entities(
        entities: List[EntityOptimized] = Field(..., description="List of entities to create"),
        tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")
    ) -> List[EntityOptimized]:
        """Create multiple new entities in the knowledge graph with tenant support."""
        logger.info(f"MCP tool: create_entities ({len(entities)} entities, tenant={tenant_id})")
        try:
            result = await memory.create_entities_optimized(entities, tenant_id=tenant_id)
            return ToolResult(
                content=[TextContent(type="text", text=json.dumps([e.model_dump() for e in result]))],
                structured_content={"result": result}
            )
        except Neo4jError as e:
            logger.error(f"Neo4j error creating entities: {e}")
            raise ToolError(f"Neo4j error creating entities: {e}")
        except Exception as e:
            logger.error(f"Error creating entities: {e}")
            raise ToolError(f"Error creating entities: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Create Relations Optimized", 
                                          readOnlyHint=False, 
                                          destructiveHint=False, 
                                          idempotentHint=True, 
                                          openWorldHint=True))
    async def create_relations(
        relations: List[RelationOptimized] = Field(..., description="List of relations to create"),
        tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")
    ) -> List[RelationOptimized]:
        """Create multiple new relations between entities with tenant support."""
        logger.info(f"MCP tool: create_relations ({len(relations)} relations, tenant={tenant_id})")
        try:
            result = await memory.create_relations_optimized(relations, tenant_id=tenant_id)
            return ToolResult(
                content=[TextContent(type="text", text=json.dumps([r.model_dump() for r in result]))],
                structured_content={"result": result}
            )
        except Neo4jError as e:
            logger.error(f"Neo4j error creating relations: {e}")
            raise ToolError(f"Neo4j error creating relations: {e}")
        except Exception as e:
            logger.error(f"Error creating relations: {e}")
            raise ToolError(f"Error creating relations: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Search Memories Optimized", 
                                          readOnlyHint=True, 
                                          destructiveHint=False, 
                                          idempotentHint=True, 
                                          openWorldHint=True))
    async def search_memories(
        query: str = Field(..., description="Search query for nodes"),
        tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy"),
        max_level: Optional[int] = Field(None, description="Maximum graph expansion depth"),
        node_limit: Optional[int] = Field(None, description="Maximum number of nodes to return"),
        rel_limit: Optional[int] = Field(None, description="Maximum number of relationships to return"),
        props_keep: Optional[List[str]] = Field(None, description="Properties to keep in nodes (for token optimization)"),
        cursor: Optional[str] = Field(None, description="Pagination cursor"),
        page_size: Optional[int] = Field(None, description="Page size for pagination"),
        simple_mode: bool = Field(False, description="Use simple search without graph expansion")
    ) -> KnowledgeGraphOptimized:
        """
        Search for memories with advanced optimization options.
        
        This optimized version supports:
        - Multi-tenancy for data isolation
        - Configurable limits to control response size
        - Pagination for large result sets
        - Property filtering to reduce token consumption
        - Simple mode for faster searches
        """
        logger.info(f"MCP tool: search_memories_optimized (query='{query}', tenant={tenant_id})")
        try:
            result = await memory.search_memories_optimized(
                query=query,
                tenant_id=tenant_id,
                max_level=max_level,
                node_limit=node_limit,
                rel_limit=rel_limit,
                props_keep=props_keep,
                cursor=cursor,
                page_size=page_size,
                simple_mode=simple_mode
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.model_dump_json())],
                structured_content=result
            )
        except Neo4jError as e:
            logger.error(f"Neo4j error searching memories: {e}")
            raise ToolError(f"Neo4j error searching memories: {e}")
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise ToolError(f"Error searching memories: {e}")

    # Mantener funciones originales para retrocompatibilidad
    @mcp.tool(annotations=ToolAnnotations(title="Search Memories (Legacy)", 
                                          readOnlyHint=True, 
                                          destructiveHint=False, 
                                          idempotentHint=True, 
                                          openWorldHint=True))
    async def search_memories_legacy(
        query: str = Field(..., description="Search query for nodes")
    ) -> KnowledgeGraphOptimized:
        """Legacy search function for backward compatibility with n8n integrations."""
        logger.info(f"MCP tool: search_memories_legacy ('{query}')")
        try:
            # Usar configuración por defecto pero optimizada
            result = await memory.search_memories_optimized(
                query=query,
                tenant_id=config.default_tenant,
                simple_mode=True,  # Modo simple para compatibilidad
                page_size=config.default_page_size
            )
            return ToolResult(
                content=[TextContent(type="text", text=result.model_dump_json())],
                structured_content=result
            )
        except Neo4jError as e:
            logger.error(f"Neo4j error in legacy search: {e}")
            raise ToolError(f"Neo4j error in legacy search: {e}")
        except Exception as e:
            logger.error(f"Error in legacy search: {e}")
            raise ToolError(f"Error in legacy search: {e}")

    @mcp.tool(annotations=ToolAnnotations(title="Get Server Config", 
                                          readOnlyHint=True, 
                                          destructiveHint=False, 
                                          idempotentHint=True, 
                                          openWorldHint=False))
    async def get_server_config() -> dict:
        """Get current server configuration and limits."""
        return ToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "version": "1.0.0-optimized",
                "multi_tenancy_enabled": config.enable_tenant,
                "default_tenant": config.default_tenant,
                "default_limits": {
                    "max_level": config.default_max_level,
                    "node_limit": config.default_node_limit,
                    "rel_limit": config.default_rel_limit,
                    "page_size": config.default_page_size
                },
                "features": {
                    "pagination": True,
                    "property_filtering": True,
                    "simple_mode": True,
                    "auto_indexes": config.auto_create_indexes
                }
            }, indent=2))],
            structured_content={
                "version": "1.0.0-optimized",
                "config": config.model_dump()
            }
        )

    return mcp


async def main_optimized(
    neo4j_uri: str, 
    neo4j_user: str, 
    neo4j_password: str, 
    neo4j_database: str,
    transport: Literal["stdio", "sse", "http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
) -> None:
    """Main function for optimized MCP server"""
    
    logger.info(f"Starting Neo4j MCP Memory Server (Optimized v1.0)")
    logger.info(f"Multi-tenancy: {config.enable_tenant}, Default tenant: {config.default_tenant}")
    logger.info(f"Connecting to Neo4j: {neo4j_uri}")

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

    # Initialize optimized memory
    memory = Neo4jMemoryOptimized(neo4j_driver)
    logger.info("Neo4jMemoryOptimized initialized")
    
    # Create indexes if enabled
    if config.auto_create_indexes:
        await memory.create_indexes()
        logger.info("Indexes created/verified")
    
    # Create optimized MCP server
    mcp = create_optimized_mcp_server(memory)
    logger.info("Optimized MCP server created")

    # Run the server with the specified transport
    logger.info(f"Starting server with transport: {transport}")
    match transport:
        case "http":
            logger.info(f"HTTP server starting on {host}:{port}{path}")
            await mcp.run_http_async(host=host, port=port, path=path)
        case "stdio":
            logger.info("STDIO server starting")
            await mcp.run_stdio_async()
        case "sse":
            logger.info(f"SSE server starting on {host}:{port}{path}")
            await mcp.run_sse_async(host=host, port=port, path=path)
        case _:
            raise ValueError(f"Unsupported transport: {transport}")