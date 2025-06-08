# Multi-Protocol Usage Guide

## 🚀 Quick Start

Your MCP Neo4j Memory server now supports **all connection types**:
- **stdio** - For embedded usage (LibreChat spawns the process)
- **http** - REST API endpoints  
- **sse** - Server-Sent Events (for LibreChat container integration)

## 🐳 Docker Usage

### 1. Development (Standalone)
```bash
# Copy environment file
cp .env.example .env
# Edit passwords in .env file

# Run development stack
./run.sh dev     # Linux/Mac
run.bat dev      # Windows
```

### 2. Production (with LibreChat)
```bash
# Set environment variables
export NEO4J_PASSWORD="your_strong_password"

# Run production stack  
./run.sh prod    # Linux/Mac
run.bat prod     # Windows
```

## 🔧 Configuration Modes

### 1. HTTP Mode (Default for Docker)
```bash
mcp-neo4j-memory --mode http --port 3001
```
Access points:
- Health: http://localhost:3001/health
- Tools: http://localhost:3001/tools
- Execute: http://localhost:3001/execute (POST)
- SSE: http://localhost:3001/sse

### 2. Stdio Mode (LibreChat embedded)
```bash
mcp-neo4j-memory --mode stdio
```
Use with LibreChat `librechat-multi.yaml` stdio configuration.

### 3. Both Modes
```bash
mcp-neo4j-memory --mode both --port 3001
```

## 📡 API Examples

### HTTP REST API
```bash
# List available tools
curl http://localhost:3001/tools

# Execute a tool
curl -X POST http://localhost:3001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "read_graph",
    "arguments": {}
  }'

# Create entities
curl -X POST http://localhost:3001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_entities",
    "arguments": {
      "entities": [
        {
          "name": "John",
          "type": "Person", 
          "observations": ["Works at Neo4j", "Lives in San Francisco"]
        }
      ]
    }
  }'
```

### Server-Sent Events (SSE)
```bash
# Connect to SSE stream
curl -N http://localhost:3001/sse
```

## 🔌 LibreChat Integration

### Option 1: Container Mode (SSE)
Use `librechat.yaml` - LibreChat connects to your containerized MCP server via SSE.

### Option 2: Embedded Mode (stdio)  
Use `librechat-multi.yaml` - LibreChat spawns MCP server as a child process.

## 🌐 Access Points

After running `./run.sh dev`:
- **MCP Server**: http://localhost:3001
- **Neo4j Browser**: http://localhost:7474
- **API Health**: http://localhost:3001/health

After running `./run.sh prod`:
- **LibreChat**: http://localhost:3080
- **MCP Server**: http://localhost:3001
- **Neo4j Browser**: http://localhost:7474

## 🛠️ Environment Variables

Set these in your `.env` file:

```env
# Neo4j Configuration
NEO4J_URL=neo4j://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password_here
NEO4J_DATABASE=neo4j

# MCP Server Configuration
MCP_MODE=http  # stdio, http, or both
MCP_SERVER_PORT=3001
MCP_SERVER_HOST=0.0.0.0
```

## 🧪 Testing

```bash
# Test all endpoints
curl http://localhost:3001/
curl http://localhost:3001/health
curl http://localhost:3001/tools

# Test Neo4j connection
docker exec -it neo4j-db cypher-shell -u neo4j -p your_password_here "RETURN 'Connected!' as status"
```
