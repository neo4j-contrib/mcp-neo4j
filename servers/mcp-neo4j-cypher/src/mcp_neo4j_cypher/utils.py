import tiktoken

import argparse
import logging
from typing import Any, Union

from common.utils import (
    process_db_url,
    process_username,
    process_password,
    process_database,
    process_namespace,
    process_transport,
    process_server_host,
    process_server_port,
    process_server_path,
    process_allow_origins,
    process_allowed_hosts,
    process_token_limit,
    process_read_timeout,
)

logger = logging.getLogger("mcp_neo4j_cypher")
logger.setLevel(logging.INFO)


def process_config(args: argparse.Namespace) -> dict[str, Union[str, int, None]]:
    """
    Process the command line arguments and environment variables to create a config dictionary.
    This may then be used as input to the main server function.
    If any value is not provided, then a warning is logged and a default value is used, if appropriate.

    Parameters
    ----------
    args : argparse.Namespace
        The command line arguments.

    Returns
    -------
    config : dict[str, Union[str, int, None]]
        The configuration dictionary.
    """
    config = {}
    
    # Process database connection arguments
    config["db_url"] = process_db_url(args)
    config["username"] = process_username(args)
    config["password"] = process_password(args)
    config["database"] = process_database(args)

    # Process MCP configuration arguments
    config["namespace"] = process_namespace(args)
    config["transport"] = process_transport(args)
    
    # Process transport-dependent arguments
    config["host"] = process_server_host(args, config["transport"])
    config["port"] = process_server_port(args, config["transport"])
    config["path"] = process_server_path(args, config["transport"])
    
    # Process middleware arguments
    config["allow_origins"] = process_allow_origins(args)
    config["allowed_hosts"] = process_allowed_hosts(args)

    # Process Cypher query config arguments
    config["token_limit"] = process_token_limit(args)
    config["read_timeout"] = process_read_timeout(args)
    
    return config


def _value_sanitize(d: Any, list_limit: int = 128) -> Any:
    """
    Sanitize the input dictionary or list.

    Sanitizes the input by removing embedding-like values,
    lists with more than 128 elements, that are mostly irrelevant for
    generating answers in a LLM context. These properties, if left in
    results, can occupy significant context space and detract from
    the LLM's performance by introducing unnecessary noise and cost.

    Sourced from: https://github.com/neo4j/neo4j-graphrag-python/blob/main/src/neo4j_graphrag/schema.py#L88

    Parameters
    ----------
    d : Any
        The input dictionary or list to sanitize.
    list_limit : int
        The limit for the number of elements in a list.

    Returns
    -------
    Any
        The sanitized dictionary or list.
    """
    if isinstance(d, dict):
        new_dict = {}
        for key, value in d.items():
            if isinstance(value, dict):
                sanitized_value = _value_sanitize(value)
                if (
                    sanitized_value is not None
                ):  # Check if the sanitized value is not None
                    new_dict[key] = sanitized_value
            elif isinstance(value, list):
                if len(value) < list_limit:
                    sanitized_value = _value_sanitize(value)
                    if (
                        sanitized_value is not None
                    ):  # Check if the sanitized value is not None
                        new_dict[key] = sanitized_value
                # Do not include the key if the list is oversized
            else:
                new_dict[key] = value
        return new_dict
    elif isinstance(d, list):
        if len(d) < list_limit:
            return [
                _value_sanitize(item) for item in d if _value_sanitize(item) is not None
            ]
        else:
            return None
    else:
        return d

def _truncate_string_to_tokens(
    text: str, token_limit: int, model: str = "gpt-4"
) -> str:
    """
    Truncates the input string to fit within the specified token limit.

    Parameters
    ----------
    text : str
        The input text string.
    token_limit : int
        Maximum number of tokens allowed.
    model : str
        Model name (affects tokenization). Defaults to "gpt-4".

    Returns
    -------
    str
        The truncated string that fits within the token limit.
    """
    # Load encoding for the chosen model
    encoding = tiktoken.encoding_for_model(model)

    # Encode text into tokens
    tokens = encoding.encode(text)

    # Truncate tokens if they exceed the limit
    if len(tokens) > token_limit:
        tokens = tokens[:token_limit]

    # Decode back into text
    truncated_text = encoding.decode(tokens)
    return truncated_text
