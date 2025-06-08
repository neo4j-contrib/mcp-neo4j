#!/usr/bin/env python3
"""
Unit tests for basic functionality and imports in MCP Neo4j Memory.

These tests verify that the module structure, imports, data models, and tool definitions
work correctly without requiring external dependencies like Neo4j.
"""

import pytest
from mcp_neo4j_memory.core import (
    Neo4jMemory, Entity, Relation, KnowledgeGraph,
    ObservationAddition, ObservationDeletion, get_mcp_tools
)


class TestImports:
    """Test that all modules can be imported correctly."""

    def test_core_module_imports(self):
        """Test core module imports."""
        from mcp_neo4j_memory.core import Neo4jMemory, Entity, Relation, KnowledgeGraph
        from mcp_neo4j_memory.core import ObservationAddition, ObservationDeletion
        from mcp_neo4j_memory.core import get_mcp_tools, execute_tool

        # Verify classes are importable
        assert Neo4jMemory is not None
        assert Entity is not None
        assert Relation is not None

    def test_protocol_module_imports(self):
        """Test protocol module imports."""
        from mcp_neo4j_memory.protocols import run_stdio_server, run_sse_server

        # Verify functions are importable
        assert run_stdio_server is not None
        assert run_sse_server is not None

    def test_cli_module_import(self):
        """Test CLI module import."""
        from mcp_neo4j_memory.cli import main

        assert main is not None

    def test_main_package_import(self):
        """Test main package import."""
        from mcp_neo4j_memory import main as package_main

        assert package_main is not None


class TestDataModels:
    """Test that data models work correctly."""

    def test_entity_model(self):
        """Test Entity model functionality."""
        entity = Entity(name="Test Entity", type="TestType", observations=["Test observation"])

        assert entity.name == "Test Entity"
        assert entity.type == "TestType"
        assert len(entity.observations) == 1
        assert entity.observations[0] == "Test observation"

    def test_relation_model(self):
        """Test Relation model functionality."""
        relation = Relation(source="Entity A", target="Entity B", relationType="CONNECTS_TO")

        assert relation.source == "Entity A"
        assert relation.target == "Entity B"
        assert relation.relationType == "CONNECTS_TO"

    def test_knowledge_graph_model(self):
        """Test KnowledgeGraph model functionality."""
        entity = Entity(name="Test Entity", type="TestType", observations=["Test observation"])
        relation = Relation(source="Entity A", target="Entity B", relationType="CONNECTS_TO")

        graph = KnowledgeGraph(entities=[entity], relations=[relation])

        assert len(graph.entities) == 1
        assert len(graph.relations) == 1
        assert graph.entities[0].name == "Test Entity"
        assert graph.relations[0].relationType == "CONNECTS_TO"

    def test_observation_addition_model(self):
        """Test ObservationAddition model functionality."""
        obs_add = ObservationAddition(entityName="Test Entity", contents=["New observation"])

        assert obs_add.entityName == "Test Entity"
        assert len(obs_add.contents) == 1
        assert obs_add.contents[0] == "New observation"

    def test_observation_deletion_model(self):
        """Test ObservationDeletion model functionality."""
        obs_del = ObservationDeletion(entityName="Test Entity", observations=["Old observation"])

        assert obs_del.entityName == "Test Entity"
        assert len(obs_del.observations) == 1
        assert obs_del.observations[0] == "Old observation"


class TestMcpTools:
    """Test MCP tools definition and structure."""

    def test_get_mcp_tools_returns_tools(self):
        """Test that get_mcp_tools returns a list of tools."""
        tools = get_mcp_tools()

        assert len(tools) > 0, "No tools returned"
        assert isinstance(tools, list), "Tools should be returned as a list"

    def test_expected_tools_present(self):
        """Test that all expected tools are present."""
        tools = get_mcp_tools()
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "create_entities", "create_relations", "add_observations",
            "delete_entities", "delete_observations", "delete_relations",
            "read_graph", "search_nodes", "find_nodes", "open_nodes"
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Missing tool: {expected_tool}"

    def test_tool_count(self):
        """Test that we have the expected number of tools."""
        tools = get_mcp_tools()

        # We expect exactly 10 tools as defined in the core
        assert len(tools) == 10, f"Expected 10 tools, got {len(tools)}"

    def test_tool_structure(self):
        """Test that tools have the required structure."""
        tools = get_mcp_tools()

        for tool in tools:
            # Each tool should have name, description, and inputSchema
            assert hasattr(tool, 'name'), f"Tool missing name attribute"
            assert hasattr(tool, 'description'), f"Tool {tool.name} missing description"
            assert hasattr(tool, 'inputSchema'), f"Tool {tool.name} missing inputSchema"

            # Name should be non-empty string
            assert isinstance(tool.name, str), f"Tool name should be string"
            assert len(tool.name) > 0, f"Tool name should not be empty"

            # Description should be non-empty string
            assert isinstance(tool.description, str), f"Tool {tool.name} description should be string"
            assert len(tool.description) > 0, f"Tool {tool.name} description should not be empty"


class TestModuleStructure:
    """Test the overall module structure."""

    def test_core_module_exports(self):
        """Test that core module exports expected items."""
        import mcp_neo4j_memory.core as core

        # Check that __all__ is defined and contains expected items
        expected_exports = [
            "Neo4jMemory", "Entity", "Relation", "KnowledgeGraph",
            "ObservationAddition", "ObservationDeletion",
            "get_mcp_tools", "execute_tool"
        ]

        for export in expected_exports:
            assert hasattr(core, export), f"Core module missing export: {export}"

    def test_protocols_module_exports(self):
        """Test that protocols module exports expected items."""
        import mcp_neo4j_memory.protocols as protocols

        expected_exports = ["run_stdio_server", "run_sse_server"]

        for export in expected_exports:
            assert hasattr(protocols, export), f"Protocols module missing export: {export}"

    def test_package_version(self):
        """Test that package has version information."""
        import mcp_neo4j_memory

        # Should have version defined
        assert hasattr(mcp_neo4j_memory, '__version__'), "Package missing __version__"

        # Version should be a string
        assert isinstance(mcp_neo4j_memory.__version__, str), "Version should be a string"

        # Version should not be empty
        assert len(mcp_neo4j_memory.__version__) > 0, "Version should not be empty"


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_unit.py -v
    pytest.main([__file__, "-v"])
