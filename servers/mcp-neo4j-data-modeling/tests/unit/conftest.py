import argparse
import os
from typing import Any
from unittest.mock import Mock

import pytest
from fastmcp.server import FastMCP

from mcp_neo4j_data_modeling.data_model import DataModel, Node, Property, Relationship
from mcp_neo4j_data_modeling.server import create_mcp_server


@pytest.fixture
def clean_env():
    """Fixture to clean environment variables before each test."""
    env_vars = [
        "NEO4J_TRANSPORT",
        "NEO4J_MCP_SERVER_HOST",
        "NEO4J_MCP_SERVER_PORT",
        "NEO4J_MCP_SERVER_PATH",
        "NEO4J_MCP_SERVER_ALLOW_ORIGINS",
        "NEO4J_MCP_SERVER_ALLOWED_HOSTS",
        "NEO4J_NAMESPACE",
    ]
    # Store original values
    original_values = {}
    for var in env_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        os.environ[var] = value


@pytest.fixture
def args_factory():
    """Factory fixture to create argparse.Namespace objects with default None values."""

    def _create_args(**kwargs):
        defaults = {
            "transport": None,
            "server_host": None,
            "server_port": None,
            "server_path": None,
            "allow_origins": None,
            "allowed_hosts": None,
            "namespace": None,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    return _create_args


@pytest.fixture
def mock_logger():
    """Mock logger for testing logging behavior."""
    return Mock()


@pytest.fixture
def test_mcp_server() -> FastMCP:
    """Create an MCP server instance for testing."""
    return create_mcp_server()


@pytest.fixture(scope="function")
def arrows_data_model_dict() -> dict[str, Any]:
    return {
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
        },
        "nodes": [
            {
                "id": "n0",
                "position": {"x": 105.3711141386136, "y": -243.80584874322315},
                "caption": "",
                "labels": ["Person"],
                "properties": {"name": "STRING | KEY", "age": "INTEGER"},
                "style": {},
            },
            {
                "id": "n1",
                "position": {"x": 142.1337531280864, "y": 50},
                "caption": "",
                "labels": ["Address"],
                "properties": {
                    "fullAddress": "STRING | KEY",
                },
                "style": {},
            },
            {
                "id": "n2",
                "position": {"x": 484.55353547755726, "y": -279.86295267473423},
                "caption": "",
                "labels": ["Pet"],
                "properties": {"name": "STRING | KEY", "kind": "STRING"},
                "style": {},
            },
            {
                "id": "n3",
                "position": {"x": 675, "y": 50},
                "caption": "",
                "labels": ["Toy"],
                "properties": {"name": "STRING | KEY", "kind": "STRING"},
                "style": {},
            },
        ],
        "relationships": [
            {
                "id": "n0",
                "fromId": "n0",
                "toId": "n1",
                "type": "HAS_ADDRESS",
                "properties": {},
                "style": {},
            },
            {
                "id": "n1",
                "fromId": "n0",
                "toId": "n0",
                "type": "KNOWS",
                "properties": {},
                "style": {},
            },
            {
                "id": "n2",
                "fromId": "n0",
                "toId": "n2",
                "type": "HAS_PET",
                "properties": {},
                "style": {},
            },
            {
                "id": "n3",
                "fromId": "n2",
                "toId": "n3",
                "type": "PLAYS_WITH",
                "properties": {},
                "style": {},
            },
        ],
    }


@pytest.fixture(scope="function")
def valid_data_model() -> DataModel:
    "A simple valid data model with a Person node, a Place node, and a LIVES_IN relationship."
    nodes = [
        Node(
            label="Person",
            key_property=Property(
                name="id", type="STRING", description="Unique identifier"
            ),
            properties=[
                Property(name="name", type="STRING", description="Name of the person"),
                Property(name="age", type="INTEGER", description="Age of the person"),
            ],
        ),
        Node(
            label="Place",
            key_property=Property(
                name="id", type="STRING", description="Unique identifier"
            ),
            properties=[
                Property(name="name", type="STRING", description="Name of the place")
            ],
        ),
    ]

    relationship = Relationship(
        type="LIVES_IN",
        start_node_label="Person",
        end_node_label="Place",
    )
    return DataModel(nodes=nodes, relationships=[relationship])
