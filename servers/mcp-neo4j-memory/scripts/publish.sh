#!/bin/bash
set -e

echo "MCP Neo4j Memory - Docker Image Publisher"
echo "========================================"

# Check for dry-run flag
DRY_RUN=false
if [ "$1" = "--dry-run" ] || [ "$1" = "-n" ]; then
    DRY_RUN=true
    shift  # Remove the dry-run flag from arguments
    echo "DRY RUN MODE - No actual pushing will occur"
    echo ""
fi

# Configuration
REGISTRY="${DOCKER_REGISTRY:-docker.io}"  # Default to Docker Hub
NAMESPACE="${DOCKER_NAMESPACE:-your-username}"  # Change this!
IMAGE_NAME="mcp-neo4j-memory"

# Extract version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

if [ -z "$VERSION" ]; then
    echo "Could not extract version from pyproject.toml"
    exit 1
fi

echo "Configuration:"
echo "Registry: $REGISTRY"
echo "Namespace: $NAMESPACE"
echo "Image: $IMAGE_NAME"
echo "Version: $VERSION"
if [ "$DRY_RUN" = true ]; then
    echo "Mode: DRY RUN (simulation only)"
fi
echo ""

# Function to tag and push an image
publish_variant() {
    local variant=$1
    local local_tag=$2
    local push_latest=$3

    echo "Publishing $variant variant..."
    echo "----------------------------------------"

    # Tag with registry/namespace
    local remote_base="$REGISTRY/$NAMESPACE/$IMAGE_NAME"

    # Tag version-specific
    echo "Tagging: $local_tag -> $remote_base:$VERSION-$variant"
    if [ "$DRY_RUN" = false ]; then
        docker tag "$local_tag" "$remote_base:$VERSION-$variant"
    fi

    # Tag variant
    echo "Tagging: $local_tag -> $remote_base:$variant"
    if [ "$DRY_RUN" = false ]; then
        docker tag "$local_tag" "$remote_base:$variant"
    fi

    # Tag latest (only for stdio)
    if [ "$push_latest" = "true" ]; then
        echo "Tagging: $local_tag -> $remote_base:$VERSION"
        if [ "$DRY_RUN" = false ]; then
            docker tag "$local_tag" "$remote_base:$VERSION"
        fi
        echo "Tagging: $local_tag -> $remote_base:latest"
        if [ "$DRY_RUN" = false ]; then
            docker tag "$local_tag" "$remote_base:latest"
        fi
    fi

    # Push all tags
    echo "Pushing $variant images..."
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY RUN] docker push $remote_base:$VERSION-$variant"
        echo "  [DRY RUN] docker push $remote_base:$variant"
        if [ "$push_latest" = "true" ]; then
            echo "  [DRY RUN] docker push $remote_base:$VERSION"
            echo "  [DRY RUN] docker push $remote_base:latest"
        fi
    else
        docker push "$remote_base:$VERSION-$variant"
        docker push "$remote_base:$variant"
        if [ "$push_latest" = "true" ]; then
            docker push "$remote_base:$VERSION"
            docker push "$remote_base:latest"
        fi
    fi

    echo "$variant variant published successfully!"
    echo ""
}

# Check if user is logged in (skip in dry-run mode)
if [ "$DRY_RUN" = false ]; then
    echo "Checking Docker registry authentication..."
    if ! docker info >/dev/null 2>&1; then
        echo "Error: Docker is not running"
        exit 1
    fi
fi

# Parse command line arguments
case "$1" in
    "stdio")
        publish_variant "stdio" "mcp-neo4j-memory:stdio" true
        ;;
    "sse")
        publish_variant "sse" "mcp-neo4j-memory:sse" false
        ;;
    "test")
        publish_variant "test" "mcp-neo4j-memory:test" false
        ;;
    "all"|"")
        echo "Publishing all variants..."
        echo ""

        publish_variant "stdio" "mcp-neo4j-memory:stdio" true
        publish_variant "sse" "mcp-neo4j-memory:sse" false
        publish_variant "test" "mcp-neo4j-memory:test" false

        echo "All variants published successfully!"
        ;;
    "login")
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY RUN] Would execute: docker login"
            exit 0
        fi
        echo "Logging into Docker registry..."
        if [ "$REGISTRY" = "docker.io" ]; then
            docker login
        else
            docker login "$REGISTRY"
        fi
        echo "Login successful!"
        exit 0
        ;;
    *)
        echo "Usage: $0 [--dry-run] [stdio|sse|test|all|login]"
        echo ""
        echo "Options:"
        echo "  --dry-run, -n   Show what would be done without actually doing it"
        echo ""
        echo "Commands:"
        echo "  stdio  - Publish stdio variant (becomes latest)"
        echo "  sse    - Publish SSE streaming variant"
        echo "  test   - Publish test environment variant"
        echo "  all    - Publish all variants (default)"
        echo "  login  - Login to Docker registry"
        echo ""
        echo "Environment Variables:"
        echo "  DOCKER_REGISTRY  - Registry URL (default: docker.io)"
        echo "  DOCKER_NAMESPACE - Namespace/username (default: your-username)"
        echo ""
        echo "Examples:"
        echo "  $0 --dry-run                         # Dry run all variants"
        echo "  $0 --dry-run stdio                   # Dry run stdio only"
        echo "  $0 login                             # Login first"
        echo "  $0                                   # Publish all variants"
        echo "  $0 stdio                             # Publish stdio only"
        echo "  DOCKER_NAMESPACE=myuser $0           # Use custom namespace"
        echo "  DOCKER_REGISTRY=ghcr.io $0           # Use GitHub Container Registry"
        exit 1
        ;;
esac

echo ""
echo "Publication Summary"
echo "=================="
echo "Registry: $REGISTRY"
if [ "$DRY_RUN" = true ]; then
    echo "Mode: DRY RUN - No actual changes made"
    echo ""
    echo "Would have published these tags:"
else
    echo "Published tags:"
fi

if [ "$1" = "all" ] || [ "$1" = "" ] || [ "$1" = "stdio" ]; then
    echo "  $REGISTRY/$NAMESPACE/$IMAGE_NAME:latest"
    echo "  $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION"
    echo "  $REGISTRY/$NAMESPACE/$IMAGE_NAME:stdio"
    echo "  $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION-stdio"
fi

if [ "$1" = "all" ] || [ "$1" = "" ] || [ "$1" = "sse" ]; then
    echo "  $REGISTRY/$NAMESPACE/$IMAGE_NAME:sse"
    echo "  $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION-sse"
fi

if [ "$1" = "all" ] || [ "$1" = "" ] || [ "$1" = "test" ]; then
    echo "  $REGISTRY/$NAMESPACE/$IMAGE_NAME:test"
    echo "  $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION-test"
fi

echo ""
echo "Usage examples:"
echo "# Pull and run stdio (default):"
echo "docker run -it $REGISTRY/$NAMESPACE/$IMAGE_NAME:latest"
echo ""
echo "# Pull and run SSE server:"
echo "docker run -p 3001:3001 $REGISTRY/$NAMESPACE/$IMAGE_NAME:sse"
echo ""
if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN Complete - No actual publishing occurred"
else
    echo "Publication complete!"
fi
