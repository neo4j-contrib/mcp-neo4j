import logging
import mcp.types as types
from mcp.server.fastmcp import FastMCP
import mcp.server.stdio
from pydantic import Field
from typing import Any
from neo4j import AsyncGraphDatabase, AsyncTransaction, AsyncDriver
from neo4j.exceptions import DatabaseError
import time
import re
import os
from typing import Optional

logger = logging.getLogger("mcp_neo4j_cypher")
logger.info("Starting MCP neo4j Server")

neo4j_driver = AsyncGraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(
        os.getenv("NEO4J_USERNAME", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "password"),
    ),
)

mcp: FastMCP = FastMCP("mcp-neo4j-cypher", dependencies=["neo4j", "pydantic"])


def _is_write_query(query: str) -> bool:
    """Check if the query is a write query."""
    return (
        re.search(r"\b(MERGE|CREATE|SET|DELETE|REMOVE|ADD)\b", query, re.IGNORECASE)
        is not None
    )


@mcp.tool()
async def get_neo4j_schema() -> list[types.TextContent]:
    """List all node, their attributes and their relationships to other nodes in the neo4j database"""

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

        async def read(tx: AsyncTransaction, query: str, params: dict[str, Any]):
            raw_results = await tx.run(query, params)
            results = [r.data() async for r in raw_results]
            return results

        async with neo4j_driver.session(
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        ) as session:
            results = await session.execute_read(read, query, params)

            logger.debug(f"Read query returned {len(results)} rows")

            return [types.TextContent(type="text", text=str(results))]

    except Exception as e:
        logger.error(f"Database error executing query: {e}\n{query}\n{params}")
        return [types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")]


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

        async def write(tx: AsyncTransaction, query: str, params: dict[str, Any]):
            return await tx.run(query, params)

        async with neo4j_driver.session(
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        ) as session:
            raw_results = await session.execute_write(write, query, params)
            counters = raw_results._summary.counters

        logger.debug(f"Write query affected {counters}")

        return [types.TextContent(type="text", text=str([counters]))]

    except Exception as e:
        logger.error(f"Database error executing query: {e}\n{query}\n{params}")
        return [types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")]


def healthcheck(neo4j_driver: AsyncDriver) -> None:
    """Confirm that Neo4j is running before continuing."""

    attempts = 0
    success = False
    print("\nWaiting for Neo4j to Start...\n")
    time.sleep(3)
    ex = DatabaseError()
    while not success and attempts < 3:
        try:
            with neo4j_driver.session() as session:
                session.run("RETURN 1")
            success = True
        except Exception as e: 
            ex = e
            attempts += 1
            print( f"failed connection {attempts} | waiting {(1 + attempts) * 2} seconds..." )
            print( f"Error: {e}" )
            time.sleep((1 + attempts) * 2)
    if not success:
        raise ex


def main() -> None:
    # Test the connection
    healthcheck(neo4j_driver)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
