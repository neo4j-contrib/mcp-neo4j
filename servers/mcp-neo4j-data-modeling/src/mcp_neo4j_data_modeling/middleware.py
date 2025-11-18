from fastmcp.server.middleware import Middleware, MiddlewareContext
import json
import logging

logger = logging.getLogger(__name__)


class ParseStringifiedJSONObjectMiddleware(Middleware):
    """
    Middleware that parses stringified JSON arguments before tool execution.

    This allows MCP clients to pass JSON strings for complex object parameters
    (DataModel, Node, Relationship), which will be automatically parsed into
    dictionaries before the tool function receives them.

    Tools must accept a union of a Pydantic object or a string as input. 
    This input is validated before the middleware and will throw an error if a JSON string is provided, but the argument type is only a Pydantic object.
    """

    DATA_MODEL_ARG_TOOLS = [
        "validate_data_model",
        "export_to_arrows_json",
        "get_mermaid_config_str",
        "get_relationship_cypher_ingest_query",
        "get_constraints_cypher_queries",
        "export_to_owl_turtle",
    ]
    NODE_ARG_TOOLS = [
        "validate_node",
        "get_node_cypher_ingest_query",
    ]
    RELATIONSHIP_ARG_TOOLS = [
        "validate_relationship",
    ]

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Intercept MCP tool calls and parse stringified JSON arguments.
        This runs before the tool function is executed.
        """
        # Access tool name and arguments
        if hasattr(context.message, "name") and hasattr(context.message, "arguments"):
            tool_name = context.message.name
            arguments = context.message.arguments

            # Parse stringified JSON arguments before tool execution
            if tool_name in self.DATA_MODEL_ARG_TOOLS:
                if isinstance(arguments.get("data_model"), str):
                    logger.debug(f"Parsing stringified data_model for tool {tool_name}")
                    try:
                        arguments["data_model"] = json.loads(arguments["data_model"])
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse data_model JSON: {e}")
                        raise
            elif tool_name in self.NODE_ARG_TOOLS:
                if isinstance(arguments.get("node"), str):
                    logger.debug(f"Parsing stringified node for tool {tool_name}")
                    try:
                        arguments["node"] = json.loads(arguments["node"])
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse node JSON: {e}")
                        raise
            elif tool_name in self.RELATIONSHIP_ARG_TOOLS:
                if isinstance(arguments.get("relationship"), str):
                    logger.debug(f"Parsing stringified relationship for tool {tool_name}")
                    try:
                        arguments["relationship"] = json.loads(arguments["relationship"])
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse relationship JSON: {e}")
                        raise

        return await call_next(context)
