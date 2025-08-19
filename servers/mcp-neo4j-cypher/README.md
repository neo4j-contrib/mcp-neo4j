# 🔍⁉️ Neo4j MCP Server

## 🌟 Overview

A Model Context Protocol (MCP) server implementation that provides database interaction and allows graph exploration capabilities through Neo4j. This server enables running Cypher graph queries, analyzing complex domain data, and automatically generating business insights that can be enhanced with Claude's analysis.

## 🧩 Components

### 🛠️ Tools

The server offers these core tools:

#### 📊 Query Tools

- `read_neo4j_cypher`

  - Execute Cypher read queries to read data from the database
  - Input:
    - `query` (string): The Cypher query to execute
    - `params` (dictionary, optional): Parameters to pass to the Cypher query
  - Returns: Query results as JSON serialized array of objects

- `write_neo4j_cypher`
  - Execute updating Cypher queries
  - Input:
    - `query` (string): The Cypher update query
    - `params` (dictionary, optional): Parameters to pass to the Cypher query
  - Returns: A JSON serialized result summary counter with `{ nodes_updated: number, relationships_created: number, ... }`

#### 🕸️ Schema Tools

- `get_neo4j_schema`
  - Get a list of all nodes types in the graph database, their attributes with name, type and relationships to other node types
  - No input required
  - Returns: JSON serialized list of node labels with two dictionaries: one for attributes and one for relationships

### 🏷️ Namespacing

The server supports namespacing to allow multiple Neo4j MCP servers to be used simultaneously. When a namespace is provided, all tool names are prefixed with the namespace followed by a hyphen (e.g., `mydb-read_neo4j_cypher`).

This is useful when you need to connect to multiple Neo4j databases or instances from the same session.

## 🏗️ Local Development & Deployment

### 🐳 Local Docker Development

Build and run locally for testing or remote deployment:

```bash
# Build the Docker image with a custom name
docker build -t mcp-neo4j-cypher:latest .

# Run locally (uses http transport by default for Docker)
docker run -p 8000:8000 \
  -e NEO4J_URI="bolt://host.docker.internal:7687" \
  -e NEO4J_USERNAME="neo4j" \
  -e NEO4J_PASSWORD="your-password" \
  mcp-neo4j-cypher:latest

# Access the server at http://localhost:8000/api/mcp/
```

### 🚀 Transport Modes

The server supports different transport protocols depending on your deployment:

- **STDIO** (default for local development): Standard input/output for Claude Desktop and local tools
- **HTTP** (default for Docker): RESTful HTTP for web deployments and microservices
- **SSE**: Server-Sent Events for legacy web-based deployments

Choose your transport based on use case:

- **Local development/Claude Desktop**: Use `stdio`
- **Docker/Remote deployment**: Use `http`
- **Legacy web clients**: Use `sse`

## 🔧 Usage with Claude Desktop

### Using DXT

Download the latest `.dxt` file from the [releases page](https://github.com/neo4j-contrib/mcp-neo4j/releases) and install it with your MCP client.

### 💾 Released Package

Can be found on PyPi https://pypi.org/project/mcp-neo4j-cypher/

Add the server to your `claude_desktop_config.json` with the database connection configuration through environment variables. You may also specify the transport method and namespace with cli arguments or environment variables.

```json
"mcpServers": {
  "neo4j-database": {
    "command": "uvx",
    "args": [ "mcp-neo4j-cypher@0.3.1", "--transport", "stdio"  ],
    "env": {
      "NEO4J_URI": "bolt://localhost:7687",
      "NEO4J_USERNAME": "neo4j",
      "NEO4J_PASSWORD": "<your-password>",
      "NEO4J_DATABASE": "neo4j"
    }
  }
}
```

### 🌐 HTTP Transport Configuration

For custom HTTP configurations beyond the defaults:

```bash
# Custom HTTP configuration
mcp-neo4j-cypher --transport http --server-host 127.0.0.1 --server-port 8080 --server-path /api/mcp/

# Or using environment variables
export NEO4J_TRANSPORT=http
export NEO4J_MCP_SERVER_HOST=127.0.0.1
export NEO4J_MCP_SERVER_PORT=8080
export NEO4J_MCP_SERVER_PATH=/api/mcp/
mcp-neo4j-cypher
```

### Multiple Database Example

Here's an example of connecting to multiple Neo4j databases using namespaces:

```json
{
  "mcpServers": {
    "movies-neo4j": {
      "command": "uvx",
      "args": ["mcp-neo4j-cypher@0.3.1", "--namespace", "movies"],
      "env": {
        "NEO4J_URI": "neo4j+s://demo.neo4jlabs.com",
        "NEO4J_USERNAME": "recommendations",
        "NEO4J_PASSWORD": "recommendations",
        "NEO4J_DATABASE": "recommendations"
      }
    },
    "local-neo4j": {
      "command": "uvx",
      "args": ["mcp-neo4j-cypher@0.3.1"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password",
        "NEO4J_DATABASE": "neo4j",
        "NEO4J_NAMESPACE": "local"
      }
    }
  }
}
```

In this setup:

- The movies database tools will be prefixed with `movies-` (e.g., `movies-read_neo4j_cypher`)
- The local database tools will be prefixed with `local-` (e.g., `local-get_neo4j_schema`)

Syntax with `--db-url`, `--username`, `--password` and other command line arguments is still supported but environment variables are preferred:

<details>
  <summary>Legacy Syntax</summary>

```json
"mcpServers": {
  "neo4j": {
    "command": "uvx",
    "args": [
      "mcp-neo4j-cypher@0.3.1",
      "--db-url",
      "bolt://localhost",
      "--username",
      "neo4j",
      "--password",
      "<your-password>",
      "--namespace",
      "mydb",
      "--transport",
      "sse",
      "--server-host",
      "127.0.0.1",
      "--server-port",
      "8000"
      "--server-path",
      "/api/mcp/"
    ]
  }
}
```

</details>

### 🐳 Using with Docker

```json
"mcpServers": {
  "neo4j": {
    "command": "docker",
    "args": [
      "run",
      "--rm",
      "-e", "NEO4J_URI=bolt://host.docker.internal:7687",
      "-e", "NEO4J_USERNAME=neo4j",
      "-e", "NEO4J_PASSWORD=<your-password>",
      "-e", "NEO4J_NAMESPACE=mydb",
      "-e", "NEO4J_TRANSPORT=http",
      "-e", "NEO4J_MCP_SERVER_HOST=0.0.0.0",
      "-e", "NEO4J_MCP_SERVER_PORT=8000",
      "-e", "NEO4J_MCP_SERVER_PATH=/api/mcp/",
      "mcp/neo4j-cypher:latest"
    ]
  }
}
```

**Note**: This assumes you've built the image locally with `docker build -t mcp-neo4j-cypher:latest .`. Docker transport defaults to HTTP mode.

## 🐳 Docker Deployment

The Neo4j MCP server can be deployed using Docker for remote deployments. Docker deployment uses HTTP transport by default for web accessibility.

### 📦 Using Your Built Image

After building locally with `docker build -t mcp-neo4j-cypher:latest .`:

```bash
# Run with http transport (default for Docker)
docker run --rm -p 8000:8000 \
  -e NEO4J_URI="bolt://host.docker.internal:7687" \
  -e NEO4J_USERNAME="neo4j" \
  -e NEO4J_PASSWORD="password" \
  -e NEO4J_DATABASE="neo4j" \
  -e NEO4J_TRANSPORT="http" \
  -e NEO4J_MCP_SERVER_HOST="0.0.0.0" \
  -e NEO4J_MCP_SERVER_PORT="8000" \
  -e NEO4J_MCP_SERVER_PATH="/api/mcp/" \
  mcp/neo4j-cypher:latest
```

### 🔧 Environment Variables

| Variable                | Default                                 | Description                                    |
| ----------------------- | --------------------------------------- | ---------------------------------------------- |
| `NEO4J_URI`             | `bolt://localhost:7687`                 | Neo4j connection URI                           |
| `NEO4J_USERNAME`        | `neo4j`                                 | Neo4j username                                 |
| `NEO4J_PASSWORD`        | `password`                              | Neo4j password                                 |
| `NEO4J_DATABASE`        | `neo4j`                                 | Neo4j database name                            |
| `NEO4J_TRANSPORT`       | `stdio` (local), `http` (Docker)        | Transport protocol (`stdio`, `http`, or `sse`) |
| `NEO4J_NAMESPACE`       | _(empty)_                               | Tool namespace prefix                          |
| `NEO4J_MCP_SERVER_HOST` | `127.0.0.1` (local), `0.0.0.0` (Docker) | Host to bind to                                |
| `NEO4J_MCP_SERVER_PORT` | `8000`                                  | Port for HTTP/SSE transport                    |
| `NEO4J_MCP_SERVER_PATH` | `/api/mcp/`                             | Path for accessing MCP server                  |

### 🌐 SSE Transport for Legacy Web Access

When using SSE transport (for legacy web clients), the server exposes an HTTP endpoint:

```bash
# Start the server with SSE transport
docker run -d -p 8000:8000 \
  -e NEO4J_URI="neo4j+s://demo.neo4jlabs.com" \
  -e NEO4J_USERNAME="recommendations" \
  -e NEO4J_PASSWORD="recommendations" \
  -e NEO4J_DATABASE="recommendations" \
  -e NEO4J_TRANSPORT="sse" \
  -e NEO4J_MCP_SERVER_HOST="0.0.0.0" \
  -e NEO4J_MCP_SERVER_PORT="8000" \
  --name neo4j-mcp-server \
  mcp-neo4j-cypher:latest

# Test the SSE endpoint
curl http://localhost:8000/sse

# Use with MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8000/sse
```

### 🐳 Docker Compose

For more complex deployments, you may use Docker Compose:

```yaml
version: '3.8'

services:
  # Deploy Neo4j Database (optional)
  neo4j:
    image: neo4j:5.26.1 # or another version
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    ports:
      - '7474:7474' # HTTP
      - '7687:7687' # Bolt
    volumes:
      - neo4j_data:/data

  # Deploy Cypher MCP Server
  mcp-neo4j-cypher-server:
    image: mcp/neo4j-cypher:latest
    ports:
      - '8000:8000'
    environment:
      - NEO4J_URI=bolt://host.docker.internal:7687
      - NEO4J_USERNAME=neo4j
      - NEO4J_PASSWORD=password
      - NEO4J_DATABASE=neo4j
      - NEO4J_TRANSPORT=http
      - NEO4J_MCP_SERVER_HOST=0.0.0.0 # must be 0.0.0.0 for sse  or http transport in Docker
      - NEO4J_MCP_SERVER_PORT=8000
      - NEO4J_MCP_SERVER_PATH=/api/mcp/
      - NEO4J_NAMESPACE=local
    depends_on:
      - neo4j

volumes:
  neo4j_data:
```

Run with: `docker-compose up -d`

### 🔗 Claude Desktop Integration with Docker

For Claude Desktop integration with a Dockerized server using http transport:

```json
{
  "mcpServers": {
    "neo4j-docker": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "http://localhost:8000/api/mcp/"]
    }
  }
}
```

**Note**: First start your Docker container with HTTP transport, then Claude Desktop can connect to it via the HTTP endpoint.

## 🚀 Development

### 📦 Prerequisites

1. Install [`uv`](https://github.com/astral-sh/uv):

```bash
# Using pip
pip install uv

# Using Homebrew on macOS
brew install uv

# Using cargo (Rust package manager)
cargo install uv
```

2. Clone the repository and set up development environment:

```bash
# Clone the repository
git clone https://github.com/neo4j-contrib/mcp-neo4j.git
cd mcp-neo4j-cypher

# Create and activate virtual environment using uv
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows

# Install dependencies including dev dependencies
uv pip install -e ".[dev]"
```

3. Run Integration Tests

```bash
./tests.sh
```

### 🔧 Development Configuration

For development with Claude Desktop using the local source:

```json
{
  "mcpServers": {
    "neo4j-dev": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-neo4j-cypher", "run", "mcp-neo4j-cypher", "--transport", "stdio", "--namespace", "dev"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "<your-password>",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

Replace `/path/to/mcp-neo4j-cypher` with your actual project directory path.

## 📄 License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
