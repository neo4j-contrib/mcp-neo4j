"""
Command-line interface for MCP Neo4j Memory server.
"""

import argparse
import asyncio
import logging
import os

from neo4j import GraphDatabase

from .core import Neo4jMemory
from .protocols import run_stdio_server, run_sse_server

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory.cli')


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(description='Neo4j Cypher MCP Server')
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
    parser.add_argument("--mode",
                        choices=["stdio", "sse"],
                        default=os.getenv("MCP_MODE", "stdio"),
                        help="Server mode: stdio (default) or sse")
    parser.add_argument("--host",
                        default=os.getenv("MCP_SERVER_HOST", "0.0.0.0"),
                        help="Host to bind HTTP/SSE server")
    parser.add_argument("--port",
                        type=int,
                        default=int(os.getenv("MCP_SERVER_PORT", "3001")),
                        help="Port for HTTP/SSE server")

    return parser


def validate_config(args: argparse.Namespace) -> None:
    """Validate configuration arguments."""
    if not args.db_url:
        raise ValueError("Neo4j URL is required")
    if not args.username:
        raise ValueError("Neo4j username is required")
    if not args.password:
        raise ValueError("Neo4j password is required")
    if not args.database:
        raise ValueError("Neo4j database is required")


async def create_memory(args: argparse.Namespace) -> Neo4jMemory:
    """Create and initialize Neo4j memory instance."""
    logger.info(f"Connecting to Neo4j at {args.db_url}")

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(
        args.db_url,
        auth=(args.username, args.password),
        database=args.database
    )

    # Verify connection
    try:
        neo4j_driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {args.db_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise

    # Initialize memory
    memory = Neo4jMemory(neo4j_driver)
    return memory


async def run_server(args: argparse.Namespace) -> None:
    """Run the server based on configuration."""
    validate_config(args)

    if args.mode == "stdio":
        # Use stdio protocol
        await run_stdio_server(args.db_url, args.username, args.password, args.database)
    elif args.mode == "sse":
        # Use SSE protocol
        memory = await create_memory(args)
        await run_sse_server(memory, args.host, args.port)
    else:
        raise ValueError(f"Invalid mode: {args.mode}. Use 'stdio' or 'sse'")


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(run_server(args))
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        exit(1)
