import logging
import os
from datetime import datetime

import pytz
from fastapi import FastAPI

from src.server import create_mcp_server, create_neo4j_driver, healthcheck
from src.transport import TransportLayer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_neo4j_cypher")


async def start_server(transport_type="sse"):
    """Start the MCP server with the specified transport"""
    # Get environment variables for Neo4j connection
    neo4j_uri = os.environ.get(
        "NEO4J_URI", os.environ.get("NEO4J_URL", "bolt://host.docker.internal:7687")
    )
    neo4j_user = os.environ.get("NEO4J_USERNAME", os.environ.get("NEO4J_USER", "neo4j"))
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "neo4j_password")
    neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")

    try:
        # Health check Neo4j connection
        try:
            healthcheck(neo4j_uri, neo4j_user, neo4j_password, neo4j_database)
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise e

        # Create Neo4j driver
        neo4j_driver = await create_neo4j_driver(neo4j_uri, neo4j_user, neo4j_password)

        # Create the MCP server
        logger.info(f"Creating MCP server with transport type: {transport_type}")
        mcp_server = create_mcp_server(neo4j_driver, neo4j_database)

        # Create transport and run server
        transport = TransportLayer.create_transport(transport_type)
        return await transport.run_server(mcp_server)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise e


# For FastAPI app
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    global app
    transport_type = os.environ.get("MCP_TRANSPORT", "sse")
    if transport_type.lower() == "sse":
        # If using SSE, mount the SSE app to this app
        sse_app = await start_server("sse")

        # Add health check endpoint
        @app.get("/health")
        def health_check():
            neo4j_uri = os.environ.get(
                "NEO4J_URI",
                os.environ.get("NEO4J_URL", "bolt://host.docker.internal:7687"),
            )
            neo4j_user = os.environ.get(
                "NEO4J_USERNAME", os.environ.get("NEO4J_USER", "neo4j")
            )
            neo4j_password = os.environ.get("NEO4J_PASSWORD", "neo4j_password")
            neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")
            timestamp = datetime.now(pytz.UTC).isoformat()

            try:
                healthcheck(neo4j_uri, neo4j_user, neo4j_password, neo4j_database)
                return {"status": "ok", "timestamp": timestamp}
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                return {"status": "connection failed", "timestamp": timestamp}

        # Add root endpoint
        @app.get("/")
        def read_root():
            return {
                "message": "Neo4j MCP Cypher Server",
                "transport": "SSE",
                "sse_endpoint": "/sse",
            }

        # Mount all routes from the SSE app
        for route in sse_app.routes:
            app.routes.append(route)
    else:
        # For stdio, just inform that this app should not be used
        @app.get("/")
        def read_root():
            return {
                "error": "This server is configured to use stdio transport, not HTTP/SSE",
                "message": "Please run this server directly from the command line",
            }

        @app.get("/health")
        def health_check():
            return {
                "status": "error",
                "message": "Server is configured for stdio transport",
            }
