FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatchling

COPY pyproject.toml /app/

# Install dependencies
RUN pip install --no-cache-dir neo4j>=5.26.0 fastmcp>=2.10.5


# Copy the source code
COPY src/ /app/src/
COPY README.md /app/

RUN pip install --no-cache-dir -e .

# Environment variables for Neo4j connection
ENV NEO4J_URI="bolt://host.docker.internal:7687"
ENV NEO4J_USERNAME="neo4j"
ENV NEO4J_PASSWORD="password"
ENV NEO4J_DATABASE="neo4j"
ENV NEO4J_NAMESPACE=""
ENV NEO4J_TRANSPORT="http"
ENV NEO4J_MCP_SERVER_HOST="0.0.0.0"
ENV NEO4J_MCP_SERVER_PORT="8000"
ENV NEO4J_MCP_SERVER_PATH="/api/mcp/"

EXPOSE 8000

# Command to run the server using the package entry point
CMD ["mcp-neo4j-cypher"]