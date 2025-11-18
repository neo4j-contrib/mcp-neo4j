import asyncio
import json
import subprocess

import aiohttp
import pytest
import pytest_asyncio


async def parse_sse_response(response: aiohttp.ClientResponse) -> dict:
    """Parse Server-Sent Events response from FastMCP 2.0."""
    content = await response.text()
    lines = content.strip().split("\n")

    # Find the data line that contains the JSON
    for line in lines:
        if line.startswith("data: "):
            json_str = line[6:]  # Remove 'data: ' prefix
            return json.loads(json_str)

    raise ValueError("No data line found in SSE response")


class TestParseStringifiedJSONObjectMiddlewareIntegration:
    """Integration tests for the ParseStringifiedJSONObjectMiddleware."""

    STRINGIFIED_DATA_MODEL = '{\n  "nodes": [\n    {\n      "label": "Person",\n      "key_property": {\n        "name": "personId",\n        "type": "STRING",\n        "description": "Unique identifier for the person"\n      },\n      "properties": [\n        {\n          "name": "personId",\n          "type": "STRING",\n          "description": "Unique identifier for the person"\n        },\n        {\n          "name": "name",\n          "type": "STRING",\n          "description": "Full name of the person"\n        },\n        {\n          "name": "email",\n          "type": "STRING",\n          "description": "Email address"\n        }\n      ]\n    },\n    {\n      "label": "Company",\n      "key_property": {\n        "name": "companyId",\n        "type": "STRING",\n        "description": "Unique identifier for the company"\n      },\n      "properties": [\n        {\n          "name": "companyId",\n          "type": "STRING",\n          "description": "Unique identifier for the company"\n        },\n        {\n          "name": "name",\n          "type": "STRING",\n          "description": "Company name"\n        },\n        {\n          "name": "industry",\n          "type": "STRING",\n          "description": "Industry sector"\n        }\n      ]\n    },\n    {\n      "label": "Project",\n      "key_property": {\n        "name": "projectId",\n        "type": "STRING",\n        "description": "Unique identifier for the project"\n      },\n      "properties": [\n        {\n          "name": "projectId",\n          "type": "STRING",\n          "description": "Unique identifier for the project"\n        },\n        {\n          "name": "title",\n          "type": "STRING",\n          "description": "Project title"\n        },\n        {\n          "name": "status",\n          "type": "STRING",\n          "description": "Current project status"\n        },\n        {\n          "name": "budget",\n          "type": "FLOAT",\n          "description": "Project budget"\n        }\n      ]\n    }\n  ],\n  "relationships": [\n    {\n      "type": "WORKS_FOR",\n      "start_node_label": "Person",\n      "end_node_label": "Company",\n      "properties": [\n        {\n          "name": "startDate",\n          "type": "DATE",\n          "description": "Employment start date"\n        },\n        {\n          "name": "role",\n          "type": "STRING",\n          "description": "Job role or title"\n        }\n      ]\n    },\n    {\n      "type": "MANAGES",\n      "start_node_label": "Person",\n      "end_node_label": "Project",\n      "properties": [\n        {\n          "name": "assignedDate",\n          "type": "DATE",\n          "description": "Date assigned as manager"\n        }\n      ]\n    },\n    {\n      "type": "SPONSORS",\n      "start_node_label": "Company",\n      "end_node_label": "Project",\n      "properties": [\n        {\n          "name": "fundingAmount",\n          "type": "FLOAT",\n          "description": "Amount of funding provided"\n        }\n      ]\n    }\n  ]\n}'

    @pytest_asyncio.fixture
    async def http_server(self):
        """Start the server in HTTP mode with middleware."""
        import os

        # Get the current directory
        server_dir = os.getcwd()

        # Start server process
        process = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "mcp-neo4j-data-modeling",
            "--transport",
            "http",
            "--server-host",
            "127.0.0.1",
            "--server-port",
            "8009",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=server_dir,
        )

        # Wait for server to start
        await asyncio.sleep(3)

        yield process

        # Cleanup
        try:
            process.terminate()
            await process.wait()
        except ProcessLookupError:
            pass

    @pytest.mark.asyncio
    async def test_validate_data_model_with_stringified_json(self, http_server):
        """Test that validate_data_model works with stringified JSON (middleware enabled by default)."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8009/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "validate_data_model",
                        "arguments": {
                            "data_model": self.STRINGIFIED_DATA_MODEL,
                            "return_validated": True,
                        },
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)

                # Should succeed (no error)
                assert "result" in result
                assert "error" not in result
                assert result["result"]["isError"] is False

                # The validated model should be returned
                content = result["result"]["content"]
                assert len(content) > 0
                assert content[0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_export_to_arrows_json_with_stringified_json(self, http_server):
        """Test that export_to_arrows_json works with stringified JSON."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8009/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "export_to_arrows_json",
                        "arguments": {"data_model": self.STRINGIFIED_DATA_MODEL},
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)

                # Should succeed
                assert "result" in result
                assert result["result"]["isError"] is False

                # Should return Arrows JSON
                content = result["result"]["content"]
                assert len(content) > 0
                arrows_json = json.loads(content[0]["text"])
                assert "nodes" in arrows_json
                assert "relationships" in arrows_json

    @pytest.mark.asyncio
    async def test_get_mermaid_config_str_with_stringified_json(self, http_server):
        """Test that get_mermaid_config_str works with stringified JSON."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8009/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_mermaid_config_str",
                        "arguments": {"data_model": self.STRINGIFIED_DATA_MODEL},
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)

                # Should succeed
                assert "result" in result
                assert result["result"]["isError"] is False

                # Should return Mermaid config
                content = result["result"]["content"]
                assert len(content) > 0
                mermaid_str = content[0]["text"]
                assert "erDiagram" in mermaid_str or "graph" in mermaid_str

    @pytest.mark.asyncio
    async def test_validate_node_with_stringified_json(self, http_server):
        """Test that validate_node works with stringified JSON."""
        stringified_node = '{\n  "label": "Person",\n  "key_property": {\n    "name": "personId",\n    "type": "STRING",\n    "description": "Unique identifier"\n  },\n  "properties": [\n    {\n      "name": "personId",\n      "type": "STRING",\n      "description": "Unique identifier"\n    },\n    {\n      "name": "name",\n      "type": "STRING",\n      "description": "Full name"\n    }\n  ]\n}'

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8009/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "validate_node",
                        "arguments": {"node": stringified_node, "return_validated": False},
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)

                # Should succeed
                assert "result" in result
                assert result["result"]["isError"] is False
                content = result["result"]["content"]
                assert content[0]["text"].lower() == "true"

    @pytest.mark.asyncio
    async def test_validate_relationship_with_stringified_json(self, http_server):
        """Test that validate_relationship works with stringified JSON."""
        stringified_relationship = '{\n  "type": "WORKS_FOR",\n  "start_node_label": "Person",\n  "end_node_label": "Company",\n  "properties": [\n    {\n      "name": "startDate",\n      "type": "DATE",\n      "description": "Employment start date"\n    }\n  ]\n}'

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8009/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "validate_relationship",
                        "arguments": {
                            "relationship": stringified_relationship,
                            "return_validated": False,
                        },
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)

                # Should succeed
                assert "result" in result
                assert result["result"]["isError"] is False
                content = result["result"]["content"]
                assert content[0]["text"].lower() == "true"

    @pytest.mark.asyncio
    async def test_get_constraints_cypher_queries_with_stringified_json(
        self, http_server
    ):
        """Test that get_constraints_cypher_queries works with stringified JSON."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8009/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_constraints_cypher_queries",
                        "arguments": {"data_model": self.STRINGIFIED_DATA_MODEL},
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)

                # Should succeed
                assert "result" in result
                assert result["result"]["isError"] is False

                # Should return list of queries
                content = result["result"]["content"]
                queries = json.loads(content[0]["text"])
                assert isinstance(queries, list)
                assert len(queries) > 0

    @pytest.mark.asyncio
    async def test_get_relationship_cypher_ingest_query_with_stringified_json(
        self, http_server
    ):
        """Test that get_relationship_cypher_ingest_query works with stringified JSON."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8009/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_relationship_cypher_ingest_query",
                        "arguments": {
                            "data_model": self.STRINGIFIED_DATA_MODEL,
                            "relationship_type": "WORKS_FOR",
                            "relationship_start_node_label": "Person",
                            "relationship_end_node_label": "Company",
                        },
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            ) as response:
                assert response.status == 200
                result = await parse_sse_response(response)

                # Should succeed
                assert "result" in result
                assert result["result"]["isError"] is False

                # Should return Cypher query
                content = result["result"]["content"]
                cypher = content[0]["text"]
                assert "UNWIND" in cypher or "MATCH" in cypher
