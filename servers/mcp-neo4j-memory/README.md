# 🧠🕸️ Neo4j Knowledge Graph Memory MCP Server

## 🌟 Overview

A Model Context Protocol (MCP) server implementation that provides persistent memory capabilities through Neo4j graph database integration.

By storing information in a graph structure, this server maintains complex relationships between entities as memory nodes and enables long-term retention of knowledge that can be queried and analyzed across multiple conversations or sessions.

With [Neo4j Aura](https://console.neo4j.io) you can host your own database server for free or share it with your collaborators. Otherwise you can run your own Neo4j server locally.

The MCP server leverages Neo4j's graph database capabilities to create an interconnected knowledge base that serves as an external memory system. Through Cypher queries, it allows exploration and retrieval of stored information, relationship analysis between different data points, and generation of insights from the accumulated knowledge. This memory can be further enhanced with Claude's capabilities.

### 🕸️ Graph Schema

* `Memory` - A node representing an entity with a name, type, and observations.
* `Relationship` - A relationship between two entities with a type.

### 🔍 Usage Example

```
Let's add some memories 
I, Michael, living in Dresden, Germany work at Neo4j which is headquartered in Sweden with my colleagues Andreas (Cambridge, UK) and Oskar (Gothenburg, Sweden)
I work in Product Management, Oskar in Engineering and Andreas in Developer Relations.
```

Results in Claude calling the create_entities and create_relations tools.

![](./docs/images/employee_create_entities_and_relations.png)

![](./docs/images/employee_graph.png)

## 📦 Components

### 🔧 Tools

The server offers these core tools:

#### 🔎 Query Tools
- `read_graph`
   - Read the entire knowledge graph
   - No input required
   - Returns: Complete graph with entities and relations

- `search_nodes`
   - Search for nodes based on a query
   - Input:
     - `query` (string): Search query matching names, types, observations
   - Returns: Matching subgraph

- `find_nodes`
   - Find specific nodes by name
   - Input:
     - `names` (array of strings): Entity names to retrieve
   - Returns: Subgraph with specified nodes

#### ♟️ Entity Management Tools
- `create_entities`
   - Create multiple new entities in the knowledge graph
   - Input:
     - `entities`: Array of objects with:
       - `name` (string): Name of the entity
       - `type` (string): Type of the entity  
       - `observations` (array of strings): Initial observations about the entity
   - Returns: Created entities

- `delete_entities` 
   - Delete multiple entities and their associated relations
   - Input:
     - `entityNames` (array of strings): Names of entities to delete
   - Returns: Success confirmation

#### 🔗 Relation Management Tools
- `create_relations`
   - Create multiple new relations between entities
   - Input:
     - `relations`: Array of objects with:
       - `source` (string): Name of source entity
       - `target` (string): Name of target entity
       - `relationType` (string): Type of relation
   - Returns: Created relations

- `delete_relations`
   - Delete multiple relations from the graph
   - Input:
     - `relations`: Array of objects with same schema as create_relations
   - Returns: Success confirmation

#### 📝 Observation Management Tools
- `add_observations`
   - Add new observations to existing entities
   - Input:
     - `observations`: Array of objects with:
       - `entityName` (string): Entity to add to
       - `contents` (array of strings): Observations to add
   - Returns: Added observation details

- `delete_observations`
   - Delete specific observations from entities
   - Input:
     - `deletions`: Array of objects with:
       - `entityName` (string): Entity to delete from
       - `observations` (array of strings): Observations to remove
   - Returns: Success confirmation

## 🔧 Usage with Claude Desktop

### 💾 Installation

```bash
pip install mcp-neo4j-memory
```

### ⚙️ Configuration

Add the server to your `claude_desktop_config.json` with configuration of:

```json
"mcpServers": {
  "neo4j": {
    "command": "uvx",
    "args": [
      "mcp-neo4j-memory@0.2.0",
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
    "args": [ "mcp-neo4j-memory@0.2.0" ],
    "env": {
      "NEO4J_URL": "neo4j+s://xxxx.databases.neo4j.io",
      "NEO4J_USERNAME": "<your-username>",
      "NEO4J_PASSWORD": "<your-password>"
    }
  }
}
```

### 🌐 HTTP Transport Mode

The server supports HTTP transport for web-based deployments and microservices:

```bash
# Basic HTTP mode (defaults: host=127.0.0.1, port=8000, path=/mcp/)
mcp-neo4j-memory --transport http

# Custom HTTP configuration
mcp-neo4j-memory --transport http --host 0.0.0.0 --port 8080 --path /api/mcp/
```

Environment variables for HTTP configuration:

```bash
export NEO4J_TRANSPORT=http
export NEO4J_MCP_SERVER_HOST=0.0.0.0
export NEO4J_MCP_SERVER_PORT=8080
export NEO4J_MCP_SERVER_PATH=/api/mcp/
mcp-neo4j-memory
```

### 🔄 Transport Modes

The server supports three transport modes:

- **STDIO** (default): Standard input/output for local tools and Claude Desktop
- **SSE**: Server-Sent Events for web-based deployments  
- **HTTP**: Streamable HTTP for modern web deployments and microservices

### 🐳 Using with Docker

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
      "mcp/neo4j-memory:0.2.0"
    ]
  }
}
```

## 🚀 Development

### 📦 Prerequisites

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

### 🐳 Docker

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

## 📄 License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
