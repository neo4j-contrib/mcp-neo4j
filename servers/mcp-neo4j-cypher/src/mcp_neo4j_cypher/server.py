import json
import logging
import re
import sys
import time
from typing import Any

from neo4j import (
    AsyncDriver,
    AsyncGraphDatabase,
    AsyncResult,
    AsyncTransaction,
    GraphDatabase,
)
from neo4j.exceptions import DatabaseError

import mcp.types as types
from mcp.server import Server

logger = logging.getLogger("mcp_neo4j_cypher")


def healthcheck(db_url: str, username: str, password: str, database: str) -> None:
    """
    Confirm that Neo4j is running before continuing.
    Creates a sync Neo4j driver instance for checking connection and closes it after connection is established.
    """

    print("Confirming Neo4j is running...", file=sys.stderr)
    sync_driver = GraphDatabase.driver(
        db_url,
        auth=(
            username,
            password,
        ),
    )
    attempts = 0
    success = False
    print("\nWaiting for Neo4j to Start...\n", file=sys.stderr)
    time.sleep(3)
    ex = DatabaseError()
    while not success and attempts < 3:
        try:
            with sync_driver.session(database=database) as session:
                session.run("RETURN 1")
            success = True
            sync_driver.close()
        except Exception as e:
            ex = e
            attempts += 1
            print(
                f"failed connection {attempts} | waiting {(1 + attempts) * 2} seconds...",
                file=sys.stderr,
            )
            print(f"Error: {e}", file=sys.stderr)
            time.sleep((1 + attempts) * 2)
    if not success:
        sync_driver.close()
        raise ex


async def _read(tx: AsyncTransaction, query: str, params: dict[str, Any]) -> str:
    raw_results = await tx.run(query, params)
    eager_results = await raw_results.to_eager_result()

    return json.dumps([r.data() for r in eager_results.records], default=str)


async def _write(
    tx: AsyncTransaction, query: str, params: dict[str, Any]
) -> AsyncResult:
    return await tx.run(query, params)


def _is_write_query(query: str) -> bool:
    """Check if the query is a write query."""
    return (
        re.search(r"\b(MERGE|CREATE|SET|DELETE|REMOVE|ADD)\b", query, re.IGNORECASE)
        is not None
    )


async def create_neo4j_driver(db_url: str, username: str, password: str) -> AsyncDriver:
    """
    Create and return an AsyncDriver instance for Neo4j.
    """
    driver = AsyncGraphDatabase.driver(
        db_url,
        auth=(
            username,
            password,
        ),
    )
    return driver


def create_mcp_server(neo4j_driver: AsyncDriver, database: str = "neo4j") -> Server:
    """
    Create and return a Server instance for Neo4j Cypher queries.
    """
    server = Server("mcp-neo4j-cypher")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools for the Neo4j Cypher server."""
        return [
            types.Tool(
                name="get_neo4j_schema",
                description="List all node, their attributes and their relationships to other nodes in the neo4j database.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="read_neo4j_cypher",
                description="Execute a read Cypher query on the neo4j database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The Cypher query to execute.",
                        },
                        "params": {
                            "type": "object",
                            "description": "Optional parameters for the query.",
                            "additionalProperties": True,
                        },
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="write_neo4j_cypher",
                description="Execute a write Cypher query on the neo4j database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The Cypher query to execute.",
                        },
                        "params": {
                            "type": "object",
                            "description": "Optional parameters for the query.",
                            "additionalProperties": True,
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent]:
        """Handle tool calls for the Neo4j Cypher server."""
        try:
            if name == "get_neo4j_schema":
                get_schema_query = """
                call apoc.meta.data() yield label, property, type, other, unique, index, elementType
                where elementType = 'node' and not label starts with '_'
                with label,
                    collect(case when type <> 'RELATIONSHIP' then [property, type + case when unique then " unique" else "" end + case when index then " indexed" else "" end] end) as attributes,
                    collect(case when type = 'RELATIONSHIP' then [property, head(other)] end) as relationships
                RETURN label, apoc.map.fromPairs(attributes) as attributes, apoc.map.fromPairs(relationships) as relationships
                """

                try:
                    async with neo4j_driver.session(database=database) as session:
                        results_json_str = await session.execute_read(
                            _read, get_schema_query, {}
                        )

                    logger.debug(f"Read query returned {len(results_json_str)} rows")

                    return [types.TextContent(type="text", text=results_json_str)]

                except Exception as e:
                    logger.error(f"Database error retrieving schema: {e}")
                    return [types.TextContent(type="text", text=f"Error: {e}")]

            elif name == "read_neo4j_cypher":
                if not arguments:
                    raise ValueError("No arguments provided")

                query = arguments.get("query")
                params = arguments.get("params", {})

                if _is_write_query(query):
                    raise ValueError("Only MATCH queries are allowed for read-query")

                try:
                    async with neo4j_driver.session(database=database) as session:
                        results_json_str = await session.execute_read(
                            _read, query, params
                        )

                    logger.debug(f"Read query returned {len(results_json_str)} rows")

                    return [types.TextContent(type="text", text=results_json_str)]

                except Exception as e:
                    logger.error(
                        f"Database error executing query: {e}\n{query}\n{params}"
                    )
                    return [
                        types.TextContent(
                            type="text", text=f"Error: {e}\n{query}\n{params}"
                        )
                    ]

            elif name == "write_neo4j_cypher":
                if not arguments:
                    raise ValueError("No arguments provided")

                query = arguments.get("query")
                params = arguments.get("params", {})

                if not _is_write_query(query):
                    raise ValueError("Only write queries are allowed for write-query")

                try:
                    async with neo4j_driver.session(database=database) as session:
                        raw_results = await session.execute_write(_write, query, params)
                        counters_json_str = json.dumps(
                            raw_results._summary.counters.__dict__, default=str
                        )

                    logger.debug(f"Write query affected {counters_json_str}")

                    return [types.TextContent(type="text", text=counters_json_str)]

                except Exception as e:
                    logger.error(
                        f"Database error executing query: {e}\n{query}\n{params}"
                    )
                    return [
                        types.TextContent(
                            type="text", text=f"Error: {e}\n{query}\n{params}"
                        )
                    ]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    return server
