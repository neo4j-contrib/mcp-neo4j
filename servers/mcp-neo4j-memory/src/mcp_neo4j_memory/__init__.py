from . import server
import asyncio
import argparse
import os


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='Neo4j Memory MCP Server')
    parser.add_argument('--db-url', 
                       default=os.getenv("NEO4J_URL", "bolt://localhost:7687"),
                       help='Neo4j connection URL')
    parser.add_argument('--username', 
                       default=os.getenv("NEO4J_USERNAME", "neo4j"),
                       help='Neo4j username')
    parser.add_argument('--password', 
                       default=os.getenv("NEO4J_PASSWORD", "password"),
                       help='Neo4j password')
    parser.add_argument("--database",
                        default=os.getenv("NEO4J_DATABASE", "neo4j"),
                        help="Neo4j database name")
    parser.add_argument("--transport", default="stdio", help="Transport type (stdio, sse, http)")
    parser.add_argument("--host", default=None, help="HTTP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="HTTP port (default: 8000)")
    parser.add_argument("--path", default=None, help="HTTP path (default: /mcp/)")
    
    args = parser.parse_args()
    asyncio.run(server.main(
        args.db_url, 
        args.username, 
        args.password, 
        args.database,
        args.transport or os.getenv("NEO4J_TRANSPORT", "stdio"),
        args.host or os.getenv("NEO4J_HTTP_HOST", "127.0.0.1"),
        args.port or int(os.getenv("NEO4J_HTTP_PORT", "8000")),
        args.path or os.getenv("NEO4J_HTTP_PATH", "/mcp/"),
    ))


# Optionally expose other important items at package level
__all__ = ["main", "server"]
