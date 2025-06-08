@echo off
setlocal EnableDelayedExpansion

echo MCP Neo4j Memory - Docker Test Runner
echo ======================================

REM Color definitions (Windows 10+ with ANSI support)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Helper function to print colored output
:print_success
echo %GREEN%✅ %~1%NC%
goto :eof

:print_error
echo %RED%❌ %~1%NC%
goto :eof

:print_warning
echo %YELLOW%⚠️ %~1%NC%
goto :eof

:print_header
echo.
echo %BLUE%================================%NC%
echo %BLUE%%~1%NC%
echo %BLUE%================================%NC%
echo.
goto :eof

REM Function to run docker-compose tests
:run_tests
set service=%~1
set description=%~2
set compose_file=%~3
if "%compose_file%"=="" set compose_file=docker/docker-compose.test.yml

echo.
echo Running: %description%
echo Service: %service%
echo Compose File: %compose_file%
echo --------------------------------------

docker-compose -f "%compose_file%" run --rm "%service%"
if %ERRORLEVEL% == 0 (
    call :print_success "%description% completed successfully"
) else (
    call :print_error "%description% failed"
    exit /b 1
)
goto :eof

REM Function to run MCP compliance tests
:run_mcp_compliance
call :print_header "MCP Protocol Compliance Testing"

echo Starting test infrastructure...

REM Start required services
docker-compose -f docker/docker-compose.mcp-compliance.yml up -d neo4j-test mcp-sse-server

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 15 /nobreak > nul

REM Check service health
echo Checking service health...
for %%s in (neo4j-test mcp-sse-server) do (
    docker-compose -f docker/docker-compose.mcp-compliance.yml ps %%s | findstr /i "healthy Up" > nul
    if !ERRORLEVEL! == 0 (
        call :print_success "%%s is ready"
    ) else (
        call :print_warning "%%s may not be fully ready"
    )
)

echo.
echo Running comprehensive MCP compliance test suite...
echo --------------------------------------

REM Run the comprehensive test suite
docker-compose -f docker/docker-compose.mcp-compliance.yml run --rm mcp-compliance-suite
if %ERRORLEVEL% == 0 (
    call :print_success "MCP compliance tests passed!"

    echo.
    echo Running SSE protocol specific tests...
    docker-compose -f docker/docker-compose.mcp-compliance.yml run --rm sse-protocol-tests

    echo.
    echo Running live integration tests...
    docker-compose -f docker/docker-compose.mcp-compliance.yml run --rm live-integration-tests

    call :print_success "All MCP compliance tests completed successfully!"
) else (
    call :print_error "MCP compliance tests failed"
    echo.
    echo Showing service logs for debugging:
    docker-compose -f docker/docker-compose.mcp-compliance.yml logs mcp-sse-server
    docker-compose -f docker/docker-compose.mcp-compliance.yml down
    exit /b 1
)

REM Cleanup
docker-compose -f docker/docker-compose.mcp-compliance.yml down
goto :eof

REM Function to run live tests
:run_live_tests
call :print_header "Live Integration Testing"

echo Starting live test environment...

REM Start infrastructure but keep it running
docker-compose -f docker/docker-compose.mcp-compliance.yml up -d neo4j-test mcp-sse-server test-results-viewer

echo Waiting for services to be ready...
timeout /t 15 /nobreak > nul

REM Run live integration tests
docker-compose -f docker/docker-compose.mcp-compliance.yml run --rm live-integration-tests
if %ERRORLEVEL% == 0 (
    call :print_success "Live integration tests passed!"

    echo.
    echo 🌐 Test environment is running:
    echo   📊 SSE Server:      http://localhost:3001
    echo   📊 Neo4j Browser:   http://localhost:7474 (neo4j/testpassword)
    echo   📊 Test Results:    http://localhost:8080
    echo.
    echo Press Ctrl+C to stop all services...
    echo Opening test results in browser...

    REM Try to open browser
    start http://localhost:8080 2>nul

    echo Press any key to stop services...
    pause > nul

    echo Shutting down services...
    docker-compose -f docker/docker-compose.mcp-compliance.yml down
) else (
    call :print_error "Live integration tests failed"
    docker-compose -f docker/docker-compose.mcp-compliance.yml down
    exit /b 1
)
goto :eof

REM Main command processing
if "%1"=="build" goto :build
if "%1"=="BUILD" goto :build
if "%1"=="unit" goto :unit
if "%1"=="UNIT" goto :unit
if "%1"=="integration" goto :integration
if "%1"=="INTEGRATION" goto :integration
if "%1"=="mcp-compliance" goto :mcp_compliance
if "%1"=="MCP-COMPLIANCE" goto :mcp_compliance
if "%1"=="sse-compliance" goto :sse_compliance
if "%1"=="SSE-COMPLIANCE" goto :sse_compliance
if "%1"=="mcp-live" goto :mcp_live
if "%1"=="MCP-LIVE" goto :mcp_live
if "%1"=="live" goto :live
if "%1"=="LIVE" goto :live
if "%1"=="coverage" goto :coverage
if "%1"=="COVERAGE" goto :coverage
if "%1"=="performance" goto :performance
if "%1"=="PERFORMANCE" goto :performance
if "%1"=="clean" goto :clean
if "%1"=="CLEAN" goto :clean
if "%1"=="logs" goto :logs
if "%1"=="LOGS" goto :logs
if "%1"=="all" goto :all
if "%1"=="ALL" goto :all
if "%1"=="help" goto :help
if "%1"=="HELP" goto :help
if "%1"=="-h" goto :help
if "%1"=="--help" goto :help
if "%1"=="" goto :all

REM If no match, show error and help
call :print_error "Unknown command: %1"
echo.
echo Use '%0 help' to see available commands
goto :end_with_error

:build
call :print_header "Build"
echo Building test images
docker-compose -f docker/docker-compose.test.yml build
docker-compose -f docker/docker-compose.mcp-compliance.yml build
call :print_success "Build complete"
goto :end

:unit
call :print_header "Unit Tests"
echo Running unit tests only (no external dependencies)
call :run_tests "unit-tests" "Unit Tests"
goto :end

:integration
call :print_header "Integration Tests"
echo Running integration tests (requires Neo4j)
call :run_tests "integration-tests" "Integration Tests"
goto :end

:mcp_compliance
call :run_mcp_compliance
goto :end

:sse_compliance
call :print_header "SSE MCP Compliance Tests"
echo Running SSE MCP compliance tests
call :run_tests "sse-compliance-tests" "SSE MCP Compliance Tests"
goto :end

:mcp_live
call :print_header "MCP Live Server Tests"
echo Running MCP tests against live servers
call :run_tests "live-sse-tests" "Live SSE Integration Tests"
goto :end

:live
call :run_live_tests
goto :end

:coverage
call :print_header "Coverage Tests"
echo Running all tests with coverage reporting
call :run_tests "coverage-tests" "Coverage Tests"
goto :end

:performance
call :print_header "Performance Tests"
echo Running performance and load tests
call :run_tests "performance-tests" "Performance Tests"
goto :end

:clean
call :print_header "Cleanup"
echo Cleaning up test containers and volumes
docker-compose -f docker/docker-compose.test.yml down -v
docker-compose -f docker/docker-compose.mcp-compliance.yml down -v

REM Clean up test results
if exist "./test-results" (
    del /q /s "./test-results/*" 2>nul
    echo Cleaned test results directory
)

REM Clean up Docker system
echo Cleaning up Docker system...
docker system prune -f

call :print_success "Cleanup complete"
goto :end

:logs
echo Showing test logs
echo Which logs would you like to see?
echo 1. Test environment logs
echo 2. MCP compliance logs
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    docker-compose -f docker/docker-compose.test.yml logs
) else if "%choice%"=="2" (
    docker-compose -f docker/docker-compose.mcp-compliance.yml logs
) else (
    docker-compose -f docker/docker-compose.test.yml logs
)
goto :end

:all
call :print_header "Comprehensive Test Suite"
echo Running comprehensive test suite

echo 1. Unit Tests...
call :run_tests "unit-tests" "Unit Tests"
if %ERRORLEVEL% neq 0 goto :end_with_error

echo 2. Integration Tests...
call :run_tests "integration-tests" "Integration Tests"
if %ERRORLEVEL% neq 0 goto :end_with_error

echo 3. MCP Compliance Tests...
call :run_mcp_compliance
if %ERRORLEVEL% neq 0 goto :end_with_error

echo 4. Coverage Tests...
call :run_tests "coverage-tests" "Coverage Tests"
if %ERRORLEVEL% neq 0 goto :end_with_error

call :print_success "All test suites completed successfully!"
goto :end

:help
echo Usage: %0 [COMMAND]
echo.
echo Test Commands:
echo   unit                - Run unit tests only (fast, no dependencies)
echo   integration         - Run integration tests (requires Neo4j)
echo   mcp-compliance      - Run comprehensive MCP protocol compliance tests
echo   sse-compliance      - Run SSE MCP compliance tests specifically
echo   mcp-live           - Run MCP tests against live servers
echo   live               - Start live test environment with running servers
echo   coverage           - Run all tests with coverage reporting
echo   performance        - Run performance and load tests
echo   all                - Run comprehensive test suite (default)
echo.
echo Utility Commands:
echo   build              - Build test images
echo   clean              - Clean up containers, volumes, and test results
echo   logs               - Show container logs
echo   help               - Show this help message
echo.
echo Examples:
echo   %0                     # Run all tests
echo   %0 unit               # Quick unit tests only
echo   %0 mcp-compliance     # Full MCP compliance validation
echo   %0 live               # Interactive testing with running servers
echo   %0 coverage           # Generate detailed coverage reports
echo   %0 clean              # Clean up everything
echo.
echo Test Results:
echo   📁 Test outputs:     ./test-results/
echo   📊 Coverage reports: ./test-results/htmlcov/index.html
echo   🌐 Live servers:     http://localhost:3001 (SSE), http://localhost:7474 (Neo4j)
echo.
echo MCP Compliance Features:
echo   ✅ JSON-RPC 2.0 protocol validation
echo   ✅ SSE transport compliance testing
echo   ✅ Session management verification
echo   ✅ Tool execution validation
echo   ✅ Error handling compliance
echo   ✅ Live server integration testing
goto :end

:end_with_error
echo.
call :print_error "Test execution failed!"
echo.
echo 💡 Tips:
echo   📁 Test results are saved in ./test-results/
echo   📊 Use '%0 coverage' for detailed coverage reports
echo   🧹 Use '%0 clean' to clean up containers and results
echo   📋 Use '%0 logs' to view container logs
echo   🌐 Use '%0 live' for interactive testing with running servers
echo   ✅ Use '%0 mcp-compliance' for full MCP protocol validation
pause
exit /b 1

:end
echo.
call :print_success "Test execution completed successfully!"
echo.
echo 💡 Tips:
echo   📁 Test results are saved in ./test-results/
echo   📊 Use '%0 coverage' for detailed coverage reports
echo   🧹 Use '%0 clean' to clean up containers and results
echo   📋 Use '%0 logs' to view container logs
echo   🌐 Use '%0 live' for interactive testing with running servers
echo   ✅ Use '%0 mcp-compliance' for full MCP protocol validation
pause
