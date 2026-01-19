# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See the parent [CLAUDE.md](../../CLAUDE.md) for monorepo-wide patterns and commands.

## Server Overview

MCP server providing persistent knowledge graph memory through Neo4j. Entities are stored as nodes with name, type, and observations; relationships connect entities.

## Development Commands

```bash
# Setup
uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"

# Run tests (starts Neo4j testcontainer automatically)
./test.sh

# Run single test file
uv run pytest tests/unit/test_utils.py -s

# Run single test
uv run pytest tests/unit/test_utils.py::test_function_name -s

# Linting
uv run ruff check --select I . --fix && uv run ruff check --fix . && uv run ruff format .

# Run server locally
uv run mcp-neo4j-memory --db-url bolt://localhost:7687 --username neo4j --password password
```

## Architecture

```
src/mcp_neo4j_memory/
├── __init__.py      # CLI entry point (argparse -> process_config -> server.main)
├── server.py        # create_mcp_server() + main() async server loop
├── neo4j_memory.py  # Neo4jMemory class with all graph operations
└── utils.py         # process_config() merges CLI args with env vars
```

### World Model Schema

Entities use typed labels from `Neo4jMemory.ENTITY_LABELS` (Person, Organization, Project, etc.) rather than a single `Memory` label. The fulltext index spans all entity types for search.

### Key Classes

- **`Neo4jMemory`**: Core graph operations - CRUD for entities/relations/observations, fulltext search via `load_graph(filter_query)`
- **`Entity`/`Relation`/`KnowledgeGraph`**: Pydantic models in `neo4j_memory.py`

### MCP Tools

Tools are registered with optional namespace prefix (`{namespace}-tool_name`):
- `read_graph`, `search_memories`, `find_memories_by_name` (read-only)
- `create_entities`, `create_relations`, `add_observations` (idempotent writes)
- `delete_entities`, `delete_relations`, `delete_observations` (destructive)

### Configuration Priority

CLI args override environment variables. Key mappings:
- `--db-url` / `NEO4J_URL` / `NEO4J_URI`
- `--transport` / `NEO4J_TRANSPORT` (stdio|sse|http)
- `--namespace` / `NEO4J_NAMESPACE`

## Testing

Integration tests use `testcontainers[neo4j]` - no manual Neo4j setup needed. The conftest.py fixture starts a container per module.

```bash
# Unit tests only (no Neo4j needed)
uv run pytest tests/unit -s

# Integration tests (auto-starts Neo4j container)
uv run pytest tests/integration -s
```
