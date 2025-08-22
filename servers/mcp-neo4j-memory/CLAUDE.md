# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- **Install dependencies**: `uv pip install -e ".[dev]"`
- **Run server locally**: `uv run mcp-neo4j-memory --db-url <url> --username <user> --password <pass>`
- **Run tests**: `uv run pytest`
- **Run integration tests**: `uv run pytest tests/integration/`
- **Run unit tests**: `uv run pytest tests/unit/`
- **Type checking**: `uv run pyright`

## Architecture Overview

This is a **Model Context Protocol (MCP) server** that provides persistent memory capabilities through Neo4j graph database integration. The architecture consists of:

### Core Components

- **`server.py`**: FastMCP server implementation with MCP tool definitions and Neo4j connection management
- **`neo4j_memory.py`**: Core Neo4j memory operations (CRUD operations on entities, relations, observations)
- **`utils.py`**: Configuration processing utilities
- **`__init__.py`**: Main entry point with CLI argument parsing

### Data Model

The memory system uses a simple graph schema:
- **Memory nodes**: Entities with `name`, `type`, and `observations` properties
- **Relationships**: Typed connections between entities with `relationType`

### Transport Modes

The server supports three transport mechanisms:
- **STDIO** (default): For Claude Desktop integration
- **HTTP**: For web-based deployments and microservices  
- **SSE**: Server-Sent Events for web applications

### MCP Tools Architecture

All tools follow the FastMCP pattern with:
- Pydantic model validation for inputs/outputs
- Structured error handling with Neo4jError catching
- ToolResult responses with both text and structured content
- Proper tool annotations (readOnly, destructive, idempotent hints)

## Key Implementation Details

- Uses **FastMCP 2.x** framework for MCP server implementation
- Requires **Neo4j 5.26.0+** with fulltext search index creation
- All database operations are async using Neo4j Python driver
- Integration tests use **testcontainers** for isolated Neo4j instances
- Configuration supports both CLI arguments and environment variables

## Testing Strategy

- **Unit tests**: Test individual utility functions
- **Integration tests**: Full server testing with real Neo4j containers for each transport mode
- **Test fixtures**: Shared Neo4j container setup and driver management in `conftest.py`
- Use `uv run pytest` to ensure proper dependency resolution