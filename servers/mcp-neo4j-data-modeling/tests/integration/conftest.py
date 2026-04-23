import asyncio
import os
import subprocess
from typing import Any

import pytest
import pytest_asyncio
from neo4j import AsyncGraphDatabase
from testcontainers.neo4j import Neo4jContainer

from mcp_neo4j_data_modeling.server import create_mcp_server

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
async def mcp_server():
    mcp = create_mcp_server()
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
async def sse_server():
    """Start the MCP server in SSE mode."""

    process = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "mcp-neo4j-data-modeling",
        "--transport",
        "sse",
        "--server-host",
        "127.0.0.1",
        "--server-port",
        "8002",
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
