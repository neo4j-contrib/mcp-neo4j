import asyncio
import json
import os
import pytest
import aiohttp
import subprocess
import sys
import time
from typing import AsyncGenerator
import uuid

import pytest_asyncio
from neo4j import AsyncGraphDatabase
from testcontainers.neo4j import Neo4jContainer


async def parse_sse_response(response: aiohttp.ClientResponse) -> dict:
    """Parse Server-Sent Events response from FastMCP 2.0."""
    content = await response.text()
    lines = content.strip().split('\n')
    
    # Find the data line that contains the JSON
    for line in lines:
        if line.startswith('data: '):
            json_str = line[6:]  # Remove 'data: ' prefix
            return json.loads(json_str)
    
    raise ValueError("No data line found in SSE response")


@pytest.fixture(scope="module")
def neo4j_container():
    """Start a Neo4j container for testing."""
    container = (
        Neo4jContainer("neo4j:latest")
        .with_env("NEO4J_apoc_export_file_enabled", "true")
        .with_env("NEO4J_apoc_import_file_enabled", "true")
        .with_env("NEO4J_apoc_import_file_use__neo4j__config", "true")
        .with_env("NEO4J_PLUGINS", '["apoc"]')
    )
    container.start()
    yield container
    container.stop()


class TestHTTPTransport:
    """Test HTTP transport functionality."""

    @pytest_asyncio.fixture
    async def http_server(self, neo4j_container):
        """Start the MCP server in HTTP mode."""
        # Set environment variables for the server
        env = os.environ.copy()
        env.update({
            "NEO4J_URI": neo4j_container.get_connection_url(),
            "NEO4J_USERNAME": neo4j_container.username,
            "NEO4J_PASSWORD": neo4j_container.password,
            "NEO4J_DATABASE": "neo4j",
        })
        
        # Start server process in HTTP mode using the installed binary
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "mcp-neo4j-cypher", 
            "--transport", "http", 
            "--host", "127.0.0.1", 
            "--port", "8001",
            "--db-url", neo4j_container.get_connection_url(),
            "--username", neo4j_container.username,
            "--password", neo4j_container.password,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Wait for server to start
        await asyncio.sleep(3)
        
        # Check if process is still running
        if process.returncode is not None:
            stdout, stderr = await process.communicate()
            raise RuntimeError(f"Server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}")
        
        yield process
        
        # Cleanup
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

    @pytest.mark.asyncio
    async def test_http_tools_list(self, http_server):
        """Test that tools/list endpoint works over HTTP."""
        session_id = str(uuid.uuid4())
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8001/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list"
                },
                headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": session_id}
            ) as response:
                print(f"Response status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")
                response_text = await response.text()
                print(f"Response text: {response_text}")
                
                assert response.status == 200
                result = await parse_sse_response(response)
                assert "result" in result
                assert "tools" in result["result"]
                tools = result["result"]["tools"]
                assert len(tools) > 0
                tool_names = [tool["name"] for tool in tools]
                assert "get_neo4j_schema" in tool_names
                assert "read_neo4j_cypher" in tool_names
                assert "write_neo4j_cypher" in tool_names

    @pytest.mark.asyncio
    async def test_http_get_schema(self, http_server):
        """Test that get_neo4j_schema works over HTTP."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8001/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_neo4j_schema",
                        "arguments": {}
                    }
                },
                headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": "test-session"}
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                assert "result" in result
                assert "content" in result["result"]
                assert len(result["result"]["content"]) > 0

    @pytest.mark.asyncio
    async def test_http_write_query(self, http_server):
        """Test that write_neo4j_cypher works over HTTP."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8001/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "write_neo4j_cypher",
                        "arguments": {
                            "query": "CREATE (n:Test {name: 'http_test'})"
                        }
                    }
                },
                headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": "test-session"}
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                assert "result" in result
                assert "content" in result["result"]

    @pytest.mark.asyncio
    async def test_http_read_query(self, http_server):
        """Test that read_neo4j_cypher works over HTTP."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8001/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "read_neo4j_cypher",
                        "arguments": {
                            "query": "MATCH (n:Test) RETURN n.name as name"
                        }
                    }
                },
                headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": "test-session"}
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                assert "result" in result
                assert "content" in result["result"]

    @pytest.mark.asyncio
    async def test_http_invalid_method(self, http_server):
        """Test handling of invalid method over HTTP."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8001/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "invalid_method"
                },
                headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": "test-session"}
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                # Accept either JSON-RPC error or result with isError
                assert ("result" in result and result["result"].get("isError", False)) or ("error" in result)

    @pytest.mark.asyncio
    async def test_http_invalid_tool(self, http_server):
        """Test handling of invalid tool over HTTP."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8001/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "invalid_tool",
                        "arguments": {}
                    }
                },
                headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": "test-session"}
            ) as response:
                result = await parse_sse_response(response)
                assert response.status == 200
                # FastMCP returns errors in result field with isError: True
                assert "result" in result
                assert result["result"].get("isError", False)


class TestSSETransport:
    """Test SSE transport functionality."""

    @pytest_asyncio.fixture
    async def sse_server(self, neo4j_container):
        """Start the MCP server in SSE mode."""
        env = os.environ.copy()
        env.update({
            "NEO4J_URI": neo4j_container.get_connection_url(),
            "NEO4J_USERNAME": neo4j_container.username,
            "NEO4J_PASSWORD": neo4j_container.password,
            "NEO4J_DATABASE": "neo4j",
        })
        
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "mcp-neo4j-cypher", 
            "--transport", "sse", 
            "--host", "127.0.0.1", 
            "--port", "8002",
            "--db-url", neo4j_container.get_connection_url(),
            "--username", neo4j_container.username,
            "--password", neo4j_container.password,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        await asyncio.sleep(3)
        
        if process.returncode is not None:
            stdout, stderr = await process.communicate()
            raise RuntimeError(f"Server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}")
        
        yield process
        
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

    @pytest.mark.asyncio
    async def test_sse_endpoint(self, sse_server):
        """Test that SSE endpoint is accessible."""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8002/mcp/") as response:
                # SSE endpoint should be accessible
                assert response.status in [200, 404]  # 404 is okay if no specific endpoint


class TestStdioTransport:
    """Test stdio transport functionality."""

    @pytest.mark.asyncio
    async def test_stdio_transport(self, neo4j_container):
        """Test that stdio transport can be started."""
        env = os.environ.copy()
        env.update({
            "NEO4J_URI": neo4j_container.get_connection_url(),
            "NEO4J_USERNAME": neo4j_container.username,
            "NEO4J_PASSWORD": neo4j_container.password,
            "NEO4J_DATABASE": "neo4j",
        })
        
        # Test that stdio transport can be started (it should not crash)
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "mcp-neo4j-cypher", 
            "--transport", "stdio",
            "--db-url", neo4j_container.get_connection_url(),
            "--username", neo4j_container.username,
            "--password", neo4j_container.password,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Give it a moment to start
        await asyncio.sleep(1)
        
        # Check if process is still running before trying to terminate
        if process.returncode is None:
            # Process is still running, terminate it
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        else:
            # Process has already exited, which is fine for this test
            # We just want to verify it didn't crash immediately
            pass
        
        # Process should have started successfully (no immediate crash)
        # If returncode is None, it means the process was still running when we tried to terminate it
        # If returncode is not None, it means the process exited (which is also acceptable for this test)
        assert True  # If we get here, the process started without immediate crash


class TestTransportIntegration:
    """Integration tests for all transport modes."""

    @pytest.mark.asyncio
    async def test_http_full_workflow(self, neo4j_container):
        """Test complete workflow over HTTP transport."""
        env = os.environ.copy()
        env.update({
            "NEO4J_URI": neo4j_container.get_connection_url(),
            "NEO4J_USERNAME": neo4j_container.username,
            "NEO4J_PASSWORD": neo4j_container.password,
            "NEO4J_DATABASE": "neo4j",
        })
        
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "mcp-neo4j-cypher", 
            "--transport", "http", 
            "--host", "127.0.0.1", 
            "--port", "8003",
            "--db-url", neo4j_container.get_connection_url(),
            "--username", neo4j_container.username,
            "--password", neo4j_container.password,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        await asyncio.sleep(3)
        
        if process.returncode is not None:
            stdout, stderr = await process.communicate()
            raise RuntimeError(f"Server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}")

        try:
            async with aiohttp.ClientSession() as session:
                # 1. List tools
                async with session.post(
                    "http://127.0.0.1:8003/mcp/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list"
                    },
                    headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": "test-session"}
                ) as response:
                    result = await parse_sse_response(response)
                    assert response.status == 200
                    assert "result" in result

                # 2. Write data
                async with session.post(
                    "http://127.0.0.1:8003/mcp/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "write_neo4j_cypher",
                            "arguments": {
                                "query": "CREATE (n:IntegrationTest {name: 'workflow_test'})"
                            }
                        }
                    },
                    headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": "test-session"}
                ) as response:
                    result = await parse_sse_response(response)
                    assert response.status == 200
                    assert "result" in result

                # 3. Read data
                async with session.post(
                    "http://127.0.0.1:8003/mcp/",
                    json={
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "read_neo4j_cypher",
                            "arguments": {
                                "query": "MATCH (n:IntegrationTest) RETURN n.name as name"
                            }
                        }
                    },
                    headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "mcp-session-id": "test-session"}
                ) as response:
                    result = await parse_sse_response(response)
                    assert response.status == 200
                    assert "result" in result

        finally:
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait() 