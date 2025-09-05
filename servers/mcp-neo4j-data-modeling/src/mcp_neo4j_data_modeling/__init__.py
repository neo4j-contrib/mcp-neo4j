import argparse
import asyncio
import os

from . import server


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="Neo4j Data Modeling MCP Server")
    parser.add_argument(
        "--transport", default=None, help="Transport type (stdio, sse, http)"
    )
    parser.add_argument("--server-host", default=None, help="HTTP host (default: 127.0.0.1)")
    parser.add_argument(
        "--server-port", type=int, default=None, help="HTTP port (default: 8000)"
    )
    parser.add_argument("--server-path", default=None, help="HTTP path (default: /mcp/)")

    args = parser.parse_args()
    asyncio.run(
        server.main(
            args.transport or os.getenv("NEO4J_TRANSPORT", "stdio"),
            args.server_host or os.getenv("NEO4J_MCP_SERVER_HOST", "127.0.0.1"),
            args.server_port or int(os.getenv("NEO4J_MCP_SERVER_PORT", "8000")),
            args.server_path or os.getenv("NEO4J_MCP_SERVER_PATH", "/mcp/"),
        )
    )


__all__ = ["main", "server"]
