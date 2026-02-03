"""
Test the data model conversion for the Neo4j Graphrag Python Package.
"""

import pytest
from neo4j_graphrag.experimental.components.schema import (
    SchemaBuilder,
)

from mcp_neo4j_data_modeling.data_model import DataModel


@pytest.mark.asyncio
async def test_data_model_for_graphrag_package_to_neo4j_graphrag_python_package_schema(
    test_data_model_for_graphrag_package: DataModel,
):
    """Test the data model conversion for the Neo4j Graphrag Python Package."""
    result = (
        test_data_model_for_graphrag_package.to_neo4j_graphrag_python_package_schema()
    )

    assert result is not None

    schema_builder = SchemaBuilder()
    graphrag_schema = await schema_builder.run(**result["schema"])

    assert len(graphrag_schema.node_types) == len(
        test_data_model_for_graphrag_package.nodes
    )
    assert len(graphrag_schema.relationship_types) == len(
        test_data_model_for_graphrag_package.relationships
    )
    assert len(graphrag_schema.patterns) == len(
        test_data_model_for_graphrag_package.relationships
    )

    assert (
        graphrag_schema.node_types[0].label
        == test_data_model_for_graphrag_package.nodes[0].label
    )
    assert (
        graphrag_schema.node_types[0].description
        == test_data_model_for_graphrag_package.nodes[0].description
    )
    assert (
        graphrag_schema.node_types[0].properties[0].name
        == test_data_model_for_graphrag_package.nodes[0].key_property.name
    )
    assert (
        graphrag_schema.node_types[0].properties[0].type
        == test_data_model_for_graphrag_package.nodes[0].key_property.type
    )
    assert (
        graphrag_schema.node_types[0].properties[0].description
        == test_data_model_for_graphrag_package.nodes[0].key_property.description
    )
    assert graphrag_schema.node_types[0].properties[0].required

    assert (
        graphrag_schema.node_types[0].properties[1].name
        == test_data_model_for_graphrag_package.nodes[0].properties[0].name
    )
    assert (
        graphrag_schema.node_types[0].properties[1].type
        == test_data_model_for_graphrag_package.nodes[0].properties[0].type
    )
    assert (
        graphrag_schema.node_types[0].properties[1].description
        == "The name of the person"
    )
    assert not graphrag_schema.node_types[0].properties[1].required

    assert (
        graphrag_schema.node_types[1].label
        == test_data_model_for_graphrag_package.nodes[1].label
    )
    assert (
        graphrag_schema.node_types[1].description == ""  # no description for this node
    )
    assert (
        graphrag_schema.node_types[1].properties[0].name
        == test_data_model_for_graphrag_package.nodes[1].key_property.name
    )
    assert (
        graphrag_schema.node_types[1].properties[0].type
        == test_data_model_for_graphrag_package.nodes[1].key_property.type
    )
    assert graphrag_schema.node_types[1].properties[0].description == ""
    assert graphrag_schema.node_types[1].properties[0].required

    assert (
        graphrag_schema.relationship_types[0].label
        == test_data_model_for_graphrag_package.relationships[0].type
    )
    assert (
        graphrag_schema.relationship_types[0].description
        == test_data_model_for_graphrag_package.relationships[0].description
    )
    assert (
        graphrag_schema.relationship_types[0].properties[0].name
        == test_data_model_for_graphrag_package.relationships[0].properties[0].name
    )
    assert (
        graphrag_schema.relationship_types[0].properties[0].type
        == test_data_model_for_graphrag_package.relationships[0].properties[0].type
    )
    assert (
        graphrag_schema.relationship_types[0].properties[0].description
        == "The number of years the person has lived in the city"
    )
    assert not graphrag_schema.relationship_types[0].properties[0].required
