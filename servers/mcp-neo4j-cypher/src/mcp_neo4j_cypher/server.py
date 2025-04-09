import asyncio
import neo4j
import logging
from logging.handlers import RotatingFileHandler
from contextlib import closing
from pathlib import Path
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.fastmcp import FastMCP, Context
import mcp.server.stdio
from pydantic import Field
from typing import Any
from neo4j import AsyncGraphDatabase
import re
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("mcp_neo4j_cypher")
logger.info("Starting MCP neo4j Server")


# @dataclass
# class AppContext:
#     neo4j_driver: neo4j.AsyncDriver


# @asynccontextmanager
# async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
#     """Manage application lifecycle with type-safe context"""
#     # Initialize on startup
#     neo4j_driver = await AsyncGraphDatabase.driver(
#         os.getenv("NEO4J_URI", "bolt://localhost:7687"),
#         auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
#     )
#     try:
#         yield AppContext(neo4j_driver=neo4j_driver)
#     finally:
#         # Cleanup on shutdown
#         await neo4j_driver.close()
neo4j_driver =  AsyncGraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
)

mcp = FastMCP("neo4j-mcp")


def _is_write_query(query: str) -> bool:
    """Check if the query is a write query."""
    return (
        re.search(r"\b(MERGE|CREATE|SET|DELETE|REMOVE|ADD)\b", query, re.IGNORECASE)
        is not None
    )


@mcp.tool()
async def get_neo4j_schema() -> list[types.TextContent]:
    """List all node types, their attributes and their relationships TO other node-types in the neo4j database"""

    # neo4j_driver = ctx.app_context.neo4j_driver

    try:
        results = await neo4j_driver.execute_query(
            """
    call apoc.meta.data() yield label, property, type, other, unique, index, elementType
    where elementType = 'node' and not label starts with '_'
    with label, 
        collect(case when type <> 'RELATIONSHIP' then [property, type + case when unique then " unique" else "" end + case when index then " indexed" else "" end] end) as attributes,
        collect(case when type = 'RELATIONSHIP' then [property, head(other)] end) as relationships
    RETURN label, apoc.map.fromPairs(attributes) as attributes, apoc.map.fromPairs(relationships) as relationships
                        """
        )

        return [types.TextContent(type="text", text=str(results))]

    except Exception as e:
        logger.error(f"Database error retrieving schema: {e}")
        # raise
        return [types.TextContent(type="text", text=f"Error: {e}")]


@mcp.tool()
async def read_neo4j_cypher(
   
    query: str = Field(..., description="The Cypher query to execute."),
    params: Optional[dict[str, Any]] = Field(
        None, description="The parameters to pass to the Cypher query."
    ),
) -> list[types.TextContent]:
    """Execute a read Cypher query on the neo4j database."""
    # neo4j_driver = ctx.app_context.neo4j_driver

    if _is_write_query(query):
        raise ValueError("Only MATCH queries are allowed for read-query")

    try:
        raw_results = await neo4j_driver.execute_query(query, params)

        results = [dict(r) for r in raw_results.records]

        logger.debug(f"Read query returned {len(results)} rows")

        return [types.TextContent(type="text", text=str(results))]

    except Exception as e:
        logger.error(f"Database error executing query: {e}\n{query}\n{params}")
        # raise
        return [types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")]


@mcp.tool()
async def write_neo4j_cypher(
   
    query: str = Field(..., description="The Cypher query to execute."),
    params: Optional[dict[str, Any]] = Field(
        None, description="The parameters to pass to the Cypher query."
    ),
) -> list[types.TextContent]:
    """Execute a write Cypher query on the neo4j database."""
    # neo4j_driver = ctx.app_context.neo4j_driver

    if not _is_write_query(query):
        raise ValueError("Only write queries are allowed for write-query")

    try:
        raw_results = await neo4j_driver.execute_query(query, params)
        counters = vars(raw_results.summary.counters)

        logger.debug(f"Write query affected {counters}")

        return [types.TextContent(type="text", text=str([counters]))]

    except Exception as e:
        logger.error(f"Database error executing query: {e}\n{query}\n{params}")
        # raise
        return [types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")]


async def main():
    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())
# -------


# class neo4jDatabase:
#     def __init__(self, neo4j_uri: str, neo4j_username: str, neo4j_password: str):
#         """Initialize connection to the neo4j database"""
#         logger.debug(f"Initializing database connection to {neo4j_uri}")
#         d = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
#         d.verify_connectivity()
#         self.driver = d

#     def _execute_query(
#         self, query: str, params: dict[str, Any] | None = None
#     ) -> list[dict[str, Any]]:
#         """Execute a Cypher query and return results as a list of dictionaries"""
#         logger.debug(f"Executing query: {query}")
#         try:
#             result = self.driver.execute_query(query, params)
#             counters = vars(result.summary.counters)
#             if _is_write_query(query):
#                 logger.debug(f"Write query affected {counters}")
#                 return [counters]
#             else:
#                 results = [dict(r) for r in result.records]
#                 logger.debug(f"Read query returned {len(results)} rows")
#                 return results
#         except Exception as e:
#             logger.error(f"Database error executing query: {e}\n{query}")
#             raise

#     def close(self) -> None:
#         "Close the Neo4j Driver"
#         self.driver.close()


# async def main(neo4j_url: str, neo4j_username: str, neo4j_password: str):
#     logger.info(f"Connecting to neo4j MCP Server with DB URL: {neo4j_url}")

#     db = neo4jDatabase(neo4j_url, neo4j_username, neo4j_password)
#     server = Server("neo4j-manager")

#     # Register handlers
#     logger.debug("Registering handlers")

#     @server.list_tools()
#     async def handle_list_tools() -> list[types.Tool]:
#         """List available tools"""
#         return [
#             types.Tool(
#                 name="read-neo4j-cypher",
#                 description="Execute a Cypher query on the neo4j database",
#                 annotations={
#                     "destructiveHint": False,
#                     "idempotentHint": True,
#                     "readOnlyHint": True,
#                     "title": "Read from Neo4j Database",
#                 },
#                 inputSchema={
#                     "type": "object",
#                     "properties": {
#                         "query": {
#                             "type": "string",
#                             "description": "Cypher read query to execute",
#                         },
#                     },
#                     "required": ["query"],
#                 },
#             ),
#             types.Tool(
#                 name="write-neo4j-cypher",
#                 description="Execute a write Cypher query on the neo4j database",
#                 annotations={
#                     "destructiveHint": True,
#                     "idempotentHint": False,
#                     "readOnlyHint": False,
#                     "title": "Update Neo4j Database",
#                 },
#                 inputSchema={
#                     "type": "object",
#                     "properties": {
#                         "query": {
#                             "type": "string",
#                             "description": "Cypher write query to execute",
#                         },
#                     },
#                     "required": ["query"],
#                 },
#             ),
#             types.Tool(
#                 name="get-neo4j-schema",
#                 description="List all node types, their attributes and their relationships TO other node-types in the neo4j database",
#                 annotations={
#                     "destructiveHint": False,
#                     "idempotentHint": True,
#                     "readOnlyHint": True,
#                     "title": "Get Neo4j Database Schema",
#                 },
#                 inputSchema={
#                     "type": "object",
#                     "properties": {},
#                 },
#             ),
#         ]

#     @server.call_tool()
#     async def handle_call_tool(
#         name: str, arguments: dict[str, Any] | None
#     ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
#         """Handle tool execution requests"""
#         try:
#             if name == "get-neo4j-schema":
#                 results = db._execute_query(
#                     """
# call apoc.meta.data() yield label, property, type, other, unique, index, elementType
# where elementType = 'node' and not label starts with '_'
# with label,
#     collect(case when type <> 'RELATIONSHIP' then [property, type + case when unique then " unique" else "" end + case when index then " indexed" else "" end] end) as attributes,
#     collect(case when type = 'RELATIONSHIP' then [property, head(other)] end) as relationships
# RETURN label, apoc.map.fromPairs(attributes) as attributes, apoc.map.fromPairs(relationships) as relationships
#                     """
#                 )
#                 return [types.TextContent(type="text", text=str(results))]

#             elif name == "read-neo4j-cypher":
#                 if _is_write_query(arguments["query"]):
#                     raise ValueError("Only MATCH queries are allowed for read-query")
#                 results = db._execute_query(arguments["query"])
#                 return [types.TextContent(type="text", text=str(results))]

#             elif name == "write-neo4j-cypher":
#                 if not _is_write_query(arguments["query"]):
#                     raise ValueError("Only write queries are allowed for write-query")
#                 results = db._execute_query(arguments["query"])
#                 return [types.TextContent(type="text", text=str(results))]

#             else:
#                 raise ValueError(f"Unknown tool: {name}")

#         except Exception as e:
#             return [types.TextContent(type="text", text=f"Error: {str(e)}")]

#     async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
#         logger.info("Server running with stdio transport")
#         await server.run(
#             read_stream,
#             write_stream,
#             InitializationOptions(
#                 server_name="neo4j",
#                 server_version="0.1.0",
#                 capabilities=server.get_capabilities(
#                     notification_options=NotificationOptions(),
#                     experimental_capabilities={},
#                 ),
#             ),
#         )
