# Neo4j Labs MCP Servers

## Neo4j Labs

These MCP servers are a part of the [Neo4j Labs](https://neo4j.com/labs/) program. 
They are developed and maintained by the Neo4j Field GenAI team and welcome contributions from the larger developer community. 
These servers are frequently updated with new and experimental features, but are not supported by the Neo4j product team. 

**They are actively developed and maintained, but we don’t provide any SLAs or guarantees around backwards compatibility and deprecation.**

If you are looking for the official product Neo4j MCP server please find it [here](https://github.com/neo4j/mcp).

## Overview

Model Context Protocol (MCP) is a [standardized protocol](https://modelcontextprotocol.io/introduction) for managing context between large language models (LLMs) and external systems. 

This lets you use Claude Desktop, or any other MCP Client (VS Code, Cursor, Windsurf, Gemini CLI), to use natural language to accomplish things with Neo4j and your Aura account, e.g.:

* What is in this graph?
* Render a chart from the top products sold by frequency, total and average volume
* List my instances
* Create a new instance named mcp-test for Aura Professional with 4GB and Graph Data Science enabled
* Store the fact that I worked on the Neo4j MCP Servers today with Andreas and Oskar

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Blog Posts

* [Everything a Developer Needs to Know About the Model Context Protocol (MCP)](https://neo4j.com/blog/developer/model-context-protocol/)
* [Claude Converses With Neo4j Via MCP - Graph Database & Analytics](https://neo4j.com/blog/developer/claude-converses-neo4j-via-mcp/)
* [Building Knowledge Graphs With Claude and Neo4j: A No-Code MCP Approach - Graph Database & Analytics](https://neo4j.com/blog/developer/knowledge-graphs-claude-neo4j-mcp/)
* [Using the Neo4j Extension in Gemini CLI](https://cloud.google.com/blog/topics/developers-practitioners/using-the-neo4j-extension-in-gemini-cli)

## License

MIT License
