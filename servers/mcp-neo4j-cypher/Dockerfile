FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatchling

COPY pyproject.toml /app/

# Install dependencies
RUN pip install --no-cache-dir neo4j>=5.26.0 mcp>=1.6.0


# Copy the source code
COPY src/ /app/src/
COPY README.md /app/

RUN pip install --no-cache-dir -e .

# Environment variables for Neo4j connection
ENV NEO4J_URL="bolt://host.docker.internal:7687"
ENV NEO4J_USERNAME="neo4j"
ENV NEO4J_PASSWORD="neo4j_password"
ENV NEO4J_DATABASE="neo4j"

# Set transport type (can be "sse" or "stdio")
ENV MCP_TRANSPORT="sse"

# Expose port for SSE transport
EXPOSE 8000

# Command to run the server using the entry point (will use transport type from MCP_TRANSPORT env var)
CMD ["python", "-m", "src.mcp_neo4j_memory.main"]