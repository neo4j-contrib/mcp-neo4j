# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a monorepo containing four MCP (Model Context Protocol) servers for Neo4j integration, developed by the Neo4j Labs team. All servers are Python-based, use FastMCP, and support STDIO/SSE/HTTP transport modes.

### Servers

| Server | Directory | Purpose | PyPI Package |
|--------|-----------|---------|--------------|
| **mcp-neo4j-cypher** | `servers/mcp-neo4j-cypher/` | Execute Cypher queries, get schema | `mcp-neo4j-cypher` |
| **mcp-neo4j-memory** | `servers/mcp-neo4j-memory/` | Knowledge graph memory storage | `mcp-neo4j-memory` |
| **mcp-neo4j-data-modeling** | `servers/mcp-neo4j-data-modeling/` | Graph data model design/validation | `mcp-neo4j-data-modeling` |
| **mcp-neo4j-cloud-aura-api** | `servers/mcp-neo4j-cloud-aura-api/` | Neo4j Aura instance management | `mcp-neo4j-aura-manager` |

## Development Commands

Each server is developed independently within its directory. Commands must be run from the specific server directory.

### Setup (per server)
```bash
cd servers/mcp-neo4j-<server-name>
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Testing
```bash
# Integration tests (requires Neo4j running for cypher/memory servers)
cd servers/mcp-neo4j-cypher
./test.sh  # runs: uv run pytest tests/integration -s

# Memory server tests (sets env vars)
cd servers/mcp-neo4j-memory
./test.sh  # runs all tests with NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD set

# Data modeling (no Neo4j required)
cd servers/mcp-neo4j-data-modeling
./test.sh  # runs: uv run pytest -s
```

### Linting & Formatting
```bash
uv run ruff check --select I . --fix  # import sorting
uv run ruff check --fix .             # linting
uv run ruff format .                  # formatting
```

### Running a Server Locally
```bash
# STDIO mode (for Claude Desktop)
uv run mcp-neo4j-cypher --transport stdio

# HTTP mode (for web deployments)
uv run mcp-neo4j-cypher --transport http --server-host 127.0.0.1 --server-port 8000
```

### Building Docker Images
```bash
cd servers/mcp-neo4j-<server-name>
docker build -t mcp-neo4j-<server-name>:latest .
```

## Architecture

### Common Patterns Across All Servers

1. **Entry Point**: `src/<package>/__init__.py` contains `main()` with argparse CLI, calls `asyncio.run(server.main())`

2. **Server Creation**: `src/<package>/server.py` contains `create_mcp_server()` factory function that:
   - Creates `FastMCP` instance with `stateless_http=True`
   - Registers tools with namespace prefixing (e.g., `namespace-tool_name`)
   - Tools use `@mcp.tool()` decorator with `ToolAnnotations`

3. **Configuration**: Dual-source config via CLI args and environment variables:
   - `--db-url` / `NEO4J_URI`
   - `--transport` / `NEO4J_TRANSPORT`
   - `--namespace` / `NEO4J_NAMESPACE`
   - See individual READMEs for server-specific options

4. **Utilities**: `src/<package>/utils.py` contains shared helpers including `process_config()` for merging CLI/env config

5. **Security Middleware**: HTTP transport includes:
   - `TrustedHostMiddleware` for DNS rebinding protection
   - `CORSMiddleware` for cross-origin control

### Server-Specific Architecture

**mcp-neo4j-cypher**: Uses `neo4j.AsyncDriver` for database connections. Tools: `get_neo4j_schema`, `read_neo4j_cypher`, `write_neo4j_cypher`. Schema inspection uses APOC's `apoc.meta.schema()`.

**mcp-neo4j-memory**: `neo4j_memory.py` contains `Neo4jMemory` class managing typed entity nodes (Person, Organization, Project, etc.) with properties and relationships. Entities have name, type, observations, and a properties dict for structured data. Supports temporal tracking (`validAt`/`invalidAt`) for the Event Clock pattern. Tools: `read_graph`, `create_entities`, `create_relations`, `search_memories`, `find_memories_by_name`, `update_entity_properties`, `update_relation_properties`, etc. See `docs/WORLD_MODEL_SCHEMA.md` for the full schema.

**mcp-neo4j-data-modeling**: Pure validation/transformation - no Neo4j connection required. `data_model.py` contains validation logic, `models.py` has Pydantic models. Supports Arrows.app and OWL import/export.

**mcp-neo4j-cloud-aura-api**: `aura_api_client.py` handles OAuth2 authentication with Aura API. `aura_manager.py` wraps API operations. Tools manage instances and tenants.

## Test Structure

```
servers/<server>/tests/
├── integration/
│   ├── test_http_transport_IT.py
│   ├── test_sse_transport_IT.py
│   ├── test_stdio_transport_IT.py
│   └── test_*_IT.py (server-specific)
└── unit/
    └── test_*.py
```

Integration tests use `testcontainers[neo4j]` to spin up Neo4j instances. Tests use `pytest-asyncio`.

## CI/CD

- **PR Workflows**: `pr-mcp-neo4j-*.yml` - Run on changes to respective server directories
- **Publish Workflows**: `publish-*.yml` - Triggered by tags like `mcp-neo4j-cypher-v*`
- **Registry Workflows**: `github-registry-*.yml` - Publish to MCP registry

Publishing uses `uv build` and `uv publish` with PyPI trusted publishing.
