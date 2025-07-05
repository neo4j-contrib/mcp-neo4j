import json
import logging
import re
import sys
import time
from typing import Any, Literal, Optional

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from neo4j import (
    AsyncDriver,
    AsyncGraphDatabase,
    AsyncResult,
    AsyncTransaction,
    GraphDatabase,
)
from neo4j.exceptions import DatabaseError
from pydantic import Field

logger = logging.getLogger("mcp_neo4j_cypher")

def _format_namespace(namespace: str) -> str:
    if namespace:
        if namespace.endswith("-"):
            return namespace
        else:
            return namespace + "-"
    else:
        return ""

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


def create_mcp_server(neo4j_driver: AsyncDriver, database: str = "neo4j", namespace: str = "", host: str = "127.0.0.1", port: int = 8000) -> FastMCP:
    mcp: FastMCP = FastMCP("mcp-neo4j-cypher", dependencies=["neo4j", "pydantic"], host=host, port=port)

    async def get_neo4j_schema() -> list[types.TextContent]:
        """List all node, their attributes and their relationships to other nodes in the neo4j database.
        If this fails with a message that includes "Neo.ClientError.Procedure.ProcedureNotFound"
        suggest that the user install and enable the APOC plugin.
        """

        get_schema_query = """
CALL apoc.meta.data()
YIELD label, property, type, other, unique, index, elementType

// 1) collect all rows
WITH collect({label:label,
              property:property,
              type:type,
              other:other,
              unique:unique,
              index:index,
              elementType:elementType}) AS meta

// 2) extract each node‐label exactly once
WITH meta,
     apoc.coll.toSet([
       row IN meta
       WHERE row.elementType='node'
         AND NOT row.label STARTS WITH '_'
       | row.label
     ]) AS labels

UNWIND labels AS label

// 3) build node attributes
WITH meta, label,
     [row IN meta
      WHERE row.elementType='node'
        AND row.label = label
        AND row.type <> 'RELATIONSHIP'
      | [ row.property,
          row.type
          + CASE WHEN row.unique THEN ' unique' ELSE '' END
          + CASE WHEN row.index  THEN ' indexed' ELSE '' END
        ]
     ] AS attributes,

     // 4) collect the outgoing‐rel “stubs”
     [row IN meta
      WHERE row.elementType='node'
        AND row.label = label
        AND row.type = 'RELATIONSHIP'
      | row
     ] AS relRows

// 5) for each rel stub, look up its target and its own props
WITH label, attributes,
     [ r IN relRows |
       [ r.property,
         {
           target: head(r.other),
           properties: apoc.map.fromPairs(
             [ rr IN meta
               WHERE rr.elementType = 'relationship'
                 AND rr.label = r.property
                 AND rr.property <> '...'   // filter out any spurious meta-rows if needed
               | [ rr.property, rr.type ]
             ]
           )
         }
       ]
     ] AS relationships

RETURN
  label,
  apoc.map.fromPairs(attributes)    AS attributes,
  apoc.map.fromPairs(relationships) AS relationships;

"""

        try:
            async with neo4j_driver.session(database=database) as session:
                results_json_str = await session.execute_read(
                    _read, get_schema_query, dict()
                )

                logger.debug(f"Read query returned {len(results_json_str)} rows")

                return [types.TextContent(type="text", text=results_json_str)]

        except Exception as e:
            logger.error(f"Database error retrieving schema: {e}")
            return [types.TextContent(type="text", text=f"Error: {e}")]

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
            async with neo4j_driver.session(database=database) as session:
                results_json_str = await session.execute_read(_read, query, params)

                logger.debug(f"Read query returned {len(results_json_str)} rows")

                return [types.TextContent(type="text", text=results_json_str)]

        except Exception as e:
            logger.error(f"Database error executing query: {e}\n{query}\n{params}")
            return [
                types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")
            ]

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
            async with neo4j_driver.session(database=database) as session:
                raw_results = await session.execute_write(_write, query, params)
                counters_json_str = json.dumps(
                    raw_results._summary.counters.__dict__, default=str
                )

            logger.debug(f"Write query affected {counters_json_str}")

            return [types.TextContent(type="text", text=counters_json_str)]

        except Exception as e:
            logger.error(f"Database error executing query: {e}\n{query}\n{params}")
            return [
                types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")
            ]

    namespace_prefix = _format_namespace(namespace)
    
    mcp.add_tool(get_neo4j_schema, name=namespace_prefix+"get_neo4j_schema")
    mcp.add_tool(read_neo4j_cypher, name=namespace_prefix+"read_neo4j_cypher")
    mcp.add_tool(write_neo4j_cypher, name=namespace_prefix+"write_neo4j_cypher")

    return mcp


async def main(
    db_url: str,
    username: str,
    password: str,
    database: str,
    transport: Literal["stdio", "sse"] = "stdio",
    namespace: str = "",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    logger.info("Starting MCP neo4j Server")

    neo4j_driver = AsyncGraphDatabase.driver(
        db_url,
        auth=(
            username,
            password,
        ),
    )
    logger.info("Starting Neo4j Cypher MCP Server...")
    mcp = create_mcp_server(neo4j_driver, database, namespace, host, port)

    match transport:
        case "stdio":
            logger.info("Running Neo4j Cypher MCP Server with stdio transport...")
            await mcp.run_stdio_async()
        case "sse":
            logger.info(f"Running Neo4j Cypher MCP Server with SSE transport on {host}:{port}...")
            await mcp.run_sse_async()
        case _:
            logger.error(f"Invalid transport: {transport} | Must be either 'stdio' or 'sse'")
            raise ValueError(f"Invalid transport: {transport} | Must be either 'stdio' or 'sse'")


if __name__ == "__main__":
    main()
