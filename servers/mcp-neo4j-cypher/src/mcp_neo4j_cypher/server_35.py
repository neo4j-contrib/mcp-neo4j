"""
Neo4j 3.5 Compatible MCP Server

This is a synchronous version of the MCP server compatible with Neo4j 3.5.
Key changes from the 5.x version:
- Synchronous driver operations (no async/await)
- No RoutingControl (uses read_transaction/write_transaction)
- No Query timeout object
- No multi-database support
"""

import json
import logging
import re
from typing import Any, Literal, Optional

from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
from fastmcp.tools.tool import TextContent, ToolResult
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .neo4j_compat import Neo4j35Driver, QueryTimeoutError, create_driver
from .utils import _truncate_string_to_tokens, _value_sanitize

logger = logging.getLogger("mcp_neo4j_cypher")


def _format_namespace(namespace: str) -> str:
    """Format namespace by ensuring it ends with a hyphen if not empty."""
    if namespace:
        return namespace if namespace.endswith("-") else namespace + "-"
    return ""


def _is_write_query(query: str) -> bool:
    """Check if the query is a write query."""
    write_keywords = r"\b(MERGE|CREATE|INSERT|SET|DELETE|REMOVE|ADD)\b"
    return re.search(write_keywords, query, re.IGNORECASE) is not None


def _check_slow_query_patterns(query: str) -> list[str]:
    """Check for query patterns that may be slow on large databases."""
    warnings = []
    query_upper = query.upper()
    has_property_filter = "{" in query and ":" in query  # e.g., {email: "..."}
    
    # Full scan without WHERE or property filter
    if "MATCH" in query_upper and "WHERE" not in query_upper and "LIMIT" not in query_upper:
        if not has_property_filter:
            if not any(x in query_upper for x in ["COUNT(", "SUM(", "AVG("]):
                warnings.append("Query has no WHERE clause - may scan entire database")
    
    # ORDER BY without LIMIT
    if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
        warnings.append("ORDER BY without LIMIT requires sorting entire result set")
    
    # CONTAINS or regex on unindexed property
    if "CONTAINS" in query_upper or "=~" in query:
        warnings.append("String matching (CONTAINS/regex) is slow on large datasets")
    
    # Aggregation without filtering
    if any(x in query_upper for x in ["COUNT(", "SUM(", "AVG(", "COLLECT("]):
        if "WHERE" not in query_upper and "LIMIT" not in query_upper:
            if not has_property_filter:
                warnings.append("Aggregation without filters may be slow")
    
    return warnings


def create_mcp_server(
    neo4j_driver: Neo4j35Driver,
    namespace: str = "",
    token_limit: Optional[int] = None,
    read_only: bool = False,
    config_sample_size: int = 1000,
) -> FastMCP:
    """
    Create an MCP server instance for Neo4j 3.5.
    
    Note: Neo4j 3.5 does not support:
    - Multi-database (database parameter ignored)
    - Query timeouts via driver (read_timeout not used)
    """
    mcp: FastMCP = FastMCP("mcp-neo4j-cypher", stateless_http=True)

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
    def get_neo4j_schema(
        sample_size: int = Field(
            default=config_sample_size,
            description="Sample size for schema inference. Larger = slower but more accurate.",
        )
    ) -> list[ToolResult]:
        """
        Returns nodes, properties, and relationships using APOC schema inspection.
        
        Note: Requires APOC plugin installed on Neo4j 3.5.
        """
        effective_sample_size = sample_size if sample_size else config_sample_size
        logger.info(f"Running `get_neo4j_schema` with sample size {effective_sample_size}.")

        def clean_schema(schema: dict) -> dict:
            """Clean and simplify the schema response."""
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
                        rlabels = rel.get("labels", [])
                        if rlabels:
                            cr["labels"] = rlabels
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
            # Use cached schema for better performance
            schema_raw = neo4j_driver.get_schema_cached(effective_sample_size)
            
            if schema_raw:
                schema_clean = clean_schema(schema_raw)
                schema_clean_str = json.dumps(schema_clean, default=str)
                return ToolResult(content=[TextContent(type="text", text=schema_clean_str)])
            
            return ToolResult(content=[TextContent(type="text", text="{}")])

        except Exception as e:
            error_str = str(e)
            if "ProcedureNotFound" in error_str or "apoc" in error_str.lower():
                raise ToolError(
                    "Neo4j Error: APOC plugin not found. Please install APOC for Neo4j 3.5."
                )
            logger.error(f"Error retrieving Neo4j database schema: {e}")
            raise ToolError(f"Neo4j Error: {e}")

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
    def read_neo4j_cypher(
        query: str = Field(..., description="The Cypher query to execute."),
        params: dict[str, Any] = Field(
            default_factory=dict,
            description="Parameters to pass to the Cypher query.",
        ),
    ) -> list[ToolResult]:
        """Execute a read Cypher query on the Neo4j database."""
        if _is_write_query(query):
            raise ValueError("Only MATCH queries are allowed for read-query")

        # Check for slow query patterns
        warnings = _check_slow_query_patterns(query)
        for warning in warnings:
            logger.warning(f"Slow query pattern: {warning}")

        try:
            results = neo4j_driver.execute_read(query, params)
            sanitized_results = [_value_sanitize(el) for el in results]
            results_json_str = json.dumps(sanitized_results, default=str)

            if token_limit:
                results_json_str = _truncate_string_to_tokens(results_json_str, token_limit)

            logger.debug(f"Read query returned {len(results)} rows")
            return ToolResult(content=[TextContent(type="text", text=results_json_str)])

        except QueryTimeoutError as e:
            logger.warning(f"Query timed out: {query[:100]}...")
            raise ToolError(
                f"Query timed out (60s limit). {e}\n"
                "Tips: Use LIMIT, add WHERE clauses, or avoid GROUP BY on large datasets."
            )
        except Exception as e:
            logger.error(f"Error executing read query: {e}\n{query}\n{params}")
            raise ToolError(f"Neo4j Error: {e}\n{query}\n{params}")

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
    def write_neo4j_cypher(
        query: str = Field(..., description="The Cypher query to execute."),
        params: dict[str, Any] = Field(
            default_factory=dict,
            description="Parameters to pass to the Cypher query.",
        ),
    ) -> list[ToolResult]:
        """Execute a write Cypher query on the Neo4j database."""
        if not _is_write_query(query):
            raise ValueError("Only write queries are allowed for write-query")

        try:
            counters = neo4j_driver.get_summary_counters(query, params)
            counters_json_str = json.dumps(counters, default=str)
            logger.debug(f"Write query affected {counters_json_str}")
            return ToolResult(content=[TextContent(type="text", text=counters_json_str)])

        except QueryTimeoutError as e:
            logger.warning(f"Write query timed out: {query[:100]}...")
            raise ToolError(
                f"Query timed out (60s limit). {e}\n"
                "Tips: Break large writes into smaller batches."
            )
        except Exception as e:
            logger.error(f"Error executing write query: {e}\n{query}\n{params}")
            raise ToolError(f"Neo4j Error: {e}\n{query}\n{params}")

    return mcp


def main(
    db_url: str,
    username: str,
    password: str,
    database: str = "neo4j",  # Ignored in 3.5 - single database only
    transport: Literal["stdio", "sse", "http"] = "stdio",
    namespace: str = "",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
    allow_origins: list[str] = None,
    allowed_hosts: list[str] = None,
    read_timeout: int = 30,  # Not used in 3.5 - no driver-level timeout
    token_limit: Optional[int] = None,
    read_only: bool = False,
    schema_sample_size: Optional[int] = None,
) -> None:
    """
    Main entry point for the Neo4j 3.5 compatible MCP server.
    
    Note: database and read_timeout parameters are ignored in Neo4j 3.5.
    """
    logger.info("Starting MCP Neo4j Server (3.5 Compatible)")

    if database != "neo4j":
        logger.warning(
            f"Neo4j 3.5 does not support multi-database. "
            f"Ignoring database parameter: {database}"
        )

    allow_origins = allow_origins or []
    allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1"]

    # Create 3.5 compatible driver
    neo4j_driver = create_driver(db_url, username, password)

    # Verify connectivity
    try:
        neo4j_driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {db_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise

    custom_middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        ),
        Middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts),
    ]

    sample_size = schema_sample_size if schema_sample_size else 1000
    mcp = create_mcp_server(
        neo4j_driver, namespace, token_limit, read_only, sample_size
    )

    # Run the server with the specified transport
    # FastMCP uses run() method with transport parameter
    import asyncio
    
    async def run_server():
        if transport == "http":
            logger.info(f"Running Neo4j Cypher MCP Server with HTTP transport on {host}:{port}...")
            await mcp.run_http_async(host=host, port=port, path=path, middleware=custom_middleware)
        elif transport == "stdio":
            logger.info("Running Neo4j Cypher MCP Server with stdio transport...")
            await mcp.run_stdio_async()
        elif transport == "sse":
            logger.info(f"Running Neo4j Cypher MCP Server with SSE transport on {host}:{port}...")
            await mcp.run_http_async(host=host, port=port, path=path, middleware=custom_middleware, transport="sse")
        else:
            raise ValueError(f"Invalid transport: {transport} | Must be 'stdio', 'sse', or 'http'")
    
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
