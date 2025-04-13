FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatchling

# Copy dependency files first
COPY pyproject.toml /app/

# Install runtime dependencies
RUN pip install --no-cache-dir mcp>=1.6.0 requests>=2.31.0

# Copy the source code
COPY src/ /app/src/
COPY README.md /app/

# Install the package
RUN pip install --no-cache-dir -e .

# Environment variables for Neo4j Aura API credentials
ENV NEO4J_AURA_CLIENT_ID=""
ENV NEO4J_AURA_CLIENT_SECRET=""

# Command to run the server using the package entry point
CMD ["sh", "-c", "mcp-neo4j-aura-manager --client-id ${NEO4J_AURA_CLIENT_ID} --client-secret ${NEO4J_AURA_CLIENT_SECRET}"]