"""
stdio protocol implementation for MCP Neo4j Memory server.
"""

import logging
from typing import Any, Dict, List

from neo4j import GraphDatabase

import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from ..core import Neo4jMemory, get_mcp_tools, execute_tool

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory.protocols.stdio')


async def run_stdio_server(neo4j_uri: str, neo4j_user: str, neo4j_password: str, neo4j_database: str):
    """
    Run the MCP server in stdio mode.
    
    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        neo4j_database: Neo4j database name
    """
    logger.info(f"Connecting to Neo4j MCP Server with DB URL: {neo4j_uri}")

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(
        neo4j_uri,
        auth=(neo4j_user, neo4j_password),
        database=neo4j_database
    )

    # Verify connection
    try:
        neo4j_driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {neo4j_uri}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        exit(1)

    # Initialize memory
    memory = Neo4jMemory(neo4j_driver)

    # Create MCP server
    server = Server("mcp-neo4j-memory")

    # Register handlers
    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        return get_mcp_tools()

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Dict[str, Any] | None
    ) -> List[types.TextContent | types.ImageContent]:
        return await execute_tool(memory, name, arguments)

    # Start the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP Knowledge Graph Memory using Neo4j running on stdio")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-neo4j-memory",
                server_version="1.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
