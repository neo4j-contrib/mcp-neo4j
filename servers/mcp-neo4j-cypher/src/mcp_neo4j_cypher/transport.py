import logging
from abc import ABC, abstractmethod


class TransportLayer(ABC):
    """Abstract base class for MCP transport layers"""

    def __init__(self):
        self.logger = logging.getLogger("mcp_neo4j_cypher")

    @abstractmethod
    async def run_server(self, mcp_server):
        """Run the server with the given MCP server"""
        pass

    @classmethod
    def create_transport(cls, transport_type="sse"):
        """Factory method to create transport layer based on type"""
        if transport_type.lower() == "sse":
            from src.transports.sse_transport import SSETransport

            return SSETransport()
        elif transport_type.lower() == "stdio":
            from src.transports.stdio_transport import StdIOTransport

            return StdIOTransport()
        else:
            raise ValueError(f"Unsupported transport type: {transport_type}")
