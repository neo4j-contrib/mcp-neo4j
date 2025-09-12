"""
Trusted Host middleware configuration for MCP Neo4j servers.
"""

from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware


def create_trusted_host_middleware(allowed_hosts: list[str]) -> Middleware:
    """
    Create TrustedHost middleware with specified allowed hosts.

    Parameters
    ----------
    allowed_hosts : list[str]
        List of allowed hosts for DNS rebinding protection

    Returns
    -------
    Middleware
        Configured TrustedHost middleware instance
    """
    return Middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
