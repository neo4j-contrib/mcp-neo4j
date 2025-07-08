import argparse
import asyncio
import os

from . import server


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="Neo4j Data Modeling MCP Server")
    parser.add_argument(
        "--transport", default="stdio", help="Transport type (stdio, sse, http)"
    )
    parser.add_argument("--host", default=None, help="HTTP host (default: 127.0.0.1)")
    parser.add_argument(
        "--port", type=int, default=None, help="HTTP port (default: 8000)"
    )
    parser.add_argument("--path", default=None, help="HTTP path (default: /mcp/)")

    args = parser.parse_args()
    asyncio.run(
        server.main(
            args.transport or os.getenv("MCP_TRANSPORT", "stdio"),
            args.host or os.getenv("MCP_HTTP_HOST", "127.0.0.1"),
            args.port or int(os.getenv("MCP_HTTP_PORT", "8000")),
            args.path or os.getenv("MCP_HTTP_PATH", "/mcp/"),
        )
    )


__all__ = ["main", "server"]
