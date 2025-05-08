from mcp_neo4j_memory.transport import TransportLayer

import mcp.server.stdio
from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions


class StdIOTransport(TransportLayer):
    """Implementation of stdio transport for MCP server"""

    async def run_server(self, mcp_server):
        """Run the server with stdio transport"""
        self.logger.info("Starting MCP server with stdio transport")

        # Using the original implementation from server.py
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            self.logger.info("MCP Knowledge Graph Memory using Neo4j running on stdio")
            await mcp_server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-neo4j-memory",
                    server_version="1.1",
                    capabilities=mcp_server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
