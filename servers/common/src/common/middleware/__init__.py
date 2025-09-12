"""
Middleware components for MCP Neo4j servers.
"""

from .cors_middleware import create_cors_middleware
from .trusted_host_middleware import create_trusted_host_middleware

__all__ = ["create_cors_middleware", "create_trusted_host_middleware"]
