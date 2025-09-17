import argparse
import asyncio

from . import server
from .utils import process_config


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="Neo4j Data Modeling MCP Server")
    parser.add_argument(
        "--transport", default=None, help="Transport type (stdio, sse, http)"
    )
    parser.add_argument(
        "--server-host", default=None, help="HTTP host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--server-port", type=int, default=None, help="HTTP port (default: 8000)"
    )
    parser.add_argument(
        "--server-path", default=None, help="HTTP path (default: /mcp/)"
    )
    parser.add_argument(
        "--allow-origins",
        default=None,
        help="Allow origins for remote servers (comma-separated list)",
    )
    parser.add_argument(
        "--allowed-hosts",
        default=None,
        help="Allowed hosts for DNS rebinding protection on remote servers (comma-separated list)",
    )
    parser.add_argument("--namespace", default=None, help="Tool namespace prefix")

    args = parser.parse_args()

    config = process_config(args)
    asyncio.run(server.main(**config))


__all__ = ["main", "server"]
