"""
Argument processing utilities for MCP Neo4j servers.
"""

import argparse
import logging
import os
from typing import Union

logger = logging.getLogger("mcp_neo4j_common")


def process_db_url(args: argparse.Namespace) -> str:
    """
    Process database URL from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    str
        The database URL.
    """
    if args.db_url is not None:
        return args.db_url
    
    if os.getenv("NEO4J_URL") is not None:
        return os.getenv("NEO4J_URL")
        
    if os.getenv("NEO4J_URI") is not None:
        return os.getenv("NEO4J_URI")
        
    logger.warning(
        "Warning: No Neo4j connection URL provided. Using default: bolt://localhost:7687"
    )
    return "bolt://localhost:7687"


def process_username(args: argparse.Namespace) -> str:
    """
    Process username from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    str
        The username.
    """
    if args.username is not None:
        return args.username
        
    if os.getenv("NEO4J_USERNAME") is not None:
        return os.getenv("NEO4J_USERNAME")
        
    logger.warning("Warning: No Neo4j username provided. Using default: neo4j")
    return "neo4j"


def process_password(args: argparse.Namespace) -> str:
    """
    Process password from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    str
        The password.
    """
    if args.password is not None:
        return args.password
        
    if os.getenv("NEO4J_PASSWORD") is not None:
        return os.getenv("NEO4J_PASSWORD")
        
    logger.warning(
        "Warning: No Neo4j password provided. Using default: password"
    )
    return "password"


def process_database(args: argparse.Namespace) -> str:
    """
    Process database name from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    str
        The database name.
    """
    if args.database is not None:
        return args.database
        
    if os.getenv("NEO4J_DATABASE") is not None:
        return os.getenv("NEO4J_DATABASE")
        
    logger.warning("Warning: No Neo4j database provided. Using default: neo4j")
    return "neo4j"


def process_namespace(args: argparse.Namespace) -> str:
    """
    Process namespace from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    str
        The namespace.
    """
    if args.namespace is not None:
        return args.namespace
        
    if os.getenv("NEO4J_NAMESPACE") is not None:
        return os.getenv("NEO4J_NAMESPACE")
        
    logger.info("Info: No namespace provided. No namespace will be used.")
    return ""


def process_transport(args: argparse.Namespace) -> str:
    """
    Process transport type from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    str
        The transport type.
    """
    if args.transport is not None:
        return args.transport
        
    if os.getenv("NEO4J_TRANSPORT") is not None:
        return os.getenv("NEO4J_TRANSPORT")
        
    logger.warning("Warning: No transport type provided. Using default: stdio")
    return "stdio"


def process_server_host(args: argparse.Namespace, transport: str) -> Union[str, None]:
    """
    Process server host from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
    transport : str
        The transport type.
        
    Returns
    -------
    Union[str, None]
        The server host or None if transport is stdio.
    """
    if args.server_host is not None:
        if transport == "stdio":
            logger.warning(
                "Warning: Server host provided, but transport is `stdio`. The `server_host` argument will be set, but ignored."
            )
        return args.server_host
        
    if os.getenv("NEO4J_MCP_SERVER_HOST") is not None:
        if transport == "stdio":
            logger.warning(
                "Warning: Server host provided, but transport is `stdio`. The `NEO4J_MCP_SERVER_HOST` environment variable will be set, but ignored."
            )
        return os.getenv("NEO4J_MCP_SERVER_HOST")
        
    if transport != "stdio":
        logger.warning(
            "Warning: No server host provided and transport is not `stdio`. Using default server host: 127.0.0.1"
        )
        return "127.0.0.1"
        
    logger.info(
        "Info: No server host provided and transport is `stdio`. `server_host` will be None."
    )
    return None


def process_server_port(args: argparse.Namespace, transport: str) -> Union[int, None]:
    """
    Process server port from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
    transport : str
        The transport type.
        
    Returns
    -------
    Union[int, None]
        The server port or None if transport is stdio.
    """
    if args.server_port is not None:
        if transport == "stdio":
            logger.warning(
                "Warning: Server port provided, but transport is `stdio`. The `server_port` argument will be set, but ignored."
            )
        return args.server_port
        
    if os.getenv("NEO4J_MCP_SERVER_PORT") is not None:
        if transport == "stdio":
            logger.warning(
                "Warning: Server port provided, but transport is `stdio`. The `NEO4J_MCP_SERVER_PORT` environment variable will be set, but ignored."
            )
        return int(os.getenv("NEO4J_MCP_SERVER_PORT"))
        
    if transport != "stdio":
        logger.warning(
            "Warning: No server port provided and transport is not `stdio`. Using default server port: 8000"
        )
        return 8000
        
    logger.info(
        "Info: No server port provided and transport is `stdio`. `server_port` will be None."
    )
    return None


def process_server_path(args: argparse.Namespace, transport: str) -> Union[str, None]:
    """
    Process server path from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
    transport : str
        The transport type.
        
    Returns
    -------
    Union[str, None]
        The server path or None if transport is stdio.
    """
    if args.server_path is not None:
        if transport == "stdio":
            logger.warning(
                "Warning: Server path provided, but transport is `stdio`. The `server_path` argument will be set, but ignored."
            )
        return args.server_path
        
    if os.getenv("NEO4J_MCP_SERVER_PATH") is not None:
        if transport == "stdio":
            logger.warning(
                "Warning: Server path provided, but transport is `stdio`. The `NEO4J_MCP_SERVER_PATH` environment variable will be set, but ignored."
            )
        return os.getenv("NEO4J_MCP_SERVER_PATH")
        
    if transport != "stdio":
        logger.warning(
            "Warning: No server path provided and transport is not `stdio`. Using default server path: /mcp/"
        )
        return "/mcp/"
        
    logger.info(
        "Info: No server path provided and transport is `stdio`. `server_path` will be None."
    )
    return None


def process_allow_origins(args: argparse.Namespace) -> list[str]:
    """
    Process allow origins from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    list[str]
        List of allowed origins.
    """
    if args.allow_origins is not None:
        return [origin.strip() for origin in args.allow_origins.split(",") if origin.strip()]
        
    if os.getenv("NEO4J_MCP_SERVER_ALLOW_ORIGINS") is not None:
        return [
            origin.strip() for origin in os.getenv("NEO4J_MCP_SERVER_ALLOW_ORIGINS", "").split(",") 
            if origin.strip()
        ]
        
    logger.info(
        "Info: No allow origins provided. Defaulting to no allowed origins."
    )
    return []


def process_allowed_hosts(args: argparse.Namespace) -> list[str]:
    """
    Process allowed hosts from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    list[str]
        List of allowed hosts.
    """
    if args.allowed_hosts is not None:
        return [host.strip() for host in args.allowed_hosts.split(",") if host.strip()]
        
    if os.getenv("NEO4J_MCP_SERVER_ALLOWED_HOSTS") is not None:
        return [
            host.strip() for host in os.getenv("NEO4J_MCP_SERVER_ALLOWED_HOSTS", "").split(",") 
            if host.strip()
        ]
        
    logger.info(
        "Info: No allowed hosts provided. Defaulting to secure mode - only localhost and 127.0.0.1 allowed."
    )
    return ["localhost", "127.0.0.1"]


def process_token_limit(args: argparse.Namespace) -> Union[int, None]:
    """
    Process token limit from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    Union[int, None]
        The token limit or None if not provided.
    """
    if args.token_limit is not None:
        return args.token_limit
        
    if os.getenv("NEO4J_RESPONSE_TOKEN_LIMIT") is not None:
        token_limit = int(os.getenv("NEO4J_RESPONSE_TOKEN_LIMIT"))
        logger.info(
            f"Info: Cypher read query token limit provided. Using provided value: {token_limit} tokens"
        )
        return token_limit
        
    logger.info("Info: No token limit provided. No token limit will be used.")
    return None


def process_read_timeout(args: argparse.Namespace) -> int:
    """
    Process read timeout from command line arguments or environment variables.
    
    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.
        
    Returns
    -------
    int
        The read timeout in seconds.
    """
    if args.read_timeout is not None:
        return args.read_timeout
        
    if os.getenv("NEO4J_READ_TIMEOUT") is not None:
        try:
            read_timeout = int(os.getenv("NEO4J_READ_TIMEOUT"))
            logger.info(
                f"Info: Cypher read query timeout provided. Using provided value: {read_timeout} seconds"
            )
            return read_timeout
        except ValueError:
            logger.warning("Warning: Invalid read timeout provided. Using default: 30 seconds")
            return 30
            
    logger.info("Info: No read timeout provided. Using default: 30 seconds")
    return 30