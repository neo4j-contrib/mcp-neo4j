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
      "mcp-neo4j-aura-manager@0.4.3",
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
    "args": [ "mcp-neo4j-aura-manager@0.4.3" ],
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
      "mcp-neo4j-aura-manager:0.4.3"
    ]
  }
}
```

### 🏷️ Namespacing for Multi-tenant Deployments

The server supports namespacing to prefix tool names for multi-tenant deployments:

```json
"mcpServers": {
  "neo4j-aura-app1": {
    "command": "uvx",
    "args": [
      "mcp-neo4j-aura-manager@0.4.3",
      "--client-id", "<your-client-id>",
      "--client-secret", "<your-client-secret>",
      "--namespace", "app1"
    ]
  },
  "neo4j-aura-app2": {
    "command": "uvx", 
    "args": [
      "mcp-neo4j-aura-manager@0.4.3",
      "--client-id", "<your-client-id>",
      "--client-secret", "<your-client-secret>",
      "--namespace", "app2"
    ]
  }
}
```

#### CLI Usage
```bash
# With namespace
mcp-neo4j-aura-manager --client-id <id> --client-secret <secret> --namespace myapp

# Tools become: myapp-list_instances, myapp-create_instance, etc.
```

#### Environment Variables
```bash
export NEO4J_AURA_CLIENT_ID=your_client_id
export NEO4J_AURA_CLIENT_SECRET=your_client_secret  
export NEO4J_NAMESPACE=myapp
mcp-neo4j-aura-manager
```

#### Docker with Namespacing
```bash
docker run -e NEO4J_AURA_CLIENT_ID=<id> \
           -e NEO4J_AURA_CLIENT_SECRET=<secret> \
           -e NEO4J_NAMESPACE=myapp \
           mcp-neo4j-aura-manager
```

### 🌐 HTTP Transport Mode

The server supports HTTP transport for web-based deployments and microservices:

```bash
# Basic HTTP mode (defaults: host=127.0.0.1, port=8000, path=/mcp/)
mcp-neo4j-aura-manager --transport http

# Custom HTTP configuration
mcp-neo4j-aura-manager --transport http --host 127.0.0.1 --port 8080 --path /api/mcp/
```

Environment variables for HTTP configuration:

```bash
export NEO4J_TRANSPORT=http
export NEO4J_MCP_SERVER_HOST=127.0.0.1
export NEO4J_MCP_SERVER_PORT=8080
export NEO4J_MCP_SERVER_PATH=/api/mcp/
export NEO4J_MCP_SERVER_ALLOWED_HOSTS="localhost,127.0.0.1"
export NEO4J_MCP_SERVER_ALLOW_ORIGINS="http://localhost:3000"
export NEO4J_NAMESPACE=myapp
mcp-neo4j-aura-manager
```

### 🔄 Transport Modes

The server supports three transport modes:

- **STDIO** (default): Standard input/output for local tools and Claude Desktop
- **SSE**: Server-Sent Events for web-based deployments
- **HTTP**: Streamable HTTP for modern web deployments and microservices

## 🔒 Security Protection

The server includes comprehensive security protection with **secure defaults** that protect against common web-based attacks while preserving full MCP functionality when using HTTP transport.

### 🛡️ DNS Rebinding Protection

**TrustedHost Middleware** validates Host headers to prevent DNS rebinding attacks:

**Secure by Default:**
- Only `localhost` and `127.0.0.1` hosts are allowed by default
- Malicious websites cannot trick browsers into accessing your local server

**Environment Variable:**
```bash
export NEO4J_MCP_SERVER_ALLOWED_HOSTS="example.com,www.example.com"
```

### 🌐 CORS Protection

**Cross-Origin Resource Sharing (CORS)** protection blocks browser-based requests by default:

**Environment Variable:**
```bash
export NEO4J_MCP_SERVER_ALLOW_ORIGINS="https://example.com,https://example.com"
```

### 🔧 Complete Security Configuration

**Development Setup:**
```bash
mcp-neo4j-aura-manager --transport http \
  --allowed-hosts "localhost,127.0.0.1" \
  --allow-origins "http://localhost:3000"
```

**Production Setup:**
```bash
mcp-neo4j-aura-manager --transport http \
  --allowed-hosts "example.com,www.example.com" \
  --allow-origins "https://example.com,https://example.com"
```

### 🚨 Security Best Practices

**For `allow_origins`:**
- Be specific: `["https://example.com", "https://example.com"]`
- Never use `"*"` in production with credentials
- Use HTTPS origins in production

**For `allowed_hosts`:**
- Include your actual domain: `["example.com", "www.example.com"]`
- Include localhost only for development
- Never use `"*"` unless you understand the risks


## 🐳 Docker Deployment

The Neo4j Aura Manager MCP server can be deployed using Docker for remote deployments. Docker deployment should use HTTP transport for web accessibility. In order to integrate this deployment with applications like Claude Desktop, you will have to use a proxy in your MCP configuration such as `mcp-remote`.

### 🐳 Using with Docker for Claude Desktop

Here we use the Docker Hub hosted Aura Manager MCP server image with stdio transport for use with Claude Desktop.

**Config details:**
* `-i`: Interactive mode - keeps STDIN open for stdio transport communication
* `--rm`: Automatically remove container when it exits (cleanup)
* `-p 8000:8000`: Port mapping - maps host port 8000 to container port 8000
* `NEO4J_TRANSPORT=stdio`: Uses stdio transport for Claude Desktop compatibility
* `NEO4J_AURA_CLIENT_ID` and `NEO4J_AURA_CLIENT_SECRET`: Your Aura API credentials

```json
{
  "mcpServers": {
    "neo4j-aura": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-p",
        "8000:8000",
        "-e", "NEO4J_AURA_CLIENT_ID=your-client-id",
        "-e", "NEO4J_AURA_CLIENT_SECRET=your-client-secret",
        "-e", "NEO4J_TRANSPORT=stdio",
        "mcp/neo4j-aura-manager:latest"
      ]
    }
  }
}
```

### 📦 Using Your Built Image

After building locally with `docker build -t mcp-neo4j-aura-manager:latest .`:

```bash
# Build the image
docker build -t mcp-neo4j-aura-manager:<version> .

# Run with http transport (default for Docker)
docker run --rm -p 8000:8000 \
  -e NEO4J_AURA_CLIENT_ID="your-client-id" \
  -e NEO4J_AURA_CLIENT_SECRET="your-client-secret" \
  -e NEO4J_TRANSPORT="http" \
  -e NEO4J_MCP_SERVER_HOST="0.0.0.0" \
  -e NEO4J_MCP_SERVER_PORT="8000" \
  -e NEO4J_MCP_SERVER_PATH="/mcp/" \
  mcp-neo4j-aura-manager:<version>

# Run with security middleware for production
docker run --rm -p 8000:8000 \
  -e NEO4J_AURA_CLIENT_ID="your-client-id" \
  -e NEO4J_AURA_CLIENT_SECRET="your-client-secret" \
  -e NEO4J_TRANSPORT="http" \
  -e NEO4J_MCP_SERVER_HOST="0.0.0.0" \
  -e NEO4J_MCP_SERVER_PORT="8000" \
  -e NEO4J_MCP_SERVER_PATH="/mcp/" \
  -e NEO4J_MCP_SERVER_ALLOWED_HOSTS="example.com,www.example.com" \
  -e NEO4J_MCP_SERVER_ALLOW_ORIGINS="https://example.com" \
  mcp-neo4j-aura-manager:<version>
```

### 🔧 Environment Variables

| Variable                           | Default                                 | Description                                        |
| ---------------------------------- | --------------------------------------- | -------------------------------------------------- |
| `NEO4J_AURA_CLIENT_ID`             | _(none)_                                | Neo4j Aura API Client ID                          |
| `NEO4J_AURA_CLIENT_SECRET`         | _(none)_                                | Neo4j Aura API Client Secret                      |
| `NEO4J_TRANSPORT`                  | `stdio` (local), `http` (remote)        | Transport protocol (`stdio`, `http`, or `sse`)     |
| `NEO4J_MCP_SERVER_HOST`            | `127.0.0.1` (local)                     | Host to bind to                                    |
| `NEO4J_MCP_SERVER_PORT`            | `8000`                                  | Port for HTTP/SSE transport                        |
| `NEO4J_MCP_SERVER_PATH`            | `/mcp/`                                 | Path for accessing MCP server                      |
| `NEO4J_MCP_SERVER_ALLOW_ORIGINS`   | _(empty - secure by default)_           | Comma-separated list of allowed CORS origins       |
| `NEO4J_MCP_SERVER_ALLOWED_HOSTS`   | `localhost,127.0.0.1`                   | Comma-separated list of allowed hosts (DNS rebinding protection) |
| `NEO4J_NAMESPACE`                  | _(empty - no prefix)_                   | Namespace prefix for tool names (e.g., `myapp-list_instances`) |

### 🌐 SSE Transport for Legacy Web Access

When using SSE transport (for legacy web clients), the server exposes an HTTP endpoint:

```bash
# Start the server with SSE transport
docker run -d -p 8000:8000 \
  -e NEO4J_AURA_CLIENT_ID="your-client-id" \
  -e NEO4J_AURA_CLIENT_SECRET="your-client-secret" \
  -e NEO4J_TRANSPORT="sse" \
  -e NEO4J_MCP_SERVER_HOST="0.0.0.0" \
  -e NEO4J_MCP_SERVER_PORT="8000" \
  --name neo4j-aura-mcp-server \
  mcp-neo4j-aura-manager:latest

# Test the SSE endpoint
curl http://localhost:8000/sse

# Use with MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8000/sse
```

### 🔗 Claude Desktop Integration with Docker

For Claude Desktop integration with a Dockerized server using http transport:

```json
{
  "mcpServers": {
    "neo4j-aura-docker": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "http://localhost:8000/mcp/"]
    }
  }
}
```

**Note**: First start your Docker container with HTTP transport, then Claude Desktop can connect to it via the HTTP endpoint and proxy server like `mcp-remote`.

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

## 📄 License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.


