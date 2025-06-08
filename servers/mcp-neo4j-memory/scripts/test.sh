#!/bin/bash
set -e

echo "MCP Neo4j Memory - Docker Test Runner"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to run docker-compose with proper context
run_tests() {
    local service=$1
    local description=$2
    local compose_file=${3:-"docker/docker-compose.test.yml"}

    echo ""
    echo "Running: $description"
    echo "Service: $service"
    echo "Compose File: $compose_file"
    echo "--------------------------------------"

    # Set up cleanup trap
    trap 'echo "Cleaning up test containers..."; docker-compose -f "$compose_file" down; exit 1' INT ERR

    if docker-compose -f "$compose_file" run --rm "$service"; then
        print_success "$description completed successfully"
        # Cleanup on success
        docker-compose -f "$compose_file" down
        trap - INT ERR
        return 0
    else
        print_error "$description failed"
        # Cleanup on failure
        docker-compose -f "$compose_file" down
        trap - INT ERR
        return 1
    fi
}

# Function to run MCP compliance tests with full infrastructure
run_mcp_compliance() {
    print_header "MCP Protocol Compliance Testing"
    
    echo "Starting test infrastructure..."
    
    # Start required services
    docker-compose -f docker/docker-compose.mcp-compliance.yml up -d neo4j-test mcp-sse-server
    
    # Wait for services to be ready
    echo "Waiting for services to be ready..."
    sleep 15
    
    # Check service health
    echo "Checking service health..."
    for service in neo4j-test mcp-sse-server; do
        if docker-compose -f docker/docker-compose.mcp-compliance.yml ps "$service" | grep -q "healthy\|Up"; then
            print_success "$service is ready"
        else
            print_warning "$service may not be fully ready"
        fi
    done
    
    echo ""
    echo "Running comprehensive MCP compliance test suite..."
    echo "--------------------------------------"
    
    # Run the comprehensive test suite
    if docker-compose -f docker/docker-compose.mcp-compliance.yml run --rm mcp-compliance-suite; then
        print_success "MCP compliance tests passed!"
        
        # Also run specific SSE protocol tests
        echo ""
        echo "Running SSE protocol specific tests..."
        docker-compose -f docker/docker-compose.mcp-compliance.yml run --rm sse-protocol-tests
        
        echo ""
        echo "Running live integration tests..."
        docker-compose -f docker/docker-compose.mcp-compliance.yml run --rm live-integration-tests
        
        print_success "All MCP compliance tests completed successfully!"
        
    else
        print_error "MCP compliance tests failed"
        echo ""
        echo "Showing service logs for debugging:"
        docker-compose -f docker/docker-compose.mcp-compliance.yml logs mcp-sse-server
        return 1
    fi
    
    # Cleanup
    docker-compose -f docker/docker-compose.mcp-compliance.yml down
}

# Function to run live tests with servers running
run_live_tests() {
    print_header "Live Integration Testing"
    
    echo "Starting live test environment..."
    
    # Start infrastructure but keep it running
    docker-compose -f docker/docker-compose.mcp-compliance.yml up -d neo4j-test mcp-sse-server test-results-viewer
    
    echo "Waiting for services to be ready..."
    sleep 15
    
    # Run live integration tests
    if docker-compose -f docker/docker-compose.mcp-compliance.yml run --rm live-integration-tests; then
        print_success "Live integration tests passed!"
        
        echo ""
        echo "🌐 Test environment is running:"
        echo "  📊 SSE Server:      http://localhost:3001"
        echo "  📊 Neo4j Browser:   http://localhost:7474 (neo4j/testpassword)"
        echo "  📊 Test Results:    http://localhost:8080"
        echo ""
        echo "Press Ctrl+C to stop all services..."
        
        # Keep services running for manual testing
        trap 'echo ""; echo "Shutting down services..."; docker-compose -f docker/docker-compose.mcp-compliance.yml down; exit 0' INT
        
        # Wait for user to stop
        docker-compose -f docker/docker-compose.mcp-compliance.yml logs -f test-results-viewer
        
    else
        print_error "Live integration tests failed"
        docker-compose -f docker/docker-compose.mcp-compliance.yml down
        return 1
    fi
}

# Parse command line arguments
case "$1" in
    "unit")
        print_header "Unit Tests"
        echo "Running unit tests only (no external dependencies)"
        run_tests "unit-tests" "Unit Tests"
        ;;
    "integration")
        print_header "Integration Tests"
        echo "Running integration tests (requires Neo4j)"
        run_tests "integration-tests" "Integration Tests"
        ;;
    "mcp-compliance")
        run_mcp_compliance
        ;;
    "sse-compliance")
        print_header "SSE MCP Compliance Tests"
        echo "Running SSE MCP compliance tests"
        run_tests "sse-compliance-tests" "SSE MCP Compliance Tests"
        ;;
    "mcp-live")
        print_header "MCP Live Server Tests"
        echo "Running MCP tests against live servers"
        run_tests "live-sse-tests" "Live SSE Integration Tests"
        ;;
    "live")
        run_live_tests
        ;;
    "coverage")
        print_header "Coverage Tests"
        echo "Running all tests with coverage reporting"
        run_tests "coverage-tests" "Coverage Tests"
        ;;
    "performance")
        print_header "Performance Tests"
        echo "Running performance and load tests"
        run_tests "performance-tests" "Performance Tests"
        ;;
    "all"|"")
        print_header "Comprehensive Test Suite"
        echo "Running comprehensive test suite"
        
        echo "1. Unit Tests..."
        run_tests "unit-tests" "Unit Tests" || exit 1
        
        echo "2. Integration Tests..."
        run_tests "integration-tests" "Integration Tests" || exit 1
        
        echo "3. MCP Compliance Tests..."
        run_mcp_compliance || exit 1
        
        echo "4. Coverage Tests..."
        run_tests "coverage-tests" "Coverage Tests" || exit 1
        
        print_success "All test suites completed successfully!"
        ;;
    "clean")
        print_header "Cleanup"
        echo "Cleaning up test containers and volumes"
        docker-compose -f docker/docker-compose.test.yml down -v
        docker-compose -f docker/docker-compose.mcp-compliance.yml down -v
        
        # Clean up test results
        if [ -d "./test-results" ]; then
            rm -rf ./test-results/*
            echo "Cleaned test results directory"
        fi
        
        # Clean up test images (optional)
        echo "Cleaning up Docker system..."
        docker system prune -f
        
        print_success "Cleanup complete"
        ;;
    "build")
        print_header "Build"
        echo "Building test images"
        docker-compose -f docker/docker-compose.test.yml build
        docker-compose -f docker/docker-compose.mcp-compliance.yml build
        print_success "Build complete"
        ;;
    "logs")
        echo "Showing test logs"
        echo "Which logs would you like to see?"
        echo "1. Test environment logs"
        echo "2. MCP compliance logs"
        read -p "Enter choice (1 or 2): " choice
        
        case $choice in
            1)
                docker-compose -f docker/docker-compose.test.yml logs
                ;;
            2)
                docker-compose -f docker/docker-compose.mcp-compliance.yml logs
                ;;
            *)
                docker-compose -f docker/docker-compose.test.yml logs
                ;;
        esac
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Test Commands:"
        echo "  unit                - Run unit tests only (fast, no dependencies)"
        echo "  integration         - Run integration tests (requires Neo4j)"
        echo "  mcp-compliance      - Run comprehensive MCP protocol compliance tests"
        echo "  sse-compliance      - Run SSE MCP compliance tests specifically"
        echo "  mcp-live           - Run MCP tests against live servers"
        echo "  live               - Start live test environment with running servers"
        echo "  coverage           - Run all tests with coverage reporting"
        echo "  performance        - Run performance and load tests"
        echo "  all                - Run comprehensive test suite (default)"
        echo ""
        echo "Utility Commands:"
        echo "  build              - Build test images"
        echo "  clean              - Clean up containers, volumes, and test results"
        echo "  logs               - Show container logs"
        echo "  help               - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                     # Run all tests"
        echo "  $0 unit               # Quick unit tests only"
        echo "  $0 mcp-compliance     # Full MCP compliance validation"
        echo "  $0 live               # Interactive testing with running servers"
        echo "  $0 coverage           # Generate detailed coverage reports"
        echo "  $0 clean              # Clean up everything"
        echo ""
        echo "Test Results:"
        echo "  📁 Test outputs:     ./test-results/"
        echo "  📊 Coverage reports: ./test-results/htmlcov/index.html"
        echo "  🌐 Live servers:     http://localhost:3001 (SSE), http://localhost:7474 (Neo4j)"
        echo ""
        echo "MCP Compliance Features:"
        echo "  ✅ JSON-RPC 2.0 protocol validation"
        echo "  ✅ SSE transport compliance testing"
        echo "  ✅ Session management verification"
        echo "  ✅ Tool execution validation"
        echo "  ✅ Error handling compliance"
        echo "  ✅ Live server integration testing"
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        echo "Use '$0 help' to see available commands"
        exit 1
        ;;
esac

echo ""
if [ $? -eq 0 ]; then
    print_success "Test execution completed successfully!"
else
    print_error "Test execution failed!"
fi

echo ""
echo "💡 Tips:"
echo "  📁 Test results are saved in ./test-results/"
echo "  📊 Use '$0 coverage' for detailed coverage reports"
echo "  🧹 Use '$0 clean' to clean up containers and results"
echo "  📋 Use '$0 logs' to view container logs"
echo "  🌐 Use '$0 live' for interactive testing with running servers"
echo "  ✅ Use '$0 mcp-compliance' for full MCP protocol validation"
