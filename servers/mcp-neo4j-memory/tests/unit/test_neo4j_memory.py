"""Unit tests for Neo4j Memory models, focusing on regex validation for type and relationType fields."""

import pytest
from pydantic import ValidationError

from mcp_neo4j_memory.neo4j_memory import Entity, Relation


# Valid type/relationType values that should pass validation
VALID_TYPES = [
    # Examples from requirements
    "test",
    "Test",
    "Testing_test",
    "t3st1ng___",
    "__test__",
    "TEST_REL",
    "test_rel",
    "TestRel",
    "testRel",
    "t3stRel",
    "T3st_R3L",
    # Common use cases
    "person",
    "company",
    "location",
    "concept",
    "event",
    "WORKS_AT",
    "LIVES_IN",
    "MANAGES",
    "COLLABORATES_WITH",
    "LOCATED_IN",
    # Edge cases - single characters
    "a",
    "_",
    # Edge cases - underscores and numbers
    "_private",
    "Type123",
    "CamelCase",
    "snake_case",
    "UPPER_CASE",
    "MixedCase_123",
    "___triple_underscore",
    "type___with___many___underscores",
    "___private_type",
    "public_type___",
    "a123456789",
    "_0123456789",
    "Type99999",
    # Case variations
    "lowercase",
    "UPPERCASE",
    "MixedCase",
    "camelCase",
    "SCREAMING_SNAKE",
]

# Invalid type/relationType values that should fail validation
INVALID_TYPES = [
    # Injection attempts from requirements
    ("KNOWS`]->(to) WITH 1 as x MATCH (n) DETACH DELETE n //", "delete_all_injection"),
    ("X`]->(to) SET from.observations = ['HACKED BY ATTACKER'] //", "property_modification_injection"),
    ("Person` WITH 1 as x MATCH (n) DETACH DELETE n //", "label_injection"),
    ("X` WITH 1 as x MATCH (s:Secret) CREATE (e:Exfiltrated {data: s.name + ':' + s.value}) //", "exfiltration_injection"),
    # Additional injection patterns
    ("Type` MATCH (n) RETURN n //", "simple_match_injection"),
    ("Type`]->(x) DELETE x //", "relationship_delete_injection"),
    ("Type` SET n.admin = true //", "privilege_escalation_injection"),
    ("Type`]-(x) REMOVE x.password //", "property_removal_injection"),
    # Special characters that should be blocked
    ("type with spaces", "spaces"),
    ("type-with-dashes", "dashes"),
    ("type.with.dots", "dots"),
    ("type:with:colons", "colons"),
    ("type;with;semicolons", "semicolons"),
    ("type,with,commas", "commas"),
    ("type[brackets]", "brackets"),
    ("type{braces}", "braces"),
    ("type(parens)", "parens"),
    ("type'quote", "single_quote"),
    ('type"doublequote', "double_quote"),
    ("type`backtick", "backtick"),
    ("type/slash", "slash"),
    ("type\\backslash", "backslash"),
    ("type@at", "at_symbol"),
    ("type#hash", "hash"),
    ("type$dollar", "dollar"),
    ("type%percent", "percent"),
    ("type^caret", "caret"),
    ("type&ampersand", "ampersand"),
    ("type*asterisk", "asterisk"),
    ("type+plus", "plus"),
    ("type=equals", "equals"),
    ("type|pipe", "pipe"),
    ("type<less", "less_than"),
    ("type>greater", "greater_than"),
    ("type?question", "question_mark"),
    ("type!exclamation", "exclamation"),
    ("type~tilde", "tilde"),
    # Invalid starting characters
    ("123startwithnumber", "starts_with_number"),
    ("9type", "starts_with_digit"),
    ("0type", "starts_with_zero"),
    # Empty string
    ("", "empty_string"),
    # Whitespace variations
    ("type\ttab", "tab_character"),
    ("type\nnewline", "newline_character"),
    ("type\rcarriage", "carriage_return"),
    (" leadingspace", "leading_space"),
    ("trailingspace ", "trailing_space"),
    ("type\u00a0nbsp", "non_breaking_space"),
]

# Valid names with special characters (for entity names and relation source/target)
VALID_NAMES_WITH_SPECIAL_CHARS = [
    "John's Office",
    "Company (2024)",
    "Email: test@example.com",
    "Path/To/Resource",
    "Key=Value",
    "Name with spaces",
    "Name-with-dashes",
]


@pytest.mark.parametrize("type_value", VALID_TYPES)
def test_valid_entity_types(type_value):
    """Test that valid type values pass validation for Entity."""
    entity = Entity(
        name="TestEntity",
        type=type_value,
        observations=["Test observation"]
    )
    assert entity.type == type_value


@pytest.mark.parametrize("type_value", VALID_TYPES)
def test_valid_relation_types(type_value):
    """Test that valid relationType values pass validation for Relation."""
    relation = Relation(
        source="EntityA",
        target="EntityB",
        relationType=type_value
    )
    assert relation.relationType == type_value


@pytest.mark.parametrize("type_value,description", INVALID_TYPES)
def test_invalid_entity_types(type_value, description):
    """Test that invalid type values fail validation for Entity."""
    with pytest.raises(ValidationError) as exc_info:
        Entity(
            name="TestEntity",
            type=type_value,
            observations=["Test observation"]
        )
    # Verify that the validation error is related to the type field
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("type",) for error in errors), f"Failed to block {description}: {type_value}"


@pytest.mark.parametrize("type_value,description", INVALID_TYPES)
def test_invalid_relation_types(type_value, description):
    """Test that invalid relationType values fail validation for Relation."""
    with pytest.raises(ValidationError) as exc_info:
        Relation(
            source="EntityA",
            target="EntityB",
            relationType=type_value
        )
    # Verify that the validation error is related to the relationType field
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("relationType",) for error in errors), f"Failed to block {description}: {type_value}"


@pytest.mark.parametrize("name", VALID_NAMES_WITH_SPECIAL_CHARS)
def test_entity_name_with_special_chars(name):
    """Entity names should allow special characters since they're parameterized in queries."""
    entity = Entity(
        name=name,
        type="test_type",
        observations=["Test"]
    )
    assert entity.name == name


@pytest.mark.parametrize("name", VALID_NAMES_WITH_SPECIAL_CHARS)
def test_relation_source_with_special_chars(name):
    """Source names should allow special characters since they're parameterized in queries."""
    relation = Relation(
        source=name,
        target="TargetEntity",
        relationType="TEST_REL"
    )
    assert relation.source == name


@pytest.mark.parametrize("name", VALID_NAMES_WITH_SPECIAL_CHARS)
def test_relation_target_with_special_chars(name):
    """Target names should allow special characters since they're parameterized in queries."""
    relation = Relation(
        source="SourceEntity",
        target=name,
        relationType="TEST_REL"
    )
    assert relation.target == name


def test_entity_with_minimal_fields():
    """Test Entity creation with minimal valid fields."""
    entity = Entity(
        name="Test",
        type="a",
        observations=[]
    )
    assert entity.name == "Test"
    assert entity.type == "a"
    assert entity.observations == []


def test_relation_with_minimal_fields():
    """Test Relation creation with minimal valid fields."""
    relation = Relation(
        source="A",
        target="B",
        relationType="R"
    )
    assert relation.source == "A"
    assert relation.target == "B"
    assert relation.relationType == "R"
