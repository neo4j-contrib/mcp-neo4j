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
ENV NEO4J_PASSWORD="password"

# Command to run the server using the package entry point
CMD ["sh", "-c", "mcp-neo4j-cypher --db-url ${NEO4J_URL} --username ${NEO4J_USERNAME} --password ${NEO4J_PASSWORD}"]