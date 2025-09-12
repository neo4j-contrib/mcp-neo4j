# Common

Common utilities and middleware for MCP Neo4j servers.

## Installation

You should not have to manually install this package, however if you are receiving import errors you may try reinstalling with the following:

```bash
uv sync --reinstall-package common
```

## Features

This package provides three main categories of utilities:

1. **Middleware** - Pre-configured middleware for CORS and trusted host protection
2. **Config Processing** - Utilities for processing command-line arguments and environment variables
3. **Namespace Formatting** - Utilities for consistent namespace handling in tool naming

## Middleware

The middleware module provides factory functions for creating pre-configured Starlette middleware instances commonly needed by remotely deployed MCP Neo4j servers.

### CORS Middleware

```python
from common.middleware import create_cors_middleware

# Create CORS middleware with allowed origins
cors_middleware = create_cors_middleware(
    allow_origins=["https://example.com", "https://app.example.com"]
)
```

The CORS middleware is configured with:
- **Methods**: `GET`, `POST`
- **Headers**: All headers allowed (`*`)
- **Origins**: Configurable list of allowed origins

### Trusted Host Middleware

```python
from common.middleware import create_trusted_host_middleware

# Create trusted host middleware for DNS rebinding protection
trusted_host_middleware = create_trusted_host_middleware(
    allowed_hosts=["localhost", "127.0.0.1", "myapp.com"]
)
```

## Config Processing

The `arg_processing` module provides utilities for processing configuration from both command-line arguments and environment variables, with sensible defaults and logging.

### Available Processing Functions

Each function follows the pattern: check command-line args first, then environment variables, then apply defaults with appropriate logging.

```python
from common.utils.arg_processing import (
    process_db_url,
    process_username,
    process_password,
)
import argparse

# Example usage
args = argparse.Namespace()  # Your parsed arguments
db_url = process_db_url(args)
username = process_username(args)
password = process_password(args)
```

### Configuration Priority

1. **Command-line arguments** 
2. **Environment variables** 
3. **Default values** 

### Environment Variables

| Function | Environment Variables | Default |
|----------|----------------------|---------|
| `process_db_url` | `NEO4J_URL`, `NEO4J_URI` | `bolt://localhost:7687` |
| `process_username` | `NEO4J_USERNAME` | `neo4j` |
| `process_password` | `NEO4J_PASSWORD` | `password` |
| `process_database` | `NEO4J_DATABASE` | `neo4j` |
| `process_namespace` | `NEO4J_NAMESPACE` | `""` (empty) |
| `process_transport` | `NEO4J_TRANSPORT` | `stdio` |
| `process_server_host` | `NEO4J_MCP_SERVER_HOST` | `127.0.0.1` (ignored if transport is `stdio`) |
| `process_server_port` | `NEO4J_MCP_SERVER_PORT` | `8000` (ignored if transport is `stdio`) |
| `process_server_path` | `NEO4J_MCP_SERVER_PATH` | `/mcp/` (ignored if transport is `stdio`) |
| `process_allow_origins` | `NEO4J_MCP_SERVER_ALLOW_ORIGINS` | `[]` (empty list) |
| `process_allowed_hosts` | `NEO4J_MCP_SERVER_ALLOWED_HOSTS` | `["localhost", "127.0.0.1"]` |
| `process_token_limit` | `NEO4J_RESPONSE_TOKEN_LIMIT` | `None` |
| `process_read_timeout` | `NEO4J_READ_TIMEOUT` | `30` |

## Namespace Formatting

The `namespace` module provides utilities for consistent namespace formatting in tool naming conventions.

### format_namespace Function

```python
from common.utils.namespace import format_namespace

# Ensures namespace ends with hyphen for tool naming
formatted = format_namespace("myapp")      # Returns: "myapp-"
formatted = format_namespace("myapp-")     # Returns: "myapp-" (no change)
```

This ensures consistent tool naming across MCP Neo4j servers, where namespaced tools follow the pattern `namespace-toolname` and non-namespaced tools use just the tool name.