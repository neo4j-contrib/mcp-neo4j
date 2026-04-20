# Neo4j 3.5 MCP Server

A compatibility layer for running MCP servers with Neo4j 3.5.

> **Note:** Neo4j 3.5 has limitations compared to 5.x (no async driver, no multi-database, no native query timeouts).

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (it will install the right Python for you)
- Neo4j 3.5.x with APOC plugin installed
- Git

You do **not** need a pre-installed Python. `uv` reads `.python-version` and downloads a matching interpreter on first run.

Install `uv` if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/neo4j-labs/mcp-neo4j.git
cd mcp-neo4j
```

### Step 2: Verify Installation (Optional)

Test that the server starts correctly:

```bash
NEO4J_URL="bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687" \
NEO4J_USERNAME="neo4j" \
NEO4J_PASSWORD="you-know-the-password" \
uv run mcp_neo4j_35_runner.py
```

The first run downloads Python and installs dependencies. You should see the FastMCP banner and "Starting MCP server".

## Client Configuration

### Cursor IDE

1. Open Cursor Settings (`Cmd+,` on Mac, `Ctrl+,` on Windows)
2. Search for "MCP" or navigate to MCP settings
3. Click "Edit in settings.json" or open `~/.cursor/mcp.json`
4. Add the following configuration:

```json
{
  "mcpServers": {
    "neo4j-35": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/full/path/to/mcp-neo4j",
        "mcp_neo4j_35_runner.py"
      ],
      "env": {
        "NEO4J_URL": "bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "you-know-the-password",
        "READ_ONLY": "true"
      }
    }
  }
}
```

Replace `uv` with the absolute path (`which uv`) if your MCP client does not see your `PATH`.

5. Restart Cursor
6. In Cursor chat, you now have access to Neo4j tools

### Claude Desktop

1. Open the config file:

   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the configuration:

```json
{
  "mcpServers": {
    "neo4j-35": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/full/path/to/mcp-neo4j",
        "mcp_neo4j_35_runner.py"
      ],
      "env": {
        "NEO4J_URL": "bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "you-know-the-password",
        "READ_ONLY": "true"
      }
    }
  }
}
```

3. Restart Claude Desktop

### ChatGPT

> **Note:** ChatGPT does not natively support MCP. To use this server with ChatGPT, you need to:
>
> 1. Run the server in HTTP mode
> 2. Use a custom GPT with Actions that call the HTTP endpoints

**Run in HTTP mode:**

```bash
NEO4J_URL="bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687" \
NEO4J_USERNAME="neo4j" \
NEO4J_PASSWORD="you-know-the-password" \
TRANSPORT="http" \
HOST="0.0.0.0" \
PORT="8000" \
uv run mcp_neo4j_35_runner.py
```

The server will be available at `http://localhost:8000/mcp/`

## Environment Variables

| Variable             | Required | Default     | Description                                                                              |
| -------------------- | -------- | ----------- | ---------------------------------------------------------------------------------------- |
| `NEO4J_URL`          | Yes      | -           | Neo4j bolt URL (e.g., `bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687`) |
| `NEO4J_USERNAME`     | Yes      | -           | Neo4j username                                                                           |
| `NEO4J_PASSWORD`     | Yes      | -           | Neo4j password                                                                           |
| `READ_ONLY`          | No       | `false`     | Set to `true` to disable write operations                                                |
| `TRANSPORT`          | No       | `stdio`     | Transport mode: `stdio`, `http`, or `sse`                                                |
| `HOST`               | No       | `127.0.0.1` | Server host (for http/sse)                                                               |
| `PORT`               | No       | `8000`      | Server port (for http/sse)                                                               |
| `SCHEMA_SAMPLE_SIZE` | No       | `1000`      | Sample size for schema inference                                                         |

## Available Tools

| Tool                 | Description                      | Read-Only                         |
| -------------------- | -------------------------------- | --------------------------------- |
| `get_neo4j_schema`   | Explore graph structure via APOC | Yes                               |
| `read_neo4j_cypher`  | Execute read Cypher queries      | Yes                               |
| `write_neo4j_cypher` | Execute write Cypher queries     | No (disabled when READ_ONLY=true) |

## Neo4j 3.5 Limitations

| Feature                      | Neo4j 5.x | Neo4j 3.5        |
| ---------------------------- | --------- | ---------------- |
| Async driver                 | Yes       | No               |
| Multi-database               | Yes       | No               |
| Query timeouts               | Yes       | No               |
| NODE KEY constraints         | Yes       | No (UNIQUE only) |
| RELATIONSHIP KEY constraints | Yes       | No               |
| IF NOT EXISTS clauses        | Yes       | No               |
| Vector search                | Yes       | No               |

## File Structure

```
mcp-neo4j/
├── mcp_neo4j_35_runner.py                              # Main entry point
└── servers/
    ├── mcp-neo4j-cypher/
    │   ├── pyproject-35.toml                           # Dependencies
    │   └── src/mcp_neo4j_cypher/
    │       ├── neo4j_compat.py                         # Driver compatibility
    │       └── server_35.py                            # Server implementation
    ├── mcp-neo4j-memory/
    │   └── src/mcp_neo4j_memory/
    │       ├── neo4j_memory_35.py                      # Memory operations
    │       └── server_35.py                            # Server implementation
    └── mcp-neo4j-data-modeling/
        └── src/mcp_neo4j_data_modeling/
            └── cypher_35.py                            # Constraint generation
```

## APOC Requirements

Neo4j 3.5 requires APOC version 3.5.x for schema inspection:

1. Download from: https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/tag/3.5.0.15
2. Place the JAR in `$NEO4J_HOME/plugins/`
3. Restart Neo4j

Verify APOC is installed:

```cypher
CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'apoc' RETURN count(name)
```

## Troubleshooting

### Restart the MCP Server

If the server becomes unresponsive, kill and restart it:

```bash
# Find and kill the server process
lsof -ti:8000 | xargs kill -9

# Restart the server
NEO4J_URL="bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687" \
NEO4J_USERNAME="neo4j" \
NEO4J_PASSWORD="you-know-the-password" \
uv run mcp_neo4j_35_runner.py
```

### Query hangs

Neo4j 3.5 does **not support query timeouts**. Long-running queries will block the server until they complete.

**Best practices:**

- Always use `LIMIT` on large result sets
- Avoid aggregations (COUNT, GROUP BY) on unindexed properties with millions of records
- Use `WHERE` clauses to filter data before aggregation
- Test complex queries directly in Neo4j Browser first

```cypher
-- Bad: May hang on large datasets
MATCH (n:App) RETURN n.platform, count(*)

-- Good: Use LIMIT
MATCH (n:App) RETURN n.name, n.platform LIMIT 100
```

### Connection refused

Make sure Neo4j is running and accessible:

```bash
curl -I http://localhost:7474
```

### Connection dropped / defunct connection

The Neo4j connection may drop after idle time. Restart the MCP server:

```bash
lsof -ti:8000 | xargs kill -9
# Then restart the server
```

### "Procedure not found" errors

APOC is not installed. See [APOC Requirements](#apoc-requirements).

### "Index already exists" warnings

This is normal - Neo4j 3.5 doesn't support `IF NOT EXISTS`. The code handles this gracefully.

### Server won't start

Check that all required environment variables are set:

```bash
echo $NEO4J_URL $NEO4J_USERNAME $NEO4J_PASSWORD
```

### Port already in use

Kill any existing process on port 8000:

```bash
lsof -ti:8000 | xargs kill -9
```

## Cypher Syntax Differences (3.5 vs 5.x)

### Fulltext Index

**Neo4j 5.x:**

```cypher
CREATE FULLTEXT INDEX search IF NOT EXISTS
FOR (m:Memory) ON EACH [m.name, m.type]
```

**Neo4j 3.5:**

```cypher
CALL db.index.fulltext.createNodeIndex('search', ['Memory'], ['name', 'type'])
```

### Constraints

**Neo4j 5.x:**

```cypher
CREATE CONSTRAINT Person_id IF NOT EXISTS FOR (n:Person) REQUIRE (n.id) IS NODE KEY
```

**Neo4j 3.5:**

```cypher
CREATE CONSTRAINT ON (n:Person) ASSERT n.id IS UNIQUE
```

## Migration to Neo4j 5.x

When ready to upgrade:

1. Use the original server files (without `_35` suffix)
2. Update your Neo4j connection to the 5.x instance

See: https://neo4j.com/docs/upgrade-migration-guide/current/
