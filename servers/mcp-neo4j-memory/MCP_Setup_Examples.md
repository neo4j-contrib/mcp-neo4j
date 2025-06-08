

# Claude Desktop stdio config with docker
```json
{
  "mcpServers": {
    "neo4j": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--network", "host",
        "-e", "NEO4J_URL=bolt://localhost:7687",
        "-e", "NEO4J_USERNAME=neo4j",
        "-e", "NEO4J_PASSWORD=q1w2e3r4t5",
        "lesykm/mcp-neo4j-memory:stdio"
      ]
    }
  }
}
```

```json
{
  "mcpServers": {
    "neo4j": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-e",
        "NEO4J_URL=neo4j+s://xxxx.databases.neo4j.io",
        "-e",
        "NEO4J_USERNAME=<your-username>",
        "-e",
        "NEO4J_PASSWORD=<your-password>",
        "mcp/neo4j-memory:0.1.4"
      ]
    }
  }
}
```


# Claude connect to sse
```json
{
  "mcpServers": {
    "neo4j": {
      "transport": {
        "type": "sse",
        "url": "http://localhost:3002/sse"
      }
    }
  }
}

```
