#!/bin/bash
set -e

echo "Building All MCP Neo4j Memory Docker Images"
echo "=============================================="

# Extract version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

if [ -z "$VERSION" ]; then
    echo "Could not extract version from pyproject.toml"
    exit 1
fi

echo "Version detected: $VERSION"

# Function to build and tag an image
build_image() {
    local dockerfile=$1
    local base_tag=$2
    local protocol=$3
    local description=$4

    echo ""
    echo "Building $description..."
    echo "Dockerfile: $dockerfile"
    echo "Base tag: $base_tag"
    echo "Protocol: $protocol"
    echo "----------------------------------------"

    # Build the image
    docker build -f "$dockerfile" -t "mcp-neo4j-memory:$base_tag" .

    # Tag with version and protocol
    docker tag "mcp-neo4j-memory:$base_tag" "mcp-neo4j-memory:${VERSION}-$protocol"
    docker tag "mcp-neo4j-memory:$base_tag" "mcp-neo4j-memory:$protocol"

    echo "$description build complete!"
}

# Parse command line arguments
case "$1" in
    "stdio")
        build_image "docker/Dockerfile_stdio" "latest" "stdio" "stdio-only server"
        # stdio is the default/latest
        docker tag "mcp-neo4j-memory:stdio" "mcp-neo4j-memory:$VERSION"
        ;;
    "sse")
        build_image "docker/Dockerfile_sse" "sse" "sse" "Server-Sent Events server"
        ;;
    "test")
        build_image "docker/Dockerfile_test" "test" "test" "Test environment"
        ;;
    "all"|"")
        echo "Building using master Dockerfile with all variants..."

        # Build stdio (default)
        docker build -f docker/Dockerfile --target stdio -t mcp-neo4j-memory:latest .
        docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:stdio
        docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:${VERSION}
        docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:${VERSION}-stdio

        # Build SSE
        docker build -f docker/Dockerfile --target sse -t mcp-neo4j-memory:sse .
        docker tag mcp-neo4j-memory:sse mcp-neo4j-memory:${VERSION}-sse

        # Build test
        docker build -f docker/Dockerfile --target test -t mcp-neo4j-memory:test .
        docker tag mcp-neo4j-memory:test mcp-neo4j-memory:${VERSION}-test

        echo "All variants built!"
        ;;
    *)
        echo "Usage: $0 [stdio|sse|test|all]"
        echo ""
        echo "Commands:"
        echo "  stdio  - Build stdio-only optimized image"
        echo "  sse    - Build Server-Sent Events server image"
        echo "  test   - Build test environment image"
        echo "  all    - Build all variants (default)"
        echo ""
        echo "Examples:"
        echo "  $0           # Build all variants"
        echo "  $0 stdio     # Build stdio-only (becomes latest)"
        echo "  $0 sse       # Build SSE streaming server"
        exit 1
        ;;
esac

echo ""
echo "Build Summary"
echo "============="
echo "Available images:"
docker images | grep mcp-neo4j-memory | sort

echo ""
echo "Image Tags Guide:"
echo "mcp-neo4j-memory:latest      - stdio-only server (default)"
echo "mcp-neo4j-memory:stdio       - stdio-only server"
echo "mcp-neo4j-memory:sse         - Server-Sent Events server"
echo "mcp-neo4j-memory:test        - Test environment"
echo ""
echo "Versioned Tags:"
echo "mcp-neo4j-memory:${VERSION}        - Latest stdio version"
echo "mcp-neo4j-memory:${VERSION}-stdio"
echo "mcp-neo4j-memory:${VERSION}-sse"
echo "mcp-neo4j-memory:${VERSION}-test"
echo ""
echo "Usage examples:"
echo "# Run SSE server with default settings:"
echo "docker run -p 3001:3001 mcp-neo4j-memory:sse"
echo ""
echo "# Run SSE server with custom Neo4j connection:"
echo "docker run -p 3001:3001 \\"
echo "  -e NEO4J_URL=\"bolt://your-neo4j:7687\" \\"
echo "  -e NEO4J_PASSWORD=\"your-password\" \\"
echo "  mcp-neo4j-memory:${VERSION}-sse"
echo ""
echo "# Test the SSE server:"
echo "curl http://localhost:3001/sse"
echo "# Should return event-stream data for real-time streaming"
echo ""
echo "Usage examples:"
echo "# Run with default Neo4j connection:"
echo "docker run -it mcp-neo4j-memory:latest"
echo "docker run -it mcp-neo4j-memory:stdio"
echo ""
echo "# Run with custom Neo4j connection:"
echo "docker run -it \\"
echo "  -e NEO4J_URL=\"bolt://your-neo4j:7687\" \\"
echo "  -e NEO4J_PASSWORD=\"your-password\" \\"
echo "  mcp-neo4j-memory:${VERSION}-stdio"
