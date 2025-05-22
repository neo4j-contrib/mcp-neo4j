import mcp.server.stdio
from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
from src.transport import TransportLayer


class StdIOTransport(TransportLayer):
    """Implementation of stdio transport for MCP server"""

    async def run_server(self, mcp_server):
        """Run the server with stdio transport"""
        self.logger.info("Starting MCP server with stdio transport")

        # Using stdio transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            self.logger.info("MCP Neo4j Cypher server running on stdio")
            await mcp_server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-neo4j-cypher",
                    server_version="1.0",
                    capabilities=mcp_server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
