from . import server
import asyncio
import argparse
import os
import logging
import sys 

from .utils import process_config

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
    parser.add_argument("--namespace", default=None, help="Tool namespace prefix")
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
    
    config = process_config(args)

    try:
        asyncio.run(server.main(**config))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

# Optionally expose other important items at package level
__all__ = ["main", "server"]
