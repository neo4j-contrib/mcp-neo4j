import argparse
import asyncio

from . import server
from .utils import process_config


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="Neo4j Cypher MCP Server")
    parser.add_argument("--db-url", default=None, help="Neo4j connection URL")
    parser.add_argument("--username", default=None, help="Neo4j username")
    parser.add_argument("--password", default=None, help="Neo4j password")
    parser.add_argument("--database", default=None, help="Neo4j database name")
    parser.add_argument(
        "--transport", default=None, help="Transport type (stdio, sse, http)"
    )
    parser.add_argument("--namespace", default=None, help="Tool namespace")
    parser.add_argument(
        "--server-path", default=None, help="HTTP path (default: /mcp/)"
    )
    parser.add_argument("--server-host", default=None, help="Server host")
    parser.add_argument("--server-port", default=None, help="Server port")
    parser.add_argument(
        "--allow-origins",
        default=None,
        help="Allow origins for remote servers (comma-separated list)",
    )
    parser.add_argument(
        "--allowed-hosts",
        default=None,
        help="Allowed hosts for DNS rebinding protection on remote servers(comma-separated list)",
    )
    parser.add_argument(
        "--read-timeout",
        type=int,
        default=None,
        help="Timeout in seconds for read queries (default: 30)",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Allow only read-only queries (default: False)",
    )
    parser.add_argument("--token-limit", default=None, help="Response token limit")
    parser.add_argument(
        "--schema-sample-size",
        type=int,
        default=None,
        help="Default sample size for schema operations (default: 1000)",
    )
    parser.add_argument(
        "--gcf",
        action="store_true",
        help="Encode read query results as GCF instead of JSON (requires: pip install 'mcp-neo4j-cypher[gcf]')",
    )
    parser.add_argument(
        "--gcf-compare",
        action="store_true",
        help="Enable GCF output and log JSON vs GCF token savings to stderr on every query",
    )

    args = parser.parse_args()
    config = process_config(args)
    asyncio.run(server.main(**config))


__all__ = ["main", "server"]
