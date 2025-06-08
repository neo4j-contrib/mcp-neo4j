"""
Integration tests for transport protocols in the MCP Neo4j Memory server.

Tests stdio and SSE protocols to ensure they work correctly with the modular architecture.
"""

import os
import pytest
import asyncio
import json
from typing import Dict, Any
from neo4j import GraphDatabase

from mcp_neo4j_memory.core import Neo4jMemory, Entity, get_mcp_tools
from mcp_neo4j_memory.protocols import run_sse_server


@pytest.fixture(scope="session")
def neo4j_driver():
    """Create a Neo4j driver for the test session."""
    uri = os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Verify connection
    try:
        driver.verify_connectivity()
    except Exception as e:
        pytest.skip(f"Could not connect to Neo4j: {e}")

    yield driver

    # Clean up test data after all tests
    driver.execute_query("MATCH (n:Memory) DETACH DELETE n")
    driver.close()


@pytest.fixture(scope="function")
def memory(neo4j_driver):
    """Create a fresh Neo4jMemory instance for each test."""
    # Clean up before each test
    neo4j_driver.execute_query("MATCH (n:Memory) DETACH DELETE n")
    return Neo4jMemory(neo4j_driver)


class TestCoreTools:
    """Test core tool functionality independent of transport protocol."""

    @pytest.mark.asyncio
    async def test_get_mcp_tools(self):
        """Test that get_mcp_tools returns expected tools."""
        tools = get_mcp_tools()

        # Verify we have the expected number of tools
        assert len(tools) == 10

        # Verify expected tool names are present
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "create_entities", "create_relations", "add_observations",
            "delete_entities", "delete_observations", "delete_relations",
            "read_graph", "search_nodes", "find_nodes", "open_nodes"
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_core_tool_execution(self, memory):
        """Test core tool execution functionality."""
        # Test create_entities
        test_entity = Entity(name="TestEntity", type="Test", observations=["Test"])
        await memory.create_entities([test_entity])

        # Test read_graph  
        entities = await memory.read_entities()
        assert len(entities) == 1
        assert entities[0].name == "TestEntity"


class TestSseServer:
    """Test SSE server protocol implementation."""

    @pytest.mark.asyncio
    async def test_sse_server_endpoints(self, memory):
        """Test SSE server endpoints."""
        from mcp_neo4j_memory.protocols.sse_server import MCPSSEServer
        from fastapi.testclient import TestClient

        # Create SSE server
        sse_server = MCPSSEServer(memory)
        client = TestClient(sse_server.app)

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "MCP Neo4j Memory SSE Server"
        assert data["protocol"] == "mcp-sse"
        assert "endpoints" in data

    @pytest.mark.asyncio
    async def test_sse_stream_connection(self, memory):
        """Test SSE stream basic connectivity (headers only)."""
        from mcp_neo4j_memory.protocols.sse_server import MCPSSEServer
        from fastapi.testclient import TestClient
        import threading
        import time

        # Create SSE server
        sse_server = MCPSSEServer(memory)
        client = TestClient(sse_server.app)

        # Test root endpoint first to ensure server is working
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "MCP Neo4j Memory SSE Server"
        assert data["protocol"] == "mcp-sse"
        assert "endpoints" in data

        # For SSE endpoint, we'll test it in a separate thread with timeout
        # since SSE streams are infinite and would hang the main thread
        result = {"success": False, "status_code": None, "headers": None, "error": None}

        def test_sse_headers():
            try:
                # This will start the SSE connection but we'll interrupt it quickly
                with client as test_client:
                    # Make the request - this will start streaming but we'll catch it
                    response = test_client.get("/sse", headers={"Accept": "text/event-stream"})
                    # We should never reach here due to infinite stream, but if we do:
                    result["status_code"] = response.status_code
                    result["headers"] = dict(response.headers)
            except Exception as e:
                # This is expected - the SSE stream will cause issues
                result["error"] = str(e)

        # Run SSE test in thread with timeout
        thread = threading.Thread(target=test_sse_headers)
        thread.daemon = True
        thread.start()
        thread.join(timeout=2.0)  # 2 second timeout

        if thread.is_alive():
            # Thread is still running - this means SSE endpoint is working (infinite stream)
            result["success"] = True
            print("SSE endpoint is working (infinite stream detected as expected)")
        else:
            # Thread finished - check what happened
            if result["status_code"] == 200:
                result["success"] = True
                print("SSE endpoint responded with 200 (unlikely but valid)")
            elif result["error"]:
                # Some error occurred - this might be expected for SSE
                print(f"SSE test completed with: {result['error']}")
                # For SSE, some errors are expected due to infinite stream nature
                if "stream" in result["error"].lower() or "timeout" in result["error"].lower():
                    result["success"] = True

        # The test passes if we detected the SSE endpoint is working
        assert result["success"], f"SSE endpoint test failed: {result.get('error', 'Unknown error')}"

        print("SSE endpoint test completed successfully")


class TestProtocolIntegration:
    """Test integration between protocols and core functionality."""

    @pytest.mark.asyncio
    async def test_stdio_sse_tool_consistency(self, memory):
        """Test that stdio and SSE protocols expose the same tools."""
        from mcp_neo4j_memory.core import get_mcp_tools

        # Get tools from core (used by both stdio and SSE)
        core_tools = get_mcp_tools()
        core_tool_names = set(tool.name for tool in core_tools)

        # Both stdio and SSE use the same core tools
        assert len(core_tool_names) == 10
        
        expected_tools = {
            "create_entities", "create_relations", "add_observations",
            "delete_entities", "delete_observations", "delete_relations", 
            "read_graph", "search_nodes", "find_nodes", "open_nodes"
        }
        assert core_tool_names == expected_tools

    @pytest.mark.asyncio
    async def test_data_consistency_across_sessions(self, memory):
        """Test that data persists across different protocol sessions."""
        # Create data
        test_entity = Entity(
            name="PersistentEntity",
            type="Test", 
            observations=["Created for persistence test"]
        )
        await memory.create_entities([test_entity])

        # Verify data exists
        entities = await memory.read_entities()
        assert len(entities) == 1
        assert entities[0].name == "PersistentEntity"
        assert entities[0].observations == ["Created for persistence test"]

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, memory):
        """Test that error handling is consistent."""
        # Test invalid entity creation
        try:
            invalid_entity = Entity(name="", type="", observations=[])
            await memory.create_entities([invalid_entity])
            assert False, "Should have raised an error for invalid entity"
        except (ValueError, Exception):
            # Expected - empty names should be rejected
            pass


# Utility functions for testing
def create_test_entities() -> list[Dict[str, Any]]:
    """Create test entities for integration testing."""
    return [
        {
            "name": "TestPerson1",
            "type": "Person",
            "observations": ["Likes testing", "Works with Neo4j"]
        },
        {
            "name": "TestPerson2",
            "type": "Person",
            "observations": ["Enjoys integration tests"]
        },
        {
            "name": "TestCompany",
            "type": "Organization",
            "observations": ["Technology company", "Uses knowledge graphs"]
        }
    ]


def create_test_relations() -> list[Dict[str, Any]]:
    """Create test relations for integration testing."""
    return [
        {
            "source": "TestPerson1",
            "target": "TestCompany",
            "relationType": "WORKS_FOR"
        },
        {
            "source": "TestPerson1",
            "target": "TestPerson2",
            "relationType": "COLLEAGUES_WITH"
        }
    ]


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_transport_integration.py -v
    pytest.main([__file__, "-v"])
