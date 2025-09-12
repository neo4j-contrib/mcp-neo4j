"""
Namespace utilities for MCP Neo4j servers.
"""


def format_namespace(namespace: str) -> str:
    """
    Format namespace string to ensure proper suffix for tool naming. 
    This ensures that the namespace and tool name are separated by a hyphen (namespace-tool).
    
    Parameters
    ----------
    namespace : str
        The namespace string to format
        
    Returns
    -------
    str
        Formatted namespace string with hyphen suffix (namespace-)
    """
    if namespace:
        if namespace.endswith("-"):
            return namespace
        else:
            return namespace + "-"
    else:
        return ""