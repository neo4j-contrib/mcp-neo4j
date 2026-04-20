#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastmcp>=2.10.5",
#     "neo4j>=5.26.0",
#     "pydantic>=2.10.1",
#     "starlette>=0.40.0",
#     "tiktoken>=0.11.0",
# ]
# ///
"""
MCP Neo4j 3.5 Runner

Entry point for running the Neo4j 3.5 compatible MCP server.
Configure via environment variables in your MCP client config.

Run with uv (installs the right Python and deps automatically):
    uv run mcp_neo4j_35_runner.py

Environment Variables:
    NEO4J_URL: Neo4j bolt URL (required)
    NEO4J_USERNAME: Neo4j username (required)
    NEO4J_PASSWORD: Neo4j password (required)
    READ_ONLY: "true" for read-only mode (default: "false")
    TRANSPORT: "stdio" (default), "http", or "sse"
    SCHEMA_SAMPLE_SIZE: Sample size for schema inference (default: 1000)
    HOST: Server host for http/sse transport (default: 127.0.0.1)
    PORT: Server port for http/sse transport (default: 8000)
"""

import os
import sys

CYPHER_SERVER_SRC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "servers/mcp-neo4j-cypher/src",
)
sys.path.insert(0, CYPHER_SERVER_SRC)

from mcp_neo4j_cypher.server_35 import main  # noqa: E402

REQUIRED_ENV_VARS = ("NEO4J_URL", "NEO4J_USERNAME", "NEO4J_PASSWORD")


def missing_env_vars():
    return [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]


def exit_if_env_vars_missing():
    missing = missing_env_vars()
    if not missing:
        return
    print(
        f"Error: Missing required environment variables: {', '.join(missing)}",
        file=sys.stderr,
    )
    sys.exit(1)


def config_from_env():
    exit_if_env_vars_missing()
    return {
        "db_url": os.environ["NEO4J_URL"],
        "username": os.environ["NEO4J_USERNAME"],
        "password": os.environ["NEO4J_PASSWORD"],
        "database": "neo4j",
        "transport": os.environ.get("TRANSPORT", "stdio"),
        "namespace": "",
        "host": os.environ.get("HOST", "127.0.0.1"),
        "port": int(os.environ.get("PORT", "8000")),
        "path": "/mcp/",
        "read_only": os.environ.get("READ_ONLY", "false").lower() == "true",
        "schema_sample_size": int(os.environ.get("SCHEMA_SAMPLE_SIZE", "1000")),
    }


def run():
    main(**config_from_env())


if __name__ == "__main__":
    run()
