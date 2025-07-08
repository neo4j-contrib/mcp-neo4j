import os
from typing import Any

import pytest
import pytest_asyncio
from neo4j import GraphDatabase
from testcontainers.neo4j import Neo4jContainer

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