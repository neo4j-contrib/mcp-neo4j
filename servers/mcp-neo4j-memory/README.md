# Neo4j Knowledge Graph Memory MCP Server

mcp-name: io.github.neo4j-contrib/mcp-neo4j-memory

## Overview

A Model Context Protocol (MCP) server implementation that provides persistent memory capabilities through Neo4j graph database integration.

By storing information in a graph structure, this server maintains complex relationships between entities as typed nodes with properties and enables long-term retention of knowledge that can be queried and analyzed across multiple conversations or sessions.

With [Neo4j Aura](https://console.neo4j.io) you can host your own database server for free or share it with your collaborators. Otherwise you can run your own Neo4j server locally.

The MCP server leverages Neo4j's graph database capabilities to create an interconnected knowledge base that serves as an external memory system. Through Cypher queries, it allows exploration and retrieval of stored information, relationship analysis between different data points, and generation of insights from the accumulated knowledge.

## Graph Schema

### Entities (Nodes)

Entities are stored as nodes with typed labels (Person, Organization, Project, etc.) and support:

- **name** (string): Unique identifier for the entity
- **type** (string): Entity type (becomes the node label)
- **observations** (array): Unstructured notes about the entity
- **properties** (object): Structured key-value properties for queryable data

### Relationships

Relationships connect entities and support:

- **source** (string): Source entity name
- **target** (string): Target entity name
- **relationType** (string): Relationship type (WORKS_AT, KNOWS, etc.)
- **properties** (object): Structured key-value properties (validAt, invalidAt, role, etc.)

### Temporal Properties (Event Clock)

Both entities and relationships support temporal tracking:

| Property | Type | Description |
|----------|------|-------------|
| `validAt` | datetime | When this fact became true |
| `invalidAt` | datetime | When this fact stopped being true (soft delete) |
| `source` | string | Provenance (meeting, document, person) |
| `confidence` | float | Certainty level (0.0-1.0) |

This enables the **Subject → Predicate → Object** pattern with temporal context on predicates for tracking how facts change over time.

### Usage Example

```
Let's add some memories
I, Michael, living in Dresden, Germany work at Neo4j which is headquartered in Sweden with my colleagues Andreas (Cambridge, UK) and Oskar (Gothenburg, Sweden)
I work in Product Management, Oskar in Engineering and Andreas in Developer Relations.
```

Results in Claude calling the create_entities and create_relations tools.

![](./docs/images/employee_create_entities_and_relations.png)

![](./docs/images/employee_graph.png)

## Components

### Tools

The server offers these core tools:

#### Query Tools

- **`read_graph`**
   - Read the entire knowledge graph
   - No input required
   - Returns: Complete graph with entities (including properties) and relations

- **`search_memories`**
   - Search for nodes based on a query using fulltext search
   - Input:
     - `query` (string): Search query matching names, types, observations
   - Returns: Matching subgraph with properties

- **`find_memories_by_name`**
   - Find specific nodes by exact name
   - Input:
     - `names` (array of strings): Entity names to retrieve
   - Returns: Subgraph with specified nodes and their properties

#### Entity Management Tools

- **`create_entities`**
   - Create multiple new entities in the knowledge graph
   - Input:
     - `entities`: Array of objects with:
       - `name` (string): Name of the entity
       - `type` (string): Type of the entity (becomes node label)
       - `observations` (array of strings, optional): Unstructured notes
       - `properties` (object, optional): Structured properties like `email`, `validAt`, `status`
   - Returns: Created entities

- **`update_entity_properties`**
   - Update properties on existing entities (use for soft deletes)
   - Input:
     - `updates`: Array of objects with:
       - `entityName` (string): Name of entity to update
       - `properties` (object): Properties to set (use `null` to remove)
   - Returns: Updated entities with new properties
   - Example: Set `invalidAt` to soft-delete an entity

- **`delete_entities`**
   - Hard delete entities and their associated relations
   - Input:
     - `entityNames` (array of strings): Names of entities to delete
   - Returns: Success confirmation

#### Relation Management Tools

- **`create_relations`**
   - Create multiple new relations between entities
   - Input:
     - `relations`: Array of objects with:
       - `source` (string): Name of source entity
       - `target` (string): Name of target entity
       - `relationType` (string): Type of relation
       - `properties` (object, optional): Properties like `validAt`, `role`, `source`
   - Returns: Created relations

- **`update_relation_properties`**
   - Update properties on existing relationships (use for soft deletes)
   - Input:
     - `updates`: Array of objects with:
       - `source` (string): Source entity name
       - `target` (string): Target entity name
       - `relationType` (string): Relationship type
       - `properties` (object): Properties to set (use `null` to remove)
   - Returns: Updated relationships with new properties
   - Example: Set `invalidAt` to mark a relationship as ended

- **`delete_relations`**
   - Hard delete relations from the graph
   - Input:
     - `relations`: Array of objects with same schema as create_relations
   - Returns: Success confirmation

#### Observation Management Tools

- **`add_observations`**
   - Add new observations to existing entities
   - Input:
     - `observations`: Array of objects with:
       - `entityName` (string): Entity to add to
       - `observations` (array of strings): Observations to add
   - Returns: Added observation details

- **`delete_observations`**
   - Delete specific observations from entities
   - Input:
     - `deletions`: Array of objects with:
       - `entityName` (string): Entity to delete from
       - `observations` (array of strings): Observations to remove
   - Returns: Success confirmation

### Example: Creating Entities with Properties

```json
{
  "entities": [
    {
      "name": "Alice Johnson",
      "type": "Person",
      "observations": ["Prefers morning meetings"],
      "properties": {
        "email": "alice@acme.com",
        "role": "Senior Architect",
        "validAt": "2026-01-15T10:00:00Z"
      }
    }
  ]
}
```

### Example: Creating Relations with Properties

```json
{
  "relations": [
    {
      "source": "Alice Johnson",
      "target": "Acme Corp",
      "relationType": "WORKS_AT",
      "properties": {
        "validAt": "2026-01-15T10:00:00Z",
        "role": "Senior Architect",
        "department": "Engineering"
      }
    }
  ]
}
```

### Example: Soft Delete (End a Relationship)

```json
{
  "updates": [
    {
      "source": "Alice Johnson",
      "target": "Old Company",
      "relationType": "WORKS_AT",
      "properties": {
        "invalidAt": "2026-01-15T00:00:00Z"
      }
    }
  ]
}
```

## Usage with Claude Desktop

### Installation

```bash
pip install mcp-neo4j-memory
```

### Configuration

Add the server to your `claude_desktop_config.json` with configuration of:

```json
"mcpServers": {
  "neo4j": {
    "command": "uvx",
    "args": [
      "mcp-neo4j-memory@0.4.4",
      "--db-url",
      "neo4j+s://xxxx.databases.neo4j.io",
      "--username",
      "<your-username>",
      "--password",
      "<your-password>"
    ]
  }
}
```

Alternatively, you can set environment variables:

```json
"mcpServers": {
  "neo4j": {
    "command": "uvx",
    "args": [ "mcp-neo4j-memory@0.4.4" ],
    "env": {
      "NEO4J_URL": "neo4j+s://xxxx.databases.neo4j.io",
      "NEO4J_USERNAME": "<your-username>",
      "NEO4J_PASSWORD": "<your-password>"
    }
  }
}
```

#### Namespacing
For multi-tenant deployments, add `--namespace` to prefix tool names:
```json
"args": [ "mcp-neo4j-memory@0.4.4", "--namespace", "myapp", "--db-url", "..." ]
```
Tools become: `myapp-read_graph`, `myapp-create_entities`, etc.

Can also use `NEO4J_NAMESPACE` environment variable.

### HTTP Transport Mode

The server supports HTTP transport for web-based deployments and microservices:

```bash
# Basic HTTP mode (defaults: host=127.0.0.1, port=8000, path=/mcp/)
mcp-neo4j-memory --transport http

# Custom HTTP configuration
mcp-neo4j-memory --transport http --host 127.0.0.1 --port 8080 --path /api/mcp/
```

Environment variables for HTTP configuration:

```bash
export NEO4J_TRANSPORT=http
export NEO4J_MCP_SERVER_HOST=127.0.0.1
export NEO4J_MCP_SERVER_PORT=8080
export NEO4J_MCP_SERVER_PATH=/api/mcp/
export NEO4J_NAMESPACE=myapp
mcp-neo4j-memory
```

### Transport Modes

The server supports three transport modes:

- **STDIO** (default): Standard input/output for local tools and Claude Desktop
- **SSE**: Server-Sent Events for web-based deployments
- **HTTP**: Streamable HTTP for modern web deployments and microservices

### Using with Docker

```json
"mcpServers": {
  "neo4j": {
    "command": "docker",
    "args": [
      "run",
      "--rm",
      "-e", "NEO4J_URL=neo4j+s://xxxx.databases.neo4j.io",
      "-e", "NEO4J_USERNAME=<your-username>",
      "-e", "NEO4J_PASSWORD=<your-password>",
      "mcp/neo4j-memory:0.4.4"
    ]
  }
}
```

## Security Protection

The server includes comprehensive security protection with **secure defaults** that protect against common web-based attacks while preserving full MCP functionality when using HTTP transport.

### DNS Rebinding Protection

**TrustedHost Middleware** validates Host headers to prevent DNS rebinding attacks:

**Secure by Default:**
- Only `localhost` and `127.0.0.1` hosts are allowed by default

**Environment Variable:**
```bash
export NEO4J_MCP_SERVER_ALLOWED_HOSTS="example.com,www.example.com"
```

### CORS Protection

**Cross-Origin Resource Sharing (CORS)** protection blocks browser-based requests by default:

**Environment Variable:**
```bash
export NEO4J_MCP_SERVER_ALLOW_ORIGINS="https://example.com,https://app.example.com"
```

### Complete Security Configuration

**Development Setup:**
```bash
mcp-neo4j-memory --transport http \
  --allowed-hosts "localhost,127.0.0.1" \
  --allow-origins "http://localhost:3000"
```

**Production Setup:**
```bash
mcp-neo4j-memory --transport http \
  --allowed-hosts "example.com,www.example.com" \
  --allow-origins "https://example.com,https://app.example.com"
```

### Security Best Practices

**For `allow_origins`:**
- Be specific: `["https://example.com", "https://example.com"]`
- Never use `"*"` in production with credentials
- Use HTTPS origins in production

**For `allowed_hosts`:**
- Include your actual domain: `["example.com", "www.example.com"]`
- Include localhost only for development
- Never use `"*"` unless you understand the risks

## Docker Deployment

The Neo4j Memory MCP server can be deployed using Docker for remote deployments. Docker deployment should use HTTP transport for web accessibility. In order to integrate this deployment with applications like Claude Desktop, you will have to use a proxy in your MCP configuration such as `mcp-remote`.

### Using Your Built Image

After building locally with `docker build -t mcp-neo4j-memory:latest .`:

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
  -e NEO4J_MCP_SERVER_PATH="/mcp/" \
  mcp/neo4j-memory:latest

# Run with security middleware for production
docker run --rm -p 8000:8000 \
  -e NEO4J_URI="bolt://host.docker.internal:7687" \
  -e NEO4J_USERNAME="neo4j" \
  -e NEO4J_PASSWORD="password" \
  -e NEO4J_DATABASE="neo4j" \
  -e NEO4J_TRANSPORT="http" \
  -e NEO4J_MCP_SERVER_HOST="0.0.0.0" \
  -e NEO4J_MCP_SERVER_PORT="8000" \
  -e NEO4J_MCP_SERVER_PATH="/mcp/" \
  -e NEO4J_MCP_SERVER_ALLOWED_HOSTS="example.com,www.example.com" \
  -e NEO4J_MCP_SERVER_ALLOW_ORIGINS="https://example.com" \
  mcp/neo4j-memory:latest
```

### Environment Variables

| Variable                           | Default                                 | Description                                        |
| ---------------------------------- | --------------------------------------- | -------------------------------------------------- |
| `NEO4J_URI`                        | `bolt://localhost:7687`                 | Neo4j connection URI                               |
| `NEO4J_USERNAME`                   | `neo4j`                                 | Neo4j username                                     |
| `NEO4J_PASSWORD`                   | `password`                              | Neo4j password                                     |
| `NEO4J_DATABASE`                   | `neo4j`                                 | Neo4j database name                                |
| `NEO4J_TRANSPORT`                  | `stdio` (local), `http` (remote)        | Transport protocol (`stdio`, `http`, or `sse`)     |
| `NEO4J_MCP_SERVER_HOST`            | `127.0.0.1` (local)                     | Host to bind to                                    |
| `NEO4J_MCP_SERVER_PORT`            | `8000`                                  | Port for HTTP/SSE transport                        |
| `NEO4J_MCP_SERVER_PATH`            | `/mcp/`                                 | Path for accessing MCP server                      |
| `NEO4J_MCP_SERVER_ALLOW_ORIGINS`   | _(empty - secure by default)_           | Comma-separated list of allowed CORS origins       |
| `NEO4J_MCP_SERVER_ALLOWED_HOSTS`   | `localhost,127.0.0.1`                   | Comma-separated list of allowed hosts (DNS rebinding protection) |
| `NEO4J_NAMESPACE`                  | _(empty - no prefix)_                   | Namespace prefix for tool names (e.g., `myapp-read_graph`) |

### SSE Transport for Legacy Web Access

When using SSE transport (for legacy web clients), the server exposes an HTTP endpoint:

```bash
# Start the server with SSE transport
docker run -d -p 8000:8000 \
  -e NEO4J_URI="neo4j+s://demo.neo4jlabs.com" \
  -e NEO4J_USERNAME="recommendations" \
  -e NEO4J_PASSWORD="recommendations" \
  -e NEO4J_DATABASE="neo4j" \
  -e NEO4J_TRANSPORT="sse" \
  -e NEO4J_MCP_SERVER_HOST="0.0.0.0" \
  -e NEO4J_MCP_SERVER_PORT="8000" \
  --name neo4j-memory-mcp-server \
  mcp-neo4j-memory:latest

# Test the SSE endpoint
curl http://localhost:8000/sse

# Use with MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8000/sse
```

## World Model Schema

For advanced usage with temporal facts, decisions, and the Event Clock pattern, see [docs/WORLD_MODEL_SCHEMA.md](./docs/WORLD_MODEL_SCHEMA.md).

The World Model schema provides:
- Typed entity labels (Person, Organization, Project, Decision, Fact, etc.)
- Temporal tracking with `validAt`/`invalidAt` properties
- Soft delete pattern for historical preservation
- Decision chain: Context → Decision → Action → Outcome
- Migration scripts for existing data

## Development

### Prerequisites

1. Install `uv` (Universal Virtualenv):
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
git clone https://github.com/yourusername/mcp-neo4j-memory.git
cd mcp-neo4j-memory

# Create and activate virtual environment using uv
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows

# Install dependencies including dev dependencies
uv pip install -e ".[dev]"
```

### Docker

Build and run the Docker container:

```bash
# Build the image
docker build -t mcp/neo4j-memory:latest .

# Run the container
docker run -e NEO4J_URL="neo4j+s://xxxx.databases.neo4j.io" \
          -e NEO4J_USERNAME="your-username" \
          -e NEO4J_PASSWORD="your-password" \
          mcp/neo4j-memory:latest
```

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
