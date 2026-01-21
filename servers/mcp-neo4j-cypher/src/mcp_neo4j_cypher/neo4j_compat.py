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
import time
from functools import lru_cache
from typing import Any, Callable, TypeVar

from neo4j import GraphDatabase

logger = logging.getLogger("mcp_neo4j_cypher")

T = TypeVar("T")

# Default auto-limit for queries without LIMIT clause
DEFAULT_AUTO_LIMIT = 1000

# Schema cache TTL in seconds (5 minutes)
SCHEMA_CACHE_TTL = 300


class QueryTimeoutError(Exception):
    """Raised when a query exceeds the timeout limit (not used in 3.5)."""
    pass


class Neo4j35Driver:
    """
    Compatibility wrapper for connecting to Neo4j 3.5 servers.
    
    Uses modern driver API (5.x/6.x) but provides methods that are
    aware of Neo4j 3.5 server limitations.
    
    Features:
    - Schema caching (5-minute TTL)
    - Connection keep-alive
    - Auto-LIMIT for queries without LIMIT
    """

    def __init__(self, uri: str, auth: tuple[str, str], auto_limit: int = DEFAULT_AUTO_LIMIT):
        self._driver = GraphDatabase.driver(
            uri, 
            auth=auth,
            max_connection_lifetime=3600,  # 1 hour
            max_connection_pool_size=50,
            connection_acquisition_timeout=30,
        )
        self._uri = uri
        self._server_version = None
        self._auto_limit = auto_limit
        self._schema_cache = None
        self._schema_cache_time = 0

    def close(self):
        """Close the driver connection."""
        self._driver.close()

    def verify_connectivity(self):
        """Verify the driver can connect to the database."""
        with self._driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.consume()

    def get_server_version(self) -> str:
        """Get the Neo4j server version."""
        if self._server_version is None:
            with self._driver.session() as session:
                result = session.run(
                    "CALL dbms.components() YIELD versions RETURN versions[0] as version"
                )
                record = result.single()
                self._server_version = record["version"] if record else "unknown"
        return self._server_version

    def is_neo4j_35(self) -> bool:
        """Check if connected to Neo4j 3.5.x server."""
        version = self.get_server_version()
        return version.startswith("3.5")

    def _add_limit_if_missing(self, query: str) -> str:
        """Add LIMIT clause if not present in query."""
        query_upper = query.upper()
        # Don't add LIMIT to queries that already have it or are aggregations
        if "LIMIT" in query_upper:
            return query
        if "COUNT(" in query_upper and "RETURN" in query_upper:
            # Aggregation query - don't add limit
            return query
        # Add limit before any trailing semicolons or whitespace
        query = query.rstrip().rstrip(';')
        return f"{query} LIMIT {self._auto_limit}"

    def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        result_transformer: Callable | None = None,
        timeout: int | None = None,  # Ignored - Neo4j 3.5 doesn't support timeouts
        auto_limit: bool = True,
    ) -> Any:
        """
        Execute a read query.
        
        Parameters
        ----------
        auto_limit : bool
            If True and query has no LIMIT, adds LIMIT clause automatically.
        
        Note: timeout parameter is ignored in Neo4j 3.5 (not supported).
        """
        parameters = parameters or {}
        
        if auto_limit:
            query = self._add_limit_if_missing(query)

        with self._driver.session() as session:
            result = session.run(query, parameters)
            if result_transformer:
                return result_transformer(result)
            return result.data()

    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        result_transformer: Callable | None = None,
        timeout: int | None = None,  # Ignored - Neo4j 3.5 doesn't support timeouts
    ) -> Any:
        """
        Execute a write query.
        
        Note: timeout parameter is ignored in Neo4j 3.5 (not supported).
        """
        parameters = parameters or {}

        with self._driver.session() as session:
            result = session.run(query, parameters)
            if result_transformer:
                return result_transformer(result)
            return result.consume()

    def get_summary_counters(
        self, query: str, parameters: dict[str, Any] | None = None, timeout: int | None = None
    ) -> dict[str, int]:
        """
        Execute a write query and return the summary counters.
        
        Note: timeout parameter is ignored in Neo4j 3.5 (not supported).
        """
        parameters = parameters or {}

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

    def get_schema_cached(self, sample_size: int = 100) -> dict:
        """
        Get schema with caching (5-minute TTL).
        
        This significantly speeds up repeated schema requests.
        """
        current_time = time.time()
        
        # Return cached schema if still valid
        if self._schema_cache and (current_time - self._schema_cache_time) < SCHEMA_CACHE_TTL:
            logger.debug("Returning cached schema")
            return self._schema_cache
        
        # Fetch fresh schema
        logger.info(f"Fetching fresh schema (sample_size={sample_size})")
        query = f"CALL apoc.meta.schema({{sample: {sample_size}}}) YIELD value RETURN value"
        
        results = self.execute_read(query, auto_limit=False)
        if results:
            self._schema_cache = results[0].get("value", {})
            self._schema_cache_time = current_time
            return self._schema_cache
        
        return {}

    def clear_schema_cache(self):
        """Clear the schema cache."""
        self._schema_cache = None
        self._schema_cache_time = 0


def create_driver(uri: str, username: str, password: str, auto_limit: int = DEFAULT_AUTO_LIMIT) -> Neo4j35Driver:
    """
    Create a Neo4j 3.5 compatible driver.
    """
    return Neo4j35Driver(uri, auth=(username, password), auto_limit=auto_limit)
