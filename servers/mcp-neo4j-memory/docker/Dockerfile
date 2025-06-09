# Master Dockerfile with multi-stage build for MCP Neo4j Memory server
# This provides a shared build stage for all protocol-specific images

# ============================================================================
# BUILD STAGE - Shared across all protocol variants
# ============================================================================
FROM python:3.11-alpine as builder

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Copy README.md as it's referenced in pyproject.toml
COPY README.md ./

# Copy source code
COPY src/ ./src/
# Install build dependencies, build everything, then remove build deps in one layer
RUN apk add --no-cache --virtual .build-deps build-base && \
    pip install --no-cache-dir uv && \
    (uv sync --frozen --no-dev || pip install --no-cache-dir -e .) && \
    pip install --no-cache-dir -e . && \
    apk del .build-deps


# ============================================================================
# RUNTIME BASE - Shared runtime configuration
# ============================================================================
FROM python:3.11-alpine as runtime-base

# Create non-root user for security
RUN addgroup -S mcp && adduser -S -G mcp mcp

# Set working directory
WORKDIR /app

# Copy installed packages from builder (this is the main optimization)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/mcp-neo4j-memory /usr/local/bin
COPY --from=builder /app/src /app/src
COPY --from=builder /app/README.md /app/

# Create directory for potential data persistence
RUN mkdir -p /app/data && chown -R mcp:mcp /app

# Clean up caches and build artifacts
RUN rm -rf /root/.cache /tmp/* /var/cache/apk/* && \
    find /usr/local -name "*.pyc" -delete && \
    find /usr/local -name "__pycache__" -type d -exec rm -rf {} + || true

# Switch to non-root user
USER mcp

# Set PYTHONPATH to ensure module imports work
ENV PYTHONPATH=/app/src

# Common environment variables
ENV NEO4J_URL="bolt://host.docker.internal:7687"
ENV NEO4J_USERNAME="neo4j"
ENV NEO4J_PASSWORD="password"
ENV NEO4J_DATABASE="neo4j"

# Default command (overridden by specific variants)
CMD ["echo", "Base image - specify target variant"]

# ============================================================================
# STDIO VARIANT - Default MCP protocol
# ============================================================================
FROM runtime-base as stdio

# stdio-specific environment
ENV MCP_MODE="stdio"

# Health check for stdio mode (check package import)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import mcp_neo4j_memory; print('OK')" || exit 1

# stdio command
CMD ["sh", "-c", "mcp-neo4j-memory --mode ${MCP_MODE} --db-url ${NEO4J_URL} --username ${NEO4J_USERNAME} --password ${NEO4J_PASSWORD} --database ${NEO4J_DATABASE}"]

# Labels for stdio
LABEL maintainer="MCP Neo4j Memory"
LABEL description="stdio-only MCP server for Neo4j knowledge graph memory"
LABEL protocol="stdio"
LABEL variant="stdio"

# ============================================================================
# SSE VARIANT - Server-Sent Events protocol
# ============================================================================
FROM runtime-base as sse

# SSE-specific environment
ENV MCP_MODE="sse"
ENV MCP_SERVER_HOST="0.0.0.0"
ENV MCP_SERVER_PORT="3001"

# Expose SSE port
EXPOSE 3001

# Install curl for health checks
USER root
RUN apk add --no-cache curl && rm -rf /var/cache/apk/*
USER mcp

# Health check for SSE mode
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3001/health || exit 1

# SSE command
CMD ["sh", "-c", "mcp-neo4j-memory --mode ${MCP_MODE} --host ${MCP_SERVER_HOST} --port ${MCP_SERVER_PORT} --db-url ${NEO4J_URL} --username ${NEO4J_USERNAME} --password ${NEO4J_PASSWORD} --database ${NEO4J_DATABASE}"]

# Labels for SSE
LABEL maintainer="MCP Neo4j Memory"
LABEL description="Server-Sent Events MCP server for Neo4j knowledge graph memory"
LABEL protocol="sse"
LABEL variant="sse"

# ============================================================================
# TEST VARIANT - Test environment with all dependencies
# ============================================================================
FROM runtime-base as test

# Test-specific environment
ENV MCP_MODE="stdio"
ENV PYTHONPATH=/app/src

# Install test dependencies
USER root
RUN apk add --no-cache curl && rm -rf /var/cache/apk/*

# Install test packages in one layer to minimize size impact
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    pytest-xdist \
    pytest-timeout \
    pytest-mock \
    httpx \
    aiohttp \
    requests && \
    rm -rf /root/.cache

USER mcp

# Test command (runs comprehensive test suite)
CMD ["python", "tests/run_all_tests.py"]

# Labels for test
LABEL maintainer="MCP Neo4j Memory"
LABEL description="Test environment for MCP Neo4j Memory with all dependencies"
LABEL protocol="all"
LABEL variant="test"
