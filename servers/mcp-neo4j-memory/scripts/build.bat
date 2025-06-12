@echo off
setlocal enabledelayedexpansion

echo Building All MCP Neo4j Memory Docker Images
echo ==============================================

REM Extract version from pyproject.toml
set VERSION=
for /f "tokens=2 delims==" %%i in ('findstr /r "^version.*=" pyproject.toml') do (
    set VERSION=%%i
    goto :version_found
)
:version_found

REM Clean up the version (remove quotes and ALL spaces)
set VERSION=%VERSION:"=%
if defined VERSION (
    REM Remove leading and trailing spaces
    for /f "tokens=* delims= " %%j in ("%VERSION%") do set VERSION=%%j
    REM Remove quotes
    set VERSION=%VERSION:"=%
    REM Remove any remaining spaces
    set VERSION=%VERSION: =%
)

REM Fallback if extraction failed
if "%VERSION%"=="" set VERSION=0.1.4

if "%VERSION%"=="" (
    echo Could not extract version from pyproject.toml
    exit /b 1
)

echo Version detected: %VERSION%

REM Function to build and tag an image (simulated with goto)
if "%1"=="stdio" goto :stdio
if "%1"=="STDIO" goto :stdio
if "%1"=="sse" goto :sse
if "%1"=="SSE" goto :sse
if "%1"=="test" goto :test
if "%1"=="TEST" goto :test
if "%1"=="all" goto :all
if "%1"=="ALL" goto :all
if "%1"=="" goto :all

REM Default help
echo Usage: %0 [stdio^|sse^|test^|all]
echo.
echo Commands:
echo   stdio  - Build stdio-only optimized image
echo   sse    - Build Server-Sent Events server image
echo   test   - Build test environment image
echo   all    - Build all variants (default)
echo.
echo Examples:
echo   %0           # Build all variants
echo   %0 stdio     # Build stdio-only (becomes latest)
echo   %0 sse       # Build SSE streaming server
goto :end

:stdio
echo.
echo Building stdio-only server...
echo Dockerfile: docker/Dockerfile
echo Target: stdio
echo Protocol: stdio
echo ----------------------------------------
docker build --target stdio -t mcp-neo4j-memory:latest -f docker/Dockerfile .
docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:stdio
docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:%VERSION%
docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:%VERSION%-stdio
echo stdio-only server build complete!
goto :summary

:sse
echo.
echo Building Server-Sent Events server...
echo Dockerfile: docker/Dockerfile
echo Target: sse
echo Protocol: sse
echo ----------------------------------------
docker build --target sse -t mcp-neo4j-memory:sse -f docker/Dockerfile .
docker tag mcp-neo4j-memory:sse mcp-neo4j-memory:%VERSION%-sse
echo Server-Sent Events server build complete!
goto :summary

:test
echo.
echo Building Test environment...
echo Dockerfile: docker/Dockerfile
echo Target: test
echo Protocol: test
echo ----------------------------------------
docker build --target test -t mcp-neo4j-memory:test -f docker/Dockerfile .
docker tag mcp-neo4j-memory:test mcp-neo4j-memory:%VERSION%-test
echo Test environment build complete!
goto :summary

:all
echo Building using master Dockerfile with all variants...

REM Build stdio (default)
echo.
echo Building stdio (default)...
docker build --target stdio -t mcp-neo4j-memory:latest -f docker/Dockerfile .
docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:stdio
docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:%VERSION%
docker tag mcp-neo4j-memory:latest mcp-neo4j-memory:%VERSION%-stdio

REM Build SSE
echo.
echo Building SSE...
docker build --target sse -t mcp-neo4j-memory:sse -f docker/Dockerfile .
docker tag mcp-neo4j-memory:sse mcp-neo4j-memory:%VERSION%-sse

REM Build test
echo.
echo Building test...
docker build --target test -t mcp-neo4j-memory:test -f docker/Dockerfile .
docker tag mcp-neo4j-memory:test mcp-neo4j-memory:%VERSION%-test

echo All variants built!
goto :summary

:summary
echo.
echo Build Summary
echo =============
echo Available images:
docker images | findstr mcp-neo4j-memory | sort

echo.
echo Image Tags Guide:
echo mcp-neo4j-memory:latest      - stdio-only server (default)
echo mcp-neo4j-memory:stdio       - stdio-only server
echo mcp-neo4j-memory:sse         - Server-Sent Events server
echo mcp-neo4j-memory:test        - Test environment
echo.
echo Versioned Tags:
echo mcp-neo4j-memory:%VERSION%        - Latest stdio version
echo mcp-neo4j-memory:%VERSION%-stdio
echo mcp-neo4j-memory:%VERSION%-sse
echo mcp-neo4j-memory:%VERSION%-test
echo.

:end
echo.
echo Build complete!
pause
