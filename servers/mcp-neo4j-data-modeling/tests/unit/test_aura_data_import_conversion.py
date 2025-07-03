"""Unit tests for Aura Data Import conversion methods."""

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_neo4j_data_modeling.data_model import (
    DataModel,
    Node,
    Property,
    PropertySource,
    Relationship,
)


@pytest.fixture
def sample_aura_data_import_model():
    """Load the sample Aura Data Import model from the JSON file."""
    json_file = (
        Path(__file__).parent.parent
        / "resources"
        / "neo4j_importer_model_2025-06-30.json"
    )
    with open(json_file, "r") as f:
        return json.load(f)


@pytest.fixture
def sample_property_data():
    """Sample property data from the JSON file."""
    return {
        "$id": "p:0_0",
        "token": "countryId",
        "type": {"type": "integer"},
        "nullable": False,
    }


@pytest.fixture
def sample_source_mapping():
    """Sample source mapping for a property."""
    return {"tableName": "countries.csv", "fieldName": "id", "type": "local"}


@pytest.fixture
def sample_node_label():
    """Sample node label from the JSON file."""
    return {
        "$id": "nl:1",
        "token": "SubRegion",
        "properties": [
            {
                "$id": "p:3",
                "token": "subregion",
                "type": {"type": "string"},
                "nullable": True,
            }
        ],
    }


@pytest.fixture
def sample_node_mapping():
    """Sample node mapping from the JSON file."""
    return {
        "node": {"$ref": "#n:1"},
        "tableName": "countries.csv",
        "propertyMappings": [{"fieldName": "subregion", "property": {"$ref": "#p:3"}}],
    }


class TestPropertyConversion:
    """Test Property conversion methods."""

    def test_from_aura_data_import_string_property(self, sample_source_mapping):
        """Test converting a string property from Aura Data Import format."""
        aura_property = {
            "$id": "p:1",
            "token": "name",
            "type": {"type": "string"},
            "nullable": False,
        }

        prop = Property.from_aura_data_import(aura_property, sample_source_mapping)

        assert prop.name == "name"
        assert prop.type == "STRING"
        assert prop.source.column_name == "id"
        assert prop.source.table_name == "countries.csv"
        assert prop.source.location == "local"

    def test_from_aura_data_import_integer_property(self, sample_source_mapping):
        """Test converting an integer property from Aura Data Import format."""
        aura_property = {
            "$id": "p:0_0",
            "token": "countryId",
            "type": {"type": "integer"},
            "nullable": False,
        }

        prop = Property.from_aura_data_import(aura_property, sample_source_mapping)

        assert prop.name == "countryId"
        assert prop.type == "INTEGER"

    def test_from_aura_data_import_float_property(self, sample_source_mapping):
        """Test converting a float property from Aura Data Import format."""
        aura_property = {
            "$id": "p:0_15",
            "token": "latitude",
            "type": {"type": "float"},
            "nullable": False,
        }

        prop = Property.from_aura_data_import(aura_property, sample_source_mapping)

        assert prop.name == "latitude"
        assert prop.type == "FLOAT"

    def test_from_aura_data_import_boolean_property(self, sample_source_mapping):
        """Test converting a boolean property from Aura Data Import format."""
        aura_property = {
            "$id": "p:7",
            "token": "active",
            "type": {"type": "boolean"},
            "nullable": True,
        }

        prop = Property.from_aura_data_import(aura_property, sample_source_mapping)

        assert prop.name == "active"
        assert prop.type == "BOOLEAN"

    def test_to_aura_data_import_key_property(self):
        """Test converting a key property to Aura Data Import format."""
        prop = Property(name="id", type="INTEGER")

        result = prop.to_aura_data_import("p:0_0", is_key=True)

        assert result["$id"] == "p:0_0"
        assert result["token"] == "id"
        assert result["type"]["type"] == "integer"
        assert not result["nullable"]  # Key properties are not nullable

    def test_to_aura_data_import_non_key_property(self):
        """Test converting a non-key property to Aura Data Import format."""
        prop = Property(name="name", type="STRING")

        result = prop.to_aura_data_import("p:0_1", is_key=False)

        assert result["$id"] == "p:0_1"
        assert result["token"] == "name"
        assert result["type"]["type"] == "string"
        assert result["nullable"]  # Non-key properties are nullable

    def test_to_aura_data_import_unknown_type_defaults_to_string(self):
        """Test that unknown property types default to string."""
        prop = Property(name="custom", type="CUSTOM_TYPE")

        result = prop.to_aura_data_import("p:1", is_key=False)

        assert result["type"]["type"] == "string"


class TestNodeConversion:
    """Test Node conversion methods."""

    def test_from_aura_data_import_simple_node(
        self, sample_node_label, sample_node_mapping
    ):
        """Test converting a simple node from Aura Data Import format."""
        node = Node.from_aura_data_import(
            sample_node_label,
            "subregion",  # key property token
            sample_node_mapping,
            "local",  # source_type
        )

        assert node.label == "SubRegion"
        assert node.key_property.name == "subregion"
        assert node.key_property.type == "STRING"
        assert len(node.properties) == 0  # Only one property, which is the key

    def test_from_aura_data_import_complex_node(self, sample_aura_data_import_model):
        """Test converting a complex node with multiple properties."""
        # Get the Country node from the sample data
        country_node_label = sample_aura_data_import_model["dataModel"][
            "graphSchemaRepresentation"
        ]["graphSchema"]["nodeLabels"][0]
        country_node_mapping = sample_aura_data_import_model["dataModel"][
            "graphMappingRepresentation"
        ]["nodeMappings"][0]

        node = Node.from_aura_data_import(
            country_node_label,
            "countryId",  # key property token
            country_node_mapping,
            "local",  # source_type
        )

        assert node.label == "Country"
        assert node.key_property.name == "countryId"
        assert node.key_property.type == "INTEGER"
        assert (
            len(node.properties) == 12
        )  # 13 total properties - 1 key = 12 non-key properties

        # Check some specific properties
        property_names = [p.name for p in node.properties]
        assert "name" in property_names
        assert "iso3" in property_names
        assert "latitude" in property_names

    def test_from_aura_data_import_missing_key_property_uses_first(
        self, sample_node_label, sample_node_mapping
    ):
        """Test that when key property is not found, first property is used as key."""
        node = Node.from_aura_data_import(
            sample_node_label,
            "nonexistent_key",  # This key doesn't exist
            sample_node_mapping,
            "local",  # source_type
        )

        assert node.label == "SubRegion"
        assert node.key_property.name == "subregion"  # First property becomes key
        assert len(node.properties) == 0

    def test_to_aura_data_import_simple_node(self):
        """Test converting a simple node to Aura Data Import format."""
        key_prop = Property(name="id", type="INTEGER")
        other_prop = Property(name="name", type="STRING")
        node = Node(label="TestNode", key_property=key_prop, properties=[other_prop])

        node_label, key_property, constraint, index = node.to_aura_data_import(
            "nl:0", "n:0", "p:0_0", "c:0", "i:0"
        )

        # Check node label
        assert node_label["$id"] == "nl:0"
        assert node_label["token"] == "TestNode"
        assert len(node_label["properties"]) == 2

        # Check key property is first and not nullable
        assert node_label["properties"][0]["token"] == "id"
        assert not node_label["properties"][0]["nullable"]
        assert node_label["properties"][1]["token"] == "name"
        assert node_label["properties"][1]["nullable"]

        # Check key property mapping
        assert key_property["node"]["$ref"] == "#n:0"
        assert key_property["keyProperty"]["$ref"] == "#p:0_0"

        # Check constraint
        assert constraint["$id"] == "c:0"
        assert constraint["name"] == "TestNode_constraint"
        assert constraint["constraintType"] == "uniqueness"
        assert constraint["entityType"] == "node"
        assert constraint["nodeLabel"]["$ref"] == "#nl:0"
        assert constraint["properties"][0]["$ref"] == "#p:0_0"

        # Check index
        assert index["$id"] == "i:0"
        assert index["name"] == "TestNode_index"
        assert index["indexType"] == "default"
        assert index["entityType"] == "node"
        assert index["nodeLabel"]["$ref"] == "#nl:0"
        assert index["properties"][0]["$ref"] == "#p:0_0"

    def test_node_mapping_property_not_found_raises_error(self, sample_node_label):
        """Test that missing property in node mapping raises an error."""
        invalid_mapping = {
            "node": {"$ref": "#n:1"},
            "tableName": "countries.csv",
            "propertyMappings": [],  # Empty mappings
        }

        with pytest.raises(ValueError, match="Property p:3 not found in node mapping"):
            Node.from_aura_data_import(
                sample_node_label, "subregion", invalid_mapping, "local"
            )


class TestRelationshipConversion:
    """Test Relationship conversion methods."""

    def test_from_aura_data_import_simple_relationship(self):
        """Test converting a simple relationship from Aura Data Import format."""
        rel_type = {"$id": "rt:1", "token": "IN_SUBREGION", "properties": []}

        rel_obj = {
            "$id": "r:1",
            "type": {"$ref": "#rt:1"},
            "from": {"$ref": "#n:0"},
            "to": {"$ref": "#n:1"},
        }

        node_id_to_label_map = {"#n:0": "Country", "#n:1": "SubRegion"}

        # Empty relationship mapping since there are no properties
        rel_mapping = {
            "relationship": {"$ref": "#r:1"},
            "tableName": "relationships.csv",
            "propertyMappings": [],
        }

        relationship = Relationship.from_aura_data_import(
            rel_type, rel_obj, node_id_to_label_map, rel_mapping, "local"
        )

        assert relationship.type == "IN_SUBREGION"
        assert relationship.start_node_label == "Country"
        assert relationship.end_node_label == "SubRegion"
        assert relationship.key_property is None
        assert len(relationship.properties) == 0

    def test_from_aura_data_import_relationship_with_properties(self):
        """Test converting a relationship with properties."""
        rel_type = {
            "$id": "rt:2",
            "token": "CONNECTED_TO",
            "properties": [
                {
                    "$id": "p:rel_1",
                    "token": "weight",
                    "type": {"type": "float"},
                    "nullable": False,
                },
                {
                    "$id": "p:rel_2",
                    "token": "since",
                    "type": {"type": "string"},
                    "nullable": True,
                },
            ],
        }

        rel_obj = {
            "$id": "r:2",
            "type": {"$ref": "#rt:2"},
            "from": {"$ref": "#n:0"},
            "to": {"$ref": "#n:1"},
        }

        node_id_to_label_map = {"#n:0": "NodeA", "#n:1": "NodeB"}

        # Relationship mapping with properties
        rel_mapping = {
            "relationship": {"$ref": "#r:2"},
            "tableName": "relationships.csv",
            "propertyMappings": [
                {"property": {"$ref": "#p:rel_1"}, "fieldName": "weight"},
                {"property": {"$ref": "#p:rel_2"}, "fieldName": "since"},
            ],
        }

        relationship = Relationship.from_aura_data_import(
            rel_type, rel_obj, node_id_to_label_map, rel_mapping, "local"
        )

        assert relationship.type == "CONNECTED_TO"
        assert relationship.key_property is None  # No automatic key property assignment
        assert (
            len(relationship.properties) == 2
        )  # Both properties are regular properties
        assert relationship.properties[0].name == "weight"
        assert relationship.properties[1].name == "since"

    def test_to_aura_data_import_simple_relationship(self):
        """Test converting a simple relationship to Aura Data Import format."""
        relationship = Relationship(
            type="KNOWS", start_node_label="Person", end_node_label="Person"
        )

        rel_type, rel_obj, constraint, index = relationship.to_aura_data_import(
            "rt:1", "r:1", "n:0", "n:1"
        )

        # Check relationship type
        assert rel_type["$id"] == "rt:1"
        assert rel_type["token"] == "KNOWS"
        assert len(rel_type["properties"]) == 0

        # Check relationship object
        assert rel_obj["$id"] == "r:1"
        assert rel_obj["type"]["$ref"] == "#rt:1"
        assert rel_obj["from"]["$ref"] == "#n:0"
        assert rel_obj["to"]["$ref"] == "#n:1"

        # Check that constraint and index are None (no key property)
        assert constraint is None
        assert index is None

    def test_to_aura_data_import_relationship_with_properties(self):
        """Test converting a relationship with properties to Aura Data Import format."""
        key_prop = Property(name="relationshipId", type="INTEGER")
        other_prop = Property(name="strength", type="FLOAT")

        relationship = Relationship(
            type="CONNECTED",
            start_node_label="NodeA",
            end_node_label="NodeB",
            key_property=key_prop,
            properties=[other_prop],
        )

        rel_type, rel_obj, constraint, index = relationship.to_aura_data_import(
            "rt:2", "r:2", "n:0", "n:1", "c:5", "i:5"
        )

        # Check relationship type has properties
        assert len(rel_type["properties"]) == 2
        assert rel_type["properties"][0]["token"] == "relationshipId"
        assert not rel_type["properties"][0]["nullable"]  # Key property
        assert rel_type["properties"][1]["token"] == "strength"
        assert rel_type["properties"][1]["nullable"]  # Non-key property

        # Check constraint (should exist since relationship has key property)
        assert constraint is not None
        assert constraint["$id"] == "c:5"
        assert constraint["name"] == "CONNECTED_constraint"
        assert constraint["constraintType"] == "uniqueness"
        assert constraint["entityType"] == "relationship"
        assert constraint["relationshipType"]["$ref"] == "#rt:2"

        # Check index (should exist since relationship has key property)
        assert index is not None
        assert index["$id"] == "i:5"
        assert index["name"] == "CONNECTED_index"
        assert index["indexType"] == "default"
        assert index["entityType"] == "relationship"
        assert index["relationshipType"]["$ref"] == "#rt:2"

    def test_relationship_source_info_export(self):
        """Test that relationship property source information is properly exported."""
        # Create nodes with source information
        country_source = PropertySource(
            column_name="country_id",
            table_name="countries.csv",
            location="local",
            source_type="local",
        )

        country_key_prop = Property(
            name="id",
            type="INTEGER",
            source=country_source,
            description="Country identifier",
        )

        country_node = Node(
            label="Country", key_property=country_key_prop, properties=[]
        )

        region_source = PropertySource(
            column_name="region_name",
            table_name="regions.csv",
            location="local",
            source_type="local",
        )

        region_key_prop = Property(
            name="name", type="STRING", source=region_source, description="Region name"
        )

        region_node = Node(label="Region", key_property=region_key_prop, properties=[])

        # Create relationship with property that has different source table
        rel_prop_source = PropertySource(
            column_name="connection_weight",
            table_name="country_region_connections.csv",
            location="local",
            source_type="local",
        )

        rel_prop = Property(
            name="weight",
            type="FLOAT",
            source=rel_prop_source,
            description="Connection weight",
        )

        relationship = Relationship(
            type="BELONGS_TO",
            start_node_label="Country",
            end_node_label="Region",
            properties=[rel_prop],
        )

        # Create data model and export
        data_model = DataModel(
            nodes=[country_node, region_node], relationships=[relationship]
        )
        aura_dict = data_model.to_aura_data_import_dict()

        # Verify that relationship uses its own table name, not the source node's table
        rel_mappings = aura_dict["dataModel"]["graphMappingRepresentation"][
            "relationshipMappings"
        ]
        assert len(rel_mappings) == 1
        assert rel_mappings[0]["tableName"] == "country_region_connections.csv"

        # Verify that relationship property field name is correct
        rel_prop_mappings = rel_mappings[0]["propertyMappings"]
        assert len(rel_prop_mappings) == 1
        assert rel_prop_mappings[0]["fieldName"] == "connection_weight"

        # Verify that node mappings still use their own table names
        node_mappings = aura_dict["dataModel"]["graphMappingRepresentation"][
            "nodeMappings"
        ]
        assert len(node_mappings) == 2
        assert node_mappings[0]["tableName"] == "countries.csv"
        assert node_mappings[1]["tableName"] == "regions.csv"


class TestDataModelConversion:
    """Test DataModel conversion methods."""

    def test_from_aura_data_import_full_model(self, sample_aura_data_import_model):
        """Test converting the full sample Aura Data Import model."""
        data_model = DataModel.from_aura_data_import(sample_aura_data_import_model)

        # Check nodes
        assert len(data_model.nodes) == 5
        node_labels = [n.label for n in data_model.nodes]
        assert "Country" in node_labels
        assert "SubRegion" in node_labels
        assert "Region" in node_labels
        assert "TimeZones" in node_labels
        assert "Currency" in node_labels

        # Check relationships
        assert len(data_model.relationships) == 4
        rel_types = [r.type for r in data_model.relationships]
        assert "IN_SUBREGION" in rel_types
        assert "IN_REGION" in rel_types
        assert "IN_TIMEZONE" in rel_types
        assert "USES_CURRENCY" in rel_types

    def test_from_aura_data_import_node_key_properties(
        self, sample_aura_data_import_model
    ):
        """Test that node key properties are correctly identified."""
        data_model = DataModel.from_aura_data_import(sample_aura_data_import_model)

        # Find specific nodes and check their key properties
        country_node = next(n for n in data_model.nodes if n.label == "Country")
        assert country_node.key_property.name == "countryId"
        assert country_node.key_property.type == "INTEGER"

        region_node = next(n for n in data_model.nodes if n.label == "Region")
        assert region_node.key_property.name == "region"
        assert region_node.key_property.type == "STRING"

    def test_to_aura_data_import_dict_structure(self):
        """Test the structure of the exported Aura Data Import dictionary."""
        # Create a simple data model
        key_prop = Property(name="id", type="INTEGER")
        node1 = Node(label="TestNode", key_property=key_prop)

        rel = Relationship(
            type="TEST_REL", start_node_label="TestNode", end_node_label="TestNode"
        )

        data_model = DataModel(nodes=[node1], relationships=[rel])

        result = data_model.to_aura_data_import_dict()

        # Check top-level structure
        assert "version" in result
        assert "visualisation" in result
        assert "dataModel" in result

        # Check visualization structure
        assert "nodes" in result["visualisation"]
        assert len(result["visualisation"]["nodes"]) == 1

        # Check data model structure
        data_model_content = result["dataModel"]
        assert "graphSchemaRepresentation" in data_model_content
        assert "graphSchemaExtensionsRepresentation" in data_model_content
        assert "graphMappingRepresentation" in data_model_content
        assert "configurations" in data_model_content

        # Check graph schema
        graph_schema = data_model_content["graphSchemaRepresentation"]["graphSchema"]
        assert "nodeLabels" in graph_schema
        assert "relationshipTypes" in graph_schema
        assert "nodeObjectTypes" in graph_schema
        assert "relationshipObjectTypes" in graph_schema
        assert "constraints" in graph_schema
        assert "indexes" in graph_schema

    def test_to_aura_data_import_dict_node_constraints_and_indexes(self):
        """Test that constraints and indexes are properly generated."""
        key_prop = Property(name="userId", type="INTEGER")
        node = Node(label="User", key_property=key_prop)
        data_model = DataModel(nodes=[node])

        result = data_model.to_aura_data_import_dict()

        graph_schema = result["dataModel"]["graphSchemaRepresentation"]["graphSchema"]

        # Check constraints
        assert len(graph_schema["constraints"]) == 1
        constraint = graph_schema["constraints"][0]
        assert constraint["name"] == "User_constraint"
        assert constraint["constraintType"] == "uniqueness"
        assert constraint["entityType"] == "node"

        # Check indexes
        assert len(graph_schema["indexes"]) == 1
        index = graph_schema["indexes"][0]
        assert index["name"] == "User_index"
        assert index["indexType"] == "default"
        assert index["entityType"] == "node"

    def test_round_trip_conversion_simple(self):
        """Test that a simple model can be converted to Aura format and back."""
        # Create original model
        key_prop = Property(name="id", type="STRING")
        node = Node(label="TestNode", key_property=key_prop)
        original_model = DataModel(nodes=[node])

        # Convert to Aura format
        aura_dict = original_model.to_aura_data_import_dict()

        # Convert back
        converted_model = DataModel.from_aura_data_import(aura_dict)

        # Check that essential structure is preserved
        assert len(converted_model.nodes) == 1
        assert converted_model.nodes[0].label == "TestNode"
        assert converted_model.nodes[0].key_property.name == "id"
        assert converted_model.nodes[0].key_property.type == "STRING"

    def test_round_trip_conversion_with_relationships(self):
        """Test round-trip conversion with relationships."""
        # Create original model
        key_prop1 = Property(name="id1", type="INTEGER")
        key_prop2 = Property(name="id2", type="STRING")
        node1 = Node(label="Node1", key_property=key_prop1)
        node2 = Node(label="Node2", key_property=key_prop2)

        rel = Relationship(
            type="CONNECTS", start_node_label="Node1", end_node_label="Node2"
        )

        original_model = DataModel(nodes=[node1, node2], relationships=[rel])

        # Convert to Aura format and back
        aura_dict = original_model.to_aura_data_import_dict()
        converted_model = DataModel.from_aura_data_import(aura_dict)

        # Check nodes
        assert len(converted_model.nodes) == 2
        node_labels = [n.label for n in converted_model.nodes]
        assert "Node1" in node_labels
        assert "Node2" in node_labels

        # Check relationships
        assert len(converted_model.relationships) == 1
        assert converted_model.relationships[0].type == "CONNECTS"
        assert converted_model.relationships[0].start_node_label == "Node1"
        assert converted_model.relationships[0].end_node_label == "Node2"

    def test_json_serialization(self, sample_aura_data_import_model):
        """Test that the converted model can be serialized to JSON."""
        data_model = DataModel.from_aura_data_import(sample_aura_data_import_model)
        json_str = data_model.to_aura_data_import_json_str()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "dataModel" in parsed

    def test_metadata_preservation_round_trip(self, sample_aura_data_import_model):
        """Test that metadata (constraints, indexes, version, configurations) is preserved during round-trip conversion."""
        # Convert from Aura Data Import to our model
        data_model = DataModel.from_aura_data_import(sample_aura_data_import_model)

        # Verify metadata was stored
        assert "aura_data_import" in data_model.metadata
        aura_metadata = data_model.metadata["aura_data_import"]

        # Check that all expected metadata fields are present
        assert "version" in aura_metadata
        assert "dataModel_version" in aura_metadata
        assert "constraints" in aura_metadata
        assert "indexes" in aura_metadata
        assert "configurations" in aura_metadata
        assert "dataSourceSchema" in aura_metadata

        # Verify the stored values match the original
        assert aura_metadata["version"] == sample_aura_data_import_model["version"]
        assert (
            aura_metadata["dataModel_version"]
            == sample_aura_data_import_model["dataModel"]["version"]
        )
        assert (
            aura_metadata["constraints"]
            == sample_aura_data_import_model["dataModel"]["graphSchemaRepresentation"][
                "graphSchema"
            ]["constraints"]
        )
        assert (
            aura_metadata["indexes"]
            == sample_aura_data_import_model["dataModel"]["graphSchemaRepresentation"][
                "graphSchema"
            ]["indexes"]
        )
        assert (
            aura_metadata["configurations"]
            == sample_aura_data_import_model["dataModel"]["configurations"]
        )

        # Check that visualization data was stored in node metadata
        original_vis_nodes = sample_aura_data_import_model["visualisation"]["nodes"]
        for i, node in enumerate(data_model.nodes):
            node_id = f"n:{i}"
            original_vis_node = next(
                (v for v in original_vis_nodes if v["id"] == node_id), None
            )
            if original_vis_node:
                assert "visualization" in node.metadata
                assert (
                    node.metadata["visualization"]["position"]
                    == original_vis_node["position"]
                )

        # Convert back to Aura Data Import
        converted_back = data_model.to_aura_data_import_dict()

        # Verify that the metadata was restored
        assert converted_back["version"] == sample_aura_data_import_model["version"]
        assert (
            converted_back["dataModel"]["version"]
            == sample_aura_data_import_model["dataModel"]["version"]
        )
        assert (
            converted_back["dataModel"]["configurations"]
            == sample_aura_data_import_model["dataModel"]["configurations"]
        )

        # Verify that visualization was reconstructed correctly
        assert "visualisation" in converted_back
        assert "nodes" in converted_back["visualisation"]
        assert len(converted_back["visualisation"]["nodes"]) == len(data_model.nodes)

        # Check that positions were preserved for existing nodes
        original_vis_nodes = sample_aura_data_import_model["visualisation"]["nodes"]
        converted_vis_nodes = converted_back["visualisation"]["nodes"]
        for original_vis_node in original_vis_nodes:
            converted_vis_node = next(
                (v for v in converted_vis_nodes if v["id"] == original_vis_node["id"]),
                None,
            )
            if converted_vis_node:
                assert converted_vis_node["position"] == original_vis_node["position"]

        # Check that constraints and indexes were preserved
        original_constraints = sample_aura_data_import_model["dataModel"][
            "graphSchemaRepresentation"
        ]["graphSchema"]["constraints"]
        converted_constraints = converted_back["dataModel"][
            "graphSchemaRepresentation"
        ]["graphSchema"]["constraints"]
        assert converted_constraints == original_constraints

        original_indexes = sample_aura_data_import_model["dataModel"][
            "graphSchemaRepresentation"
        ]["graphSchema"]["indexes"]
        converted_indexes = converted_back["dataModel"]["graphSchemaRepresentation"][
            "graphSchema"
        ]["indexes"]
        assert converted_indexes == original_indexes

    def test_export_without_metadata_uses_defaults(self):
        """Test that exporting a DataModel without Aura metadata uses appropriate defaults."""
        # Create a simple DataModel from scratch (no metadata)
        key_prop = Property(name="id", type="INTEGER")
        node = Node(label="TestNode", key_property=key_prop)
        data_model = DataModel(nodes=[node])

        # Export to Aura Data Import format
        aura_dict = data_model.to_aura_data_import_dict()

        # Verify default values are used
        assert aura_dict["version"] == "2.3.1-beta.0"
        assert aura_dict["dataModel"]["version"] == "2.3.1-beta.0"
        assert aura_dict["dataModel"]["configurations"] == {"idsToIgnore": []}

        # Verify that table schemas are automatically generated (not empty)
        data_source_schema = aura_dict["dataModel"]["graphMappingRepresentation"][
            "dataSourceSchema"
        ]
        assert data_source_schema["type"] == "local"
        assert len(data_source_schema["tableSchemas"]) == 1
        assert data_source_schema["tableSchemas"][0]["name"] == "testnode.csv"
        assert len(data_source_schema["tableSchemas"][0]["fields"]) == 1
        assert data_source_schema["tableSchemas"][0]["fields"][0]["name"] == "id"

        # Verify visualization nodes are generated
        assert "visualisation" in aura_dict
        assert "nodes" in aura_dict["visualisation"]
        assert len(aura_dict["visualisation"]["nodes"]) == 1
        assert aura_dict["visualisation"]["nodes"][0]["id"] == "n:0"

        # Verify constraints and indexes are generated for the node
        graph_schema = aura_dict["dataModel"]["graphSchemaRepresentation"][
            "graphSchema"
        ]
        assert len(graph_schema["constraints"]) == 1
        assert len(graph_schema["indexes"]) == 1
        assert graph_schema["constraints"][0]["name"] == "TestNode_constraint"
        assert graph_schema["indexes"][0]["name"] == "TestNode_index"

    def test_visualization_reconstruction_with_new_nodes(
        self, sample_aura_data_import_model
    ):
        """Test that visualization is properly reconstructed when new nodes are added."""
        # Convert from Aura Data Import to our model
        data_model = DataModel.from_aura_data_import(sample_aura_data_import_model)

        # Add a new node that wasn't in the original data
        new_key_prop = Property(name="newId", type="STRING")
        new_node = Node(label="NewNode", key_property=new_key_prop)
        data_model.add_node(new_node)

        # Convert back to Aura Data Import
        converted_back = data_model.to_aura_data_import_dict()

        # Verify visualization includes all nodes (original + new)
        vis_nodes = converted_back["visualisation"]["nodes"]
        assert len(vis_nodes) == len(data_model.nodes)

        # Check that original nodes kept their positions
        original_vis_nodes = sample_aura_data_import_model["visualisation"]["nodes"]
        for original_vis_node in original_vis_nodes:
            converted_vis_node = next(
                (v for v in vis_nodes if v["id"] == original_vis_node["id"]), None
            )
            if converted_vis_node:
                assert converted_vis_node["position"] == original_vis_node["position"]

        # Check that new node got a default position
        new_node_id = (
            f"n:{len(data_model.nodes) - 1}"  # Last node should be the new one
        )
        new_vis_node = next((v for v in vis_nodes if v["id"] == new_node_id), None)
        assert new_vis_node is not None
        assert "position" in new_vis_node
        assert isinstance(new_vis_node["position"]["x"], float)
        assert isinstance(new_vis_node["position"]["y"], float)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_data_model_conversion(self):
        """Test converting an empty data model."""
        empty_model = DataModel()

        aura_dict = empty_model.to_aura_data_import_dict()

        # Should have basic structure even when empty
        assert "version" in aura_dict
        assert "visualisation" in aura_dict
        assert len(aura_dict["visualisation"]["nodes"]) == 0

        graph_schema = aura_dict["dataModel"]["graphSchemaRepresentation"][
            "graphSchema"
        ]
        assert len(graph_schema["nodeLabels"]) == 0
        assert len(graph_schema["relationshipTypes"]) == 0

    def test_node_with_no_properties_mapping(self, sample_node_label):
        """Test handling of node with missing property mappings."""
        empty_mapping = {
            "node": {"$ref": "#n:1"},
            "tableName": "unknown",
            "propertyMappings": [],
        }

        # Should raise error when property is not found in mapping
        with pytest.raises(ValueError):
            Node.from_aura_data_import(
                sample_node_label, "subregion", empty_mapping, "local"
            )

    def test_malformed_aura_data_missing_required_fields(self):
        """Test handling of malformed Aura Data Import data."""
        malformed_data = {
            "version": "2.3.1-beta.0",
            # Missing visualisation and dataModel
        }

        with pytest.raises(KeyError):
            DataModel.from_aura_data_import(malformed_data)

    def test_property_type_edge_cases(self, sample_source_mapping):
        """Test property type conversion edge cases."""
        # Test with unknown type
        unknown_type_prop = {
            "$id": "p:unknown",
            "token": "unknown",
            "type": {"type": "unknown_type"},
            "nullable": False,
        }

        prop = Property.from_aura_data_import(unknown_type_prop, sample_source_mapping)
        assert prop.type == "UNKNOWN_TYPE"  # Should uppercase unknown types

        # Test conversion back
        result = prop.to_aura_data_import("p:test", is_key=False)
        assert result["type"]["type"] == "string"  # Should default to string


def test_aura_data_import_round_trip_data_integrity(
    sample_aura_data_import_model: dict[str, Any],
) -> None:
    """Test that Aura Data Import model preserves essential data integrity through round-trip conversion."""
    # Load the model
    data_model = DataModel.from_aura_data_import(sample_aura_data_import_model)

    # Convert back to Aura Data Import format
    converted_back = data_model.to_aura_data_import_dict()

    # Check top-level structure
    assert converted_back["version"] == sample_aura_data_import_model["version"]
    assert (
        converted_back["dataModel"]["version"]
        == sample_aura_data_import_model["dataModel"]["version"]
    )

    # Check that all nodes are preserved
    original_node_labels = {
        nl["token"]
        for nl in sample_aura_data_import_model["dataModel"][
            "graphSchemaRepresentation"
        ]["graphSchema"]["nodeLabels"]
    }
    converted_node_labels = {
        nl["token"]
        for nl in converted_back["dataModel"]["graphSchemaRepresentation"][
            "graphSchema"
        ]["nodeLabels"]
    }
    assert original_node_labels == converted_node_labels

    # Check that all relationships are preserved
    original_rel_types = {
        rt["token"]
        for rt in sample_aura_data_import_model["dataModel"][
            "graphSchemaRepresentation"
        ]["graphSchema"]["relationshipTypes"]
    }
    converted_rel_types = {
        rt["token"]
        for rt in converted_back["dataModel"]["graphSchemaRepresentation"][
            "graphSchema"
        ]["relationshipTypes"]
    }
    assert original_rel_types == converted_rel_types

    # Check that visualization nodes are preserved for all nodes
    assert len(converted_back["visualisation"]["nodes"]) == len(
        sample_aura_data_import_model["visualisation"]["nodes"]
    )

    # Check that metadata was preserved
    assert (
        converted_back["dataModel"]["configurations"]
        == sample_aura_data_import_model["dataModel"]["configurations"]
    )
