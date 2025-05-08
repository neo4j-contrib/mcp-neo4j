import logging
import os

from fastapi import FastAPI

from src.mcp_neo4j_memory.server import create_mcp_server
from src.mcp_neo4j_memory.transport import TransportLayer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_neo4j_memory")


async def start_server(transport_type="sse"):
    """Start the MCP server with the specified transport"""
    # Get environment variables for Neo4j connection
    neo4j_uri = os.environ.get(
        "NEO4J_URI", os.environ.get("NEO4J_URL", "bolt://host.docker.internal:7687")
    )
    neo4j_user = os.environ.get("NEO4J_USERNAME", os.environ.get("NEO4J_USER", "neo4j"))
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "neo4j_password")

    try:
        # Create the MCP server
        logger.info(f"Creating MCP server with transport type: {transport_type}")
        mcp_server = await create_mcp_server(neo4j_uri, neo4j_user, neo4j_password)

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
            return {"status": "ok"}

        # Add root endpoint
        @app.get("/")
        def read_root():
            return {
                "message": "Neo4j MCP Memory Server",
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
