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
    
    mcp: FastMCP = FastMCP("mcp-neo4j-aura-manager", stateless_http=True)

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
        memory_to_storage_ratio: Optional[int] = Field(
            None,
            description="Memory-to-storage ratio denominator. "
            "Options: 1 (1:1 ratio - memory equals storage), "
            "2 (1:2 ratio - memory is half of storage), "
            "4 (1:4 ratio - memory is quarter of storage), "
            "8 (1:8 ratio - memory is eighth of storage). "
            "Must be one of these values. Raises ValueError if not. "
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
        domain: Literal["customer", "product", "employee", "supplier", "transaction", "process", "security", "generic"] = Field(
            ...,
            description="Graph domain (7 Graphs of the Enterprise) - PRIMARY INPUT. "
            "Determines growth model based on domain category: "
            "'customer', 'process', 'security' (Graphs of Behaviors → CompoundGrowthModel), "
            "'product', 'supplier' (Graphs of Things → CompoundGrowthModel), "
            "'employee' (Graphs of Things → LinearGrowthModel), "
            "'transaction' (Graphs of Transactions → LogLinearGrowthModel), "
            "'generic' (CompoundGrowthModel). "
            "Workloads parameter can override domain-based growth model."
        ),
        annual_growth_rate: Optional[float] = Field(
            None,
            description="Annual growth rate percentage. If not provided, uses smart defaults based on workloads/domain: "
            "Transactional (20%), Agentic (15%), Analytical (5%), or domain-specific defaults."
        ),
        projection_years: int = Field(3, description="Number of years to project (default: 3)"),
        workloads: Optional[List[Literal["transactional", "agentic", "analytical"]]] = Field(
            None,
            description="Workload types that override domain-based growth model. "
            "Options: 'transactional' (LogLinearGrowthModel - fast growth, high core scaling), "
            "'agentic' (CompoundGrowthModel - medium growth, medium core scaling), "
            "'analytical' (CompoundGrowthModel - moderate growth, low core scaling). "
            "If provided, overrides domain-based growth model selection. "
            "Also affects core scaling: transactional (1.5x), agentic (1.2x), analytical (1.0x)."
        ),
        memory_to_storage_ratio: int = Field(
            1,
            description="Memory-to-storage ratio denominator. "
            "Options: 1 (1:1 ratio - memory equals storage), "
            "2 (1:2 ratio - memory is half of storage), "
            "4 (1:4 ratio - memory is quarter of storage), "
            "8 (1:8 ratio - memory is eighth of storage). "
            "Must be one of these values. Raises ValueError if not. "
            "Default: 1 (1:1 ratio). "
            "The ratio determines how memory scales with projected storage size."
        ),
    ) -> ForecastResult:
        """
        Forecast database growth over multiple years.
        
        This tool projects database size, memory, and core requirements over multiple years
        based on domain (7 Graphs of the Enterprise) and optional workload overrides.
        
        You can use the output from calculate_database_sizing as input to this tool,
        or provide your own base size, memory, and cores.
        
        **Growth Model Selection:**
        - Domain is the PRIMARY driver for growth model selection
        - Workloads can override domain-based growth model when explicitly provided
        - Core scaling is dynamic based on workload type and storage growth
        
        Returns multi-year projections with scaling recommendations.
        """
        result_dict = await aura_manager.forecast_database_size(
            base_size_gb=base_size_gb,
            base_memory_gb=base_memory_gb,
            base_cores=base_cores,
            domain=domain,
            annual_growth_rate=annual_growth_rate,
            projection_years=projection_years,
            workloads=workloads,
            memory_to_storage_ratio=memory_to_storage_ratio,
        )

        return ForecastResult(**result_dict)

    @mcp.prompt(title="Calculate Database Sizing")
    def calculate_database_sizing_prompt(
        # Required parameters
        num_nodes: Optional[int] = Field(None, description="Number of nodes in the graph"),
        num_relationships: Optional[int] = Field(None, description="Number of relationships in the graph"),
        avg_properties_per_node: Optional[int] = Field(None, description="Average number of properties per node. Required for accurate sizing."),
        avg_properties_per_relationship: Optional[int] = Field(None, description="Average number of properties per relationship. Required for accurate sizing."),
        
        # Optional parameters
        total_num_large_node_properties: Optional[int] = Field(None, description="Total number of large properties (128+ bytes) across all nodes (default: 0)"),
        total_num_large_reltype_properties: Optional[int] = Field(None, description="Total number of large properties (128+ bytes) across all relationships (default: 0)"),
        vector_index_dimensions: Optional[int] = Field(None, description="Vector index dimensions (default: 0 if not using vectors)"),
        percentage_nodes_with_vector_properties: Optional[float] = Field(None, description="Percentage of nodes with properties in vector index 0-100 (default: 0.0)"),
        number_of_vector_indexes: Optional[int] = Field(None, description="Number of vector indexes (default: 0)"),
        quantization_enabled: Optional[bool] = Field(None, description="Enable scalar quantization for vectors (4x storage reduction, uses int8 instead of float32)"),
        memory_to_storage_ratio: Optional[int] = Field(None, description="Memory-to-storage ratio denominator. Options: 1 (1:1), 2 (1:2), 4 (1:4), 8 (1:8). If provided, calculates recommended_memory_gb."),
        concurrent_end_users: Optional[int] = Field(None, description="Number of concurrent end users. If provided, calculates recommended_vcpus (2 vCPU per concurrent user)."),
    ) -> str:
        """
        Guide the agent through collecting complete graph information for database sizing.
        
        Use this prompt when a user asks about database sizing. It provides a structured workflow
        to collect all necessary information before calculating sizing.
        """
        
        # Build list of provided and missing parameters
        provided_params = []
        missing_required = []
        
        if num_nodes is not None:
            provided_params.append(f"- num_nodes: {num_nodes}")
        else:
            missing_required.append("num_nodes")
            
        if num_relationships is not None:
            provided_params.append(f"- num_relationships: {num_relationships}")
        else:
            missing_required.append("num_relationships")
            
        if avg_properties_per_node is not None:
            provided_params.append(f"- avg_properties_per_node: {avg_properties_per_node}")
        else:
            missing_required.append("avg_properties_per_node")
            
        if avg_properties_per_relationship is not None:
            provided_params.append(f"- avg_properties_per_relationship: {avg_properties_per_relationship}")
        else:
            missing_required.append("avg_properties_per_relationship")
        
        # Optional parameters
        if total_num_large_node_properties is not None:
            provided_params.append(f"- total_num_large_node_properties: {total_num_large_node_properties}")
        if total_num_large_reltype_properties is not None:
            provided_params.append(f"- total_num_large_reltype_properties: {total_num_large_reltype_properties}")
        if vector_index_dimensions is not None:
            provided_params.append(f"- vector_index_dimensions: {vector_index_dimensions}")
        if percentage_nodes_with_vector_properties is not None:
            provided_params.append(f"- percentage_nodes_with_vector_properties: {percentage_nodes_with_vector_properties}")
        if number_of_vector_indexes is not None:
            provided_params.append(f"- number_of_vector_indexes: {number_of_vector_indexes}")
        if quantization_enabled is not None:
            provided_params.append(f"- quantization_enabled: {quantization_enabled}")
        if memory_to_storage_ratio is not None:
            provided_params.append(f"- memory_to_storage_ratio: {memory_to_storage_ratio}")
        if concurrent_end_users is not None:
            provided_params.append(f"- concurrent_end_users: {concurrent_end_users}")
        
        # Build the prompt
        provided_section = "\n".join(provided_params) if provided_params else "None provided yet."
        missing_section = ", ".join(missing_required) if missing_required else "None - all required parameters are provided!"
        
        prompt = f"""The user wants to calculate database sizing for their Neo4j graph.

**Information already provided:**
{provided_section}

**Missing required parameters:**
{missing_section}

**Process:**
1. **Information Gathering**
   - If any required parameters are missing, ask the user for them
   - For optional parameters, ask if they apply to the user's use case (vectors, large properties, etc.)
   - Property counts (avg_properties_per_node and avg_properties_per_relationship) are critical for accuracy
   
2. **Calculation**
   - Once you have all required parameters (or confirmed defaults are acceptable for optional ones), 
     call the `calculate_database_sizing` tool with the collected parameters
   - Only include parameters that have been provided or have meaningful defaults
   
3. **Presentation**
   - Present the results clearly, showing the breakdown of storage components
   - Explain any recommendations for memory and vCPU

**Note:** Properties significantly impact sizing calculations. Always ask about properties if the user 
hasn't provided avg_properties_per_node and avg_properties_per_relationship.
"""
        
        return prompt

    @mcp.prompt(title="Forecast Database Size")
    def forecast_database_size_prompt(
        # Required parameters
        base_size_gb: Optional[float] = Field(None, description="Current database size in GB"),
        base_memory_gb: Optional[int] = Field(None, description="Current recommended memory in GB"),
        base_cores: Optional[int] = Field(None, description="Current recommended number of cores"),
        
        # Optional parameters
        annual_growth_rate: Optional[float] = Field(None, description="Annual growth rate percentage (default: 10%)"),
        projection_years: Optional[int] = Field(None, description="Number of years to project (default: 3)"),
        domain: Optional[str] = Field(
            None,
            description="Graph domain (7 Graphs of the Enterprise). Options: 'customer', 'product', 'employee', 'supplier', 'transaction', 'process', 'security', 'generic'"
        ),
        workloads: Optional[str] = Field(
            None,
            description="Workload types that determine growth pattern. Options: 'transactional', 'agentic', 'analytical'. Can specify multiple."
        ),
        memory_to_storage_ratio: Optional[int] = Field(
            None,
            description="Memory-to-storage ratio denominator. Options: 1 (1:1), 2 (1:2), 4 (1:4), 8 (1:8). Default: 1."
        ),
    ) -> str:
        """
        Guide the agent through collecting information for database growth forecasting.
        
        Use this prompt when a user wants to forecast database growth. It provides a structured workflow
        to collect all necessary information before forecasting.
        """
        
        # Build list of provided and missing parameters
        provided_params = []
        missing_required = []
        
        if base_size_gb is not None:
            provided_params.append(f"- base_size_gb: {base_size_gb}")
        else:
            missing_required.append("base_size_gb")
            
        if base_memory_gb is not None:
            provided_params.append(f"- base_memory_gb: {base_memory_gb}")
        else:
            missing_required.append("base_memory_gb")
            
        if base_cores is not None:
            provided_params.append(f"- base_cores: {base_cores}")
        else:
            missing_required.append("base_cores")
        
        # Optional parameters
        if annual_growth_rate is not None:
            provided_params.append(f"- annual_growth_rate: {annual_growth_rate}%")
        if projection_years is not None:
            provided_params.append(f"- projection_years: {projection_years}")
        if domain is not None:
            provided_params.append(f"- domain: {domain}")
        if workloads is not None:
            provided_params.append(f"- workloads: {workloads}")
        if memory_to_storage_ratio is not None:
            provided_params.append(f"- memory_to_storage_ratio: {memory_to_storage_ratio}")
        
        # Build the prompt
        provided_section = "\n".join(provided_params) if provided_params else "None provided yet."
        missing_section = ", ".join(missing_required) if missing_required else "None - all required parameters are provided!"
        
        prompt = f"""The user wants to forecast database growth for their Neo4j graph.

**Information already provided:**
{provided_section}

**Missing required parameters:**
{missing_section}

**7 Graphs of the Enterprise:**
1. **Customer** - Customer 360, interactions, preferences, journeys (defaults to transactional+analytical)
2. **Product** - Product catalogs, recommendations, components (defaults to analytical)
3. **Employee** - Org charts, skills, collaborations (defaults to analytical)
4. **Supplier** - Supply chain, dependencies, risk (defaults to analytical)
5. **Transaction** - Fraud detection, payments, financial flows (defaults to transactional)
6. **Process** - Workflows, dependencies, bottlenecks (defaults to analytical)
7. **Security** - Access control, threats, compliance (defaults to transactional+analytical)

**Workload Types** (affect component growth patterns):
- **Transactional** - Fast growth for all components (storage, memory, vcpu use LogLinearGrowthModel)
- **Agentic** - Medium growth for all components (storage, memory, vcpu use CompoundGrowthModel)
- **Analytical** - Moderate growth for storage (CompoundGrowthModel), slower for memory/vcpu (LinearGrowthModel)

**Component-Based Growth Models:**
The forecasting system uses separate growth models for each component:
- **Storage** - Grows based on data volume
- **Memory** - Grows independently, but constrained by memory_to_storage_ratio
- **vCPU** - Grows independently based on compute needs

**Process:**
1. **Information Gathering**
   - If base_size_gb, base_memory_gb, or base_cores are missing, ask the user for them
   - These can come from the output of `calculate_database_sizing` tool
   - For optional parameters, ask if they apply or use defaults:
     * annual_growth_rate: automatically determined from workloads/domain (Transactional: 20%, Agentic: 15%, Analytical: 5%, or domain-specific)
     * projection_years: default 3 years
     * domain: identify from user's description (7 Graphs of the Enterprise)
     * workloads: identify from user's description (overrides domain defaults if provided)
     * memory_to_storage_ratio: default 1 (1:1 ratio) - acts as minimum floor for memory
   
2. **Domain and Workload Identification**
   - Domain is the primary driver for growth model selection
   - If domain is provided, it uses component-based growth models for that domain
   - If workloads are provided, they override domain defaults
   - Each component (storage, memory, vcpu) gets its own growth model based on workload/domain
   - If multiple workloads are specified, the fastest-growing model is used for each component
   
3. **Forecasting**
   - Once you have all required parameters (or confirmed defaults are acceptable for optional ones),
     call the `forecast_database_size` tool with the collected parameters
   - Only include parameters that have been provided or have meaningful defaults
   
4. **Presentation**
   - Present multi-year projections showing storage, memory, and vcpu growth independently
   - Explain when scaling might be needed for each component
   - Note that memory is constrained by memory_to_storage_ratio (minimum floor)

**Note:** Each component (storage, memory, vcpu) grows independently using its own growth model.
The memory_to_storage_ratio acts as a constraint, ensuring memory meets minimum requirements.
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
