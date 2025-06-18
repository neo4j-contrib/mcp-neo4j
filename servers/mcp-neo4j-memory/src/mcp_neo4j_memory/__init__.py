"""
MCP Neo4j Memory - A modular knowledge graph memory server.

This package provides a clean, modular implementation of an MCP server
that uses Neo4j for knowledge graph storage and retrieval.

Modules:
- core: Core business logic, data models, and tool definitions
- protocols: Protocol implementations (stdio, SSE)
- cli: Command-line interface and configuration management
"""

from .cli import main
from . import core, protocols

__version__ = "0.1.4"
__all__ = ["main", "core", "protocols"]
