from typing import List, Optional, Literal

from fastmcp.server import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .aura_manager import AuraManager
from .sizing.models import SizingResult, ForecastResult
from .utils import get_logger, format_namespace, get_calculator_parameter_info

logger = get_logger(__name__)



def create_mcp_server(aura_manager: AuraManager, namespace: str = "") -> FastMCP:
    """Create an MCP server instance for Aura management."""
    
    namespace_prefix = format_namespace(namespace)
    
    mcp: FastMCP = FastMCP("mcp-neo4j-aura-manager", dependencies=["requests", "pydantic", "starlette"])

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
        result = await aura_manager.list_instances()
        return result

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
        result = await aura_manager.get_instance_details(instance_ids)
        return result

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
        result = await aura_manager.get_instance_by_name(name)
        return result

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
        result = await aura_manager.update_instance_name(instance_id, name)
        return result

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
        result = await aura_manager.update_instance_memory(instance_id, memory)
        return result

    @mcp.tool(name=namespace_prefix + "update_instance_vector_optimization",
        annotations=ToolAnnotations(title="Update Instance Vector Optimization",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def update_instance_vector_optimization(instance_id: str, vector_optimized: bool) -> dict:
        """Update the vector optimization setting of a Neo4j Aura instance."""
        result = await aura_manager.update_instance_vector_optimization(instance_id, vector_optimized)
        return result

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
        result = await aura_manager.pause_instance(instance_id)
        return result

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
        result = await aura_manager.resume_instance(instance_id)
        return result


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
        result = await aura_manager.list_tenants()
        return result

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
        result = await aura_manager.get_tenant_details(tenant_id)
        return result

    @mcp.tool(name=namespace_prefix + "delete_instance",
    annotations=ToolAnnotations(title="Delete Instance",
                                          readOnlyHint=False,
                                          destructiveHint=True,
                                          idempotentHint=True,
                                          openWorldHint=True
        
    ))
    async def delete_instance(instance_id: str) -> dict:
        """Delete a Neo4j Aura database instance."""
        result = await aura_manager.delete_instance(instance_id)
        return result

    @mcp.tool(
        name=namespace_prefix + "calculate_database_sizing",
        annotations=ToolAnnotations(
            title="Calculate Database Sizing",
            readOnlyHint=True,
            idempotentHint=True
        )
    )
    async def calculate_database_sizing(
        # Graph metrics
        num_nodes: int = Field(..., description="Number of nodes in the graph"),
        num_relationships: int = Field(..., description="Number of relationships in the graph"),
        avg_properties_per_node: int = Field(..., description="Average number of properties per node. Required for accurate sizing."),
        avg_properties_per_relationship: int = Field(..., description="Average number of properties per relationship. Required for accurate sizing."),
        total_num_large_node_properties: Optional[int] = Field(None, description="Total number of large properties (128+ bytes) across all nodes (default: 0)"),
        total_num_large_reltype_properties: Optional[int] = Field(None, description="Total number of large properties (128+ bytes) across all relationships (default: 0)"),
        
        # Vector metrics
        vector_index_dimensions: Optional[int] = Field(None, description="Vector index dimensions (default: 0 if not using vectors)"),
        percentage_nodes_with_vector_properties: Optional[float] = Field(None, description="Percentage of nodes with properties in vector index 0-100 (default: 0.0)"),
        number_of_vector_indexes: Optional[int] = Field(None, description="Number of vector indexes (default: 0)"),
        
        # Optional overrides
        quantization_enabled: bool = Field(False, description="Enable scalar quantization for vectors (4x storage reduction, uses int8 instead of float32)"),
        memory_to_storage_ratio: Optional[float] = Field(
            None,
            description="Memory-to-storage ratio denominator. "
            "Options: 1.0 (1:1 ratio - memory equals storage), "
            "2.0 (1:2 ratio - memory is half of storage), "
            "4.0 (1:4 ratio - memory is quarter of storage), "
            "8.0 (1:8 ratio - memory is eighth of storage). "
            "If provided, calculates recommended_memory_gb based on total storage size. "
            "Default: None (no memory calculation)."
        ),
        concurrent_end_users: Optional[int] = Field(
            None,
            description="Number of concurrent end users. "
            "If provided, calculates recommended_vcpus (2 vCPU per concurrent user). "
            "Default: None (no vCPU calculation)."
        ),
    ) -> SizingResult:
        """
        Calculate current Neo4j database sizing based on graph characteristics.
        
        This tool uses Neo4j's sizing formulas to calculate storage requirements based on your 
        graph structure (nodes, relationships, properties, and indexes).
        
        **Required parameters:**
        - num_nodes: Number of nodes in the graph
        - num_relationships: Number of relationships in the graph
        - avg_properties_per_node: Average properties per node (REQUIRED - significantly affects sizing)
        - avg_properties_per_relationship: Average properties per relationship (REQUIRED - significantly affects sizing)
        
        **Optional parameters:**
        - total_num_large_node_properties: Large properties (128+ bytes) across all nodes (default: 0)
        - total_num_large_reltype_properties: Large properties (128+ bytes) across all relationships (default: 0)
        - vector_index_dimensions: Vector dimensions if using vector search (default: 0)
        - percentage_nodes_with_vector_properties: % of nodes with vectors (default: 0.0)
        - number_of_vector_indexes: Number of vector indexes (default: 0)
        
        **IMPORTANT**: Property counts are required for accurate sizing. If the user provides incomplete 
        information, ask about properties before calling this tool, as missing property data leads to 
        wildly inaccurate results.
        
        Returns detailed breakdown of storage components plus recommended memory and vCPU counts.
        Use the forecast_database_size tool to project growth over multiple years.
        """
        result_dict = await aura_manager.calculate_database_sizing(
            num_nodes=num_nodes,
            num_relationships=num_relationships,
            avg_properties_per_node=avg_properties_per_node,
            avg_properties_per_relationship=avg_properties_per_relationship,
            total_num_large_node_properties=total_num_large_node_properties,
            total_num_large_reltype_properties=total_num_large_reltype_properties,
            vector_index_dimensions=vector_index_dimensions,
            percentage_nodes_with_vector_properties=percentage_nodes_with_vector_properties,
            number_of_vector_indexes=number_of_vector_indexes,
            quantization_enabled=quantization_enabled,
            memory_to_storage_ratio=memory_to_storage_ratio,
            concurrent_end_users=concurrent_end_users,
        )

        return SizingResult(**result_dict)
    
    @mcp.tool(
        name=namespace_prefix + "forecast_database_size",
        annotations=ToolAnnotations(
            title="Forecast Database Size",
            readOnlyHint=True,
            idempotentHint=True
        )
    )
    async def forecast_database_size(
        base_size_gb: float = Field(..., description="Current database size in GB"),
        base_memory_gb: int = Field(..., description="Current recommended memory in GB"),
        base_cores: int = Field(..., description="Current recommended number of cores"),
        annual_growth_rate: float = Field(10.0, description="Annual growth rate percentage (default: 10%)"),
        projection_years: int = Field(3, description="Number of years to project (default: 3)"),
        workloads: Optional[List[Literal["transactional", "agentic", "analytical", "graph_data_science"]]] = Field(
            None,
            description="Workload types that determine growth pattern. "
            "Options: 'transactional' (fast growth - high write volume), "
            "'agentic' (fast growth - RAG, vector search), "
            "'analytical' (moderate growth - reporting, BI), "
            "'graph_data_science' (slowest growth - algorithms, analytics). "
            "Can specify multiple workloads. Growth model uses fastest-growing workload. "
            "If None, uses generic compound growth."
        ),
        domain: Optional[Literal["customer", "product", "employee", "supplier", "transaction", "process", "security", "generic"]] = Field(
            None,
            description="Graph domain (7 Graphs of the Enterprise). "
            "Options: 'customer' (defaults to transactional+analytical), "
            "'product' (defaults to analytical), 'employee' (defaults to analytical), "
            "'supplier' (defaults to analytical), 'transaction' (defaults to transactional), "
            "'process' (defaults to analytical), 'security' (defaults to transactional+analytical). "
            "If provided, uses default workload types for the domain to determine growth model. "
            "Can be overridden by explicitly providing 'workloads' parameter."
        ),
        memory_to_storage_ratio: float = Field(
            1.0,
            description="Memory-to-storage ratio denominator. "
            "Options: 1.0 (1:1 ratio - memory equals storage), "
            "2.0 (1:2 ratio - memory is half of storage), "
            "4.0 (1:4 ratio - memory is quarter of storage), "
            "8.0 (1:8 ratio - memory is eighth of storage). "
            "Default: 1.0 (1:1 ratio). "
            "The ratio determines how memory scales with projected storage size."
        ),
    ) -> ForecastResult:
        """
        Forecast database growth over multiple years.
        
        This tool projects database size, memory, and core requirements over multiple years
        based on growth rate and workload characteristics.
        
        You can use the output from calculate_database_sizing as input to this tool,
        or provide your own base size, memory, and cores.
        
        **Graph Domains (7 Graphs of the Enterprise):**
        - customer: Customer 360, interactions → Default workloads: transactional, analytical
        - product: Product catalogs, recommendations → Default workloads: analytical
        - employee: Org charts, skills → Default workloads: analytical
        - supplier: Supply chain, dependencies → Default workloads: analytical
        - transaction: Fraud detection, payments → Default workloads: transactional
        - process: Workflows, dependencies → Default workloads: analytical
        - security: Access control, threats → Default workloads: transactional, analytical
        
        **Workload Types** (affect growth speed):
        - transactional: Fast growth (high write volume, real-time)
        - agentic: Fastest growth (RAG, vector search, AI/ML)
        - analytical: Moderate growth (reporting, BI)
        - graph_data_science: Slowest growth (algorithms, batch processing)
        
        If domain is provided, it uses default workloads unless workloads are explicitly specified.
        The growth model is automatically selected based on the fastest-growing workload.
        
        Returns multi-year projections with scaling recommendations.
        """
        result_dict = await aura_manager.forecast_database_size(
            base_size_gb=base_size_gb,
            base_memory_gb=base_memory_gb,
            base_cores=base_cores,
            annual_growth_rate=annual_growth_rate,
            projection_years=projection_years,
            workloads=workloads,
            domain=domain,
            memory_to_storage_ratio=memory_to_storage_ratio,
        )

        return ForecastResult(**result_dict)

    @mcp.prompt(title="Calculate Database Sizing")
    def calculate_database_sizing_prompt(
        graph_description: str = Field(
            ...,
            description="A description of the graph including nodes, relationships, properties, and any vector search requirements."
        ),
    ) -> str:
        """
        Guide the agent through collecting complete graph information for database sizing.
        
        Use this prompt when a user asks about database sizing. It provides a structured workflow
        to collect all necessary information before calculating sizing.
        """
        
        # Get parameter information from the current calculator
        params_info = get_calculator_parameter_info()
        
        # Build required parameters section
        required_section = ""
        if params_info['required']:
            required_section = "**Required Information:**\n"
            for param in params_info['required']:
                required_section += f"- {param['name'].replace('_', ' ').title()}: {param['description']}\n"
        
        # Build important optional parameters section
        optional_section = ""
        important_params = ['avg_properties_per_node', 'avg_properties_per_relationship', 
                           'vector_index_dimensions', 'percentage_nodes_with_vector_properties',
                           'total_num_large_node_properties', 'total_num_large_reltype_properties']
        
        if params_info['optional']:
            optional_section = "\n**Important for Accuracy:**\n"
            for param in params_info['optional']:
                if param['name'] in important_params:
                    default_str = f" (default: {param['default']})" if param['default'] is not None else ""
                    optional_section += f"- {param['name'].replace('_', ' ').title()}: {param['description']}{default_str}\n"
        
        prompt = f"""The user wants to calculate database sizing for their Neo4j graph.

**What they've told us:**
{graph_description}

**Information needed:**

{required_section}{optional_section}
**Process:**
1. **Information Gathering**
   - Identify what information is already provided from the user's description
   - Ask for any missing required information (nodes, relationships)
   - Ask about properties, vectors, and other details that significantly impact sizing accuracy
   
2. **Calculation**
   - Once you have collected the information (or confirmed defaults are acceptable), 
     call the `calculate_database_sizing` tool with all parameters
   
3. **Presentation**
   - Present the results clearly, showing the breakdown of storage components
   - Explain any recommendations for memory and vCPU

**Note:** Properties significantly impact sizing calculations. If the user only mentions 
nodes/relationships, you should ask about properties before calculating.
"""
        
        return prompt

    @mcp.prompt(title="Forecast Database Size")
    def forecast_database_size_prompt(
        graph_description: str = Field(
            ...,
            description="A description of the graph use case, domain, and workload types."
        ),
    ) -> str:
        """
        Guide the agent through identifying graph domain and workload types for growth forecasting.
        
        Use this prompt when a user wants to forecast database growth. It helps identify
        which of the 7 Graphs of the Enterprise applies and what workload types are being used.
        """
        
        prompt = f"""The user wants to forecast database growth for their Neo4j graph.

**What they've told us:**
{graph_description}

**7 Graphs of the Enterprise:**

1. **Customer** - Customer 360, interactions, preferences, journeys
   - Default workloads: Transactional, Analytical
   
2. **Product** - Product catalogs, recommendations, components
   - Default workloads: Analytical
   
3. **Employee** - Org charts, skills, collaborations
   - Default workloads: Analytical
   
4. **Supplier** - Supply chain, dependencies, risk
   - Default workloads: Analytical
   
5. **Transaction** - Fraud detection, payments, financial flows
   - Default workloads: Transactional
   
6. **Process** - Workflows, dependencies, bottlenecks
   - Default workloads: Analytical
   
7. **Security** - Access control, threats, compliance
   - Default workloads: Transactional, Analytical

**Workload Types** (affect growth speed):
- **Transactional** - Fast growth (high write volume, real-time)
- **Agentic** - Fastest growth (RAG, vector search, AI/ML)
- **Analytical** - Moderate growth (reporting, BI)
- **Graph Data Science** - Slowest growth (algorithms, batch processing)

**Process:**
1. **Domain Identification**
   - Map the user's description to one of the 7 Graphs of the Enterprise
   - If domain is identified, it will use default workloads unless explicitly overridden
   
2. **Workload Identification**
   - Identify workload types from the description
   - If not clear, ask the user about their workload patterns
   - Explicit workloads override domain defaults
   
3. **Forecast Setup**
   - Collect base size, memory, and cores (can use output from `calculate_database_sizing`)
   - Ask about growth rate and projection years if not provided
   - Determine memory-to-storage ratio preference
   
4. **Forecasting**
   - Call the `forecast_database_size` tool with all collected parameters
   - The growth model is automatically selected based on the fastest-growing workload
   
5. **Presentation**
   - Present multi-year projections with scaling recommendations
   - Explain when scaling might be needed

**Note:** The growth model selection is automatic based on workload types. 
If multiple workloads are specified, the system uses the fastest-growing one.
"""
        
        return prompt



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
    logger.info("Starting MCP Neo4j Aura Manager Server")
    
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
                f"Running Neo4j Aura Manager MCP Server with HTTP transport on {host}:{port}..."
            )
            logger.info(f"Stateless mode: {stateless}")
            await mcp.run_http_async(
                host=host, port=port, path=path, middleware=custom_middleware, stateless_http=stateless
            )
        case "stdio":
            logger.info("Running Neo4j Aura Manager MCP Server with stdio transport...")
            await mcp.run_stdio_async()
        case "sse":
            logger.info(
                f"Running Neo4j Aura Manager MCP Server with SSE transport on {host}:{port}..."
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
