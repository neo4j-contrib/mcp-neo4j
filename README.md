# Neo4j Labs MCP Servers

## Neo4j Labs

These MCP servers are a part of the [Neo4j Labs](https://neo4j.com/labs/) program.
They are developed and maintained by the Neo4j Field GenAI team and welcome contributions from the larger developer community.
These servers are frequently updated with new and experimental features, but are not supported by the Neo4j product team.

**They are actively developed and maintained, but we don't provide any SLAs or guarantees around backwards compatibility and deprecation.**

If you are looking for the official product Neo4j MCP server please find it [here](https://github.com/neo4j/mcp).

## Overview

Model Context Protocol (MCP) is a [standardized protocol](https://modelcontextprotocol.io/introduction) for managing context between large language models (LLMs) and external systems.

This lets you use Claude Desktop, or any other MCP Client (VS Code, Cursor, Windsurf), to use natural language to accomplish things with Neo4j and your Aura account, e.g.:

- What is in this graph?
- Render a chart from the top products sold by frequency, total and average volume
- List my instances
- Create a new instance named mcp-test for Aura Professional with 4GB and Graph Data Science enabled
- Store the fact that I worked on the Neo4j MCP Servers today with Andreas and Oskar

## Servers

### `mcp-neo4j-cypher` - natural language to Cypher queries

[Details in Readme](./servers/mcp-neo4j-cypher/)

Get database schema for a configured database and execute generated read and write Cypher queries on that database.

### `mcp-neo4j-memory` - knowledge graph memory stored in Neo4j

[Details in Readme](./servers/mcp-neo4j-memory/)

Store and retrieve entities and relationships from your personal knowledge graph in a local or remote Neo4j instance.
Access that information over different sessions, conversations, clients.

### `mcp-neo4j-cloud-aura-api` - Neo4j Aura cloud service management API

[Details in Readme](./servers/mcp-neo4j-cloud-aura-api//)

Manage your [Neo4j Aura](https://console.neo4j.io) instances directly from the comfort of your AI assistant chat.

Create and destroy instances, find instances by name, scale them up and down and enable features.

### `mcp-neo4j-data-modeling` - interactive graph data modeling and visualization

[Details in Readme](./servers/mcp-neo4j-data-modeling/)

Create, validate, and visualize Neo4j graph data models. Allows for model import/export from Arrows.app.

## Transport Modes

All servers support multiple transport modes:

- **STDIO** (default): Standard input/output for local tools and Claude Desktop integration
- **SSE**: Server-Sent Events for web-based deployments
- **HTTP**: Streamable HTTP for modern web deployments and microservices

### HTTP Transport Configuration

To run a server in HTTP mode, use the `--transport http` flag:

```bash
# Basic HTTP mode
mcp-neo4j-cypher --transport http

# Custom HTTP configuration
mcp-neo4j-cypher --transport http --host 127.0.0.1 --port 8080 --path /api/mcp/
```

Environment variables are also supported:

```bash
export NEO4J_TRANSPORT=http
export NEO4J_MCP_SERVER_HOST=127.0.0.1
export NEO4J_MCP_SERVER_PORT=8080
export NEO4J_MCP_SERVER_PATH=/api/mcp/
mcp-neo4j-cypher
```

## Cloud Deployment

All servers in this repository are containerized and ready for cloud deployment on platforms like AWS ECS Fargate and Azure Container Apps. Each server supports HTTP transport mode specifically designed for scalable, production-ready deployments with auto-scaling and load balancing capabilities.

📋 **[Complete Cloud Deployment Guide →](README-Cloud.md)**

The deployment guide covers:

- **AWS ECS Fargate**: Step-by-step deployment with auto-scaling and Application Load Balancer
- **Azure Container Apps**: Serverless container deployment with built-in scaling and traffic management
- **Configuration Best Practices**: Security, monitoring, resource recommendations, and troubleshooting
- **Integration Examples**: Connecting MCP clients to cloud-deployed servers

---

## Neo4j 3.5 Compatibility

For users running Neo4j 3.5, a compatibility layer is available for `mcp-neo4j-cypher`, `mcp-neo4j-memory`, and `mcp-neo4j-data-modeling` servers.

> **Note:** Neo4j 3.5 has limitations compared to 5.x (no async driver, no multi-database, no query timeouts).

### Prerequisites

- Python 3.10 or higher
- Neo4j 3.5.x with APOC plugin installed
- Git

### Installation

#### Step 1: Clone the Repository

```bash
git clone https://github.com/neo4j-labs/mcp-neo4j.git
cd mcp-neo4j
```

#### Step 2: Install Python Dependencies

```bash
pip install fastmcp pydantic tiktoken neo4j
```

Or using uv:

```bash
uv pip install fastmcp pydantic tiktoken neo4j
```

#### Step 3: Verify Installation

Test the server starts correctly:

```bash
NEO4J_URL="bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687" \
NEO4J_USERNAME="neo4j" \
NEO4J_PASSWORD="your-password" \
python3 mcp_neo4j_35_runner.py
```

You should see the FastMCP banner and "Starting MCP server".

### Client Configuration

#### Cursor IDE

1. Open Cursor Settings (`Cmd+,` on Mac, `Ctrl+,` on Windows)
2. Search for "MCP" or navigate to MCP settings
3. Click "Edit in settings.json" or open `~/.cursor/mcp.json`
4. Add the following configuration:

```json
{
  "mcpServers": {
    "neo4j-cypher-35": {
      "command": "python3",
      "args": ["/full/path/to/mcp-neo4j/mcp_neo4j_35_runner.py"],
      "env": {
        "NEO4J_URL": "bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "READ_ONLY": "true"
      }
    }
  }
}
```

5. Restart Cursor
6. In Cursor chat, you now have access to Neo4j tools

#### Claude Desktop

1. Open the config file:

   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the configuration:

```json
{
  "mcpServers": {
    "neo4j-cypher-35": {
      "command": "python3",
      "args": ["/full/path/to/mcp-neo4j/mcp_neo4j_35_runner.py"],
      "env": {
        "NEO4J_URL": "bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "READ_ONLY": "true"
      }
    }
  }
}
```

3. Restart Claude Desktop

#### ChatGPT

> **Note:** ChatGPT does not natively support MCP. To use this server with ChatGPT, you need to:
>
> 1. Run the server in HTTP mode
> 2. Use a custom GPT with Actions that call the HTTP endpoints

**Run in HTTP mode:**

```bash
NEO4J_URL="bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687" \
NEO4J_USERNAME="neo4j" \
NEO4J_PASSWORD="your-password" \
TRANSPORT="http" \
HOST="0.0.0.0" \
PORT="8000" \
python3 mcp_neo4j_35_runner.py
```

The server will be available at `http://localhost:8000/mcp/`

### Environment Variables (Neo4j 3.5)

| Variable             | Required | Default     | Description                                    |
| -------------------- | -------- | ----------- | ---------------------------------------------- |
| `NEO4J_URL`          | ✅       | -           | Neo4j bolt URL (e.g., `bolt://localhost:7687`) |
| `NEO4J_USERNAME`     | ✅       | -           | Neo4j username                                 |
| `NEO4J_PASSWORD`     | ✅       | -           | Neo4j password                                 |
| `READ_ONLY`          | ❌       | `false`     | Set to `true` to disable write operations      |
| `TRANSPORT`          | ❌       | `stdio`     | Transport mode: `stdio`, `http`, or `sse`      |
| `HOST`               | ❌       | `127.0.0.1` | Server host (for http/sse)                     |
| `PORT`               | ❌       | `8000`      | Server port (for http/sse)                     |
| `SCHEMA_SAMPLE_SIZE` | ❌       | `1000`      | Sample size for schema inference               |
| `QUERY_TIMEOUT`      | ❌       | `60`        | Query timeout in seconds (Python-level)        |

### Available Tools (Neo4j 3.5)

| Tool                 | Description                      | Read-Only                         |
| -------------------- | -------------------------------- | --------------------------------- |
| `get_neo4j_schema`   | Explore graph structure via APOC | ✅                                |
| `read_neo4j_cypher`  | Execute read Cypher queries      | ✅                                |
| `write_neo4j_cypher` | Execute write Cypher queries     | ❌ (disabled when READ_ONLY=true) |

### Neo4j 3.5 Limitations

| Feature                      | Neo4j 5.x | Neo4j 3.5        |
| ---------------------------- | --------- | ---------------- |
| Async driver                 | ✅        | ❌               |
| Multi-database               | ✅        | ❌               |
| Query timeouts               | ✅        | ❌               |
| NODE KEY constraints         | ✅        | ❌ (UNIQUE only) |
| RELATIONSHIP KEY constraints | ✅        | ❌               |
| IF NOT EXISTS clauses        | ✅        | ❌               |
| Vector search                | ✅        | ❌               |

### Neo4j 3.5 Files

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

### APOC Requirements (Neo4j 3.5)

Neo4j 3.5 requires APOC version 3.5.x for schema inspection:

1. Download from: https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/tag/3.5.0.15
2. Place the JAR in `$NEO4J_HOME/plugins/`
3. Restart Neo4j

Verify APOC is installed:

```cypher
CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'apoc' RETURN count(name)
```

### Troubleshooting (Neo4j 3.5)

#### Restart the MCP Server

If the server becomes unresponsive, kill and restart it:

```bash
# Find and kill the server process
lsof -ti:8000 | xargs kill -9

# Restart the server
NEO4J_URL="bolt://neo4j-v2.domain-base.euw1.n8s.appsflyer.engineering:7687" \
NEO4J_USERNAME="neo4j" \
NEO4J_PASSWORD="your-password" \
python3 mcp_neo4j_35_runner.py
```

#### Query hangs or times out

Neo4j 3.5 does **not support native query timeouts**. However, this server includes a **Python-level timeout** (default: 60 seconds) that will abort long-running queries.

If a query times out, you'll see:

```
Query timed out (60s limit). Tips: Use LIMIT, add WHERE clauses, or avoid GROUP BY on large datasets.
```

**Best practices:**

- Always use `LIMIT` on large result sets
- Avoid `GROUP BY` on unindexed properties with millions of records
- Use `WHERE` clauses to filter data before aggregation
- Increase timeout with `QUERY_TIMEOUT` env var if needed

```cypher
-- Bad: Will timeout on large datasets
MATCH (n:App) RETURN n.platform, count(*) GROUP BY n.platform

-- Good: Use LIMIT
MATCH (n:App) RETURN n.name, n.platform LIMIT 100
```

#### Connection refused

Make sure Neo4j is running and accessible:

```bash
curl -I http://localhost:7474
```

#### Connection dropped / defunct connection

The Neo4j connection may drop after idle time. Restart the MCP server:

```bash
lsof -ti:8000 | xargs kill -9
# Then restart the server
```

#### "Procedure not found" errors

APOC is not installed. See [APOC Requirements](#apoc-requirements-neo4j-35).

#### "Index already exists" warnings

This is normal - Neo4j 3.5 doesn't support `IF NOT EXISTS`. The code handles this gracefully.

#### Server won't start

Check that all required environment variables are set:

```bash
echo $NEO4J_URL $NEO4J_USERNAME $NEO4J_PASSWORD
```

#### Port already in use

Kill any existing process on port 8000:

```bash
lsof -ti:8000 | xargs kill -9
```

### Cypher Syntax Differences (3.5 vs 5.x)

#### Fulltext Index

**Neo4j 5.x:**

```cypher
CREATE FULLTEXT INDEX search IF NOT EXISTS
FOR (m:Memory) ON EACH [m.name, m.type]
```

**Neo4j 3.5:**

```cypher
CALL db.index.fulltext.createNodeIndex('search', ['Memory'], ['name', 'type'])
```

#### Constraints

**Neo4j 5.x:**

```cypher
CREATE CONSTRAINT Person_id IF NOT EXISTS FOR (n:Person) REQUIRE (n.id) IS NODE KEY
```

**Neo4j 3.5:**

```cypher
CREATE CONSTRAINT ON (n:Person) ASSERT n.id IS UNIQUE
```

### Migration to Neo4j 5.x

When ready to upgrade:

1. Use the original server files (without `_35` suffix)
2. Update your Neo4j connection to the 5.x instance
3. Reinstall dependencies: `pip install neo4j>=5.0`

See: https://neo4j.com/docs/upgrade-migration-guide/current/

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Blog Posts

- [Everything a Developer Needs to Know About the Model Context Protocol (MCP)](https://neo4j.com/blog/developer/model-context-protocol/)
- [Claude Converses With Neo4j Via MCP - Graph Database & Analytics](https://neo4j.com/blog/developer/claude-converses-neo4j-via-mcp/)
- [Building Knowledge Graphs With Claude and Neo4j: A No-Code MCP Approach - Graph Database & Analytics](https://neo4j.com/blog/developer/knowledge-graphs-claude-neo4j-mcp/)

## License

MIT License
