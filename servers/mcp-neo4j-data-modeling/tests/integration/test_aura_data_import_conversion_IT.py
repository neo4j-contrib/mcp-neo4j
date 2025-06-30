import pytest
from mcp_neo4j_data_modeling.data_model import DataModel
import json
from typing import Any

@pytest.fixture
def aura_data_import_model() -> dict[str, Any]:
    with open("tests/resources/neo4j_importer_model_2025-06-30.json", "r") as f:
        return json.load(f)


def test_aura_data_import_round_trip_data_integrity(aura_data_import_model: dict[str, Any]) -> None:
    """Test that Aura Data Import model preserves essential data integrity through round-trip conversion."""
    # Load the model
    data_model = DataModel.from_aura_data_import(aura_data_import_model)
    
    # Convert back to Aura Data Import format
    converted_back = data_model.to_aura_data_import_dict()
    
    # Check top-level structure
    assert converted_back["version"] == aura_data_import_model["version"]
    assert converted_back["dataModel"]["version"] == aura_data_import_model["dataModel"]["version"]
    
    # Check that all nodes are preserved
    original_node_labels = {
        nl["token"] for nl in aura_data_import_model["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["nodeLabels"]
    }
    converted_node_labels = {
        nl["token"] for nl in converted_back["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["nodeLabels"]
    }
    assert original_node_labels == converted_node_labels
    
    # Check that all relationships are preserved
    original_rel_types = {
        rt["token"] for rt in aura_data_import_model["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["relationshipTypes"]
    }
    converted_rel_types = {
        rt["token"] for rt in converted_back["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["relationshipTypes"]
    }
    assert original_rel_types == converted_rel_types
    
    # Check that visualization nodes are preserved for all nodes
    assert len(converted_back["visualisation"]["nodes"]) == len(aura_data_import_model["visualisation"]["nodes"])
    
    # Check that metadata was preserved
    assert converted_back["dataModel"]["configurations"] == aura_data_import_model["dataModel"]["configurations"]