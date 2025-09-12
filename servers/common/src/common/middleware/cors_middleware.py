"""
CORS middleware configuration for MCP Neo4j servers.
"""

from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


def create_cors_middleware(allow_origins: list[str]) -> Middleware:
    """
    Create CORS middleware with specified allowed origins.
    
    Parameters
    ----------
    allow_origins : list[str]
        List of allowed origins for CORS requests
        
    Returns
    -------
    Middleware
        Configured CORS middleware instance
    """
    return Middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )