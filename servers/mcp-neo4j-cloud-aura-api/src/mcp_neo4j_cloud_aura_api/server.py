import requests
from typing import List, Optional, Literal

from fastmcp.server import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .aura_manager import AuraManager
from .utils import get_logger, format_namespace

logger = get_logger(__name__)



def create_mcp_server(aura_manager: AuraManager, namespace: str = "") -> FastMCP:
    """Create an MCP server instance for Aura management."""
    
    namespace_prefix = format_namespace(namespace)
    
    mcp: FastMCP = FastMCP("mcp-neo4j-cloud-aura-api", stateless_http=True)

    @mcp.tool(
        name=namespace_prefix + "list_instances",
        annotations=ToolAnnotations(title="List Instances",
                                          readOnlyHint=True,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def list_instances() -> dict:
        """List all Neo4j Aura database instances."""
        logger.info("MCP tool: list_instances")

        try:
            result = await aura_manager.list_instances()
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        
        except Exception as e:
            logger.error(f"Error in list_instances: {e}")
            raise ToolError("Error in list_instances") from e

    @mcp.tool(
        name=namespace_prefix + "get_instance_details",
        annotations=ToolAnnotations(
            title="Get Instance Details",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True
        
    ))
    async def get_instance_details(instance_ids: List[str]) -> dict:
        """Get details for one or more Neo4j Aura instances by ID."""
        logger.info("MCP tool: get_instance_details")
        try:
            result = await aura_manager.get_instance_details(instance_ids)
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e

        except Exception as e:
            logger.error(f"Error in get_instance_details: {e}")
            raise ToolError("Error in get_instance_details") from e

    @mcp.tool(
        name=namespace_prefix + "get_instance_by_name",
        annotations=ToolAnnotations(title="Get Instance by Name",
                                          readOnlyHint=True,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def get_instance_by_name(name: str) -> dict:
        """Find a Neo4j Aura instance by name and returns the details including the id."""
        logger.info("MCP tool: get_instance_by_name")
        try:
            result = await aura_manager.get_instance_by_name(name)
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        
        except Exception as e:
            logger.error(f"Error in get_instance_by_name: {e}")
            raise ToolError("Error in get_instance_by_name") from e

    @mcp.tool(
        name=namespace_prefix + "create_instance",
        annotations=ToolAnnotations(title="Create Instance",
                                          readOnlyHint=False,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def create_instance(
        tenant_id: str = Field(..., description="ID of the tenant/project where the instance will be created"),
        name: str = Field(..., description="Name for the new instance"),
        memory: int = Field(1, description="Memory allocation in GB"),
        region: str = Field("us-central1", description="Region for the instance (e.g., 'us-central1')"),
        type: str = Field("free-db", description="Instance type (free-db, professional-db, enterprise-db, or business-critical)"),
        vector_optimized: bool = Field(False, description="Whether the instance is optimized for vector operations"),
        cloud_provider: str = Field("gcp", description="Cloud provider (gcp, aws, azure)"),
        graph_analytics_plugin: bool = Field(False, description="Whether to enable the graph analytics plugin"),
        source_instance_id: Optional[str] = Field(None, description="ID of the source instance to clone from")
    ) -> dict:
        """Create a new Neo4j Aura database instance."""
        try:

            result = await aura_manager.create_instance(
                tenant_id=tenant_id,
                name=name,
                memory=memory,
                region=region,
                type=type,
                vector_optimized=vector_optimized,
                cloud_provider=cloud_provider,
                graph_analytics_plugin=graph_analytics_plugin,
                source_instance_id=source_instance_id
            )
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        
        except Exception as e:
            logger.error(f"Error in create_instance: {e}")
            raise ToolError("Error in create_instance") from e

    @mcp.tool(
        name=namespace_prefix + "update_instance_name",
        annotations=ToolAnnotations(title="Update Instance Name",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def update_instance_name(instance_id: str, name: str) -> dict:
        """Update the name of a Neo4j Aura instance."""
        try:
            result = await aura_manager.update_instance_name(instance_id, name)
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        
        except Exception as e:
            logger.error(f"Error in update_instance_name: {e}")
            raise ToolError("Error in update_instance_name") from e

    @mcp.tool(
        name=namespace_prefix + "update_instance_memory",
        annotations=ToolAnnotations(title="Update Instance Memory",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def update_instance_memory(instance_id: str, memory: int) -> dict:
        """Update the memory allocation of a Neo4j Aura instance."""
        try:
            result = await aura_manager.update_instance_memory(instance_id, memory)
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        
        except Exception as e:
            logger.error(f"Error in update_instance_memory: {e}")
            raise ToolError(f"Error in update_instance_memory: {e}")

    @mcp.tool(name=namespace_prefix + "update_instance_vector_optimization",
        annotations=ToolAnnotations(title="Update Instance Vector Optimization",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def update_instance_vector_optimization(instance_id: str, vector_optimized: bool) -> dict:
        """Update the vector optimization setting of a Neo4j Aura instance."""
        try:
            result = await aura_manager.update_instance_vector_optimization(instance_id, vector_optimized)
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        
        except Exception as e:
            logger.error(f"Error in update_instance_vector_optimization: {e}")
            raise ToolError("Error in update_instance_vector_optimization") from e

    @mcp.tool(
        name=namespace_prefix + "pause_instance",
        annotations=ToolAnnotations(title="Pause Instance",
                                          readOnlyHint=False,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def pause_instance(instance_id: str) -> dict:
        """Pause a Neo4j Aura database instance."""
        try:
            result = await aura_manager.pause_instance(instance_id)
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        
        except Exception as e:
            logger.error(f"Error in pause_instance: {e}")
            raise ToolError("Error in pause_instance") from e

    @mcp.tool(
        name=namespace_prefix + "resume_instance",
        annotations=ToolAnnotations(title="Resume Instance",
                                          readOnlyHint=False,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def resume_instance(instance_id: str) -> dict:
        """Resume a paused Neo4j Aura database instance."""
        try:
            result = await aura_manager.resume_instance(instance_id)
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        except Exception as e:
            logger.error(f"Error in resume_instance: {e}")
            raise ToolError("Error in resume_instance") from e

    @mcp.tool(
        name=namespace_prefix + "list_tenants",
        annotations=ToolAnnotations(title="List Tenants",
                                          readOnlyHint=True,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def list_tenants() -> dict:
        """List all Neo4j Aura tenants/projects."""
        try:
            result = await aura_manager.list_tenants()
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        except Exception as e:
            logger.error(f"Error in list_tenants: {e}")
            raise ToolError("Error in list_tenants") from e

    @mcp.tool(
        name=namespace_prefix + "get_tenant_details",
        annotations=ToolAnnotations(title="Get Tenant Details",
                                          readOnlyHint=True,
                                          destructiveHint=False,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def get_tenant_details(tenant_id: str) -> dict:
        """Get details for a specific Neo4j Aura tenant/project."""
        try:
            result = await aura_manager.get_tenant_details(tenant_id)
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        except Exception as e:
            logger.error(f"Error in get_tenant_details: {e}")
            raise ToolError("Error in get_tenant_details") from e

    @mcp.tool(name=namespace_prefix + "delete_instance",
    annotations=ToolAnnotations(title="Delete Instance",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def delete_instance(instance_id: str) -> dict:
        """Delete a Neo4j Aura database instance."""
        try:
            result = await aura_manager.delete_instance(instance_id)
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Aura API request failed: {e}")
            raise ToolError("Aura API request failed") from e
        except Exception as e:
            logger.error(f"Error in delete_instance: {e}")
            raise ToolError("Error in delete_instance") from e

    return mcp


async def main(
    client_id: str,
    client_secret: str,
    transport: Literal["stdio", "sse", "http"] = "stdio",
    namespace: str = "",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
    allow_origins: list[str] = [],
    allowed_hosts: list[str] = [],
    stateless: bool = False,
) -> None:
    """Start the MCP server."""
    logger.info("Starting MCP Neo4j Cloud Aura API Server")
    
    aura_manager = AuraManager(client_id, client_secret)
    custom_middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        ),
        Middleware(TrustedHostMiddleware,
                   allowed_hosts=allowed_hosts)
    ]
    
    # Create MCP server
    mcp = create_mcp_server(aura_manager, namespace)

    # Run the server with the specified transport
    match transport:
        case "http":
            logger.info(
                f"Running Neo4j Cloud Aura API MCP Server with HTTP transport on {host}:{port}..."
            )
            logger.info(f"Stateless mode: {stateless}")
            await mcp.run_http_async(
                host=host, port=port, path=path, middleware=custom_middleware, stateless_http=stateless
            )
        case "stdio":
            logger.info("Running Neo4j Cloud Aura API MCP Server with stdio transport...")
            await mcp.run_stdio_async()
        case "sse":
            logger.info(
                f"Running Neo4j Cloud Aura API MCP Server with SSE transport on {host}:{port}..."
            )
            logger.info(f"Stateless mode: {stateless}")
            await mcp.run_http_async(host=host, port=port, path=path, middleware=custom_middleware, transport="sse", stateless_http=stateless)
        case _:
            logger.error(
                f"Invalid transport: {transport} | Must be either 'stdio', 'sse', or 'http'"
            )
            raise ValueError(
                f"Invalid transport: {transport} | Must be either 'stdio', 'sse', or 'http'"
            )


if __name__ == "__main__":
    main()
