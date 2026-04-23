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
    nodes = [
        Node(
            label="Person",
            key_property=Property(
                name="id", type="string", description="Unique identifier"
            ),
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
            type="KNOWS",
            start_node_label="Person",
            end_node_label="Person",
            properties=[],
        ),
    ]
    # Since we removed duplicate relationship validation, this should now pass
    data_model = DataModel(nodes=nodes, relationships=relationships)
    assert len(data_model.relationships) == 2


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


def test_data_model_to_owl_turtle_str():
    """Test converting a data model to an OWL Turtle string."""
    nodes = [
        Node(
            label="Person",
            key_property=Property(
                name="personId", type="STRING", description="Unique identifier"
            ),
            properties=[
                Property(name="name", type="STRING", description="Name of the person"),
                Property(name="birthYear", type="INTEGER", description="Birth year"),
            ],
        ),
        Node(
            label="Address",
            key_property=Property(
                name="addressId", type="STRING", description="Unique identifier"
            ),
            properties=[
                Property(
                    name="streetAddress", type="STRING", description="Street address"
                ),
            ],
        ),
    ]
    relationships = [
        Relationship(
            type="LIVES_AT",
            start_node_label="Person",
            end_node_label="Address",
            properties=[],
        ),
    ]

    data_model = DataModel(nodes=nodes, relationships=relationships)
    turtle_str = data_model.to_owl_turtle_str()

    # Basic checks to ensure the turtle string contains expected elements
    assert "owl:Ontology" in turtle_str
    assert ":Person" in turtle_str
    assert ":Address" in turtle_str
    assert ":LIVES_AT" in turtle_str
    assert ":personId" in turtle_str
    assert ":name" in turtle_str
    assert ":birthYear" in turtle_str
    assert "owl:Class" in turtle_str
    assert "owl:ObjectProperty" in turtle_str
    assert "owl:DatatypeProperty" in turtle_str


def test_data_model_from_owl_turtle_str():
    """Test converting an OWL Turtle string to a data model."""
    # Read the test TTL file
    import pathlib

    ttl_file = pathlib.Path(__file__).parent.parent / "resources" / "blueplaques.ttl"
    with open(ttl_file, "r") as f:
        turtle_str = f.read()

    data_model = DataModel.from_owl_turtle_str(turtle_str)

    # Check that nodes were created
    assert len(data_model.nodes) > 0

    # Check for expected classes
    node_labels = {n.label for n in data_model.nodes}
    assert "Person" in node_labels
    assert "Address" in node_labels
    assert "Plaque" in node_labels
    assert "MusicalComposition" in node_labels
    assert "Organization" in node_labels

    # Check for expected relationships
    assert len(data_model.relationships) > 0
    relationship_types = {r.type for r in data_model.relationships}
    assert "COMPOSED" in relationship_types
    assert "HONORED_BY" in relationship_types
    assert "LOCATED_AT" in relationship_types

    # Check that Person node has properties
    person_node = next((n for n in data_model.nodes if n.label == "Person"), None)
    assert person_node is not None
    assert person_node.key_property is not None

    # Check for expected properties on Person
    all_person_props = [person_node.key_property.name] + [
        p.name for p in person_node.properties
    ]
    assert "personId" in all_person_props
    assert any(
        "name" in prop.lower()
        or "nationality" in prop.lower()
        or "profession" in prop.lower()
        for prop in all_person_props
    )


def test_data_model_owl_turtle_round_trip():
    """Test converting a data model to OWL Turtle and back."""
    nodes = [
        Node(
            label="Person",
            key_property=Property(name="personId", type="STRING"),
            properties=[
                Property(name="name", type="STRING"),
                Property(name="age", type="INTEGER"),
            ],
        ),
        Node(
            label="Company",
            key_property=Property(name="companyId", type="STRING"),
            properties=[
                Property(name="companyName", type="STRING"),
            ],
        ),
    ]
    relationships = [
        Relationship(
            type="WORKS_FOR",
            start_node_label="Person",
            end_node_label="Company",
            properties=[],
        ),
    ]

    original_model = DataModel(nodes=nodes, relationships=relationships)

    # Convert to Turtle
    turtle_str = original_model.to_owl_turtle_str()

    # Convert back to DataModel
    restored_model = DataModel.from_owl_turtle_str(turtle_str)

    # Check that basic structure is preserved
    assert len(restored_model.nodes) == len(original_model.nodes)
    assert len(restored_model.relationships) == len(original_model.relationships)

    restored_labels = {n.label for n in restored_model.nodes}
    original_labels = {n.label for n in original_model.nodes}
    assert restored_labels == original_labels

    restored_rel_types = {r.type for r in restored_model.relationships}
    original_rel_types = {r.type for r in original_model.relationships}
    assert restored_rel_types == original_rel_types


def test_property_to_pydantic_model_str_with_description():
    """Test Property.to_pydantic_model_str() with description - validates exact format."""
    prop = Property(name="userName", type="STRING", description="The user's name")
    result = prop.to_pydantic_model_str()

    expected = 'userName: str = Field(..., description="The user\'s name")'
    assert result == expected


def test_property_to_pydantic_model_str_without_description():
    """Test Property.to_pydantic_model_str() without description - validates exact format."""
    prop = Property(name="userId", type="STRING")
    result = prop.to_pydantic_model_str()

    expected = "userId: str"
    assert result == expected


def test_property_to_pydantic_model_str_integer_type():
    """Test Property.to_pydantic_model_str() with INTEGER type - validates exact format."""
    prop = Property(name="count", type="INTEGER", description="Item count")
    result = prop.to_pydantic_model_str()

    expected = 'count: int = Field(..., description="Item count")'
    assert result == expected


def test_property_to_pydantic_model_str_float_type():
    """Test Property.to_pydantic_model_str() with FLOAT type - validates exact format."""
    prop = Property(name="amount", type="FLOAT", description="Dollar amount")
    result = prop.to_pydantic_model_str()

    expected = 'amount: float = Field(..., description="Dollar amount")'
    assert result == expected


def test_property_to_pydantic_model_str_boolean_type():
    """Test Property.to_pydantic_model_str() with BOOLEAN type - validates exact format."""
    prop = Property(name="active", type="BOOLEAN", description="Is active")
    result = prop.to_pydantic_model_str()

    expected = 'active: bool = Field(..., description="Is active")'
    assert result == expected


def test_property_to_pydantic_model_str_datetime_type():
    """Test Property.to_pydantic_model_str() with DATETIME type - validates exact format."""
    prop = Property(name="createdAt", type="DATETIME", description="Creation timestamp")
    result = prop.to_pydantic_model_str()

    expected = 'createdAt: datetime = Field(..., description="Creation timestamp")'
    assert result == expected


def test_node_to_pydantic_model_str_simple():
    """Test Node.to_pydantic_model_str() with simple node - validates exact format."""
    node = Node(
        label="User",
        key_property=Property(name="userId", type="STRING", description="User ID"),
        properties=[],
    )
    result = node.to_pydantic_model_str()

    expected = """class User(BaseModel):
    node_label: ClassVar[str] = "User"

    userId: str = Field(..., description="User ID")""".strip()
    assert result == expected


def test_node_to_pydantic_model_str_with_properties():
    """Test Node.to_pydantic_model_str() with multiple properties - validates exact format."""
    node = Node(
        label="Product",
        key_property=Property(
            name="productId", type="STRING", description="Product identifier"
        ),
        properties=[
            Property(name="name", type="STRING", description="Product name"),
            Property(name="price", type="FLOAT", description="Product price"),
            Property(name="inStock", type="BOOLEAN", description="Availability"),
        ],
    )
    result = node.to_pydantic_model_str()

    expected = """class Product(BaseModel):
    node_label: ClassVar[str] = "Product"

    productId: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    inStock: bool = Field(..., description="Availability")""".strip()
    assert result == expected


def test_node_to_pydantic_model_str_various_types():
    """Test Node.to_pydantic_model_str() with various property types - validates exact format."""
    node = Node(
        label="Event",
        key_property=Property(name="eventId", type="STRING", description="Event ID"),
        properties=[
            Property(
                name="attendees", type="INTEGER", description="Number of attendees"
            ),
            Property(name="startTime", type="DATETIME", description="Start time"),
            Property(name="tags", type="LIST", description="Event tags"),
        ],
    )
    result = node.to_pydantic_model_str()

    expected = """class Event(BaseModel):
    node_label: ClassVar[str] = "Event"

    eventId: str = Field(..., description="Event ID")
    attendees: int = Field(..., description="Number of attendees")
    startTime: datetime = Field(..., description="Start time")
    tags: list = Field(..., description="Event tags")""".strip()
    assert result == expected


def test_node_to_pydantic_model_str_pascal_case_label():
    """Test Node.to_pydantic_model_str() maintains PascalCase label - validates exact format."""
    node = Node(
        label="CustomerAccount",
        key_property=Property(
            name="accountId", type="STRING", description="Account ID"
        ),
        properties=[],
    )
    result = node.to_pydantic_model_str()

    expected = """class CustomerAccount(BaseModel):
    node_label: ClassVar[str] = "CustomerAccount"

    accountId: str = Field(..., description="Account ID")""".strip()
    assert result == expected


def test_relationship_to_pydantic_model_str_simple():
    """Test Relationship.to_pydantic_model_str() with simple relationship - validates exact format."""
    relationship = Relationship(
        type="FOLLOWS", start_node_label="User", end_node_label="User", properties=[]
    )
    start_key_prop = Property(name="userId", type="STRING", description="User ID")
    end_key_prop = Property(name="userId", type="STRING", description="User ID")

    result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

    expected = """class Follows(BaseModel):
    relationship_type: ClassVar[str] = "FOLLOWS"
    start_node_label: ClassVar[str] = "User"
    end_node_label: ClassVar[str] = "User"
    pattern: ClassVar[str] = "(:User)-[:FOLLOWS]->(:User)"

    start_node_User_userId: str = Field(..., description="User ID")
    end_node_User_userId: str = Field(..., description="User ID")"""
    assert result == expected


def test_relationship_to_pydantic_model_str_with_key_property():
    """Test Relationship.to_pydantic_model_str() with relationship key property - validates exact format."""
    relationship = Relationship(
        type="EMPLOYED_BY",
        start_node_label="Person",
        end_node_label="Company",
        key_property=Property(
            name="employmentId", type="STRING", description="Employment record ID"
        ),
        properties=[],
    )
    start_key_prop = Property(name="personId", type="STRING", description="Person ID")
    end_key_prop = Property(name="companyId", type="STRING", description="Company ID")

    result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

    expected = """class EmployedBy(BaseModel):
    relationship_type: ClassVar[str] = "EMPLOYED_BY"
    start_node_label: ClassVar[str] = "Person"
    end_node_label: ClassVar[str] = "Company"
    pattern: ClassVar[str] = \"(:Person)-[:EMPLOYED_BY]->(:Company)\"

    start_node_Person_personId: str = Field(..., description="Person ID")
    end_node_Company_companyId: str = Field(..., description="Company ID")
    employmentId: str = Field(..., description="Employment record ID")""".strip()
    assert result.strip() == expected


def test_relationship_to_pydantic_model_str_with_properties():
    """Test Relationship.to_pydantic_model_str() with relationship properties - validates exact format."""
    relationship = Relationship(
        type="REVIEWED",
        start_node_label="Customer",
        end_node_label="Product",
        properties=[
            Property(name="rating", type="INTEGER", description="Star rating"),
            Property(name="comment", type="STRING", description="Review text"),
            Property(name="reviewDate", type="DATE", description="Date of review"),
        ],
    )
    start_key_prop = Property(
        name="customerId", type="STRING", description="Customer ID"
    )
    end_key_prop = Property(name="productId", type="STRING", description="Product ID")

    result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

    expected = """class Reviewed(BaseModel):
    relationship_type: ClassVar[str] = "REVIEWED"
    start_node_label: ClassVar[str] = "Customer"
    end_node_label: ClassVar[str] = "Product"
    pattern: ClassVar[str] = \"(:Customer)-[:REVIEWED]->(:Product)\"

    start_node_Customer_customerId: str = Field(..., description="Customer ID")
    end_node_Product_productId: str = Field(..., description="Product ID")
    rating: int = Field(..., description="Star rating")
    comment: str = Field(..., description="Review text")
    reviewDate: datetime = Field(..., description="Date of review")""".strip()
    assert result.strip() == expected


def test_relationship_to_pydantic_model_str_with_key_and_properties():
    """Test Relationship.to_pydantic_model_str() with both key property and properties - validates exact format."""
    relationship = Relationship(
        type="PURCHASED",
        start_node_label="User",
        end_node_label="Item",
        key_property=Property(
            name="transactionId", type="STRING", description="Transaction ID"
        ),
        properties=[
            Property(name="quantity", type="INTEGER", description="Quantity purchased"),
            Property(name="totalPrice", type="FLOAT", description="Total price"),
            Property(
                name="purchaseDate", type="DATETIME", description="Purchase timestamp"
            ),
        ],
    )
    start_key_prop = Property(name="userId", type="STRING", description="User ID")
    end_key_prop = Property(name="itemId", type="STRING", description="Item ID")

    result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

    expected = """class Purchased(BaseModel):
    relationship_type: ClassVar[str] = "PURCHASED"
    start_node_label: ClassVar[str] = "User"
    end_node_label: ClassVar[str] = "Item"
    pattern: ClassVar[str] = \"(:User)-[:PURCHASED]->(:Item)\"

    start_node_User_userId: str = Field(..., description="User ID")
    end_node_Item_itemId: str = Field(..., description="Item ID")
    transactionId: str = Field(..., description="Transaction ID")
    quantity: int = Field(..., description="Quantity purchased")
    totalPrice: float = Field(..., description="Total price")
    purchaseDate: datetime = Field(..., description="Purchase timestamp")""".strip()
    assert result.strip() == expected


def test_relationship_to_pydantic_model_str_screaming_to_pascal():
    """Test Relationship.to_pydantic_model_str() converts SCREAMING_SNAKE_CASE to PascalCase - validates exact format."""
    relationship = Relationship(
        type="BELONGS_TO_GROUP",
        start_node_label="Member",
        end_node_label="Group",
        properties=[],
    )
    start_key_prop = Property(name="memberId", type="STRING", description="Member ID")
    end_key_prop = Property(name="groupId", type="STRING", description="Group ID")

    result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

    expected = """class BelongsToGroup(BaseModel):
    relationship_type: ClassVar[str] = "BELONGS_TO_GROUP"
    start_node_label: ClassVar[str] = "Member"
    end_node_label: ClassVar[str] = "Group"
    pattern: ClassVar[str] = \"(:Member)-[:BELONGS_TO_GROUP]->(:Group)\"

    start_node_Member_memberId: str = Field(..., description="Member ID")
    end_node_Group_groupId: str = Field(..., description="Group ID")"""
    assert result == expected


def test_relationship_to_pydantic_model_str_different_node_types():
    """Test Relationship.to_pydantic_model_str() with different start and end node types - validates exact format."""
    relationship = Relationship(
        type="LIVES_IN",
        start_node_label="Person",
        end_node_label="City",
        properties=[Property(name="since", type="DATE", description="Resident since")],
    )
    start_key_prop = Property(name="personId", type="STRING", description="Person ID")
    end_key_prop = Property(name="cityId", type="INTEGER", description="City ID")

    result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

    expected = """class LivesIn(BaseModel):
    relationship_type: ClassVar[str] = "LIVES_IN"
    start_node_label: ClassVar[str] = "Person"
    end_node_label: ClassVar[str] = "City"
    pattern: ClassVar[str] = \"(:Person)-[:LIVES_IN]->(:City)\"

    start_node_Person_personId: str = Field(..., description="Person ID")
    end_node_City_cityId: int = Field(..., description="City ID")
    since: datetime = Field(..., description="Resident since")""".strip()
    assert result.strip() == expected


def test_relationship_to_pydantic_model_str_self_referential():
    """Test Relationship.to_pydantic_model_str() with self-referential relationship - validates exact format."""
    relationship = Relationship(
        type="MANAGES",
        start_node_label="Employee",
        end_node_label="Employee",
        properties=[Property(name="since", type="DATE", description="Managing since")],
    )
    start_key_prop = Property(
        name="employeeId", type="STRING", description="Employee ID"
    )
    end_key_prop = Property(name="employeeId", type="STRING", description="Employee ID")

    result = relationship.to_pydantic_model_str(start_key_prop, end_key_prop)

    expected = """class Manages(BaseModel):
    relationship_type: ClassVar[str] = "MANAGES"
    start_node_label: ClassVar[str] = "Employee"
    end_node_label: ClassVar[str] = "Employee"
    pattern: ClassVar[str] = \"(:Employee)-[:MANAGES]->(:Employee)\"

    start_node_Employee_employeeId: str = Field(..., description="Employee ID")
    end_node_Employee_employeeId: str = Field(..., description="Employee ID")
    since: datetime = Field(..., description="Managing since")""".strip()
    assert result.strip() == expected


def test_data_model_to_pydantic_model_str_nodes_only():
    """Test DataModel.to_pydantic_model_str() with nodes only - validates exact format."""
    data_model = DataModel(
        nodes=[
            Node(
                label="User",
                key_property=Property(
                    name="userId", type="STRING", description="User ID"
                ),
                properties=[
                    Property(name="name", type="STRING", description="User name"),
                ],
            ),
            Node(
                label="Product",
                key_property=Property(
                    name="productId", type="STRING", description="Product ID"
                ),
                properties=[],
            ),
        ],
        relationships=[],
    )

    result = data_model.to_pydantic_model_str()

    expected = """from pydantic import BaseModel, Field
from typing import ClassVar


class User(BaseModel):
    node_label: ClassVar[str] = "User"

    userId: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")


class Product(BaseModel):
    node_label: ClassVar[str] = "Product"

    productId: str = Field(..., description="Product ID")"""
    assert result == expected


def test_data_model_to_pydantic_model_str_with_relationships():
    """Test DataModel.to_pydantic_model_str() with nodes and relationships - validates exact format."""
    data_model = DataModel(
        nodes=[
            Node(
                label="Person",
                key_property=Property(
                    name="personId", type="STRING", description="Person ID"
                ),
                properties=[],
            ),
            Node(
                label="Company",
                key_property=Property(
                    name="companyId", type="STRING", description="Company ID"
                ),
                properties=[],
            ),
        ],
        relationships=[
            Relationship(
                type="WORKS_FOR",
                start_node_label="Person",
                end_node_label="Company",
                properties=[
                    Property(
                        name="since", type="DATE", description="Employment start date"
                    ),
                ],
            ),
        ],
    )

    result = data_model.to_pydantic_model_str()

    expected = """from pydantic import BaseModel, Field
from datetime import datetime
from typing import ClassVar


class Person(BaseModel):
    node_label: ClassVar[str] = "Person"

    personId: str = Field(..., description="Person ID")


class Company(BaseModel):
    node_label: ClassVar[str] = "Company"

    companyId: str = Field(..., description="Company ID")


class WorksFor(BaseModel):
    relationship_type: ClassVar[str] = "WORKS_FOR"
    start_node_label: ClassVar[str] = "Person"
    end_node_label: ClassVar[str] = "Company"
    pattern: ClassVar[str] = \"(:Person)-[:WORKS_FOR]->(:Company)\"

    start_node_Person_personId: str = Field(..., description="Person ID")
    end_node_Company_companyId: str = Field(..., description="Company ID")
    since: datetime = Field(..., description="Employment start date")""".strip()
    assert result.strip() == expected


def test_data_model_to_pydantic_model_str_complex():
    """Test DataModel.to_pydantic_model_str() with complex model - validates exact format."""
    data_model = DataModel(
        nodes=[
            Node(
                label="User",
                key_property=Property(
                    name="userId", type="STRING", description="User ID"
                ),
                properties=[
                    Property(name="email", type="STRING", description="Email address"),
                    Property(name="age", type="INTEGER", description="User age"),
                ],
            ),
            Node(
                label="Post",
                key_property=Property(
                    name="postId", type="STRING", description="Post ID"
                ),
                properties=[
                    Property(name="title", type="STRING", description="Post title"),
                    Property(
                        name="createdAt", type="DATETIME", description="Creation time"
                    ),
                ],
            ),
        ],
        relationships=[
            Relationship(
                type="AUTHORED",
                start_node_label="User",
                end_node_label="Post",
                key_property=Property(
                    name="authorshipId", type="STRING", description="Authorship ID"
                ),
                properties=[
                    Property(
                        name="publishedAt",
                        type="DATETIME",
                        description="Publish timestamp",
                    ),
                ],
            ),
            Relationship(
                type="LIKES",
                start_node_label="User",
                end_node_label="Post",
                properties=[],
            ),
        ],
    )

    result = data_model.to_pydantic_model_str()

    expected = """from pydantic import BaseModel, Field
from datetime import datetime
from typing import ClassVar


class User(BaseModel):
    node_label: ClassVar[str] = "User"

    userId: str = Field(..., description="User ID")
    email: str = Field(..., description="Email address")
    age: int = Field(..., description="User age")


class Post(BaseModel):
    node_label: ClassVar[str] = "Post"

    postId: str = Field(..., description="Post ID")
    title: str = Field(..., description="Post title")
    createdAt: datetime = Field(..., description="Creation time")


class Authored(BaseModel):
    relationship_type: ClassVar[str] = "AUTHORED"
    start_node_label: ClassVar[str] = "User"
    end_node_label: ClassVar[str] = "Post"
    pattern: ClassVar[str] = \"(:User)-[:AUTHORED]->(:Post)\"

    start_node_User_userId: str = Field(..., description="User ID")
    end_node_Post_postId: str = Field(..., description="Post ID")
    authorshipId: str = Field(..., description="Authorship ID")
    publishedAt: datetime = Field(..., description="Publish timestamp")



class Likes(BaseModel):
    relationship_type: ClassVar[str] = "LIKES"
    start_node_label: ClassVar[str] = "User"
    end_node_label: ClassVar[str] = "Post"
    pattern: ClassVar[str] = \"(:User)-[:LIKES]->(:Post)\"

    start_node_User_userId: str = Field(..., description="User ID")
    end_node_Post_postId: str = Field(..., description="Post ID")""".strip()
    assert result.strip() == expected


def test_data_model_to_pydantic_model_str_empty():
    """Test DataModel.to_pydantic_model_str() with empty model - validates exact format."""
    data_model = DataModel(nodes=[], relationships=[])

    result = data_model.to_pydantic_model_str()

    expected = """from pydantic import BaseModel, Field
from typing import ClassVar


"""
    assert result == expected


# Tests for Neo4j GraphRAG Python Package export methods


def test_property_to_neo4j_graphrag_python_package_property_dict_required():
    """Test Property.to_neo4j_graphrag_python_package_property_dict() with required property."""
    prop = Property(name="id", type="STRING", description="The ID of the person")
    result = prop.to_neo4j_graphrag_python_package_property_dict(required_property=True)

    expected = {
        "name": "id",
        "type": "STRING",
        "description": "The ID of the person",
        "required": True,
    }
    assert result == expected


def test_property_to_neo4j_graphrag_python_package_property_dict_not_required():
    """Test Property.to_neo4j_graphrag_python_package_property_dict() with non-required property."""
    prop = Property(name="name", type="STRING", description="The name")
    result = prop.to_neo4j_graphrag_python_package_property_dict(
        required_property=False
    )

    expected = {
        "name": "name",
        "type": "STRING",
        "description": "The name",
        "required": False,
    }
    assert result == expected


def test_property_to_neo4j_graphrag_python_package_property_dict_no_description():
    """Test Property.to_neo4j_graphrag_python_package_property_dict() without description."""
    prop = Property(name="age", type="INTEGER")
    result = prop.to_neo4j_graphrag_python_package_property_dict(
        required_property=False
    )

    expected = {"name": "age", "type": "INTEGER", "description": "", "required": False}
    assert result == expected


def test_property_to_neo4j_graphrag_python_package_property_dict_various_types():
    """Test Property.to_neo4j_graphrag_python_package_property_dict() with various types."""
    # FLOAT type
    prop_float = Property(name="amount", type="FLOAT", description="Dollar amount")
    result_float = prop_float.to_neo4j_graphrag_python_package_property_dict(
        required_property=True
    )
    assert result_float["type"] == "FLOAT"

    # BOOLEAN type
    prop_bool = Property(name="active", type="BOOLEAN", description="Is active")
    result_bool = prop_bool.to_neo4j_graphrag_python_package_property_dict(
        required_property=False
    )
    assert result_bool["type"] == "BOOLEAN"

    # DATETIME type converts to ZONED_DATETIME
    prop_datetime = Property(
        name="createdAt", type="DATETIME", description="Created at"
    )
    result_datetime = prop_datetime.to_neo4j_graphrag_python_package_property_dict(
        required_property=False
    )
    assert result_datetime["type"] == "ZONED_DATETIME"


def test_node_to_neo4j_graphrag_python_package_node_dict_simple():
    """Test Node.to_neo4j_graphrag_python_package_node_dict() with simple node."""
    node = Node(
        label="Person",
        key_property=Property(name="id", type="STRING", description="Person ID"),
        properties=[],
    )
    result = node.to_neo4j_graphrag_python_package_node_dict()

    expected = {
        "label": "Person",
        "description": "",
        "properties": [
            {
                "name": "id",
                "type": "STRING",
                "description": "Person ID",
                "required": True,
            }
        ],
    }
    assert result == expected


def test_node_to_neo4j_graphrag_python_package_node_dict_with_metadata():
    """Test Node.to_neo4j_graphrag_python_package_node_dict() ignores metadata."""
    node = Node(
        label="House",
        key_property=Property(name="name", type="STRING"),
        metadata={"description": "Family the person belongs to"},
        properties=[],
    )
    result = node.to_neo4j_graphrag_python_package_node_dict()

    expected = {
        "label": "House",
        "description": "",
        "properties": [
            {"name": "name", "type": "STRING", "description": "", "required": True}
        ],
    }
    assert result == expected


def test_node_to_neo4j_graphrag_python_package_node_dict_with_properties():
    """Test Node.to_neo4j_graphrag_python_package_node_dict() with additional properties."""
    node = Node(
        label="Planet",
        key_property=Property(
            name="name", type="STRING", description="Name of the planet"
        ),
        properties=[
            Property(
                name="weather", type="STRING", description="Weather of the planet"
            ),
        ],
    )
    result = node.to_neo4j_graphrag_python_package_node_dict()

    expected = {
        "label": "Planet",
        "description": "",
        "properties": [
            {
                "name": "name",
                "type": "STRING",
                "description": "Name of the planet",
                "required": True,
            },
            {
                "name": "weather",
                "type": "STRING",
                "description": "Weather of the planet",
                "required": False,
            },
        ],
    }
    assert result == expected


def test_node_to_neo4j_graphrag_python_package_node_dict_multiple_properties():
    """Test Node.to_neo4j_graphrag_python_package_node_dict() with multiple properties."""
    node = Node(
        label="Product",
        key_property=Property(
            name="productId", type="STRING", description="Product ID"
        ),
        properties=[
            Property(name="name", type="STRING", description="Product name"),
            Property(name="price", type="FLOAT", description="Product price"),
            Property(name="inStock", type="BOOLEAN", description="In stock flag"),
        ],
    )
    result = node.to_neo4j_graphrag_python_package_node_dict()

    expected = {
        "label": "Product",
        "description": "",
        "properties": [
            {
                "name": "productId",
                "type": "STRING",
                "description": "Product ID",
                "required": True,
            },
            {
                "name": "name",
                "type": "STRING",
                "description": "Product name",
                "required": False,
            },
            {
                "name": "price",
                "type": "FLOAT",
                "description": "Product price",
                "required": False,
            },
            {
                "name": "inStock",
                "type": "BOOLEAN",
                "description": "In stock flag",
                "required": False,
            },
        ],
    }
    assert result == expected


def test_relationship_to_neo4j_graphrag_python_package_relationship_dict_simple():
    """Test Relationship.to_neo4j_graphrag_python_package_relationship_dict() with simple relationship."""
    relationship = Relationship(
        type="PARENT_OF",
        start_node_label="Person",
        end_node_label="Person",
        properties=[],
    )
    result = relationship.to_neo4j_graphrag_python_package_relationship_dict()

    expected = {
        "label": "PARENT_OF",
        "description": "",
        "properties": [],
    }
    assert result == expected


def test_relationship_to_neo4j_graphrag_python_package_relationship_dict_with_metadata():
    """Test Relationship.to_neo4j_graphrag_python_package_relationship_dict() ignores metadata."""
    relationship = Relationship(
        type="HEIR_OF",
        start_node_label="Person",
        end_node_label="House",
        metadata={
            "description": "Used for inheritor relationship between father and sons"
        },
        properties=[],
    )
    result = relationship.to_neo4j_graphrag_python_package_relationship_dict()

    expected = {
        "label": "HEIR_OF",
        "description": "",
        "properties": [],
    }
    assert result == expected


def test_relationship_to_neo4j_graphrag_python_package_relationship_dict_with_properties():
    """Test Relationship.to_neo4j_graphrag_python_package_relationship_dict() with properties."""
    relationship = Relationship(
        type="RULES",
        start_node_label="House",
        end_node_label="Planet",
        properties=[
            Property(
                name="fromYear",
                type="INTEGER",
                description="Year from which the rules are in effect",
            ),
        ],
    )
    result = relationship.to_neo4j_graphrag_python_package_relationship_dict()

    expected = {
        "label": "RULES",
        "description": "",
        "properties": [
            {
                "name": "fromYear",
                "type": "INTEGER",
                "description": "Year from which the rules are in effect",
                "required": False,
            }
        ],
    }
    assert result == expected


def test_relationship_to_neo4j_graphrag_python_package_relationship_dict_with_key_property():
    """Test Relationship.to_neo4j_graphrag_python_package_relationship_dict() with key property."""
    relationship = Relationship(
        type="RATED",
        start_node_label="User",
        end_node_label="Movie",
        key_property=Property(name="ratingId", type="STRING", description="Rating ID"),
        properties=[
            Property(name="score", type="FLOAT", description="Rating score"),
        ],
    )
    result = relationship.to_neo4j_graphrag_python_package_relationship_dict()

    expected = {
        "label": "RATED",
        "description": "",
        "properties": [
            {
                "name": "ratingId",
                "type": "STRING",
                "description": "Rating ID",
                "required": True,
            },
            {
                "name": "score",
                "type": "FLOAT",
                "description": "Rating score",
                "required": False,
            },
        ],
    }
    assert result == expected


def test_relationship_to_neo4j_graphrag_python_package_relationship_pattern_simple():
    """Test Relationship.to_neo4j_graphrag_python_package_relationship_pattern() with simple relationship."""
    relationship = Relationship(
        type="LIVES_IN",
        start_node_label="Person",
        end_node_label="City",
    )
    result = relationship.to_neo4j_graphrag_python_package_relationship_pattern()

    expected = ("Person", "LIVES_IN", "City")
    assert result == expected


def test_relationship_to_neo4j_graphrag_python_package_relationship_pattern_various():
    """Test Relationship.to_neo4j_graphrag_python_package_relationship_pattern() with various relationships."""
    # Self-referential
    rel1 = Relationship(
        type="PARENT_OF", start_node_label="Person", end_node_label="Person"
    )
    assert rel1.to_neo4j_graphrag_python_package_relationship_pattern() == (
        "Person",
        "PARENT_OF",
        "Person",
    )

    # Different nodes
    rel2 = Relationship(
        type="HEIR_OF", start_node_label="Person", end_node_label="House"
    )
    assert rel2.to_neo4j_graphrag_python_package_relationship_pattern() == (
        "Person",
        "HEIR_OF",
        "House",
    )

    # Another combination
    rel3 = Relationship(type="RULES", start_node_label="House", end_node_label="Planet")
    assert rel3.to_neo4j_graphrag_python_package_relationship_pattern() == (
        "House",
        "RULES",
        "Planet",
    )


def test_data_model_to_neo4j_graphrag_python_package_schema_empty():
    """Test DataModel.to_neo4j_graphrag_python_package_schema() with empty model."""
    data_model = DataModel(nodes=[], relationships=[])
    result = data_model.to_neo4j_graphrag_python_package_schema()

    expected = {
        "schema": {
            "node_types": [],
            "relationship_types": [],
            "patterns": [],
        }
    }
    assert result == expected


def test_data_model_to_neo4j_graphrag_python_package_schema_simple():
    """Test DataModel.to_neo4j_graphrag_python_package_schema() with simple model."""
    data_model = DataModel(
        nodes=[
            Node(
                label="Person",
                key_property=Property(name="id", type="STRING"),
                properties=[],
            ),
            Node(
                label="City",
                key_property=Property(name="name", type="STRING"),
                properties=[],
            ),
        ],
        relationships=[
            Relationship(
                type="LIVES_IN",
                start_node_label="Person",
                end_node_label="City",
                properties=[],
            )
        ],
    )
    result = data_model.to_neo4j_graphrag_python_package_schema()

    expected = {
        "schema": {
            "node_types": [
                {
                    "label": "Person",
                    "description": "",
                    "properties": [
                        {
                            "name": "id",
                            "type": "STRING",
                            "description": "",
                            "required": True,
                        }
                    ],
                },
                {
                    "label": "City",
                    "description": "",
                    "properties": [
                        {
                            "name": "name",
                            "type": "STRING",
                            "description": "",
                            "required": True,
                        }
                    ],
                },
            ],
            "relationship_types": [
                {
                    "label": "LIVES_IN",
                    "description": "",
                    "properties": [],
                }
            ],
            "patterns": [("Person", "LIVES_IN", "City")],
        }
    }
    assert result == expected


def test_data_model_to_neo4j_graphrag_python_package_schema_complex():
    """Test DataModel.to_neo4j_graphrag_python_package_schema() with complex model."""
    data_model = DataModel(
        nodes=[
            Node(
                label="Person",
                key_property=Property(name="id", type="STRING"),
                properties=[],
            ),
            Node(
                label="House",
                key_property=Property(name="name", type="STRING"),
                properties=[],
            ),
            Node(
                label="Planet",
                key_property=Property(
                    name="name", type="STRING", description="Name of the planet"
                ),
                properties=[
                    Property(
                        name="weather",
                        type="STRING",
                        description="Weather of the planet",
                    ),
                ],
            ),
        ],
        relationships=[
            Relationship(
                type="PARENT_OF",
                start_node_label="Person",
                end_node_label="Person",
                properties=[],
            ),
            Relationship(
                type="HEIR_OF",
                start_node_label="Person",
                end_node_label="House",
                properties=[],
            ),
            Relationship(
                type="RULES",
                start_node_label="House",
                end_node_label="Planet",
                properties=[
                    Property(
                        name="fromYear",
                        type="INTEGER",
                        description="Year from which the rules are in effect",
                    ),
                ],
            ),
        ],
    )
    result = data_model.to_neo4j_graphrag_python_package_schema()

    expected = {
        "schema": {
            "node_types": [
                {
                    "label": "Person",
                    "description": "",
                    "properties": [
                        {
                            "name": "id",
                            "type": "STRING",
                            "description": "",
                            "required": True,
                        }
                    ],
                },
                {
                    "label": "House",
                    "description": "",
                    "properties": [
                        {
                            "name": "name",
                            "type": "STRING",
                            "description": "",
                            "required": True,
                        }
                    ],
                },
                {
                    "label": "Planet",
                    "description": "",
                    "properties": [
                        {
                            "name": "name",
                            "type": "STRING",
                            "description": "Name of the planet",
                            "required": True,
                        },
                        {
                            "name": "weather",
                            "type": "STRING",
                            "description": "Weather of the planet",
                            "required": False,
                        },
                    ],
                },
            ],
            "relationship_types": [
                {
                    "label": "PARENT_OF",
                    "description": "",
                    "properties": [],
                },
                {
                    "label": "HEIR_OF",
                    "description": "",
                    "properties": [],
                },
                {
                    "label": "RULES",
                    "description": "",
                    "properties": [
                        {
                            "name": "fromYear",
                            "type": "INTEGER",
                            "description": "Year from which the rules are in effect",
                            "required": False,
                        }
                    ],
                },
            ],
            "patterns": [
                ("Person", "PARENT_OF", "Person"),
                ("Person", "HEIR_OF", "House"),
                ("House", "RULES", "Planet"),
            ],
        }
    }
    assert result == expected


# Tests for Neo4j GraphRAG Python Package from methods


def test_property_from_neo4j_graphrag_python_package_property_dict():
    """Test Property.from_neo4j_graphrag_python_package_property_dict()."""
    property_dict = {
        "name": "id",
        "type": "STRING",
        "description": "The ID of the person",
        "required": True,
    }
    result = Property.from_neo4j_graphrag_python_package_property_dict(property_dict)

    assert result.name == "id"
    assert result.type == "STRING"
    assert result.description == "The ID of the person"


def test_property_from_neo4j_graphrag_python_package_property_dict_empty_description():
    """Test Property.from_neo4j_graphrag_python_package_property_dict() with empty description."""
    property_dict = {
        "name": "id",
        "type": "STRING",
        "description": "",
        "required": True,
    }
    result = Property.from_neo4j_graphrag_python_package_property_dict(property_dict)

    assert result.name == "id"
    assert result.type == "STRING"
    assert result.description is None


def test_property_from_neo4j_graphrag_python_package_property_dict_with_underscores():
    """Test Property.from_neo4j_graphrag_python_package_property_dict() converts underscores to spaces."""
    property_dict = {
        "name": "createdAt",
        "type": "ZONED_DATETIME",
        "description": "Creation timestamp",
        "required": False,
    }
    result = Property.from_neo4j_graphrag_python_package_property_dict(property_dict)

    assert result.name == "createdAt"
    assert result.type == "ZONED DATETIME"
    assert result.description == "Creation timestamp"


def test_node_from_neo4j_graphrag_python_package_node_dict():
    """Test Node.from_neo4j_graphrag_python_package_node_dict()."""
    node_dict = {
        "label": "Person",
        "description": "",
        "properties": [
            {
                "name": "id",
                "type": "STRING",
                "description": "Person ID",
                "required": True,
            },
            {
                "name": "name",
                "type": "STRING",
                "description": "Name",
                "required": False,
            },
        ],
    }
    result = Node.from_neo4j_graphrag_python_package_node_dict(node_dict)

    assert result.label == "Person"
    assert result.key_property.name == "id"
    assert result.key_property.type == "STRING"
    assert result.key_property.description == "Person ID"
    assert len(result.properties) == 1
    assert result.properties[0].name == "name"


def test_relationship_from_neo4j_graphrag_python_package_relationship_dict():
    """Test Relationship.from_neo4j_graphrag_python_package_relationship_dict()."""
    relationship_dict = {
        "label": "LIVES_IN",
        "description": "",
        "properties": [
            {
                "name": "since",
                "type": "DATE",
                "description": "Since when",
                "required": False,
            }
        ],
    }
    result = Relationship.from_neo4j_graphrag_python_package_relationship_dict(
        relationship_dict, "Person", "City"
    )

    assert result.type == "LIVES_IN"
    assert result.start_node_label == "Person"
    assert result.end_node_label == "City"
    assert len(result.properties) == 1
    assert result.properties[0].name == "since"
    assert result.key_property is None


def test_relationship_from_neo4j_graphrag_python_package_relationship_dict_with_key():
    """Test Relationship.from_neo4j_graphrag_python_package_relationship_dict() with key property."""
    relationship_dict = {
        "label": "RATED",
        "description": "",
        "properties": [
            {
                "name": "ratingId",
                "type": "STRING",
                "description": "Rating ID",
                "required": True,
            },
            {
                "name": "score",
                "type": "FLOAT",
                "description": "Score",
                "required": False,
            },
        ],
    }
    result = Relationship.from_neo4j_graphrag_python_package_relationship_dict(
        relationship_dict, "User", "Movie"
    )

    assert result.type == "RATED"
    assert result.start_node_label == "User"
    assert result.end_node_label == "Movie"
    assert result.key_property is not None
    assert result.key_property.name == "ratingId"
    assert len(result.properties) == 1
    assert result.properties[0].name == "score"


def test_data_model_from_neo4j_graphrag_python_package_schema():
    """Test DataModel.from_neo4j_graphrag_python_package_schema()."""
    schema_dict = {
        "schema": {
            "node_types": [
                {
                    "label": "Person",
                    "description": "",
                    "properties": [
                        {
                            "name": "id",
                            "type": "STRING",
                            "description": "",
                            "required": True,
                        }
                    ],
                },
                {
                    "label": "City",
                    "description": "",
                    "properties": [
                        {
                            "name": "name",
                            "type": "STRING",
                            "description": "",
                            "required": True,
                        }
                    ],
                },
            ],
            "relationship_types": [
                {"label": "LIVES_IN", "description": "", "properties": []}
            ],
            "patterns": [("Person", "LIVES_IN", "City")],
        }
    }
    result = DataModel.from_neo4j_graphrag_python_package_schema(schema_dict)

    assert len(result.nodes) == 2
    assert result.nodes[0].label == "Person"
    assert result.nodes[1].label == "City"
    assert len(result.relationships) == 1
    assert result.relationships[0].type == "LIVES_IN"
    assert result.relationships[0].start_node_label == "Person"
    assert result.relationships[0].end_node_label == "City"


def test_data_model_neo4j_graphrag_python_package_schema_round_trip():
    """Test round-trip conversion of DataModel to/from Neo4j GraphRAG Python Package schema."""
    original_model = DataModel(
        nodes=[
            Node(
                label="Person",
                key_property=Property(
                    name="id", type="STRING", description="Person ID"
                ),
                properties=[
                    Property(name="name", type="STRING", description="Person name")
                ],
            ),
            Node(
                label="City",
                key_property=Property(
                    name="name", type="STRING", description="City name"
                ),
                properties=[],
            ),
        ],
        relationships=[
            Relationship(
                type="LIVES_IN",
                start_node_label="Person",
                end_node_label="City",
                properties=[
                    Property(name="since", type="INTEGER", description="Year moved")
                ],
            )
        ],
    )

    # Convert to schema and back
    schema = original_model.to_neo4j_graphrag_python_package_schema()
    restored_model = DataModel.from_neo4j_graphrag_python_package_schema(schema)

    # Check nodes
    assert len(restored_model.nodes) == len(original_model.nodes)
    assert {n.label for n in restored_model.nodes} == {
        n.label for n in original_model.nodes
    }

    # Check person node
    person_node = next(n for n in restored_model.nodes if n.label == "Person")
    assert person_node.key_property.name == "id"
    assert len(person_node.properties) == 1
    assert person_node.properties[0].name == "name"

    # Check relationships
    assert len(restored_model.relationships) == 1
    assert restored_model.relationships[0].type == "LIVES_IN"
    assert restored_model.relationships[0].start_node_label == "Person"
    assert restored_model.relationships[0].end_node_label == "City"
    assert len(restored_model.relationships[0].properties) == 1
    assert restored_model.relationships[0].properties[0].name == "since"
