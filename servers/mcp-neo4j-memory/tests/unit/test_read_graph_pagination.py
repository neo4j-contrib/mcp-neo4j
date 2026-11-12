"""Unit tests for read_graph pagination (limit/offset) with a mocked Neo4j driver."""

from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError

from mcp_neo4j_memory.neo4j_memory import KnowledgeGraph, Neo4jMemory
from mcp_neo4j_memory.server import create_mcp_server


def _mock_driver(nodes=None, relations=None):
    """Create a mock async driver whose execute_query returns a single graph record."""
    record = {"nodes": nodes or [], "relations": relations or []}
    result = Mock()
    result.records = [record]
    driver = Mock()
    driver.execute_query = AsyncMock(return_value=result)
    return driver


def _query_and_params(driver):
    args, _ = driver.execute_query.call_args
    return args[0], args[1]


class TestNeo4jMemoryReadGraphPagination:
    """Test that read_graph builds the expected Cypher for pagination."""

    @pytest.mark.asyncio
    async def test_read_graph_without_arguments_is_unpaginated(self):
        driver = _mock_driver()
        memory = Neo4jMemory(driver)

        await memory.read_graph()

        query, params = _query_and_params(driver)
        assert params == {"filter": "*"}
        assert "SKIP" not in query
        assert "LIMIT" not in query
        assert "ORDER BY" not in query

    @pytest.mark.asyncio
    async def test_read_graph_with_limit(self):
        driver = _mock_driver()
        memory = Neo4jMemory(driver)

        await memory.read_graph(limit=10)

        query, params = _query_and_params(driver)
        assert params == {"filter": "*", "offset": 0, "limit": 10}
        assert "WITH entity ORDER BY entity.name SKIP $offset LIMIT $limit" in query
        # Pagination must be applied to entities before relations are expanded
        assert query.index("LIMIT $limit") < query.index("OPTIONAL MATCH")

    @pytest.mark.asyncio
    async def test_read_graph_with_limit_and_offset(self):
        driver = _mock_driver()
        memory = Neo4jMemory(driver)

        await memory.read_graph(limit=5, offset=20)

        query, params = _query_and_params(driver)
        assert params == {"filter": "*", "offset": 20, "limit": 5}
        assert "SKIP $offset LIMIT $limit" in query

    @pytest.mark.asyncio
    async def test_read_graph_with_offset_only(self):
        driver = _mock_driver()
        memory = Neo4jMemory(driver)

        await memory.read_graph(offset=3)

        query, params = _query_and_params(driver)
        assert params == {"filter": "*", "offset": 3}
        assert "ORDER BY entity.name SKIP $offset" in query
        assert "LIMIT" not in query

    @pytest.mark.asyncio
    @pytest.mark.parametrize("kwargs", [{"limit": -1}, {"offset": -1}])
    async def test_read_graph_rejects_negative_values(self, kwargs):
        driver = _mock_driver()
        memory = Neo4jMemory(driver)

        with pytest.raises(ValueError):
            await memory.read_graph(**kwargs)

        driver.execute_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_read_graph_returns_page_results(self):
        driver = _mock_driver(
            nodes=[{"name": "Alice", "type": "person", "observations": ["Works at Neo4j"]}],
            relations=[{"source": "Alice", "target": "Neo4j", "relationType": "WORKS_AT"}],
        )
        memory = Neo4jMemory(driver)

        graph = await memory.read_graph(limit=1)

        assert [entity.name for entity in graph.entities] == ["Alice"]
        assert [(r.source, r.target, r.relationType) for r in graph.relations] == [("Alice", "Neo4j", "WORKS_AT")]

    @pytest.mark.asyncio
    async def test_search_memories_is_not_paginated(self):
        driver = _mock_driver()
        memory = Neo4jMemory(driver)

        await memory.search_memories("Alice")

        query, params = _query_and_params(driver)
        assert params == {"filter": "Alice"}
        assert "SKIP" not in query
        assert "LIMIT" not in query


class TestReadGraphToolPagination:
    """Test the read_graph MCP tool exposes and forwards pagination arguments."""

    @pytest.fixture
    def mock_memory(self):
        memory = Mock(spec=Neo4jMemory)
        memory.read_graph = AsyncMock(return_value=KnowledgeGraph(entities=[], relations=[]))
        return memory

    @pytest.mark.asyncio
    async def test_tool_schema_exposes_optional_limit_and_offset(self, mock_memory):
        server = create_mcp_server(mock_memory)
        tool = (await server.get_tools())["read_graph"]

        properties = tool.parameters["properties"]
        assert "limit" in properties
        assert "offset" in properties
        assert tool.parameters.get("required", []) == []

    @pytest.mark.asyncio
    async def test_tool_without_arguments_reads_full_graph(self, mock_memory):
        server = create_mcp_server(mock_memory)
        tool = (await server.get_tools())["read_graph"]

        await tool.run({})

        mock_memory.read_graph.assert_awaited_once_with(limit=None, offset=0)

    @pytest.mark.asyncio
    async def test_tool_forwards_limit_and_offset(self, mock_memory):
        server = create_mcp_server(mock_memory, namespace="ns")
        tool = (await server.get_tools())["ns-read_graph"]

        await tool.run({"limit": 25, "offset": 50})

        mock_memory.read_graph.assert_awaited_once_with(limit=25, offset=50)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("arguments", [{"limit": 0}, {"limit": -5}, {"offset": -1}])
    async def test_tool_rejects_invalid_pagination(self, mock_memory, arguments):
        server = create_mcp_server(mock_memory)
        tool = (await server.get_tools())["read_graph"]

        with pytest.raises(ValidationError):
            await tool.run(arguments)

        mock_memory.read_graph.assert_not_called()
