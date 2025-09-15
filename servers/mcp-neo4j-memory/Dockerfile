FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatchling

# Copy dependency files first
COPY pyproject.toml /app/

# Install runtime dependencies
RUN pip install --no-cache-dir fastmcp>=2.0.0 neo4j>=5.26.0

# Copy the source code
COPY src/ /app/src/
COPY README.md /app/

# Install the package
RUN pip install --no-cache-dir -e .

# Environment variables for Neo4j connection
ENV NEO4J_URL="bolt://host.docker.internal:7687"
ENV NEO4J_USERNAME="neo4j"
ENV NEO4J_PASSWORD="password"
ENV NEO4J_DATABASE="neo4j"
ENV NEO4J_TRANSPORT="stdio"
ENV NEO4J_MCP_SERVER_HOST="0.0.0.0"
ENV NEO4J_MCP_SERVER_PORT="8000"
ENV NEO4J_MCP_SERVER_PATH="/api/mcp/"
ENV NEO4J_MCP_SERVER_ALLOW_ORIGINS=""
ENV NEO4J_MCP_SERVER_ALLOWED_HOSTS="localhost,127.0.0.1"

# Command to run the server using the package entry point
CMD ["sh", "-c", "mcp-neo4j-memory"]