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

    args = parser.parse_args()

    # Parse comma-separated lists for middleware configuration
    allow_origins = []
    if args.allow_origins or os.getenv("NEO4J_MCP_SERVER_ALLOW_ORIGINS"):
        origins_str = args.allow_origins or os.getenv("NEO4J_MCP_SERVER_ALLOW_ORIGINS", "")
        allow_origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    allowed_hosts = ["localhost", "127.0.0.1"]  # Default secure hosts
    if args.allowed_hosts or os.getenv("NEO4J_MCP_SERVER_ALLOWED_HOSTS"):
        hosts_str = args.allowed_hosts or os.getenv("NEO4J_MCP_SERVER_ALLOWED_HOSTS", "")
        allowed_hosts = [host.strip() for host in hosts_str.split(",") if host.strip()]

    asyncio.run(
        server.main(
            args.transport or os.getenv("NEO4J_TRANSPORT", "stdio"),
            args.server_host or os.getenv("NEO4J_MCP_SERVER_HOST", "127.0.0.1"),
            args.server_port or int(os.getenv("NEO4J_MCP_SERVER_PORT", "8000")),
            args.server_path or os.getenv("NEO4J_MCP_SERVER_PATH", "/mcp/"),
            allow_origins,
            allowed_hosts,
        )
    )


__all__ = ["main", "server"]
