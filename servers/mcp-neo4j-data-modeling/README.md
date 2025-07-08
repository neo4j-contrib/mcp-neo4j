# 🔍📊 Neo4j Data Modeling MCP Server

## 🌟 Overview

A Model Context Protocol (MCP) server implementation that provides tools for creating, visualizing, and managing Neo4j graph data models. This server enables you to define nodes, relationships, and properties to design graph database schemas that can be visualized interactively.

## 🧩 Components

### 📦 Resources

The server provides these resources:

- `resource://schema/node`
   - Get the JSON schema for a Node object
   - Returns: JSON schema defining the structure of a Node

- `resource://schema/relationship`
   - Get the JSON schema for a Relationship object
   - Returns: JSON schema defining the structure of a Relationship

- `resource://schema/property`
   - Get the JSON schema for a Property object
   - Returns: JSON schema defining the structure of a Property

- `resource://schema/data_model`
   - Get the JSON schema for a DataModel object
   - Returns: JSON schema defining the structure of a DataModel
  
- `resource://neo4j_data_ingest_process`
   - Get a detailed explanation of the recommended process for ingesting data into Neo4j using the data model
   - Returns: Markdown document explaining the ingest process


### 🛠️ Tools

The server offers these core tools:

#### ✅ Validation Tools
- `validate_node`
   - Validate a single node structure
   - Input:
     - `node` (Node): The node to validate
   - Returns: True if valid, raises ValueError if invalid

- `validate_relationship`
   - Validate a single relationship structure
   - Input:
     - `relationship` (Relationship): The relationship to validate
   - Returns: True if valid, raises ValueError if invalid

- `validate_data_model`
   - Validate the entire data model structure
   - Input:
     - `data_model` (DataModel): The data model to validate
   - Returns: True if valid, raises ValueError if invalid

#### 👁️ Visualization Tools
- `get_mermaid_config_str`
   - Generate a Mermaid diagram configuration string for the data model, suitable for visualization in tools that support Mermaid
   - Input:
     - `data_model` (DataModel): The data model to visualize
   - Returns: Mermaid configuration string representing the data model

#### 🔄 Import/Export Tools

These tools provide integration with **[Arrows](https://arrows.app/)** - a graph drawing web application for creating detailed Neo4j data models with an intuitive visual interface.

- `load_from_arrows_json`
   - Load a data model from Arrows app JSON format
   - Input:
     - `arrows_data_model_dict` (dict): JSON dictionary from Arrows app export
   - Returns: DataModel object

- `export_to_arrows_json`
   - Export a data model to Arrows app JSON format
   - Input:
     - `data_model` (DataModel): The data model to export
   - Returns: JSON string compatible with Arrows app

#### 📝 Cypher Ingest Tools

These tools may be used to create Cypher ingest queries based on the data model. These queries may then be used by other MCP servers or applications to load data into Neo4j.

- `get_constraints_cypher_queries`
   - Generate Cypher queries to create constraints (e.g., unique keys) for all nodes in the data model
   - Input:
     - `data_model` (DataModel): The data model to generate constraints for
   - Returns: List of Cypher statements for constraints

- `get_node_cypher_ingest_query`
   - Generate a Cypher query to ingest a list of node records into Neo4j
   - Input:
     - `node` (Node): The node definition (label, key property, properties)
   - Returns: Parameterized Cypher query for bulk node ingestion (using `$records`)

- `get_relationship_cypher_ingest_query`
   - Generate a Cypher query to ingest a list of relationship records into Neo4j
   - Input:
     - `data_model` (DataModel): The data model containing nodes and relationships
     - `relationship_type` (str): The type of the relationship
     - `relationship_start_node_label` (str): The label of the start node
     - `relationship_end_node_label` (str): The label of the end node
   - Returns: Parameterized Cypher query for bulk relationship ingestion (using `$records`)

## 🔧 Usage with Claude Desktop

### 💾 Released Package

Can be found on PyPi https://pypi.org/project/mcp-neo4j-data-modeling/

Add the server to your `claude_desktop_config.json` with the transport method specified:

```json
"mcpServers": {
  "neo4j-data-modeling": {
    "command": "uvx",
    "args": [ "mcp-neo4j-data-modeling@0.1.1", "--transport", "stdio" ]
  }
}
```

### 🌐 HTTP Transport Mode

The server supports HTTP transport for web-based deployments and microservices:

```bash
# Basic HTTP mode (defaults: host=127.0.0.1, port=8000, path=/mcp/)
mcp-neo4j-data-modeling --transport http

# Custom HTTP configuration
mcp-neo4j-data-modeling --transport http --host 0.0.0.0 --port 8080 --path /api/mcp/
```

Environment variables for HTTP configuration:

```bash
export MCP_TRANSPORT=http
export MCP_HTTP_HOST=0.0.0.0
export MCP_HTTP_PORT=8080
export MCP_HTTP_PATH=/api/mcp/
mcp-neo4j-data-modeling
```

### 🔄 Transport Modes

The server supports three transport modes:

- **STDIO** (default): Standard input/output for local tools and Claude Desktop
- **SSE**: Server-Sent Events for web-based deployments  
- **HTTP**: Streamable HTTP for modern web deployments and microservices

### 🐳 Using with Docker

```json
"mcpServers": {
  "neo4j-data-modeling": {
    "command": "docker",
    "args": [
      "run",
      "--rm",
      "mcp/neo4j-data-modeling:latest"
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
git clone https://github.com/yourusername/mcp-neo4j-data-modeling.git
cd mcp-neo4j-data-modeling

# Create and activate virtual environment using uv
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows

# Install dependencies including dev dependencies
uv pip install -e ".[dev]"
```

3. Run Tests

```bash
./test.sh
```

### 🔧 Development Configuration

```json
# Add the server to your claude_desktop_config.json
"mcpServers": {
  "neo4j-data-modeling": {
    "command": "uv",
    "args": [
      "--directory", "path_to_repo/src",
      "run", "mcp-neo4j-data-modeling", "--transport", "stdio"]
  }
}
```

### 🐳 Docker

Build and run the Docker container:

```bash
# Build the image
docker build -t mcp/neo4j-data-modeling:latest .

# Run the container
docker run mcp/neo4j-data-modeling:latest
```

## 📄 License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
