from typing import Dict, Any, List, Optional, Literal
from .aura_api_client import AuraAPIClient
from .sizing import AuraSizingService
from .utils import get_logger

logger = get_logger(__name__)

class AuraManager:
    """Service layer for the Aura API MCP Server."""
    
    def __init__(
        self, 
        client_id: str, 
        client_secret: str,
        sizing_service: Optional[AuraSizingService] = None
    ):
        """
        Initialize the Aura Manager.
        
        Args:
            client_id: Aura API client ID
            client_secret: Aura API client secret
            sizing_service: Optional sizing service instance. If None, creates a default instance.
                           Useful for dependency injection in tests.
        """
        self.client = AuraAPIClient(client_id, client_secret)
        self.sizing_service = sizing_service or AuraSizingService()
    
    async def list_instances(self, **kwargs) -> Dict[str, Any]:
        """List all Aura database instances."""
        try:
            instances = self.client.list_instances()
            return {
                "instances": instances,
                "count": len(instances)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_instance_details(self, instance_ids: List[str], **kwargs) -> Dict[str, Any]:
        """Get details for one or more instances by ID."""
        try:
            results = self.client.get_instance_details(instance_ids)
            return {
                "instances": results,
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_instance_by_name(self, name: str, **kwargs) -> Dict[str, Any]:
        """Find an instance by name."""
        try:
            instance = self.client.get_instance_by_name(name)
            if instance:
                return instance
            return {"error": f"Instance with name '{name}' not found"}
        except Exception as e:
            return {"error": str(e)}
    
    async def create_instance(self, tenant_id: str, name: str, memory: int = 1, region: str = "us-central1", 
                             version: str = "5", type: str = "free-db", 
                             vector_optimized: bool = False,
                             cloud_provider: str = "gcp", graph_analytics_plugin: bool = False,
                             source_instance_id: str = None, **kwargs) -> Dict[str, Any]:
        """Create a new database instance."""
        try:
            return self.client.create_instance(
                tenant_id=tenant_id,
                name=name,
                memory=memory,
                region=region,
                version=version,
                type=type,
                vector_optimized=vector_optimized,
                cloud_provider=cloud_provider,
                graph_analytics_plugin=graph_analytics_plugin,
                source_instance_id=source_instance_id
            )
        except Exception as e:
            return {"error": str(e)}
    
    async def update_instance_name(self, instance_id: str, name: str, **kwargs) -> Dict[str, Any]:
        """Update an instance's name."""
        try:
            return self.client.update_instance(instance_id=instance_id, name=name)
        except Exception as e:
            return {"error": str(e)}
    
    async def update_instance_memory(self, instance_id: str, memory: int, **kwargs) -> Dict[str, Any]:
        """Update an instance's memory allocation."""
        try:
            return self.client.update_instance(instance_id=instance_id, memory=memory)
        except Exception as e:
            return {"error": str(e)}
    
    async def update_instance_vector_optimization(self, instance_id: str, 
                                                vector_optimized: bool, **kwargs) -> Dict[str, Any]:
        """Update an instance's vector optimization setting."""
        try:
            return self.client.update_instance(
                instance_id=instance_id, 
                vector_optimized=vector_optimized
            )
        except Exception as e:
            return {"error": str(e)}
    
    async def pause_instance(self, instance_id: str, **kwargs) -> Dict[str, Any]:
        """Pause a database instance."""
        try:
            return self.client.pause_instance(instance_id)
        except Exception as e:
            return {"error": str(e)}
    
    async def resume_instance(self, instance_id: str, **kwargs) -> Dict[str, Any]:
        """Resume a paused database instance."""
        try:
            return self.client.resume_instance(instance_id)
        except Exception as e:
            return {"error": str(e)}
    
    async def list_tenants(self, **kwargs) -> Dict[str, Any]:
        """List all tenants/projects."""
        try:
            tenants = self.client.list_tenants()
            return {
                "tenants": tenants,
                "count": len(tenants)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_tenant_details(self, tenant_id: str, **kwargs) -> Dict[str, Any]:
        """Get details for a specific tenant/project."""
        try:
            return self.client.get_tenant_details(tenant_id)
        except Exception as e:
            return {"error": str(e)}
    
    async def delete_instance(self, instance_id: str, **kwargs) -> Dict[str, Any]:
        """Delete one database instance."""
        try:
            return self.client.delete_instance(instance_id)
        except Exception as e:
            return {"error": str(e)}
    
    async def calculate_database_sizing(
        self,
        num_nodes: int,
        num_relationships: int,
        avg_properties_per_node: int,
        avg_properties_per_relationship: int,
        total_num_large_node_properties: Optional[int] = None,
        total_num_large_reltype_properties: Optional[int] = None,
        vector_index_dimensions: Optional[int] = None,
        percentage_nodes_with_vector_properties: Optional[float] = None,
        number_of_vector_indexes: Optional[int] = None,
        quantization_enabled: bool = False,
        memory_to_storage_ratio: Optional[int] = None,
        concurrent_end_users: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Calculate current database sizing based on graph metrics."""
        try:
            result = self.sizing_service.calculate_sizing(
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
            # Convert Pydantic model to dict
            return result.model_dump()
        except Exception as e:
            logger.error(f"Error calculating sizing: {str(e)}")
            raise  # Re-raise exception so FastMCP can handle it properly
    
    async def forecast_database_size(
        self,
        base_size_gb: float,
        base_memory_gb: int,
        base_cores: int,
        annual_growth_rate: float = 10.0,
        projection_years: int = 3,
        workloads: Optional[List[str]] = None,
        domain: Optional[str] = None,
        memory_to_storage_ratio: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """Forecast database growth over multiple years."""
        try:
            result = self.sizing_service.forecast_sizing(
                base_size_gb=base_size_gb,
                base_memory_gb=base_memory_gb,
                base_cores=base_cores,
                annual_growth_rate=annual_growth_rate,
                projection_years=projection_years,
                workloads=workloads,
                domain=domain,
                memory_to_storage_ratio=memory_to_storage_ratio,
            )
            # Convert Pydantic model to dict
            return result.model_dump()
        except Exception as e:
            logger.error(f"Error forecasting sizing: {str(e)}")
            raise  # Re-raise exception so FastMCP can handle it properly