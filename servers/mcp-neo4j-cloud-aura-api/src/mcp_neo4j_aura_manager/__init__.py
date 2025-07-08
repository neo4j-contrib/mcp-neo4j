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
    
    args = parser.parse_args()
    
    if not args.client_id or not args.client_secret:
        logger.error("Client ID and Client Secret are required. Provide them as arguments or environment variables.")
        sys.exit(1)
    
    try:
        asyncio.run(server.main(
            args.client_id, 
            args.client_secret,
        ))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

# Optionally expose other important items at package level
__all__ = ["main", "server"]
