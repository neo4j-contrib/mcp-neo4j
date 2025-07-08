# 🔍⁉️ Neo4j MCP Server

## 🌟 Overview

A Model Context Protocol (MCP) server implementation that provides database interaction and allows graph exploration capabilities through Neo4j. This server enables running Cypher graph queries, analyzing complex domain data, and automatically generating business insights that can be enhanced with Claude's analysis.

## 🧩 Components

### 🛠️ Tools

The server offers these core tools:

#### 📊 Query Tools
- `read-neo4j-cypher`
   - Execute Cypher read queries to read data from the database
   - Input: 
     - `query` (string): The Cypher query to execute
     - `params` (dictionary, optional): Parameters to pass to the Cypher query
   - Returns: Query results as JSON serialized array of objects

- `write-neo4j-cypher`
   - Execute updating Cypher queries
   - Input:
     - `query` (string): The Cypher update query
     - `params` (dictionary, optional): Parameters to pass to the Cypher query
   - Returns: A JSON serialized result summary counter with `{ nodes_updated: number, relationships_created: number, ... }`

#### 🕸️ Schema Tools
- `get-neo4j-schema`
   - Get a list of all nodes types in the graph database, their attributes with name, type and relationships to other node types
   - No input required
   - Returns: JSON serialized list of node labels with two dictionaries: one for attributes and one for relationships

### 🏷️ Namespacing

The server supports namespacing to allow multiple Neo4j MCP servers to be used simultaneously. When a namespace is provided, all tool names are prefixed with the namespace followed by a hyphen (e.g., `mydb-read-neo4j-cypher`).

This is useful when you need to connect to multiple Neo4j databases or instances from the same session.

## 🔧 Usage with Claude Desktop

### 💾 Released Package

Can be found on PyPi https://pypi.org/project/mcp-neo4j-cypher/

Add the server to your `claude_desktop_config.json` with the database connection configuration through environment variables. You may also specify the transport method and namespace with cli arguments or environment variables.

```json
"mcpServers": {
  "neo4j-aura": {
    "command": "uvx",
    "args": [ "mcp-neo4j-cypher@0.2.3", "--transport", "stdio"  ],
    "env": {
      "NEO4J_URI": "bolt://localhost:7687",
      "NEO4J_USERNAME": "neo4j",
      "NEO4J_PASSWORD": "<your-password>",
      "NEO4J_DATABASE": "neo4j"
    }
  }
}
```

#### Multiple Database Example

Here's an example of connecting to multiple Neo4j databases using namespaces:

```json
{
  "mcpServers": {
    "movies-neo4j": {
      "command": "uvx",
      "args": [ "mcp-neo4j-cypher@0.2.3", "--namespace", "movies" ],
      "env": {
        "NEO4J_URI": "neo4j+s://demo.neo4jlabs.com",
        "NEO4J_USERNAME": "recommendations",
        "NEO4J_PASSWORD": "recommendations",
        "NEO4J_DATABASE": "recommendations"
      }
    },
    "local-neo4j": {
      "command": "uvx",
      "args": [ "mcp-neo4j-cypher@0.2.3" ],
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
- The movies database tools will be prefixed with `movies-` (e.g., `movies-read-neo4j-cypher`)
- The local database tools will be prefixed with `local-` (e.g., `local-get-neo4j-schema`)

Here is an example connection for the movie database with Movie, Person (Actor, Director), Genre, User and ratings:

```json
{
  "mcpServers": {
    "movies-neo4j": {
      "command": "uvx",
      "args": [ "mcp-neo4j-cypher@0.2.3" ],
      "env": {
        "NEO4J_URI": "neo4j+s://demo.neo4jlabs.com",
        "NEO4J_USERNAME": "recommendations",
        "NEO4J_PASSWORD": "recommendations",
        "NEO4J_DATABASE": "recommendations"
      }
    }   
  }
}
```

Syntax with `--db-url`, `--username` and `--password` command line arguments is still supported but environment variables are preferred:

<details>
  <summary>Legacy Syntax</summary>

```json
"mcpServers": {
  "neo4j": {
    "command": "uvx",
    "args": [
      "mcp-neo4j-cypher@0.2.3",
      "--db-url",
      "bolt://localhost",
      "--username",
      "neo4j",
      "--password",
      "<your-password>",
      "--namespace",
      "mydb"
    ]
  }
}
```

Here is an example connection for the movie database with Movie, Person (Actor, Director), Genre, User and ratings:

```json
{
  "mcpServers": {
    "movies-neo4j": {
      "command": "uvx",
      "args": ["mcp-neo4j-cypher@0.2.3", 
      "--db-url", "neo4j+s://demo.neo4jlabs.com", 
      "--user", "recommendations", 
      "--password", "recommendations",
      "--database", "recommendations"]
    }   
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
      "mcp/neo4j-cypher:latest"
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
git clone https://github.com/yourusername/mcp-neo4j-cypher.git
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

```json
# Add the server to your claude_desktop_config.json
"mcpServers": {
  "neo4j": {
    "command": "uv",
    "args": [
      "--directory", "parent_of_servers_repo/servers/mcp-neo4j-cypher/src",
      "run", "mcp-neo4j-cypher", "--transport", "stdio", "--namespace", "dev"],
    "env": {
      "NEO4J_URI": "bolt://localhost",
      "NEO4J_USERNAME": "neo4j",
      "NEO4J_PASSWORD": "<your-password>",
      "NEO4J_DATABASE": "neo4j"
    }
  }
}
```

### 🐳 Docker

Build and run the Docker container:

```bash
# Build the image
docker build -t mcp/neo4j-cypher:latest .

# Run the container
docker run -e NEO4J_URI="bolt://host.docker.internal:7687" \
          -e NEO4J_USERNAME="neo4j" \
          -e NEO4J_PASSWORD="your-password" \
          -e NEO4J_NAMESPACE="mydb" \
          mcp/neo4j-cypher:latest
```

## 📄 License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
