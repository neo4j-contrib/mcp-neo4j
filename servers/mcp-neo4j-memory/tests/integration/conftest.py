import asyncio
import os
import subprocess
from typing import Any

import pytest
import pytest_asyncio
from neo4j import GraphDatabase
from testcontainers.neo4j import Neo4jContainer

from mcp_neo4j_memory.server import Neo4jMemory, create_mcp_server

neo4j = (
    Neo4jContainer("neo4j:latest")
    .with_env("NEO4J_apoc_export_file_enabled", "true")
    .with_env("NEO4J_apoc_import_file_enabled", "true")
    .with_env("NEO4J_apoc_import_file_use__neo4j__config", "true")
    .with_env("NEO4J_PLUGINS", '["apoc"]')
)

@pytest.fixture(scope="module", autouse=True)
def setup(request):
    neo4j.start()

    def remove_container():
        neo4j.get_driver().close()
        neo4j.stop()

    request.addfinalizer(remove_container)
    os.environ["NEO4J_URI"] = neo4j.get_connection_url()
    os.environ["NEO4J_HOST"] = neo4j.get_container_host_ip()
    os.environ["NEO4J_PORT"] = neo4j.get_exposed_port(7687)

    yield neo4j

@pytest_asyncio.fixture(scope="function")
async def async_neo4j_driver(setup: Neo4jContainer):
    driver = GraphDatabase.driver(
        setup.get_connection_url(), auth=(setup.username, setup.password)
    )
    try:
        yield driver
    finally:
        await driver.close() 

@pytest.fixture
def memory(neo4j_driver):
    """Create a memory instance."""
    return Neo4jMemory(neo4j_driver)

@pytest.fixture
def mcp_server(neo4j_driver, memory):
    """Create an MCP server instance."""
    return create_mcp_server(neo4j_driver, memory)


@pytest_asyncio.fixture
async def sse_server(setup: Neo4jContainer):
    """Start the MCP server in SSE mode."""


    process = await asyncio.create_subprocess_exec(
        "uv", "run", "mcp-neo4j-memory",
        "--transport", "sse",
        "--server-host", "127.0.0.1",
        "--server-port", "8002",
        "--db-url", setup.get_connection_url(),
        "--username", setup.username,
        "--password", setup.password,
        "--database", "neo4j",
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


@pytest_asyncio.fixture
async def http_server(setup: Neo4jContainer):
    """Start the MCP server in HTTP mode."""

    # Start server process in HTTP mode using the installed binary
    process = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "mcp-neo4j-memory",
        "--transport",
        "http",
        "--server-host",
        "127.0.0.1",
        "--server-port",
        "8001",
        "--db-url",
        setup.get_connection_url(),
        "--username",
        setup.username,
        "--password",
        setup.password,
        "--database",
        "neo4j",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd(),
    )

    # Wait for server to start
    await asyncio.sleep(3)

    # Check if process is still running
    if process.returncode is not None:
        stdout, stderr = await process.communicate()
        raise RuntimeError(
            f"Server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}"
        )

    yield process

    # Cleanup
    try:
        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()


@pytest_asyncio.fixture
async def http_server_restricted_cors(setup: Neo4jContainer):
    """Start the MCP server in HTTP mode with restricted CORS origins."""

    # Start server process in HTTP mode with restricted CORS
    process = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "mcp-neo4j-memory",
        "--transport",
        "http",
        "--server-host",
        "127.0.0.1",
        "--server-port",
        "8003",
        "--allow-origins",
        "http://localhost:3000,https://trusted-site.com",
        "--db-url",
        setup.get_connection_url(),
        "--username",
        setup.username,
        "--password",
        setup.password,
        "--database",
        "neo4j",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd(),
    )

    # Wait for server to start
    await asyncio.sleep(3)

    # Check if process is still running
    if process.returncode is not None:
        stdout, stderr = await process.communicate()
        raise RuntimeError(
            f"Restricted CORS server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}"
        )

    yield process

    # Cleanup
    try:
        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()


@pytest_asyncio.fixture
async def http_server_custom_hosts(setup: Neo4jContainer):
    """Start the MCP server in HTTP mode with custom allowed hosts."""

    # Start server process in HTTP mode with custom allowed hosts
    process = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "mcp-neo4j-memory",
        "--transport",
        "http",
        "--server-host",
        "127.0.0.1",
        "--server-port",
        "8004",
        "--allowed-hosts",
        "example.com,test.local",
        "--db-url",
        setup.get_connection_url(),
        "--username",
        setup.username,
        "--password",
        setup.password,
        "--database",
        "neo4j",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd(),
    )

    # Wait for server to start
    await asyncio.sleep(3)

    # Check if process is still running
    if process.returncode is not None:
        stdout, stderr = await process.communicate()
        raise RuntimeError(
            f"Custom hosts server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}"
        )

    yield process

    # Cleanup
    try:
        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()