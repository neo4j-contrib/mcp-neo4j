from . import server
import asyncio
import argparse
import os
import logging
import sys 


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Neo4j Aura Database Instance Manager")
    parser.add_argument("--client-id", help="Neo4j Aura API Client ID", 
                        default=os.environ.get("NEO4J_AURA_CLIENT_ID"))
    parser.add_argument("--client-secret", help="Neo4j Aura API Client Secret", 
                        default=os.environ.get("NEO4J_AURA_CLIENT_SECRET"))
    parser.add_argument("--transport", default=None, help="Transport type")
    parser.add_argument("--server-host", default=None, help="Server host")
    parser.add_argument("--server-port", default=None, help="Server port")
    parser.add_argument("--server-path", default=None, help="Server path")
    parser.add_argument(
        "--allow-origins",
        default=None,
        help="Allow origins for remote servers (comma-separated list)",
    )
    parser.add_argument(
        "--allowed-hosts",
        default=None,
        help="Allowed hosts for DNS rebinding protection on remote servers(comma-separated list)",
    )
    
    args = parser.parse_args()
    
    if not args.client_id or not args.client_secret:
        logger.error("Client ID and Client Secret are required. Provide them as arguments or environment variables.")
        sys.exit(1)
    
    # Parse security arguments
    allow_origins_str = args.allow_origins or os.getenv("NEO4J_MCP_SERVER_ALLOW_ORIGINS", "")
    allow_origins = [origin.strip() for origin in allow_origins_str.split(",") if origin.strip()] if allow_origins_str else []

    allowed_hosts_str = args.allowed_hosts or os.getenv("NEO4J_MCP_SERVER_ALLOWED_HOSTS", "localhost,127.0.0.1")
    allowed_hosts = [host.strip() for host in allowed_hosts_str.split(",") if host.strip()] if allowed_hosts_str else []

    try:
        asyncio.run(server.main(
            args.client_id,
            args.client_secret,
            args.transport or os.getenv("NEO4J_TRANSPORT", "stdio"),
            args.server_host or os.getenv("NEO4J_MCP_SERVER_HOST", "127.0.0.1"),
            int(args.server_port or os.getenv("NEO4J_MCP_SERVER_PORT", 8000)),
            args.server_path or os.getenv("NEO4J_MCP_SERVER_PATH", "/mcp/"),
            allow_origins,
            allowed_hosts,
        ))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

# Optionally expose other important items at package level
__all__ = ["main", "server"]
