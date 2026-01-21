"""
Neo4j 3.5 Compatibility Layer

This module provides a compatibility layer for connecting to Neo4j 3.5 servers
using modern Neo4j Python drivers (5.x/6.x).

Key considerations when using modern driver with Neo4j 3.5 server:
- No multi-database support (single database only, ignore database param)
- Different Cypher syntax for constraints and indexes
- APOC procedures may have different signatures
- Fulltext index creation uses CALL procedures, not CREATE syntax
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, TypeVar

from neo4j import GraphDatabase

logger = logging.getLogger("mcp_neo4j_cypher")

T = TypeVar("T")

# Default query timeout in seconds (Neo4j 3.5 doesn't support native timeouts)
# 60 seconds is reasonable for most queries; increase for very large datasets
DEFAULT_QUERY_TIMEOUT = 60


class QueryTimeoutError(Exception):
    """Raised when a query exceeds the timeout limit."""
    pass


class Neo4j35Driver:
    """
    Compatibility wrapper for connecting to Neo4j 3.5 servers.
    
    Uses modern driver API (5.x/6.x) but provides methods that are
    aware of Neo4j 3.5 server limitations.
    """

    def __init__(self, uri: str, auth: tuple[str, str]):
        self._driver = GraphDatabase.driver(uri, auth=auth)
        self._uri = uri
        self._server_version = None

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

    def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        result_transformer: Callable | None = None,
        timeout: int | None = None,
    ) -> Any:
        """
        Execute a read query with optional timeout.
        
        Parameters
        ----------
        query : str
            The Cypher query to execute.
        parameters : dict, optional
            Parameters to pass to the query.
        result_transformer : callable, optional
            Function to transform the result. Defaults to returning data().
        timeout : int, optional
            Query timeout in seconds. Defaults to DEFAULT_QUERY_TIMEOUT.
            
        Returns
        -------
        Any
            The query results, transformed if a transformer is provided.
            
        Raises
        ------
        QueryTimeoutError
            If the query exceeds the timeout limit.
        """
        parameters = parameters or {}
        timeout = timeout or DEFAULT_QUERY_TIMEOUT

        def _run_query():
            with self._driver.session() as session:
                result = session.run(query, parameters)
                if result_transformer:
                    return result_transformer(result)
                return result.data()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_query)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                logger.warning(f"Query timed out after {timeout}s: {query[:100]}...")
                raise QueryTimeoutError(
                    f"Query timed out after {timeout} seconds. "
                    "Consider using LIMIT or adding WHERE clauses to reduce result set."
                )

    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        result_transformer: Callable | None = None,
        timeout: int | None = None,
    ) -> Any:
        """
        Execute a write query with optional timeout.
        
        Parameters
        ----------
        query : str
            The Cypher query to execute.
        parameters : dict, optional
            Parameters to pass to the query.
        result_transformer : callable, optional
            Function to transform the result.
        timeout : int, optional
            Query timeout in seconds. Defaults to DEFAULT_QUERY_TIMEOUT.
            
        Returns
        -------
        Any
            The query results or summary, depending on transformer.
            
        Raises
        ------
        QueryTimeoutError
            If the query exceeds the timeout limit.
        """
        parameters = parameters or {}
        timeout = timeout or DEFAULT_QUERY_TIMEOUT

        def _run_query():
            with self._driver.session() as session:
                result = session.run(query, parameters)
                if result_transformer:
                    return result_transformer(result)
                return result.consume()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_query)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                logger.warning(f"Query timed out after {timeout}s: {query[:100]}...")
                raise QueryTimeoutError(
                    f"Query timed out after {timeout} seconds. "
                    "Consider breaking this query into smaller operations."
                )

    def get_summary_counters(
        self, query: str, parameters: dict[str, Any] | None = None, timeout: int | None = None
    ) -> dict[str, int]:
        """
        Execute a write query and return the summary counters with optional timeout.
        
        Returns
        -------
        dict
            Dictionary with counter names and values.
            
        Raises
        ------
        QueryTimeoutError
            If the query exceeds the timeout limit.
        """
        parameters = parameters or {}
        timeout = timeout or DEFAULT_QUERY_TIMEOUT

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

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_query)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                logger.warning(f"Query timed out after {timeout}s: {query[:100]}...")
                raise QueryTimeoutError(
                    f"Query timed out after {timeout} seconds. "
                    "Consider breaking this into smaller operations."
                )


def create_driver(uri: str, username: str, password: str) -> Neo4j35Driver:
    """
    Create a Neo4j 3.5 compatible driver.
    
    Parameters
    ----------
    uri : str
        Neo4j connection URI (e.g., bolt://localhost:7687)
    username : str
        Neo4j username
    password : str
        Neo4j password
        
    Returns
    -------
    Neo4j35Driver
        A compatibility driver wrapper.
    """
    return Neo4j35Driver(uri, auth=(username, password))
