#!/usr/bin/env python3
"""
Unit tests for JSON string parsing fix in MCP Neo4j Memory tool execution.

These tests verify that the tools can handle both properly formatted input
and the problematic JSON string format that some LLM clients send.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch

from mcp_neo4j_memory.core.tools import execute_tool
from mcp_neo4j_memory.core.models import Entity, Relation
import mcp.types as types


class TestJSONStringParsing:
    """Test JSON string parsing functionality in tool execution."""

    @pytest.fixture
    def mock_memory(self):
        """Create a mock Neo4jMemory instance."""
        memory = AsyncMock()

        # Mock return values for different operations
        memory.create_entities.return_value = [
            Entity(name="Entity1", type="Person", observations=["Age: 30", "Occupation: Doctor"]),
            Entity(name="Entity2", type="Car", observations=["Brand: Toyota", "Model: Camry"])
        ]

        memory.create_relations.return_value = [
            Relation(source="Entity1", target="Entity2", relationType="OWNS")
        ]

        return memory

    @pytest.mark.asyncio
    async def test_create_entities_with_json_string_input(self, mock_memory):
        """Test create_entities handles JSON string input correctly."""
        # This is the problematic format that LLMs were sending
        arguments_with_json_string = {
            "entities": '[{"name":"Entity1","type":"Person","observations":["Age: 30", "Occupation: Doctor"]}, {"name":"Entity2","type":"Car","observations":["Brand: Toyota", "Model: Camry"]}]'
        }

        result = await execute_tool(mock_memory, "create_entities", arguments_with_json_string)

        # Verify the result
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert result[0].type == "text"

        # Parse the JSON result to verify it's valid
        result_data = json.loads(result[0].text)
        assert len(result_data) == 2
        assert result_data[0]["name"] == "Entity1"
        assert result_data[1]["name"] == "Entity2"

        # Verify the mock was called with correct parsed entities
        mock_memory.create_entities.assert_called_once()
        call_args = mock_memory.create_entities.call_args[0][0]  # First positional argument
        assert len(call_args) == 2
        assert call_args[0].name == "Entity1"
        assert call_args[0].type == "Person"
        assert call_args[1].name == "Entity2"
        assert call_args[1].type == "Car"

    @pytest.mark.asyncio
    async def test_create_entities_with_normal_input(self, mock_memory):
        """Test create_entities still works with normal input format."""
        # This is the correct format
        arguments_normal = {
            "entities": [
                {"name": "Entity1", "type": "Person", "observations": ["Age: 30", "Occupation: Doctor"]},
                {"name": "Entity2", "type": "Car", "observations": ["Brand: Toyota", "Model: Camry"]}
            ]
        }

        result = await execute_tool(mock_memory, "create_entities", arguments_normal)

        # Verify the result
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        # Verify the mock was called correctly
        mock_memory.create_entities.assert_called_once()
        call_args = mock_memory.create_entities.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0].name == "Entity1"

    @pytest.mark.asyncio
    async def test_create_relations_with_json_string_input(self, mock_memory):
        """Test create_relations handles JSON string input correctly."""
        arguments_with_json_string = {
            "relations": '[{"source":"Entity1","target":"Entity2","relationType":"OWNS"}]'
        }

        result = await execute_tool(mock_memory, "create_relations", arguments_with_json_string)

        # Verify the result
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        # Parse the JSON result
        result_data = json.loads(result[0].text)
        assert len(result_data) == 1
        assert result_data[0]["source"] == "Entity1"
        assert result_data[0]["target"] == "Entity2"
        assert result_data[0]["relationType"] == "OWNS"

        # Verify the mock was called correctly
        mock_memory.create_relations.assert_called_once()
        call_args = mock_memory.create_relations.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].source == "Entity1"
        assert call_args[0].target == "Entity2"
        assert call_args[0].relationType == "OWNS"

    @pytest.mark.asyncio
    async def test_invalid_json_string_raises_error(self, mock_memory):
        """Test that invalid JSON string raises appropriate error."""
        arguments_with_invalid_json = {
            "entities": '{"name":"Entity1","type":"Person"'  # Incomplete JSON
        }

        result = await execute_tool(mock_memory, "create_entities", arguments_with_invalid_json)

        # Should return error content
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Error:" in result[0].text
        assert "Invalid JSON string" in result[0].text

    @pytest.mark.asyncio
    @patch('mcp_neo4j_memory.core.tools.logger')
    async def test_json_string_parsing_logs_warning(self, mock_logger, mock_memory):
        """Test that JSON string parsing logs a warning."""
        arguments_with_json_string = {
            "entities": '[{"name":"Entity1","type":"Person","observations":["Age: 30"]}]'
        }

        await execute_tool(mock_memory, "create_entities", arguments_with_json_string)

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Parsed entities from JSON string" in warning_call

    @pytest.mark.asyncio
    async def test_empty_entities_array_as_json_string(self, mock_memory):
        """Test handling empty entities array as JSON string."""
        mock_memory.create_entities.return_value = []

        arguments_with_empty_json = {
            "entities": "[]"
        }

        result = await execute_tool(mock_memory, "create_entities", arguments_with_empty_json)

        # Should work without errors
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        # Verify empty array was parsed correctly
        mock_memory.create_entities.assert_called_once()
        call_args = mock_memory.create_entities.call_args[0][0]
        assert len(call_args) == 0

    @pytest.mark.asyncio
    async def test_backward_compatibility_not_broken(self, mock_memory):
        """Test that normal clients still work exactly as before."""
        # Test with various normal input formats
        test_cases = [
            # Empty array
            {"entities": []},
            # Single entity
            {"entities": [{"name": "Test", "type": "Person", "observations": ["Obs1"]}]},
            # Multiple entities
            {"entities": [
                {"name": "Test1", "type": "Person", "observations": ["Obs1"]},
                {"name": "Test2", "type": "Car", "observations": ["Obs2"]}
            ]},
        ]

        for i, arguments in enumerate(test_cases):
            mock_memory.reset_mock()
            mock_memory.create_entities.return_value = [
                Entity(name=f"Entity{j}", type="Type", observations=["Obs"])
                for j in range(len(arguments["entities"]))
            ]

            result = await execute_tool(mock_memory, "create_entities", arguments)

            # Should work normally
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)

            # Verify correct number of entities processed
            mock_memory.create_entities.assert_called_once()
            call_args = mock_memory.create_entities.call_args[0][0]
            assert len(call_args) == len(arguments["entities"])


class TestJSONStringParsingEdgeCases:
    """Test edge cases for JSON string parsing."""

    @pytest.fixture
    def mock_memory(self):
        """Create a mock Neo4jMemory instance."""
        memory = AsyncMock()
        memory.create_entities.return_value = []
        memory.create_relations.return_value = []
        return memory

    @pytest.mark.asyncio
    async def test_null_entities_parameter(self, mock_memory):
        """Test handling when entities parameter is None."""
        result = await execute_tool(mock_memory, "create_entities", {"entities": None})

        # Should handle gracefully
        assert len(result) == 1
        assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_non_string_non_list_entities(self, mock_memory):
        """Test handling when entities is neither string nor list."""
        result = await execute_tool(mock_memory, "create_entities", {"entities": 123})

        # Should handle gracefully
        assert len(result) == 1
        assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_mixed_format_not_supported(self, mock_memory):
        """Test that we don't try to parse normal arrays as JSON."""
        normal_arguments = {
            "entities": [{"name": "Test", "type": "Person", "observations": ["Obs"]}]
        }

        mock_memory.create_entities.return_value = [
            Entity(name="Test", type="Person", observations=["Obs"])
        ]

        result = await execute_tool(mock_memory, "create_entities", normal_arguments)

        # Should work normally without trying to JSON parse
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        mock_memory.create_entities.assert_called_once()


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_json_string_parsing.py -v
    pytest.main([__file__, "-v"])
