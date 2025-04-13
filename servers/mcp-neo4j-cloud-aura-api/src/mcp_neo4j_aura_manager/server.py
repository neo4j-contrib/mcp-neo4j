import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Union

import mcp
import requests
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AuraAPIClient:
    """Client for interacting with Neo4j Aura API."""
    
    BASE_URL = "https://api.neo4j.io/v1"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expiry = 0
    
    def _get_auth_token(self) -> str:
        """Get authentication token for Aura API."""
        auth_url = "https://api.neo4j.io/oauth/token"
        
        # Create base64 encoded credentials
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        payload = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(auth_url, headers=headers, data=payload)
            response.raise_for_status()
            token_data = response.json()
            if not isinstance(token_data, dict) or \
               not token_data.get("access_token") or \
               not token_data.get("expires_in") or \
               not token_data.get("token_type") or \
               token_data.get("token_type").lower() != "bearer":
                raise Exception("Invalid token response format")
            self.token = token_data["access_token"]
            return self.token
        except requests.RequestException as e:
            logger.error(f"Authentication error: {str(e)}")
            raise Exception(f"Failed to authenticate with Neo4j Aura API: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests including authentication."""
        current_time = time.time()
        if not self.token or current_time >= self.token_expiry:
            self.token = self._get_auth_token()
            
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            data = response.json()
            if "data" in data:
                return data["data"]
            else:
                return data
        except requests.HTTPError as e:
            error_msg = f"HTTP error: {e}"
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_msg = f"{error_msg} - {error_data['message']}"
            except:
                pass
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            logger.error("Failed to parse API response")
            raise Exception("Failed to parse API response")
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all database instances."""
        url = f"{self.BASE_URL}/instances"
        response = requests.get(url, headers=self._get_headers())
        return self._handle_response(response)
    
    def get_instance_details(self, instance_ids: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get details for one or more instances by ID.
        
        Args:
            instance_ids: Either a single instance ID string or a list of instance ID strings
            
        Returns:
            A single instance details dict or a list of instance details dicts
        """
        if isinstance(instance_ids, str):
            # Handle single instance ID
            url = f"{self.BASE_URL}/instances/{instance_ids}"
            response = requests.get(url, headers=self._get_headers())
            return self._handle_response(response)
        else:
            # Handle list of instance IDs
            results = []
            for instance_id in instance_ids:
                url = f"{self.BASE_URL}/instances/{instance_id}"
                response = requests.get(url, headers=self._get_headers())
                try:
                    data = self._handle_response(response)
                    results.append(data)
                except Exception as e:
                    results.append({"error": str(e), "instance_id": instance_id})
            return results
    
    def get_instance_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an instance by name."""
        instances = self.list_instances()
        for instance in instances:
            if name.lower() in instance.get("name", "").lower():
                # Get full instance details using the instance ID
                return self.get_instance_details(instance.get("id"))
        return None
    
    def create_instance(self, tenant_id: str, name: str, memory: int = 1, region: str = "europe-west1", 
                        version: str = "5", type: str = "free-db", 
                        vector_optimized: bool = False,
                        cloud_provider: str = "gcp", graph_analytics_plugin: bool = False,
                        source_instance_id: str = None) -> Dict[str, Any]:
        """Create a new database instance."""
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        
        # Always set version to "5"
        version = "5"
        
        # Validate based on instance type
        if type == "free-db":
            if memory != 1:
                raise ValueError("free-db instances can only have 1GB memory")
            
            if not cloud_provider == "gcp":
                raise ValueError("free-db instances can only be created in GCP regions")
            
            if vector_optimized:
                raise ValueError("free-db instances cannot be vector optimized")
        
        # Validate for professional/enterprise/business-critical types
        elif type in ["professional-db", "enterprise-db", "business-critical"]:
            if cloud_provider and cloud_provider not in ["gcp", "aws", "azure"]:
                raise ValueError("cloud_provider must be one of: gcp, aws, azure")
            
            # If cloning, source_instance_id is required
            if source_instance_id is not None:
                if not isinstance(source_instance_id, str):
                    raise ValueError("source_instance for clone from instance must be defined")
        else:
            raise ValueError(f"Invalid type {type}")
            
        url = f"{self.BASE_URL}/instances"
        payload = {
            "name": name,
            "memory": f"{memory}GB",  # in GB
            "region": region,
            "version": version,
            "type": type,
            "tenant_id": tenant_id,
            "cloud_provider": cloud_provider
        }
        
        # Add optional parameters only if they're provided and applicable            
        if graph_analytics_plugin and type in ["professional-db", "enterprise-db", "business-critical"]:
            payload["graph_analytics_plugin"] = lower(str(graph_analytics_plugin))
            
        if vector_optimized and type in ["professional-db", "enterprise-db", "business-critical"]:
            payload["vector_optimized"] = lower(str(vector_optimized))
            
        if source_instance_id and type in ["professional-db", "enterprise-db", "business-critical"]:
            payload["source_instance_id"] = source_instance_id
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        return self._handle_response(response)

    
    def update_instance(self, instance_id: str, name: Optional[str] = None, 
                        memory: Optional[int] = None, 
                        vector_optimized: Optional[bool] = None) -> Dict[str, Any]:
        """Update an existing instance."""
        url = f"{self.BASE_URL}/instances/{instance_id}"
        
        payload = {}
        if name is not None:
            payload["name"] = name
        if memory is not None:
            payload["memory"] = f"{memory}GB"
        if vector_optimized is not None:
            payload["vector_optimized"] = lower(str(vector_optimized))
        
        print("Update instance payload:")
        print(payload)
        response = requests.patch(url, headers=self._get_headers(), json=payload)
        print("Update instance response: "+str(response.status_code))
        print(response.json())
        return self._handle_response(response)
    
    def pause_instance(self, instance_id: str) -> Dict[str, Any]:
        """Pause a database instance."""
        url = f"{self.BASE_URL}/instances/{instance_id}/pause"
        response = requests.post(url, headers=self._get_headers())
        return self._handle_response(response)
    
    def resume_instance(self, instance_id: str) -> Dict[str, Any]:
        """Resume a paused database instance."""
        url = f"{self.BASE_URL}/instances/{instance_id}/resume"
        response = requests.post(url, headers=self._get_headers())
        return self._handle_response(response)
    
    def list_tenants(self) -> List[Dict[str, Any]]:
        """List all tenants/projects."""
        url = f"{self.BASE_URL}/tenants"
        response = requests.get(url, headers=self._get_headers())
        return self._handle_response(response)
    
    def get_tenant_details(self, tenant_id: str) -> Dict[str, Any]:
        """Get details for a specific tenant/project."""
        url = f"{self.BASE_URL}/tenants/{tenant_id}"
        response = requests.get(url, headers=self._get_headers())
        return self._handle_response(response)

    def delete_instance(self, instance_id: str) -> Dict[str, Any]:
        """Delete a database instance.
        
        Args:
            instance_id: ID of the instance to delete
            
        Returns:
            Response dict with status information
        """
        url = f"{self.BASE_URL}/instances/{instance_id}"
        response = requests.delete(url, headers=self._get_headers())
        return self._handle_response(response)

class AuraManager:
    """MCP server for Neo4j Aura instance management."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client = AuraAPIClient(client_id, client_secret)
    
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
            return self.client.delete_instance(instance_id=instance_id)
        except Exception as e:
            return {"error": str(e)}

async def main(client_id: str, client_secret: str):
    """Start the MCP server."""
    aura_manager = AuraManager(client_id, client_secret)
    
    # Create MCP server
    server = Server("mcp-neo4j-aura-manager")

    # Register handlers
    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="list_instances",
                description="List all Neo4j Aura database instances",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "readOnlyHint": True,
                    "title": "List all Neo4j Aura database instances"
                },
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="get_instance_details",
                description="Get details for one or more Neo4j Aura instances by ID, including status, region, memory, storage",
                annotations={
                    "destructiveHint": False, 
                    "idempotentHint": True,
                    "readOnlyHint": True,
                    "title": "Get instance details"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "instance_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of instance IDs to retrieve"
                        }
                    },
                    "required": ["instance_ids"],
                },
            ),
            types.Tool(
                name="get_instance_by_name",
                description="Find a Neo4j Aura instance by name and returns the details including the id",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "readOnlyHint": True,
                    "title": "Find instance by name"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the instance to find"
                        }
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="create_instance",
                description="Create a new Neo4j Aura database instance",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": False,
                    "readOnlyHint": False,
                    "title": "Create instance"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tenant_id": {
                            "type": "string",
                            "description": "ID of the tenant/project where the instance will be created"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name for the new instance"
                        },
                        "memory": {
                            "type": "integer",
                            "description": "Memory allocation in GB",
                            "default": 1
                        },
                        "region": {
                            "type": "string",
                            "description": "Region for the instance (e.g., 'us-east-1')",
                            "default": "us-central1"
                        },
                        "type": {
                            "type": "string",
                            "description": "Instance type (free-db, professional-db, enterprise-db, or business-critical)",
                            "default": "free-db"
                        },
                        "vector_optimized": {
                            "type": "boolean",
                            "description": "Whether the instance is optimized for vector operations",
                            "default": False
                        },
                        "cloud_provider": {
                            "type": "string",
                            "description": "Cloud provider (gcp, aws, azure)",
                            "default": "gcp"
                        },
                        "graph_analytics_plugin": {
                            "type": "boolean",
                            "description": "Whether to enable the graph analytics plugin",
                            "default": False
                        },
                        "source_instance_id": {
                            "type": "string",
                            "description": "ID of the source instance to clone from (for professional/enterprise instances)",
                        }
                    },
                    "required": ["tenant_id", "name"],
                },
            ),
            types.Tool(
                name="update_instance_name",
                description="Update the name of a Neo4j Aura instance",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "readOnlyHint": False,
                    "title": "Update instance name"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "ID of the instance to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "New name for the instance"
                        }
                    },
                    "required": ["instance_id", "name"],
                },
            ),
            types.Tool(
                name="update_instance_memory",
                description="Update the memory allocation of a Neo4j Aura instance",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "readOnlyHint": False,
                    "title": "Update instance memory"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "ID of the instance to update"
                        },
                        "memory": {
                            "type": "integer",
                            "description": "New memory allocation in GB"
                        }
                    },
                    "required": ["instance_id", "memory"],
                },
            ),
            types.Tool(
                name="update_instance_vector_optimization",
                description="Update the vector optimization setting of a Neo4j Aura instance",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "readOnlyHint": False,
                    "title": "Update instance vector optimization"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "ID of the instance to update"
                        },
                        "vector_optimized": {
                            "type": "boolean",
                            "description": "Whether the instance should be optimized for vector operations"
                        }
                    },
                    "required": ["instance_id", "vector_optimized"],
                },
            ),
            types.Tool(
                name="pause_instance",
                description="Pause a Neo4j Aura database instance",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": False,
                    "readOnlyHint": False,
                    "title": "Pause instance"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "ID of the instance to pause"
                        }
                    },
                    "required": ["instance_id"],
                },
            ),
            types.Tool(
                name="resume_instance",
                description="Resume a paused Neo4j Aura database instance",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": False,
                    "readOnlyHint": False,
                    "title": "Resume instance"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "ID of the instance to resume"
                        }
                    },
                    "required": ["instance_id"],
                },
            ),
            types.Tool(
                name="list_tenants",
                description="List all Neo4j Aura tenants/projects",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "readOnlyHint": True,
                    "title": "List tenants"
                },
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="get_tenant_details",
                description="Get details for a specific Neo4j Aura tenant/project",
                annotations={
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "readOnlyHint": True,
                    "title": "Get tenant details"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tenant_id": {
                            "type": "string",
                            "description": "ID of the tenant/project to retrieve"
                        }
                    },
                    "required": ["tenant_id"],
                },
            ),
            types.Tool(
                name="delete_instance",
                description="Delete a Neo4j Aura database instance",
                annotations={
                    "destructiveHint": True,
                    "idempotentHint": False,
                    "readOnlyHint": False,
                    "title": "Delete instance"
                },
                inputSchema={
                    "type": "object",
                    "properties": {
                        "instance_id": {
                            "type": "string",
                            "description": "ID of the instance to delete"
                        }
                    },
                    "required": ["instance_id"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Dict[str, Any] | None
    ) -> List[types.TextContent | types.ImageContent]:
        try:
            if not arguments and name not in ["list_instances", "list_tenants"]:
                raise ValueError(f"No arguments provided for tool: {name}")

            if name == "list_instances":
                result = await aura_manager.list_instances()
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "get_instance_details":
                result = await aura_manager.get_instance_details(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "get_instance_by_name":
                result = await aura_manager.get_instance_by_name(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "create_instance":
                result = await aura_manager.create_instance(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "update_instance_name":
                result = await aura_manager.update_instance_name(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "update_instance_memory":
                result = await aura_manager.update_instance_memory(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "update_instance_vector_optimization":
                result = await aura_manager.update_instance_vector_optimization(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "pause_instance":
                result = await aura_manager.pause_instance(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "resume_instance":
                result = await aura_manager.resume_instance(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "list_tenants":
                result = await aura_manager.list_tenants()
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "get_tenant_details":
                result = await aura_manager.get_tenant_details(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "delete_instance":
                result = await aura_manager.delete_instance(**arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # Start the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Neo4j Aura Database Manager MCP Server running on stdio")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-neo4j-aura-manager",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
    
    return server


if __name__ == "__main__":
    main()
