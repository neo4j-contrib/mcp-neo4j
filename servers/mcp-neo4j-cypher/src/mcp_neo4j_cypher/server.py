import logging
import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Any
from neo4j import (
    AsyncGraphDatabase,
    AsyncResult,
    AsyncTransaction,
    GraphDatabase,
)
from neo4j.exceptions import DatabaseError
import time
import re
import os
from typing import Optional
import sys
import json


def healthcheck(db_url: str, username: str, password: str, database: str) -> None:
    """
    Confirm that Neo4j is running before continuing.
    Creates a a sync Neo4j driver instance for checking connection and closes it after connection is established.
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


def main(
    db_url: str,
    username: str,
    password: str,
    database: str,
) -> None:
    logger = logging.getLogger("mcp_neo4j_cypher")
    logger.info("Starting MCP neo4j Server")

    neo4j_driver = AsyncGraphDatabase.driver(
        db_url,
        auth=(
            username,
            password,
        ),
    )

    mcp: FastMCP = FastMCP("mcp-neo4j-cypher", dependencies=["neo4j", "pydantic"])

    @mcp.tool()
    async def get_neo4j_schema() -> list[types.TextContent]:
        """List all node, their attributes and their relationships to other nodes in the neo4j database"""

        get_schema_query = """
call apoc.meta.data() yield label, property, type, other, unique, index, elementType
where elementType = 'node' and not label starts with '_'
with label, 
    collect(case when type <> 'RELATIONSHIP' then [property, type + case when unique then " unique" else "" end + case when index then " indexed" else "" end] end) as attributes,
    collect(case when type = 'RELATIONSHIP' then [property, head(other)] end) as relationships
RETURN label, apoc.map.fromPairs(attributes) as attributes, apoc.map.fromPairs(relationships) as relationships
"""

        try:
            async with neo4j_driver.session(
                database=os.getenv("NEO4J_DATABASE", "neo4j")
            ) as session:
                results_json_str = await session.execute_read(
                    _read, get_schema_query, dict()
                )

                logger.debug(f"Read query returned {len(results_json_str)} rows")

                return [types.TextContent(type="text", text=results_json_str)]

        except Exception as e:
            logger.error(f"Database error retrieving schema: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    @mcp.tool()
    async def read_neo4j_cypher(
        query: str = Field(..., description="The Cypher query to execute."),
        params: Optional[dict[str, Any]] = Field(
            None, description="The parameters to pass to the Cypher query."
        ),
    ) -> list[types.TextContent]:
        """Execute a read Cypher query on the neo4j database."""

        if _is_write_query(query):
            raise ValueError("Only MATCH queries are allowed for read-query")

        try:
            async with neo4j_driver.session(
                database=os.getenv("NEO4J_DATABASE", "neo4j")
            ) as session:
                results_json_str = await session.execute_read(_read, query, params)

                logger.debug(f"Read query returned {len(results_json_str)} rows")

                return [types.TextContent(type="text", text=results_json_str)]

        except Exception as e:
            logger.error(f"Database error executing query: {e}\n{query}\n{params}")
            return [
                types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")
            ]

    @mcp.tool()
    async def write_neo4j_cypher(
        query: str = Field(..., description="The Cypher query to execute."),
        params: Optional[dict[str, Any]] = Field(
            None, description="The parameters to pass to the Cypher query."
        ),
    ) -> list[types.TextContent]:
        """Execute a write Cypher query on the neo4j database."""

        if not _is_write_query(query):
            raise ValueError("Only write queries are allowed for write-query")

        try:
            async with neo4j_driver.session(
                database=os.getenv("NEO4J_DATABASE", "neo4j")
            ) as session:
                raw_results = await session.execute_write(_write, query, params)
                counters_json_str = json.dumps(raw_results._summary.counters.__dict__, default=str)

            logger.debug(f"Write query affected {counters_json_str}")

            return [types.TextContent(type="text", text=counters_json_str)]

        except Exception as e:
            logger.error(f"Database error executing query: {e}\n{query}\n{params}")
            return [
                types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")
            ]

    healthcheck(db_url, username, password, database)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
