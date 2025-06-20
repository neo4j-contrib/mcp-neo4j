from . import server
import asyncio
import argparse
import os


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='Neo4j Cypher MCP Server')
    parser.add_argument('--db-url',
                       default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
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
    
    args = parser.parse_args()
    asyncio.run(server.main(args.db_url, args.username, args.password, args.database))


# Optionally expose other important items at package level
__all__ = ["main", "server"]
