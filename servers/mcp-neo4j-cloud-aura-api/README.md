# 🚀💖☁️ Neo4j Aura Database Manager MCP Server

## 🌟 Overview

A Model Context Protocol (MCP) server implementation that provides tools for managing Neo4j Aura database instances through the Neo4j Aura API.

This server allows you to create, monitor, and manage Neo4j Aura instances directly through Claude, making it easy to provision and maintain your graph database infrastructure.

## 🔑 Authentication

Authentication with the Neo4j Aura API requires:
- Client ID
- Client Secret

You can obtain these credentials from the Neo4j Aura console, see the [documentation of the Aura API](https://neo4j.com/docs/aura/classic/platform/api/overview/)

Here is the [API Specification](https://neo4j.com/docs/aura/platform/api/specification/)

## 📦 Components

### 🔧 Tools

The server offers these core tools:

#### 🛠️ Instance Management
- `list_instances`
  - List all Neo4j Aura database instances
  - No input required
  - Returns: List of all instances with their details

- `get_instance_details`
  - Get details for a specific instance or multiple instances by ID
  - Input:
    - `instance_ids` (string or array): ID of the instance to retrieve, or array of instance IDs
  - Returns: Detailed information about the instance(s)

- `get_instance_by_name`
  - Find an instance by name
  - Input:
    - `name` (string): Name of the instance to find
  - Returns: Instance details if found

- `create_instance`
  - Create a new Neo4j Aura database instance
  - Input:
    - `tenant_id` (string): ID of the tenant/project where the instance will be created
    - `name` (string): Name for the new instance
    - `memory` (integer): Memory allocation in GB
    - `region` (string): Region for the instance (e.g., 'us-east-1')
    - `version` (string): Neo4j version (e.g., '5.15')
    - `type` (string, optional): Instance type (enterprise or professional)
    - `vector_optimized` (boolean, optional): Whether the instance is optimized for vector operations
  - Returns: Created instance details

- `update_instance_name`
  - Update the name of an instance
  - Input:
    - `instance_id` (string): ID of the instance to update
    - `name` (string): New name for the instance
  - Returns: Updated instance details

- `update_instance_memory`
  - Update the memory allocation of an instance
  - Input:
    - `instance_id` (string): ID of the instance to update
    - `memory` (integer): New memory allocation in GB
  - Returns: Updated instance details

- `update_instance_vector_optimization`
  - Update the vector optimization setting of an instance
  - Input:
    - `instance_id` (string): ID of the instance to update
    - `vector_optimized` (boolean): Whether the instance should be optimized for vector operations
  - Returns: Updated instance details

- `pause_instance`
  - Pause a database instance
  - Input:
    - `instance_id` (string): ID of the instance to pause
  - Returns: Instance status information

- `resume_instance`
  - Resume a paused database instance
  - Input:
    - `instance_id` (string): ID of the instance to resume
  - Returns: Instance status information

- `delete_instance`
  - Delete a database instance
  - Input:
    - `tenant_id` (string): ID of the tenant/project where the instance exists
    - `instance_id` (string): ID of the instance to delete
  - Returns: Deletion status information

#### 🏢 Tenant/Project Management
- `list_tenants`
  - List all Neo4j Aura tenants/projects
  - No input required
  - Returns: List of all tenants with their details

- `get_tenant_details`
  - Get details for a specific tenant/project
  - Input:
    - `tenant_id` (string): ID of the tenant/project to retrieve
  - Returns: Detailed information about the tenant/project


## 🔧 Usage with Claude Desktop

### 💾 Installation

```bash
pip install mcp-neo4j-aura-manager
```

### ⚙️ Configuration

Add the server to your `claude_desktop_config.json`:

```json
"mcpServers": {
  "neo4j-aura": {
    "command": "uvx",
    "args": [
      "mcp-neo4j-aura-manager@0.2.2",
      "--client-id",
      "<your-client-id>",
      "--client-secret",
      "<your-client-secret>"
      ]
  }
}
```

Alternatively, you can set environment variables:

```json
"mcpServers": {
  "neo4j-aura": {
    "command": "uvx",
    "args": [ "mcp-neo4j-aura-manager@0.2.2" ],
    "env": {
      "NEO4J_AURA_CLIENT_ID": "<your-client-id>",
      "NEO4J_AURA_CLIENT_SECRET": "<your-client-secret>"
    }
  }
}
```

### 🐳 Using with Docker

```json
"mcpServers": {
  "neo4j-aura": {
    "command": "docker",
    "args": [
      "run",
      "--rm",
      "-e", "NEO4J_AURA_CLIENT_ID=${NEO4J_AURA_CLIENT_ID}",
      "-e", "NEO4J_AURA_CLIENT_SECRET=${NEO4J_AURA_CLIENT_SECRET}",
      "mcp-neo4j-aura-manager:0.2.2"
    ]
  }
}
```

### 🌐 HTTP Transport Mode

The server supports HTTP transport for web-based deployments and microservices:

```bash
# Basic HTTP mode (defaults: host=127.0.0.1, port=8000, path=/mcp/)
mcp-neo4j-aura-manager --transport http

# Custom HTTP configuration
mcp-neo4j-aura-manager --transport http --host 0.0.0.0 --port 8080 --path /api/mcp/
```

Environment variables for HTTP configuration:

```bash
export NEO4J_AURA_TRANSPORT=http
export NEO4J_AURA_HTTP_HOST=0.0.0.0
export NEO4J_AURA_HTTP_PORT=8080
export NEO4J_AURA_HTTP_PATH=/api/mcp/
mcp-neo4j-aura-manager
```

### 🔄 Transport Modes

The server supports three transport modes:

- **STDIO** (default): Standard input/output for local tools and Claude Desktop
- **SSE**: Server-Sent Events for web-based deployments  
- **HTTP**: Streamable HTTP for modern web deployments and microservices

## 📝 Usage Examples

### 🔍 Give overview over my tenants

![](docs/images/mcp-aura-tenant-overview.png)

### 🔎 Find an instance by name

![](docs/images/mcp-aura-find-by-name.png)

### 📋 List instances and find paused instance
![](docs/images/mcp-aura-find-paused.png)

### ▶️ Resume paused instances
![](docs/images/mcp-aura-list-resume.png)

### ➕ Create a new instance

![](docs/images/mcp-aura-create-instance.png)

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
git clone https://github.com/yourusername/mcp-neo4j-aura-manager.git
cd mcp-neo4j-aura-manager

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
docker build -t mcp-neo4j-aura-manager:<version> .

# Run the container
docker run -e NEO4J_AURA_CLIENT_ID="your-client-id" \
          -e NEO4J_AURA_CLIENT_SECRET="your-client-secret" \
          mcp-neo4j-aura-manager:<version>
```

## 📄 License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.


