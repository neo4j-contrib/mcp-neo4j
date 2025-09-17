import json
import logging
import re
from typing import Any, Literal, Optional

from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
from fastmcp.tools.tool import TextContent, ToolResult
from mcp.types import ToolAnnotations
from neo4j import AsyncDriver, AsyncGraphDatabase, Query, RoutingControl
from neo4j.exceptions import ClientError, Neo4jError
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .utils import _truncate_string_to_tokens, _value_sanitize

logger = logging.getLogger("mcp_neo4j_cypher")


def _format_namespace(namespace: str) -> str:
    if namespace:
        if namespace.endswith("-"):
            return namespace
        else:
            return namespace + "-"
    else:
        return ""


def _is_write_query(query: str) -> bool:
    """Check if the query is a write query."""
    return (
        re.search(r"\b(MERGE|CREATE|SET|DELETE|REMOVE|ADD)\b", query, re.IGNORECASE)
        is not None
    )


def create_mcp_server(
    neo4j_driver: AsyncDriver,
    database: str = "neo4j",
    namespace: str = "",
    read_timeout: int = 30,
    token_limit: Optional[int] = None,
    read_only: bool = False,
) -> FastMCP:
    mcp: FastMCP = FastMCP(
        "mcp-neo4j-cypher", dependencies=["neo4j", "pydantic"], stateless_http=True
    )

    namespace_prefix = _format_namespace(namespace)
    allow_writes = not read_only

    @mcp.tool(
        name=namespace_prefix + "get_neo4j_schema",
        annotations=ToolAnnotations(
            title="Get Neo4j Schema",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    async def get_neo4j_schema() -> list[ToolResult]:
        """
        List all nodes, their attributes and their relationships to other nodes in the neo4j database.
        This requires that the APOC plugin is installed and enabled.
        """

        get_schema_query = """
        CALL apoc.meta.schema();
        """

        def clean_schema(schema: dict) -> dict:
            cleaned = {}

            for key, entry in schema.items():
                new_entry = {"type": entry["type"]}
                if "count" in entry:
                    new_entry["count"] = entry["count"]

                labels = entry.get("labels", [])
                if labels:
                    new_entry["labels"] = labels

                props = entry.get("properties", {})
                clean_props = {}
                for pname, pinfo in props.items():
                    cp = {}
                    if "indexed" in pinfo:
                        cp["indexed"] = pinfo["indexed"]
                    if "type" in pinfo:
                        cp["type"] = pinfo["type"]
                    if cp:
                        clean_props[pname] = cp
                if clean_props:
                    new_entry["properties"] = clean_props

                if entry.get("relationships"):
                    rels_out = {}
                    for rel_name, rel in entry["relationships"].items():
                        cr = {}
                        if "direction" in rel:
                            cr["direction"] = rel["direction"]
                        # nested labels
                        rlabels = rel.get("labels", [])
                        if rlabels:
                            cr["labels"] = rlabels
                        # nested properties
                        rprops = rel.get("properties", {})
                        clean_rprops = {}
                        for rpname, rpinfo in rprops.items():
                            crp = {}
                            if "indexed" in rpinfo:
                                crp["indexed"] = rpinfo["indexed"]
                            if "type" in rpinfo:
                                crp["type"] = rpinfo["type"]
                            if crp:
                                clean_rprops[rpname] = crp
                        if clean_rprops:
                            cr["properties"] = clean_rprops

                        if cr:
                            rels_out[rel_name] = cr

                    if rels_out:
                        new_entry["relationships"] = rels_out

                cleaned[key] = new_entry

            return cleaned

        try:
            results_json_str = await neo4j_driver.execute_query(
                get_schema_query,
                routing_control=RoutingControl.READ,
                database_=database,
                result_transformer_=lambda r: r.data(),
            )

            logger.debug(f"Read query returned {len(results_json_str)} rows")

            schema_clean = clean_schema(results_json_str[0].get("value"))

            schema_clean_str = json.dumps(schema_clean, default=str)

            return ToolResult(content=[TextContent(type="text", text=schema_clean_str)])

        except ClientError as e:
            if "Neo.ClientError.Procedure.ProcedureNotFound" in str(e):
                raise ToolError(
                    "Neo4j Client Error: This instance of Neo4j does not have the APOC plugin installed. Please install and enable the APOC plugin to use the `get_neo4j_schema` tool."
                )
            else:
                raise ToolError(f"Neo4j Client Error: {e}")

        except Neo4jError as e:
            raise ToolError(f"Neo4j Error: {e}")

        except Exception as e:
            logger.error(f"Error retrieving Neo4j database schema: {e}")
            raise ToolError(f"Unexpected Error: {e}")

    @mcp.tool(
        name=namespace_prefix + "read_neo4j_cypher",
        annotations=ToolAnnotations(
            title="Read Neo4j Cypher",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    async def read_neo4j_cypher(
        query: str = Field(..., description="The Cypher query to execute."),
        params: dict[str, Any] = Field(
            dict(), description="The parameters to pass to the Cypher query."
        ),
    ) -> list[ToolResult]:
        """Execute a read Cypher query on the neo4j database."""

        if _is_write_query(query):
            raise ValueError("Only MATCH queries are allowed for read-query")

        try:
            query_obj = Query(query, timeout=float(read_timeout))
            results = await neo4j_driver.execute_query(
                query_obj,
                parameters_=params,
                routing_control=RoutingControl.READ,
                database_=database,
                result_transformer_=lambda r: r.data(),
            )
            sanitized_results = [_value_sanitize(el) for el in results]
            results_json_str = json.dumps(sanitized_results, default=str)
            if token_limit:
                results_json_str = _truncate_string_to_tokens(
                    results_json_str, token_limit
                )

            logger.debug(f"Read query returned {len(results_json_str)} rows")

            return ToolResult(content=[TextContent(type="text", text=results_json_str)])

        except Neo4jError as e:
            logger.error(f"Neo4j Error executing read query: {e}\n{query}\n{params}")
            raise ToolError(f"Neo4j Error: {e}\n{query}\n{params}")

        except Exception as e:
            logger.error(f"Error executing read query: {e}\n{query}\n{params}")
            raise ToolError(f"Error: {e}\n{query}\n{params}")

    @mcp.tool(
        name=namespace_prefix + "write_neo4j_cypher",
        annotations=ToolAnnotations(
            title="Write Neo4j Cypher",
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        ),
        enabled=allow_writes,
    )
    async def write_neo4j_cypher(
        query: str = Field(..., description="The Cypher query to execute."),
        params: dict[str, Any] = Field(
            dict(), description="The parameters to pass to the Cypher query."
        ),
    ) -> list[ToolResult]:
        """Execute a write Cypher query on the neo4j database."""

        if not _is_write_query(query):
            raise ValueError("Only write queries are allowed for write-query")

        try:
            _, summary, _ = await neo4j_driver.execute_query(
                query,
                parameters_=params,
                routing_control=RoutingControl.WRITE,
                database_=database,
            )

            counters_json_str = json.dumps(summary.counters.__dict__, default=str)

            logger.debug(f"Write query affected {counters_json_str}")

            return ToolResult(
                content=[TextContent(type="text", text=counters_json_str)]
            )

        except Neo4jError as e:
            logger.error(f"Neo4j Error executing write query: {e}\n{query}\n{params}")
            raise ToolError(f"Neo4j Error: {e}\n{query}\n{params}")

        except Exception as e:
            logger.error(f"Error executing write query: {e}\n{query}\n{params}")
            raise ToolError(f"Error: {e}\n{query}\n{params}")

    return mcp


async def main(
    db_url: str,
    username: str,
    password: str,
    database: str,
    transport: Literal["stdio", "sse", "http"] = "stdio",
    namespace: str = "",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
    allow_origins: list[str] = [],
    allowed_hosts: list[str] = [],
    read_timeout: int = 30,
    token_limit: Optional[int] = None,
    read_only: bool = False,
) -> None:
    logger.info("Starting MCP neo4j Server")

    neo4j_driver = AsyncGraphDatabase.driver(
        db_url,
        auth=(
            username,
            password,
        ),
    )
    custom_middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        ),
        Middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts),
    ]

    mcp = create_mcp_server(
        neo4j_driver, database, namespace, read_timeout, token_limit, read_only
    )

    # Run the server with the specified transport
    match transport:
        case "http":
            logger.info(
                f"Running Neo4j Cypher MCP Server with HTTP transport on {host}:{port}..."
            )
            await mcp.run_http_async(
                host=host, port=port, path=path, middleware=custom_middleware
            )
        case "stdio":
            logger.info("Running Neo4j Cypher MCP Server with stdio transport...")
            await mcp.run_stdio_async()
        case "sse":
            logger.info(
                f"Running Neo4j Cypher MCP Server with SSE transport on {host}:{port}..."
            )
            await mcp.run_http_async(
                host=host,
                port=port,
                path=path,
                middleware=custom_middleware,
                transport="sse",
            )
        case _:
            logger.error(
                f"Invalid transport: {transport} | Must be either 'stdio', 'sse', or 'http'"
            )
            raise ValueError(
                f"Invalid transport: {transport} | Must be either 'stdio', 'sse', or 'http'"
            )


if __name__ == "__main__":
    main()
