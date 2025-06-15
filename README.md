# Neo4j MCP Clients & Servers

Model Context Protocol (MCP) is a [standardized protocol](https://modelcontextprotocol.io/introduction) for managing context between large language models (LLMs) and external systems. 

This lets you use Claude Desktop, or any other MCP Client (VS Code, Cursor, Windsurf), to use natural language to accomplish things with Neo4j and your Aura account, e.g.:

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Blog Posts

* [Everything a Developer Needs to Know About the Model Context Protocol (MCP)](https://neo4j.com/blog/developer/model-context-protocol/)
* [Claude Converses With Neo4j Via MCP - Graph Database & Analytics](https://neo4j.com/blog/developer/claude-converses-neo4j-via-mcp/)
* [Building Knowledge Graphs With Claude and Neo4j: A No-Code MCP Approach - Graph Database & Analytics](https://neo4j.com/blog/developer/knowledge-graphs-claude-neo4j-mcp/)

## License

MIT License
