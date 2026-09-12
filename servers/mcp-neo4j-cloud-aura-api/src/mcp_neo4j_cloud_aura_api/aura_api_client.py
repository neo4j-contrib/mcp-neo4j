import requests
import time
import json
from typing import Dict, Any, List, Optional, Union
from .utils import _validate_region, get_logger

logger = get_logger(__name__)

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
            
            if vector_optimized and memory < 4:
                raise ValueError("vector optimized instances must have at least 4GB memory")
            
            # If cloning, source_instance_id is required
            if source_instance_id is not None:
                if not isinstance(source_instance_id, str):
                    raise ValueError("source_instance for clone from instance must be defined")
        else:
            raise ValueError(f"Invalid type {type}")
        
        _validate_region(cloud_provider, region)
        
        if graph_analytics_plugin and type not in ["professional-db", "enterprise-db", "business-critical"]:
            raise ValueError("graph analytics plugin is only available for professional, enterprise, and business-critical instances")

        if vector_optimized and type not in ["professional-db", "enterprise-db", "business-critical"]:
            raise ValueError("vector optimized instances are only available for professional, enterprise, and business-critical instances")


        payload = {
            "tenant_id": tenant_id,
            "name": name,
            "memory": f"{memory}GB",
            "region": region,
            "version": version,
            "type": type,
            "vector_optimized": vector_optimized,
            "cloud_provider": cloud_provider,
            "graph_analytics_plugin": graph_analytics_plugin
        }
        
        # Add source_instance_id if provided (for cloning)
        if source_instance_id is not None:
            payload["source_instance_id"] = source_instance_id
        
        url = f"{self.BASE_URL}/instances"
        response = requests.post(url, headers=self._get_headers(), json=payload)
        return self._handle_response(response)
    
    def update_instance(self, instance_id: str, name: Optional[str] = None, 
                        memory: Optional[int] = None, 
                        vector_optimized: Optional[bool] = None, 
                        storage: Optional[int] = None) -> Dict[str, Any]:
        """Update an existing instance."""
        payload = {}
        if name is not None:
            payload["name"] = name
        if memory is not None:
            payload["memory"] = f"{memory}GB"
            payload["storage"] = f"{2*memory}GB"
        if storage is not None:
            payload["storage"] = f"{storage}GB"
        if vector_optimized is not None:
            payload["vector_optimized"] = str(vector_optimized).lower()
        
        # Validate vector optimization requirements only if both memory and vector_optimized are being updated
        if (memory is not None and vector_optimized is not None and 
            vector_optimized and memory < 4):
            raise ValueError("vector optimized instances must have at least 4GB memory")
        
        url = f"{self.BASE_URL}/instances/{instance_id}"
        response = requests.patch(url, headers=self._get_headers(), json=payload)
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