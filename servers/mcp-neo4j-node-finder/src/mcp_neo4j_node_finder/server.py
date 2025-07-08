import json
import logging
import re
import sys
import time
from typing import Any, Literal, Optional, List

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from neo4j import (
    AsyncDriver,
    AsyncGraphDatabase,
    AsyncResult,
    AsyncTransaction,
    GraphDatabase,
)
from neo4j.exceptions import DatabaseError
from pydantic import Field
from .schema import get_schema_definition

logger = logging.getLogger("mcp_neo4j_node_finder")

def _value_sanitize(d: Any) -> Any:
    """Sanitize the input dictionary or list.

    Sanitizes the input by removing embedding-like values,
    lists with more than 128 elements, that are mostly irrelevant for
    generating answers in a LLM context. These properties, if left in
    results, can occupy significant context space and detract from
    the LLM's performance by introducing unnecessary noise and cost.

    Args:
        d (Any): The input dictionary or list to sanitize.

    Returns:
        Any: The sanitized dictionary or list.
    """
    LIST_LIMIT = 128
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
                if len(value) < LIST_LIMIT:
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
        if len(d) < LIST_LIMIT:
            return [
                _value_sanitize(item) for item in d if _value_sanitize(item) is not None
            ]
        else:
            return None
    else:
        return d

def _format_namespace(namespace: str) -> str:
    if namespace:
        if namespace.endswith("-"):
            return namespace
        else:
            return namespace + "-"
    else:
        return ""
    
def _extract_node_properties(string_props, node_label):
    """
    Safely extract property names from nodes of a specific type.
    
    Args:
        string_props: List of dictionaries containing node information
        node_label: The type of node to search for (e.g., 'Person', 'Movie')
    
    Returns:
        List of property names for the first node of the specified type found, 
        or empty list if no matching nodes exist
    """
    matching_nodes = [el["properties"] for el in string_props if el["nodeLabel"] == node_label]
    
    if not matching_nodes:
        return []
    
    return [f"n.`{prop["property"]}`" for prop in matching_nodes[0]]

def _format_graph_for_llm(data):
    """Format graph data with nodes and relationships for LLM interpretation."""
    output = []

    for item in data:
        # Add total nodes count if present
        if 'total_nodes' in item:
            output.append(f"Total Nodes: {item['total_nodes']}")
            output.append("")

        # Process nodes
        for node_item in item.get('nodes', []):
            # Format main node
            node_props = ', '.join(f"{k}={repr(v)}" for k, v in node_item['node'].items())
            output.append(f"Node: {node_props}")

            # Format relationships
            for neighbor in node_item.get('neighbors', []):
                rel_type = neighbor['type']
                rel_count = neighbor.get('total_rel_count', len(neighbor['nodes']))
                output.append(f"  -{rel_type} (count: {rel_count})->")

                # Format connected nodes
                for node in neighbor['nodes']:
                    props = ', '.join(f"{k}={repr(v)}" for k, v in node.items())
                    output.append(f"    {props}")

            output.append("")  # Empty line between nodes

    return '\n'.join(output).strip()

def create_mcp_server(neo4j_driver: AsyncDriver, database: str = "neo4j", namespace: str = "", schema: list = []) -> FastMCP:
    mcp: FastMCP = FastMCP("mcp-neo4j-node-finder", dependencies=["neo4j", "pydantic"])

    async def find_node(
        entity_type: str = Field(..., description=f"The type of entity to find in the graph. Available options are {[el["nodeLabel"] for el in schema]}"),
        values: List[str] = Field(
            ..., description="Values to search for."
        ),
        expand: bool = Field(..., description="Whether to return it neighbors in the response or not")
    ) -> list[types.TextContent]:
        """Finds a node in the Neo4j graph and return its properties. If expand is true, then also information about its neighbors is returned"""
        topK = 5
        try:    
                node_properties = _extract_node_properties(schema, entity_type)
                for value in values:
                    cypher_statement = f"MATCH (n:`{entity_type}`) WHERE "
                    cypher_statement += " CONTAINS $value OR ".join(node_properties) + " CONTAINS $value "
                    cypher_statement += "WITH collect({node: n})[..$topK] AS initial_nodes, count(*) AS total_nodes "
                    
                    if not expand:
                        cypher_statement += "RETURN total_nodes, initial_nodes AS nodes"
                    else:
                        cypher_statement += """
                        UNWIND initial_nodes AS n
                        WITH total_nodes, n.node AS n
                        MATCH (n)-[r]->(m)
                        WITH total_nodes, n, type(r) as type, count(*) AS total_rel_count, collect(m)[..25] as names
                        WITH total_nodes, n, collect({type:type, nodes:names, total_rel_count: total_rel_count}) AS neighbors
                        RETURN total_nodes, collect({node: n, neighbors: neighbors}) AS nodes
                        """
                    response, _, _ = await neo4j_driver.execute_query(cypher_statement, database_=database, value=value, topK=topK)
                    response = [el.data() for el in response]

                    # sanitize results / remove embeddings
                    output = [_value_sanitize(el) for el in response]
                    output = _format_graph_for_llm(output)
                return [types.TextContent(type="text", text=output)]

        except Exception as e:
            logger.error(f"Database error executing query: {e}\n{entity_type}\n{values}")
            return [
                types.TextContent(type="text", text=f"Error: {e}\n{entity_type}\n{values}")
            ]


    namespace_prefix = _format_namespace(namespace)
    
    mcp.add_tool(find_node, name=namespace_prefix+"find_node")

    return mcp


async def main(
    db_url: str,
    username: str,
    password: str,
    database: str,
    transport: Literal["stdio", "sse"] = "stdio",
    namespace: str = "",
) -> None:
    logger.info("Starting MCP neo4j Server")

    neo4j_driver = AsyncGraphDatabase.driver(
        db_url,
        auth=(
            username,
            password,
        ),
    )
    schema = await get_schema_definition(neo4j_driver, database)
    mcp = create_mcp_server(neo4j_driver, database, namespace, schema)

    match transport:
        case "stdio":
            await mcp.run_stdio_async()
        case "sse":
            await mcp.run_sse_async()
        case _:
            raise ValueError(f"Invalid transport: {transport} | Must be either 'stdio' or 'sse'")


if __name__ == "__main__":
    main()
