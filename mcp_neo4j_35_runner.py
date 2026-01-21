#!/usr/bin/env python3
"""
MCP Neo4j 3.5 Runner

Entry point for running the Neo4j 3.5 compatible MCP server.
Configure via environment variables in your MCP client config.

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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "servers/mcp-neo4j-cypher/src"))

from mcp_neo4j_cypher.server_35 import main


def validate_required_env_vars():
    """Validate required environment variables are set."""
    required = ["NEO4J_URL", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def get_config_from_env():
    """Build configuration from environment variables."""
    validate_required_env_vars()
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


if __name__ == "__main__":
    main(**get_config_from_env())
