import json
from typing import Any

import pytest
from pydantic import ValidationError

from mcp_neo4j_data_modeling.data_model import DataModel, Node, Property, Relationship


def test_node_add_property_new():
    """Test adding a new property to a node."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    node = Node(
        label="Person",
        key_property=key_prop,
        properties=[Property(name="name", type="string", description="Full name")],
    )

    new_prop = Property(name="age", type="integer", description="Age in years")
    node.add_property(new_prop)

    assert len(node.properties) == 2
    assert any(p.name == "age" for p in node.properties)


def test_node_add_property_existing():
    """Test adding an existing property to a node should raise an error."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    node = Node(
        label="Person",
        key_property=key_prop,
        properties=[Property(name="name", type="string", description="Full name")],
    )

    duplicate_prop = Property(name="name", type="string", description="Another name")

    with pytest.raises(ValueError, match="Property name already exists"):
        node.add_property(duplicate_prop)


def test_node_remove_property():
    """Test removing a property from a node."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    name_prop = Property(name="name", type="string", description="Full name")
    age_prop = Property(name="age", type="integer", description="Age in years")

    node = Node(label="Person", key_property=key_prop, properties=[name_prop, age_prop])

    node.remove_property(name_prop)

    assert len(node.properties) == 1
    assert not any(p.name == "name" for p in node.properties)


def test_node_validate_properties_key_prop_in_properties_list():
    """Test validating properties of a node when key property is in properties list."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    node = Node(
        label="Person",
        key_property=key_prop,
        properties=[
            Property(name="name", type="string", description="Full name"),
            Property(name="id", type="string", description="Unique identifier"),
        ],
    )

    assert len(node.properties) == 1
    assert not any(p.name == "id" for p in node.properties)


def test_node_validate_properties_dupe_property_names():
    """Test validating properties of a node when there are duplicate property names."""
    with pytest.raises(
        ValidationError, match="Property name appears 2 times in node Person"
    ):
        Node(
            label="Person",
            key_property=Property(
                name="id", type="string", description="Unique identifier"
            ),
            properties=[
                Property(name="name", type="string", description="Full name"),
                Property(name="name", type="string", description="Another name"),
            ],
        )


def test_relationship_add_property_new():
    """Test adding a new property to a relationship."""
    key_prop = Property(name="since", type="date", description="Start date")
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Person",
        key_property=key_prop,
        properties=[
            Property(name="weight", type="float", description="Relationship strength")
        ],
    )

    new_prop = Property(name="context", type="string", description="How they met")
    relationship.add_property(new_prop)

    assert len(relationship.properties) == 2
    assert any(p.name == "context" for p in relationship.properties)


def test_relationship_add_property_existing():
    """Test adding an existing property to a relationship should raise an error."""
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Person",
        properties=[
            Property(name="weight", type="float", description="Relationship strength")
        ],
    )

    duplicate_prop = Property(name="weight", type="float", description="Another weight")

    with pytest.raises(ValueError, match="Property weight already exists"):
        relationship.add_property(duplicate_prop)


def test_relationship_remove_property():
    """Test removing a property from a relationship."""
    weight_prop = Property(
        name="weight", type="float", description="Relationship strength"
    )
    context_prop = Property(name="context", type="string", description="How they met")

    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Person",
        properties=[weight_prop, context_prop],
    )

    relationship.remove_property(weight_prop)

    assert len(relationship.properties) == 1
    assert not any(p.name == "weight" for p in relationship.properties)


def test_generate_relationship_pattern():
    """Test generating relationship pattern string."""
    relationship = Relationship(
        type="KNOWS", start_node_label="Person", end_node_label="Person", properties=[]
    )

    expected_pattern = "(:Person)-[:KNOWS]->(:Person)"
    assert relationship.pattern == expected_pattern


def test_relationship_validate_properties_key_prop_in_properties_list():
    """Test validating properties of a relationship when key property is in properties list."""
    key_prop = Property(name="id", type="string", description="Unique identifier")
    relationship = Relationship(
        start_node_label="Person",
        end_node_label="Person",
        type="KNOWS",
        key_property=key_prop,
        properties=[
            Property(name="name", type="string", description="Full name"),
            Property(name="id", type="string", description="Unique identifier"),
        ],
    )

    assert len(relationship.properties) == 1
    assert not any(p.name == "id" for p in relationship.properties)


def test_relationship_validate_properties_dupe_property_names():
    """Test validating properties of a relationship when there are duplicate property names."""
    with pytest.raises(
        ValidationError,
        match=r"Property name appears 2 times in relationship \(:Person\)-\[:KNOWS\]->\(:Person\)",
    ):
        Relationship(
            start_node_label="Person",
            end_node_label="Person",
            type="KNOWS",
            key_property=Property(
                name="id", type="string", description="Unique identifier"
            ),
            properties=[
                Property(name="name", type="string", description="Full name"),
                Property(name="name", type="string", description="Another name"),
            ],
        )


def test_data_model_validate_nodes_valid():
    """Test data model validation with valid nodes."""
    key_prop1 = Property(name="id", type="string", description="Unique identifier")
    key_prop2 = Property(name="code", type="string", description="Company code")

    nodes = [
        Node(label="Person", key_property=key_prop1, properties=[]),
        Node(label="Company", key_property=key_prop2, properties=[]),
    ]

    data_model = DataModel(nodes=nodes, relationships=[])

    # Should not raise an exception
    assert len(data_model.nodes) == 2


def test_data_model_validate_nodes_invalid_dupe_labels():
    """Test data model validation with duplicate node labels."""
    key_prop = Property(name="id", type="string", description="Unique identifier")

    nodes = [
        Node(label="Person", key_property=key_prop, properties=[]),
        Node(label="Person", key_property=key_prop, properties=[]),
    ]

    with pytest.raises(
        ValidationError, match="Node with label Person appears 2 times in data model"
    ):
        DataModel(nodes=nodes, relationships=[])


def test_data_model_validate_relationships_valid():
    """Test data model validation with valid relationships."""
    nodes = [
        Node(
            label="Person",
            key_property=Property(
                name="id", type="STRING", description="Unique identifier"
            ),
            properties=[],
        ),
        Node(
            label="Company",
            key_property=Property(
                name="id", type="STRING", description="Unique identifier"
            ),
            properties=[],
        ),
    ]
    relationships = [
        Relationship(
            type="KNOWS",
            start_node_label="Person",
            end_node_label="Person",
            properties=[],
        ),
        Relationship(
            type="WORKS_FOR",
            start_node_label="Person",
            end_node_label="Company",
            properties=[],
        ),
    ]

    data_model = DataModel(nodes=nodes, relationships=relationships)

    # Should not raise an exception
    assert len(data_model.relationships) == 2


def test_data_model_validate_relationships_invalid_dupe_patterns():
    """Test data model validation with duplicate relationship patterns."""
    relationships = [
        Relationship(
            type="KNOWS",
            start_node_label="Person",
            end_node_label="Person",
            properties=[],
        ),
        Relationship(
            type="KNOWS",
            start_node_label="Person",
            end_node_label="Person",
            properties=[],
        ),
    ]
    with pytest.raises(
        ValidationError,
        match=r"Relationship with pattern \(:Person\)-\[:KNOWS\]->\(:Person\) appears 2 times in data model",
    ):
        DataModel(nodes=[], relationships=relationships)


def test_data_model_validate_relationships_invalid_start_node_does_not_exist():
    """Test data model validation with a start node that does not exist."""
    nodes = [
        Node(
            label="Pet",
            key_property=Property(
                name="id", type="string", description="Unique identifier"
            ),
        ),
        Node(
            label="Place",
            key_property=Property(
                name="id", type="string", description="Unique identifier"
            ),
        ),
    ]
    relationships = [
        Relationship(
            type="KNOWS", start_node_label="Person", end_node_label="Pet", properties=[]
        )
    ]
    with pytest.raises(
        ValidationError,
        match=r"Relationship \(:Person\)-\[:KNOWS\]->\(:Pet\) has a start node that does not exist in data model",
    ):
        DataModel(nodes=nodes, relationships=relationships)


def test_data_model_validate_relationships_invalid_end_node_does_not_exist():
    """Test data model validation with an end node that does not exist."""
    nodes = [
        Node(
            label="Person",
            key_property=Property(
                name="id", type="string", description="Unique identifier"
            ),
        ),
        Node(
            label="Place",
            key_property=Property(
                name="id", type="string", description="Unique identifier"
            ),
        ),
    ]

    relationships = [
        Relationship(
            type="KNOWS", start_node_label="Person", end_node_label="Pet", properties=[]
        )
    ]
    with pytest.raises(
        ValidationError,
        match=r"Relationship \(:Person\)-\[:KNOWS\]->\(:Pet\) has an end node that does not exist in data model",
    ):
        DataModel(nodes=nodes, relationships=relationships)


def test_data_model_from_arrows(arrows_data_model_dict: dict[str, Any]):
    """Test converting an Arrows Data Model to a Data Model."""
    data_model = DataModel.from_arrows(arrows_data_model_dict)
    assert len(data_model.nodes) == 4
    assert len(data_model.relationships) == 4
    assert data_model.nodes[0].label == "Person"
    assert data_model.nodes[0].key_property.name == "name"
    assert data_model.nodes[0].key_property.type == "STRING"
    assert data_model.nodes[0].metadata == {
        "position": {"x": 105.3711141386136, "y": -243.80584874322315},
        "caption": "",
        "style": {},
    }
    assert len(data_model.nodes[0].properties) == 1
    assert data_model.nodes[0].properties[0].name == "age"
    assert data_model.nodes[0].properties[0].type == "INTEGER"
    assert data_model.nodes[0].properties[0].description is None
    assert data_model.nodes[1].label == "Address"
    assert data_model.nodes[1].key_property.name == "fullAddress"
    assert data_model.nodes[1].key_property.type == "STRING"
    assert data_model.relationships[0].metadata == {
        "style": {},
    }
    assert {"Person", "Address", "Pet", "Toy"} == {n.label for n in data_model.nodes}
    assert {"KNOWS", "HAS_ADDRESS", "HAS_PET", "PLAYS_WITH"} == {
        r.type for r in data_model.relationships
    }
    assert data_model.metadata == {
        "style": {
            "font-family": "sans-serif",
            "background-color": "#ffffff",
            "background-image": "",
            "background-size": "100%",
            "node-color": "#ffffff",
            "border-width": 4,
            "border-color": "#000000",
            "radius": 50,
            "node-padding": 5,
            "node-margin": 2,
            "outside-position": "auto",
            "node-icon-image": "",
            "node-background-image": "",
            "icon-position": "inside",
            "icon-size": 64,
            "caption-position": "inside",
            "caption-max-width": 200,
            "caption-color": "#000000",
            "caption-font-size": 50,
            "caption-font-weight": "normal",
            "label-position": "inside",
            "label-display": "pill",
            "label-color": "#000000",
            "label-background-color": "#ffffff",
            "label-border-color": "#000000",
            "label-border-width": 4,
            "label-font-size": 40,
            "label-padding": 5,
            "label-margin": 4,
            "directionality": "directed",
            "detail-position": "inline",
            "detail-orientation": "parallel",
            "arrow-width": 5,
            "arrow-color": "#000000",
            "margin-start": 5,
            "margin-end": 5,
            "margin-peer": 20,
            "attachment-start": "normal",
            "attachment-end": "normal",
            "relationship-icon-image": "",
            "type-color": "#000000",
            "type-background-color": "#ffffff",
            "type-border-color": "#000000",
            "type-border-width": 0,
            "type-font-size": 16,
            "type-padding": 5,
            "property-position": "outside",
            "property-alignment": "colon",
            "property-color": "#000000",
            "property-font-size": 16,
            "property-font-weight": "normal",
        }
    }


def test_data_model_to_arrows():
    nodes = [
        Node(
            label="Person",
            key_property=Property(
                name="id", type="STRING", description="Unique identifier"
            ),
            properties=[
                Property(name="name", type="STRING", description="Name of the person")
            ],
        ),
        Node(
            label="Company",
            key_property=Property(
                name="id2", type="STRING", description="Unique identifier 2"
            ),
            properties=[],
        ),
    ]
    relationships = [
        Relationship(
            type="KNOWS",
            start_node_label="Person",
            end_node_label="Person",
            properties=[],
        ),
        Relationship(
            type="WORKS_FOR",
            start_node_label="Person",
            end_node_label="Company",
            properties=[],
        ),
    ]

    data_model = DataModel(nodes=nodes, relationships=relationships)

    arrows_data_model_dict = data_model.to_arrows_dict()
    assert len(arrows_data_model_dict["nodes"]) == 2
    assert len(arrows_data_model_dict["relationships"]) == 2
    assert arrows_data_model_dict["nodes"][0]["id"] == "Person"
    assert arrows_data_model_dict["nodes"][0]["properties"] == {
        "id": "STRING | Unique identifier | KEY",
        "name": "STRING | Name of the person",
    }
    assert arrows_data_model_dict["nodes"][0]["position"] == {"x": 0.0, "y": 0.0}
    assert arrows_data_model_dict["nodes"][0]["caption"] == ""
    assert arrows_data_model_dict["nodes"][0]["style"] == {}
    assert arrows_data_model_dict["nodes"][1]["id"] == "Company"
    assert arrows_data_model_dict["nodes"][1]["properties"] == {
        "id2": "STRING | Unique identifier 2 | KEY"
    }
    assert arrows_data_model_dict["nodes"][1]["position"] == {"x": 200.0, "y": 0.0}
    assert arrows_data_model_dict["nodes"][1]["caption"] == ""
    assert arrows_data_model_dict["nodes"][1]["style"] == {}
    assert arrows_data_model_dict["relationships"][0]["fromId"] == "Person"


def test_data_model_arrows_round_trip(arrows_data_model_dict: dict[str, Any]):
    """Test converting a Data Model to an Arrows Data Model and back."""
    data_model = DataModel.from_arrows(arrows_data_model_dict)
    arrows_data_model_dict_copy = json.loads(data_model.to_arrows_json_str())

    assert (
        arrows_data_model_dict_copy["nodes"][0]["properties"]["name"]
        == arrows_data_model_dict["nodes"][0]["properties"]["name"]
    )
    assert (
        arrows_data_model_dict_copy["nodes"][0]["properties"]["name"]
        == arrows_data_model_dict["nodes"][0]["properties"]["name"]
    )
    assert (
        arrows_data_model_dict_copy["nodes"][1]["properties"]
        == arrows_data_model_dict["nodes"][1]["properties"]
    )
    assert (
        arrows_data_model_dict_copy["relationships"][0]["type"]
        == arrows_data_model_dict["relationships"][0]["type"]
    )
    assert (
        arrows_data_model_dict_copy["relationships"][1]["type"]
        == arrows_data_model_dict["relationships"][1]["type"]
    )
    assert arrows_data_model_dict_copy["style"] == arrows_data_model_dict["style"]


def test_node_cypher_generation_for_many_records():
    """Test generating a Cypher query to ingest a list of Node records into a Neo4j database."""
    node = Node(
        label="Person",
        key_property=Property(
            name="id", type="STRING", description="Unique identifier"
        ),
        properties=[
            Property(name="name", type="STRING", description="Name of the person"),
            Property(name="age", type="INTEGER", description="Age of the person"),
        ],
    )

    query = node.get_cypher_ingest_query_for_many_records()

    assert (
        query
        == """UNWIND $records as record
MERGE (n: Person {id: record.id})
SET n += {name: record.name, age: record.age}"""
    )


def test_relationship_cypher_generation_for_many_records():
    """Test generating a Cypher query to ingest a list of Relationship records into a Neo4j database."""
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Place",
        key_property=Property(
            name="relId", type="STRING", description="Unique identifier"
        ),
        properties=[Property(name="since", type="DATE", description="Since date")],
    )

    query = relationship.get_cypher_ingest_query_for_many_records(
        start_node_key_property_name="personId", end_node_key_property_name="placeId"
    )

    assert (
        query
        == """UNWIND $records as record
MATCH (start: Person {personId: record.sourceId})
MATCH (end: Place {placeId: record.targetId})
MERGE (start)-[:KNOWS {relId: record.relId}]->(end)
SET end += {since: record.since}"""
    )


def test_relationship_cypher_generation_for_many_records_no_key_property():
    """Test generating a Cypher query to ingest a list of Relationship records into a Neo4j database."""
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Place",
        properties=[Property(name="since", type="DATE", description="Since date")],
    )

    query = relationship.get_cypher_ingest_query_for_many_records(
        start_node_key_property_name="personId", end_node_key_property_name="placeId"
    )

    assert (
        query
        == """UNWIND $records as record
MATCH (start: Person {personId: record.sourceId})
MATCH (end: Place {placeId: record.targetId})
MERGE (start)-[:KNOWS]->(end)
SET end += {since: record.since}"""
    )


def test_relationship_cypher_generation_for_many_records_no_properties():
    """Test generating a Cypher query to ingest a list of Relationship records into a Neo4j database."""
    relationship = Relationship(
        type="KNOWS",
        start_node_label="Person",
        end_node_label="Place",
    )
    query = relationship.get_cypher_ingest_query_for_many_records(
        start_node_key_property_name="personId", end_node_key_property_name="placeId"
    )

    assert (
        query
        == """UNWIND $records as record
MATCH (start: Person {personId: record.sourceId})
MATCH (end: Place {placeId: record.targetId})
MERGE (start)-[:KNOWS]->(end)"""
    )


def test_get_node_cypher_ingest_query_for_many_records(valid_data_model: DataModel):
    """Test generating a Cypher query to ingest a list of Node records into a Neo4j database."""

    query = valid_data_model.get_node_cypher_ingest_query_for_many_records("Person")

    assert (
        query
        == """UNWIND $records as record
MERGE (n: Person {id: record.id})
SET n += {name: record.name, age: record.age}"""
    )


def test_get_relationship_cypher_ingest_query_for_many_records(
    valid_data_model: DataModel,
):
    """Test generating a Cypher query to ingest a list of Relationship records into a Neo4j database."""
    query = valid_data_model.get_relationship_cypher_ingest_query_for_many_records(
        "LIVES_IN", "Person", "Place"
    )

    assert (
        query
        == """UNWIND $records as record
MATCH (start: Person {id: record.sourceId})
MATCH (end: Place {id: record.targetId})
MERGE (start)-[:LIVES_IN]->(end)"""
    )


def test_get_cypher_constraints_query(valid_data_model: DataModel):
    """Test generating a list of Cypher queries to create constraints on the data model."""
    queries = valid_data_model.get_cypher_constraints_query()

    assert len(queries) == 2
    assert (
        queries[0]
        == "CREATE CONSTRAINT Person_constraint IF NOT EXISTS FOR (n:Person) REQUIRE (n.id) IS NODE KEY;"
    )
    assert (
        queries[1]
        == "CREATE CONSTRAINT Place_constraint IF NOT EXISTS FOR (n:Place) REQUIRE (n.id) IS NODE KEY;"
    )


def test_from_dict_basic():
    """Test basic from_dict conversion with minimal data."""
    data = {
        "nodes": [
            {
                "label": "Person",
                "key_property": {"name": "id", "type": "STRING"},
                "properties": [{"name": "name", "type": "STRING"}],
            }
        ],
        "relationships": [
            {
                "type": "KNOWS",
                "start_node_label": "Person",
                "end_node_label": "Person",
            }
        ],
    }

    data_model = DataModel.from_dict(data)

    assert len(data_model.nodes) == 1
    assert len(data_model.relationships) == 1
    assert data_model.nodes[0].label == "Person"
    assert data_model.nodes[0].key_property.name == "id"
    assert data_model.nodes[0].key_property.type == "STRING"
    assert len(data_model.nodes[0].properties) == 1
    assert data_model.nodes[0].properties[0].name == "name"
    assert data_model.relationships[0].type == "KNOWS"


def test_from_dict_with_relationship_properties():
    """Test from_dict conversion with relationship properties."""
    data = {
        "nodes": [
            {
                "label": "Person",
                "key_property": {"name": "id", "type": "STRING"},
                "properties": [],
            }
        ],
        "relationships": [
            {
                "type": "KNOWS",
                "start_node_label": "Person",
                "end_node_label": "Person",
                "key_property": {"name": "since", "type": "DATE"},
                "properties": [{"name": "strength", "type": "FLOAT"}],
            }
        ],
    }

    data_model = DataModel.from_dict(data)

    assert len(data_model.relationships) == 1
    rel = data_model.relationships[0]
    assert rel.key_property.name == "since"
    assert rel.key_property.type == "DATE"
    assert len(rel.properties) == 1
    assert rel.properties[0].name == "strength"
    assert rel.properties[0].type == "FLOAT"


def test_from_dict_without_relationship_properties():
    """Test from_dict conversion without relationship properties."""
    data = {
        "nodes": [
            {
                "label": "Person",
                "key_property": {"name": "id", "type": "STRING"},
                "properties": [],
            }
        ],
        "relationships": [
            {
                "type": "KNOWS",
                "start_node_label": "Person",
                "end_node_label": "Person",
            }
        ],
    }

    data_model = DataModel.from_dict(data)

    assert len(data_model.relationships) == 1
    rel = data_model.relationships[0]
    assert rel.key_property is None
    assert len(rel.properties) == 0


def test_from_dict_multiple_nodes_and_relationships():
    """Test from_dict conversion with multiple nodes and relationships."""
    data = {
        "nodes": [
            {
                "label": "Person",
                "key_property": {"name": "id", "type": "STRING"},
                "properties": [{"name": "name", "type": "STRING"}],
            },
            {
                "label": "Company",
                "key_property": {"name": "id", "type": "STRING"},
                "properties": [{"name": "name", "type": "STRING"}],
            },
        ],
        "relationships": [
            {
                "type": "WORKS_FOR",
                "start_node_label": "Person",
                "end_node_label": "Company",
                "properties": [{"name": "start_date", "type": "DATE"}],
            },
            {
                "type": "MANAGES",
                "start_node_label": "Person",
                "end_node_label": "Person",
            },
        ],
    }

    data_model = DataModel.from_dict(data)

    assert len(data_model.nodes) == 2
    assert len(data_model.relationships) == 2
    
    # Check nodes
    person_node = next(n for n in data_model.nodes if n.label == "Person")
    company_node = next(n for n in data_model.nodes if n.label == "Company")
    assert person_node is not None
    assert company_node is not None
    
    # Check relationships
    works_for_rel = next(r for r in data_model.relationships if r.type == "WORKS_FOR")
    manages_rel = next(r for r in data_model.relationships if r.type == "MANAGES")
    assert works_for_rel is not None
    assert manages_rel is not None
    assert len(works_for_rel.properties) == 1
    assert works_for_rel.properties[0].name == "start_date"


def test_from_dict_empty_properties():
    """Test from_dict conversion with empty properties arrays."""
    data = {
        "nodes": [
            {
                "label": "Person",
                "key_property": {"name": "id", "type": "STRING"},
                "properties": [],
            }
        ],
        "relationships": [
            {
                "type": "KNOWS",
                "start_node_label": "Person",
                "end_node_label": "Person",
                "properties": [],
            }
        ],
    }

    data_model = DataModel.from_dict(data)

    assert len(data_model.nodes[0].properties) == 0
    assert len(data_model.relationships[0].properties) == 0


def test_from_dict_missing_properties_key():
    """Test from_dict conversion when properties key is missing."""
    data = {
        "nodes": [
            {
                "label": "Person",
                "key_property": {"name": "id", "type": "STRING"},
            }
        ],
        "relationships": [
            {
                "type": "KNOWS",
                "start_node_label": "Person",
                "end_node_label": "Person",
            }
        ],
    }

    data_model = DataModel.from_dict(data)

    assert len(data_model.nodes[0].properties) == 0
    assert len(data_model.relationships[0].properties) == 0


def test_from_dict_all_example_models():
    """Test from_dict conversion with all example models from static.py."""
    from mcp_neo4j_data_modeling.static import (
        PATIENT_JOURNEY_MODEL,
        SUPPLY_CHAIN_MODEL,
        SOFTWARE_DEPENDENCY_MODEL,
        OIL_GAS_MONITORING_MODEL,
        CUSTOMER_360_MODEL,
        FRAUD_AML_MODEL,
        HEALTH_INSURANCE_FRAUD_MODEL,
    )

    models = [
        PATIENT_JOURNEY_MODEL,
        SUPPLY_CHAIN_MODEL,
        SOFTWARE_DEPENDENCY_MODEL,
        OIL_GAS_MONITORING_MODEL,
        CUSTOMER_360_MODEL,
        FRAUD_AML_MODEL,
        HEALTH_INSURANCE_FRAUD_MODEL,
    ]

    for i, model_data in enumerate(models):
        data_model = DataModel.from_dict(model_data)
        
        # Verify the conversion worked
        assert isinstance(data_model, DataModel)
        assert len(data_model.nodes) > 0
        assert len(data_model.relationships) >= 0
        
        # Verify all nodes have required fields
        for node in data_model.nodes:
            assert node.label is not None
            assert node.key_property is not None
            assert node.key_property.name is not None
            assert node.key_property.type is not None
        
        # Verify all relationships have required fields
        for rel in data_model.relationships:
            assert rel.type is not None
            assert rel.start_node_label is not None
            assert rel.end_node_label is not None


def test_from_dict_invalid_data():
    """Test from_dict conversion with invalid data structure."""
    # Missing nodes
    with pytest.raises(KeyError):
        DataModel.from_dict({"relationships": []})

    # Missing relationships
    with pytest.raises(KeyError):
        DataModel.from_dict({"nodes": []})

    # Invalid node structure
    with pytest.raises(KeyError):
        DataModel.from_dict({
            "nodes": [{"label": "Person"}],  # Missing key_property
            "relationships": []
        })

    # Invalid relationship structure
    with pytest.raises(KeyError):
        DataModel.from_dict({
            "nodes": [{"label": "Person", "key_property": {"name": "id", "type": "STRING"}, "properties": []}],
            "relationships": [{"type": "KNOWS"}]  # Missing start_node_label and end_node_label
        })


# ============================================================================
# Server Tools and MCP Resources Tests
# ============================================================================

@pytest.mark.asyncio
async def test_list_example_data_models_tool():
    """Test the list_example_data_models tool functionality."""
    from mcp_neo4j_data_modeling.server import create_mcp_server
    
    mcp = create_mcp_server()
    
    # Get the tool function
    tools = await mcp.get_tools()
    list_tool = tools.get("list_example_data_models")
    
    assert list_tool is not None, "list_example_data_models tool not found"
    
    # Test the tool
    result = list_tool.fn()
    
    # Verify structure
    assert "available_examples" in result
    assert "total_examples" in result
    assert "usage" in result
    
    # Verify expected examples
    expected_examples = [
        "patient_journey", "supply_chain", "software_dependency", 
        "oil_gas_monitoring", "customer_360", "fraud_aml", "health_insurance_fraud"
    ]
    
    assert result["total_examples"] == 7
    assert set(result["available_examples"].keys()) == set(expected_examples)
    
    # Verify each example has required fields
    for example_key, example_data in result["available_examples"].items():
        assert "name" in example_data
        assert "description" in example_data
        assert "nodes" in example_data
        assert "relationships" in example_data
        assert isinstance(example_data["nodes"], int)
        assert isinstance(example_data["relationships"], int)
        assert example_data["nodes"] > 0
        assert example_data["relationships"] >= 0


@pytest.mark.asyncio
async def test_load_example_data_model_tool_all_examples():
    """Test the load_example_data_model tool with all available examples."""
    from mcp_neo4j_data_modeling.server import create_mcp_server
    
    mcp = create_mcp_server()
    
    # Get the tool function
    tools = await mcp.get_tools()
    load_tool = tools.get("load_example_data_model")
    
    assert load_tool is not None, "load_example_data_model tool not found"
    
    # Test all examples
    examples = [
        "patient_journey", "supply_chain", "software_dependency", 
        "oil_gas_monitoring", "customer_360", "fraud_aml", "health_insurance_fraud"
    ]
    
    for example_name in examples:
        data_model = load_tool.fn(example_name=example_name)
        
        # Verify it's a valid DataModel
        assert isinstance(data_model, DataModel)
        assert len(data_model.nodes) > 0
        assert len(data_model.relationships) >= 0
        
        # Verify all nodes have required fields
        for node in data_model.nodes:
            assert node.label is not None
            assert node.key_property is not None
            assert node.key_property.name is not None
            assert node.key_property.type is not None
        
        # Verify all relationships have required fields
        for rel in data_model.relationships:
            assert rel.type is not None
            assert rel.start_node_label is not None
            assert rel.end_node_label is not None


@pytest.mark.asyncio
async def test_load_example_data_model_tool_invalid_example():
    """Test the load_example_data_model tool with invalid example name."""
    from mcp_neo4j_data_modeling.server import create_mcp_server
    
    mcp = create_mcp_server()
    
    # Get the tool function
    tools = await mcp.get_tools()
    load_tool = tools.get("load_example_data_model")
    
    assert load_tool is not None, "load_example_data_model tool not found"
    
    # Test with invalid example name
    with pytest.raises(ValueError, match="Unknown example"):
        load_tool.fn(example_name="invalid_example")


@pytest.mark.asyncio
async def test_mcp_resources_schemas():
    """Test that all MCP schema resources return valid JSON schemas."""
    from mcp_neo4j_data_modeling.server import create_mcp_server
    
    mcp = create_mcp_server()
    
    # Test schema resources
    schema_resources = [
        "resource://schema/node",
        "resource://schema/relationship", 
        "resource://schema/property",
        "resource://schema/data_model"
    ]
    
    resources = await mcp.get_resources()
    for resource_uri in schema_resources:
        resource_func = resources.get(resource_uri)
        
        assert resource_func is not None, f"Resource {resource_uri} not found"
        
        # Test the resource
        schema = resource_func.fn()
        
        # Verify it's a valid JSON schema
        assert isinstance(schema, dict)
        assert "type" in schema or "properties" in schema or "$schema" in schema


@pytest.mark.asyncio
async def test_mcp_resources_example_models():
    """Test that all MCP example model resources return valid JSON."""
    from mcp_neo4j_data_modeling.server import create_mcp_server
    import json
    
    mcp = create_mcp_server()
    
    # Test example model resources
    example_resources = [
        "resource://examples/patient_journey_model",
        "resource://examples/supply_chain_model",
        "resource://examples/software_dependency_model",
        "resource://examples/oil_gas_monitoring_model",
        "resource://examples/customer_360_model",
        "resource://examples/fraud_aml_model",
        "resource://examples/health_insurance_fraud_model"
    ]
    
    resources = await mcp.get_resources()
    for resource_uri in example_resources:
        resource_func = resources.get(resource_uri)
        
        assert resource_func is not None, f"Resource {resource_uri} not found"
        
        # Test the resource
        json_str = resource_func.fn()
        
        # Verify it's valid JSON
        assert isinstance(json_str, str)
        
        # Parse JSON and verify structure
        data = json.loads(json_str)
        assert "nodes" in data
        assert "relationships" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["relationships"], list)
        
        # Verify nodes have required structure
        for node in data["nodes"]:
            assert "label" in node
            assert "key_property" in node
            assert "properties" in node
            assert "name" in node["key_property"]
            assert "type" in node["key_property"]
        
        # Verify relationships have required structure
        for rel in data["relationships"]:
            assert "type" in rel
            assert "start_node_label" in rel
            assert "end_node_label" in rel


@pytest.mark.asyncio
async def test_mcp_resource_neo4j_data_ingest_process():
    """Test the neo4j_data_ingest_process resource."""
    from mcp_neo4j_data_modeling.server import create_mcp_server
    
    mcp = create_mcp_server()
    
    # Find the resource
    resources = await mcp.get_resources()
    resource_func = resources.get("resource://static/neo4j_data_ingest_process")
    
    assert resource_func is not None, "neo4j_data_ingest_process resource not found"
    
    # Test the resource
    process_text = resource_func.fn()
    
    # Verify it returns a string with content
    assert isinstance(process_text, str)
    assert len(process_text) > 0
    assert "Neo4j" in process_text or "ingest" in process_text.lower()


@pytest.mark.asyncio
async def test_tool_validation_with_example_models():
    """Test that all example models can be validated using the validation tools."""
    from mcp_neo4j_data_modeling.server import create_mcp_server
    
    mcp = create_mcp_server()
    
    # Get the tools
    tools = await mcp.get_tools()
    load_tool = tools.get("load_example_data_model")
    validate_tool = tools.get("validate_data_model")
    
    assert load_tool is not None, "load_example_data_model tool not found"
    assert validate_tool is not None, "validate_data_model tool not found"
    
    # Test all examples
    examples = [
        "patient_journey", "supply_chain", "software_dependency", 
        "oil_gas_monitoring", "customer_360", "fraud_aml", "health_insurance_fraud"
    ]
    
    for example_name in examples:
        # Load the example
        data_model = load_tool.fn(example_name=example_name)
        
        # Validate it
        validation_result = validate_tool.fn(data_model=data_model)
        
        # Should return True for valid models
        assert validation_result is True


@pytest.mark.asyncio
async def test_consistency_between_resources_and_tools():
    """Test that MCP resources and tools return consistent data for the same example."""
    from mcp_neo4j_data_modeling.server import create_mcp_server
    import json
    
    mcp = create_mcp_server()
    
    # Get the patient journey example from both resource and tool
    resources = await mcp.get_resources()
    tools = await mcp.get_tools()
    
    patient_journey_resource = resources.get("resource://examples/patient_journey_model")
    load_tool = tools.get("load_example_data_model")
    
    assert patient_journey_resource is not None, "patient_journey_model resource not found"
    assert load_tool is not None, "load_example_data_model tool not found"
    
    # Get data from resource (JSON string)
    resource_json_str = patient_journey_resource.fn()
    resource_data = json.loads(resource_json_str)
    
    # Get data from tool (DataModel object)
    tool_data_model = load_tool.fn(example_name="patient_journey")
    
    # Verify consistency
    assert len(resource_data["nodes"]) == len(tool_data_model.nodes)
    assert len(resource_data["relationships"]) == len(tool_data_model.relationships)
    
    # Verify node labels match
    resource_node_labels = {node["label"] for node in resource_data["nodes"]}
    tool_node_labels = {node.label for node in tool_data_model.nodes}
    assert resource_node_labels == tool_node_labels
    
    # Verify relationship types match
    resource_rel_types = {rel["type"] for rel in resource_data["relationships"]}
    tool_rel_types = {rel.type for rel in tool_data_model.relationships}
    assert resource_rel_types == tool_rel_types
