"""
Neo4j 3.5 Compatible Cypher Generation

This module provides functions to generate Neo4j 3.5 compatible Cypher queries
for constraints and indexes.

Key differences from Neo4j 5.x:
- No named constraints (constraints are anonymous)
- No IF NOT EXISTS clause
- No NODE KEY constraints (use IS UNIQUE instead)
- No RELATIONSHIP KEY constraints
- Different index creation syntax
"""


def get_node_constraint_query_35(label: str, key_property_name: str) -> str:
    """
    Generate a Neo4j 3.5 compatible constraint query for a node.
    
    Neo4j 3.5 only supports:
    - CREATE CONSTRAINT ON (n:Label) ASSERT n.property IS UNIQUE
    - CREATE CONSTRAINT ON (n:Label) ASSERT exists(n.property)
    
    Parameters
    ----------
    label : str
        The node label.
    key_property_name : str
        The name of the key property.
        
    Returns
    -------
    str
        The Cypher constraint query.
    """
    return f"CREATE CONSTRAINT ON (n:{label}) ASSERT n.{key_property_name} IS UNIQUE"


def get_node_existence_constraint_query_35(label: str, property_name: str) -> str:
    """
    Generate a Neo4j 3.5 existence constraint query.
    
    Parameters
    ----------
    label : str
        The node label.
    property_name : str
        The property name.
        
    Returns
    -------
    str
        The Cypher existence constraint query.
    """
    return f"CREATE CONSTRAINT ON (n:{label}) ASSERT exists(n.{property_name})"


def get_relationship_constraint_query_35(
    relationship_type: str, key_property_name: str
) -> str | None:
    """
    Neo4j 3.5 does not support relationship property constraints.
    
    This function returns None to indicate no constraint can be created.
    
    Parameters
    ----------
    relationship_type : str
        The relationship type.
    key_property_name : str
        The key property name.
        
    Returns
    -------
    None
        Always returns None as 3.5 doesn't support relationship constraints.
    """
    # Neo4j 3.5 does not support relationship property constraints
    return None


def get_index_query_35(label: str, property_name: str) -> str:
    """
    Generate a Neo4j 3.5 compatible index query.
    
    Parameters
    ----------
    label : str
        The node label.
    property_name : str
        The property name to index.
        
    Returns
    -------
    str
        The Cypher index query.
    """
    return f"CREATE INDEX ON :{label}({property_name})"


def get_fulltext_index_query_35(
    index_name: str, labels: list[str], properties: list[str]
) -> str:
    """
    Generate a Neo4j 3.5 fulltext index creation query.
    
    Note: This uses APOC procedure syntax for 3.5.
    
    Parameters
    ----------
    index_name : str
        Name for the fulltext index.
    labels : list[str]
        List of node labels to index.
    properties : list[str]
        List of properties to include in the index.
        
    Returns
    -------
    str
        The APOC fulltext index creation query.
    """
    labels_str = ", ".join([f"'{l}'" for l in labels])
    props_str = ", ".join([f"'{p}'" for p in properties])
    
    return f"CALL db.index.fulltext.createNodeIndex('{index_name}', [{labels_str}], [{props_str}])"


def convert_5x_constraint_to_35(constraint_query: str) -> str | None:
    """
    Convert a Neo4j 5.x constraint query to 3.5 compatible syntax.
    
    Parameters
    ----------
    constraint_query : str
        The Neo4j 5.x constraint query.
        
    Returns
    -------
    str | None
        The 3.5 compatible query, or None if not supported.
    """
    import re
    
    # Pattern for 5.x NODE KEY constraint
    node_key_pattern = r"CREATE CONSTRAINT \w+ IF NOT EXISTS FOR \(n:(\w+)\) REQUIRE \(n\.(\w+)\) IS NODE KEY"
    match = re.match(node_key_pattern, constraint_query)
    
    if match:
        label = match.group(1)
        property_name = match.group(2)
        return get_node_constraint_query_35(label, property_name)
    
    # Pattern for 5.x RELATIONSHIP KEY constraint
    rel_key_pattern = r"CREATE CONSTRAINT \w+ IF NOT EXISTS FOR \(\)-\[r:(\w+)\]->\(\) REQUIRE"
    if re.match(rel_key_pattern, constraint_query):
        # Neo4j 3.5 doesn't support relationship constraints
        return None
    
    # If we can't parse it, return None
    return None
