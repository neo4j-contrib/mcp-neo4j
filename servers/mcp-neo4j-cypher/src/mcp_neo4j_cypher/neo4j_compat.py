"""
Neo4j 3.5 Compatibility Layer

This module provides a compatibility layer for connecting to Neo4j 3.5 servers
using modern Neo4j Python drivers (5.x/6.x).

Key considerations when using modern driver with Neo4j 3.5 server:
- No multi-database support (single database only, ignore database param)
- Different Cypher syntax for constraints and indexes
- APOC procedures may have different signatures
- Fulltext index creation uses CALL procedures, not CREATE syntax
- No query timeout support (Neo4j 3.5 limitation)
"""

import logging
import threading
import time
from typing import Any, Callable, TypeVar

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired

logger = logging.getLogger("mcp_neo4j_cypher")

T = TypeVar("T")

SCHEMA_CACHE_TTL = 300  # 5 minutes
KEEP_ALIVE_INTERVAL = 30  # seconds
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY = 1  # seconds


class QueryTimeoutError(Exception):
    """Raised when a query exceeds the timeout limit (not used in 3.5)."""
    pass


class ConnectionError(Exception):
    """Raised when connection to Neo4j fails after retries."""
    pass


class Neo4j35Driver:
    """
    Compatibility wrapper for connecting to Neo4j 3.5 servers.
    
    Features:
    - Schema caching (5-minute TTL)
    - Auto-reconnect on connection failure
    - Keep-alive ping to prevent idle disconnects
    - Connection validation before queries
    """

    def __init__(self, uri: str, auth: tuple[str, str]):
        self._uri = uri
        self._auth = auth
        self._driver = None
        self._server_version = None
        self._schema_cache = None
        self._schema_cache_time = 0
        self._last_ping_time = 0
        self._lock = threading.Lock()
        self._create_driver()

    def _create_driver(self):
        """Create or recreate the Neo4j driver."""
        if self._driver:
            try:
                self._driver.close()
            except Exception:
                pass
        
        self._driver = GraphDatabase.driver(
            self._uri, 
            auth=self._auth,
            max_connection_lifetime=1800,  # 30 minutes (shorter)
            max_connection_pool_size=10,   # smaller pool
            connection_acquisition_timeout=30,
            connection_timeout=10,
        )
        self._last_ping_time = time.time()
        logger.info("Neo4j driver created/recreated")

    def _ensure_connected(self):
        """Ensure connection is alive, reconnect if needed."""
        current_time = time.time()
        
        # Ping if idle for more than KEEP_ALIVE_INTERVAL
        if current_time - self._last_ping_time > KEEP_ALIVE_INTERVAL:
            try:
                self._ping()
            except Exception as e:
                logger.warning(f"Keep-alive ping failed: {e}, reconnecting...")
                self._reconnect()

    def _ping(self):
        """Send a simple query to keep connection alive."""
        with self._driver.session() as session:
            result = session.run("RETURN 1")
            result.consume()
        self._last_ping_time = time.time()

    def _reconnect(self):
        """Attempt to reconnect to Neo4j."""
        with self._lock:
            for attempt in range(MAX_RECONNECT_ATTEMPTS):
                try:
                    logger.info(f"Reconnect attempt {attempt + 1}/{MAX_RECONNECT_ATTEMPTS}")
                    self._create_driver()
                    self._ping()
                    logger.info("Reconnection successful")
                    return
                except Exception as e:
                    logger.warning(f"Reconnect attempt {attempt + 1} failed: {e}")
                    if attempt < MAX_RECONNECT_ATTEMPTS - 1:
                        time.sleep(RECONNECT_DELAY * (attempt + 1))
            
            raise ConnectionError(
                f"Failed to reconnect to Neo4j after {MAX_RECONNECT_ATTEMPTS} attempts"
            )

    def _execute_with_retry(self, operation: Callable[[], T]) -> T:
        """Execute an operation with automatic retry on connection failure."""
        self._ensure_connected()
        
        for attempt in range(MAX_RECONNECT_ATTEMPTS):
            try:
                return operation()
            except (ServiceUnavailable, SessionExpired) as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt < MAX_RECONNECT_ATTEMPTS - 1:
                    self._reconnect()
                else:
                    raise ConnectionError(f"Query failed after {MAX_RECONNECT_ATTEMPTS} attempts: {e}")
        
        raise ConnectionError("Unexpected: retry loop exited without result")

    def close(self):
        """Close the driver connection."""
        if self._driver:
            self._driver.close()

    def verify_connectivity(self):
        """Verify the driver can connect to the database."""
        self._ping()

    def get_server_version(self) -> str:
        """Get the Neo4j server version."""
        if self._server_version is None:
            def _get_version():
                with self._driver.session() as session:
                    result = session.run(
                        "CALL dbms.components() YIELD versions RETURN versions[0] as version"
                    )
                    record = result.single()
                    return record["version"] if record else "unknown"
            
            self._server_version = self._execute_with_retry(_get_version)
        return self._server_version

    def is_neo4j_35(self) -> bool:
        """Check if connected to Neo4j 3.5.x server."""
        version = self.get_server_version()
        return version.startswith("3.5")

    def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        result_transformer: Callable | None = None,
        timeout: int | None = None,
    ) -> Any:
        """Execute a read query with auto-reconnect."""
        parameters = parameters or {}

        def _run_query():
            with self._driver.session() as session:
                result = session.run(query, parameters)
                if result_transformer:
                    return result_transformer(result)
                return result.data()

        return self._execute_with_retry(_run_query)

    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        result_transformer: Callable | None = None,
        timeout: int | None = None,
    ) -> Any:
        """Execute a write query with auto-reconnect."""
        parameters = parameters or {}

        def _run_query():
            with self._driver.session() as session:
                result = session.run(query, parameters)
                if result_transformer:
                    return result_transformer(result)
                return result.consume()

        return self._execute_with_retry(_run_query)

    def get_summary_counters(
        self, query: str, parameters: dict[str, Any] | None = None, timeout: int | None = None
    ) -> dict[str, int]:
        """Execute a write query and return summary counters with auto-reconnect."""
        parameters = parameters or {}

        def _run_query():
            with self._driver.session() as session:
                result = session.run(query, parameters)
                summary = result.consume()
                counters = summary.counters
                return {
                    "nodes_created": counters.nodes_created,
                    "nodes_deleted": counters.nodes_deleted,
                    "relationships_created": counters.relationships_created,
                    "relationships_deleted": counters.relationships_deleted,
                    "properties_set": counters.properties_set,
                    "labels_added": counters.labels_added,
                    "labels_removed": counters.labels_removed,
                    "indexes_added": counters.indexes_added,
                    "indexes_removed": counters.indexes_removed,
                    "constraints_added": counters.constraints_added,
                    "constraints_removed": counters.constraints_removed,
                }

        return self._execute_with_retry(_run_query)

    def get_schema_cached(self, sample_size: int = 100) -> dict:
        """Get schema with caching (5-minute TTL) and auto-reconnect."""
        current_time = time.time()
        
        if self._schema_cache and (current_time - self._schema_cache_time) < SCHEMA_CACHE_TTL:
            logger.debug("Returning cached schema")
            return self._schema_cache
        
        logger.info(f"Fetching fresh schema (sample_size={sample_size})")
        query = f"CALL apoc.meta.schema({{sample: {sample_size}}}) YIELD value RETURN value"
        
        results = self.execute_read(query)  # Already uses retry
        if results:
            self._schema_cache = results[0].get("value", {})
            self._schema_cache_time = current_time
            return self._schema_cache
        
        return {}

    def clear_schema_cache(self):
        """Clear the schema cache."""
        self._schema_cache = None
        self._schema_cache_time = 0


def create_driver(uri: str, username: str, password: str) -> Neo4j35Driver:
    """
    Create a Neo4j 3.5 compatible driver.
    """
    return Neo4j35Driver(uri, auth=(username, password))
