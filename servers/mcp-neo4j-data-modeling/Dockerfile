FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install build dependencies
RUN pip install uv

# Copy dependency files first
COPY pyproject.toml /app/
COPY uv.lock /app/

# Copy the source code
COPY src/ /app/src/
COPY README.md /app/

# Install the package
RUN uv sync

ENV NEO4J_TRANSPORT="stdio"
ENV NEO4J_MCP_SERVER_HOST="0.0.0.0"
ENV NEO4J_MCP_SERVER_PORT="8000"
ENV NEO4J_MCP_SERVER_PATH="/mcp/"


# Command to run the server using the package entry point
CMD ["sh", "-c", "uv run mcp-neo4j-data-modeling"]