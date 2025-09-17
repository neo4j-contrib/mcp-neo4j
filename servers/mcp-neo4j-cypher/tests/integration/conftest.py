import asyncio
import os
import subprocess
from typing import Any

import pytest
import pytest_asyncio
from neo4j import AsyncGraphDatabase
from testcontainers.neo4j import Neo4jContainer

from mcp_neo4j_cypher.server import create_mcp_server

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
    driver = AsyncGraphDatabase.driver(
        setup.get_connection_url(), auth=(setup.username, setup.password)
    )
    try:
        yield driver
    finally:
        await driver.close()


@pytest_asyncio.fixture(scope="function")
async def mcp_server(async_neo4j_driver):
    mcp = create_mcp_server(async_neo4j_driver, "neo4j")

    return mcp


@pytest_asyncio.fixture(scope="function")
async def mcp_server_short_timeout(async_neo4j_driver):
    """MCP server with a very short timeout for testing timeout behavior."""
    mcp = create_mcp_server(async_neo4j_driver, "neo4j", read_timeout=0.01)

    return mcp


@pytest.fixture(scope="function")
def init_data(setup: Neo4jContainer, clear_data: Any):
    with setup.get_driver().session(database="neo4j") as session:
        session.run("CREATE (a:Person {name: 'Alice', age: 30})")
        session.run("CREATE (b:Person {name: 'Bob', age: 25})")
        session.run("CREATE (c:Person {name: 'Charlie', age: 35})")
        session.run(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:FRIEND]->(b)"
        )
        session.run(
            "MATCH (b:Person {name: 'Bob'}), (c:Person {name: 'Charlie'}) CREATE (b)-[:FRIEND]->(c)"
        )


@pytest.fixture(scope="function")
def clear_data(setup: Neo4jContainer):
    with setup.get_driver().session(database="neo4j") as session:
        session.run("MATCH (n) DETACH DELETE n")


@pytest_asyncio.fixture
async def sse_server(setup: Neo4jContainer):
    """Start the MCP server in SSE mode."""

    process = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "mcp-neo4j-cypher",
        "--transport",
        "sse",
        "--server-host",
        "127.0.0.1",
        "--server-port",
        "8002",
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

    await asyncio.sleep(3)

    if process.returncode is not None:
        stdout, stderr = await process.communicate()
        raise RuntimeError(
            f"Server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}"
        )

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
        "mcp-neo4j-cypher",
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
        "mcp-neo4j-cypher",
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
        "mcp-neo4j-cypher",
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


@pytest_asyncio.fixture
async def http_server_read_only(setup: Neo4jContainer):
    """Start the MCP server in HTTP mode with read-only enabled."""
    # Start server process in HTTP mode with read-only
    process = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "mcp-neo4j-cypher",
        "--transport",
        "http",
        "--server-host",
        "127.0.0.1",
        "--server-port",
        "8005",
        "--read-only",
        "--db-url",
        setup.get_connection_url(),
        "--username",
        setup.username,
        "--password",
        setup.password,
        env=os.environ.copy(),
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
            f"Read-only server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}"
        )

    yield process

    # Cleanup
    try:
        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
