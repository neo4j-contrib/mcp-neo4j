import argparse
import asyncio
import os


async def start_stdio_server():
    """Start the server with stdio transport"""
    from src.app import start_server

    await start_server("stdio")


def main():
    """Command-line entry point for running the MCP server"""
    parser = argparse.ArgumentParser(description="MCP Neo4j Cypher Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",
        help="Transport type (sse or stdio)",
    )
    parser.add_argument("--db-url", dest="neo4j_uri", help="Neo4j database URL")
    parser.add_argument("--username", dest="neo4j_username", help="Neo4j username")
    parser.add_argument("--password", dest="neo4j_password", help="Neo4j password")
    parser.add_argument(
        "--database", dest="neo4j_database", help="Neo4j database name", default="neo4j"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP server (when using SSE transport)",
    )

    args = parser.parse_args()

    # Set environment variables from arguments
    if args.neo4j_uri:
        os.environ["NEO4J_URI"] = args.neo4j_uri
    if args.neo4j_username:
        os.environ["NEO4J_USERNAME"] = args.neo4j_username
    if args.neo4j_password:
        os.environ["NEO4J_PASSWORD"] = args.neo4j_password
    if args.neo4j_database:
        os.environ["NEO4J_DATABASE"] = args.neo4j_database

    os.environ["MCP_TRANSPORT"] = args.transport

    if args.transport == "stdio":
        # Run with stdio transport
        asyncio.run(start_stdio_server())
    else:
        # Run with SSE transport via FastAPI/Uvicorn
        import uvicorn

        uvicorn.run("src.app:app", host="0.0.0.0", port=args.port, reload=False)


if __name__ == "__main__":
    main()
