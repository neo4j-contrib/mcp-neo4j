from typing import Dict, Any, List
from .aura_api_client import AuraAPIClient
from .utils import get_logger

logger = get_logger(__name__)

class AuraManager:
    """Service layer for the Aura API MCP Server."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client = AuraAPIClient(client_id, client_secret)
    
    async def list_instances(self, **kwargs) -> Dict[str, Any]:
        """List all Aura database instances."""
        instances = self.client.list_instances()
        return {
            "instances": instances,
            "count": len(instances)
        }
    
    async def get_instance_details(self, instance_ids: List[str], **kwargs) -> Dict[str, Any]:
        """Get details for one or more instances by ID."""
        results = self.client.get_instance_details(instance_ids)
        return {
            "instances": results,
            "count": len(results)
        }
    
    async def get_instance_by_name(self, name: str, **kwargs) -> Dict[str, Any]:
        """Find an instance by name."""
        instance = self.client.get_instance_by_name(name)
        if instance:
            return instance
        return {"error": f"Instance with name '{name}' not found"}
    
    async def create_instance(self, tenant_id: str, name: str, memory: int = 1, region: str = "us-central1", 
                             version: str = "5", type: str = "free-db", 
                             vector_optimized: bool = False,
                             cloud_provider: str = "gcp", graph_analytics_plugin: bool = False,
                             source_instance_id: str = None, **kwargs) -> Dict[str, Any]:
        """Create a new database instance."""
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
    
    async def update_instance_name(self, instance_id: str, name: str, **kwargs) -> Dict[str, Any]:
        """Update an instance's name."""
        return self.client.update_instance(instance_id=instance_id, name=name)
    
    async def update_instance_memory(self, instance_id: str, memory: int, **kwargs) -> Dict[str, Any]:
        """Update an instance's memory allocation."""

        return self.client.update_instance(instance_id=instance_id, memory=memory)
    
    async def update_instance_vector_optimization(self, instance_id: str, 
                                                vector_optimized: bool, **kwargs) -> Dict[str, Any]:
        """Update an instance's vector optimization setting."""
        
        return self.client.update_instance(
            instance_id=instance_id, 
            vector_optimized=vector_optimized
            )
    
    async def pause_instance(self, instance_id: str, **kwargs) -> Dict[str, Any]:
        """Pause a database instance."""
        
        return self.client.pause_instance(instance_id)
    
    async def resume_instance(self, instance_id: str, **kwargs) -> Dict[str, Any]:
        """Resume a paused database instance."""
        
        return self.client.resume_instance(instance_id)
    
    
    async def list_tenants(self, **kwargs) -> Dict[str, Any]:
        """List all tenants/projects."""
        
        tenants = self.client.list_tenants()
        return {
            "tenants": tenants,
            "count": len(tenants)
        }
    
    async def get_tenant_details(self, tenant_id: str, **kwargs) -> Dict[str, Any]:
        """Get details for a specific tenant/project."""
        
        return self.client.get_tenant_details(tenant_id)

    
    async def delete_instance(self, instance_id: str, **kwargs) -> Dict[str, Any]:
        """Delete one database instance."""
        
        return self.client.delete_instance(instance_id)

