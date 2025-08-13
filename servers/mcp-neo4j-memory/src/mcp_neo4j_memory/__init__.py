import asyncio
import argparse
import os


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='Neo4j Memory MCP Server')
    parser.add_argument('--db-url', default=None, help='Neo4j connection URL')
    parser.add_argument('--username', default=None, help='Neo4j username')
    parser.add_argument('--password', default=None, help='Neo4j password')
    parser.add_argument("--database", default=None, help="Neo4j database name")
    parser.add_argument("--transport", default=None, help="Transport type (stdio, sse, http)")
    parser.add_argument("--server-host", default=None, help="HTTP host (default: 127.0.0.1)")
    parser.add_argument("--server-port", type=int, default=None, help="HTTP port (default: 8000)")
    parser.add_argument("--server-path", default=None, help="HTTP path (default: /mcp/)")
    
    args = parser.parse_args()
    
    # Import server only when needed
    from . import server
    
    asyncio.run(server.main(
        args.db_url or os.getenv("NEO4J_URL") or os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        args.username or os.getenv("NEO4J_USERNAME", "neo4j"),
        args.password or os.getenv("NEO4J_PASSWORD", "password"),
        args.database or os.getenv("NEO4J_DATABASE", "neo4j"),
        args.transport or os.getenv("NEO4J_TRANSPORT", "stdio"),
        args.server_host or os.getenv("NEO4J_MCP_SERVER_HOST", "127.0.0.1"),
        args.server_port or int(os.getenv("NEO4J_MCP_SERVER_PORT", "8000")),
        args.server_path or os.getenv("NEO4J_MCP_SERVER_PATH", "/mcp/"),
    ))


# Optionally expose other important items at package level
__all__ = ["main"]
