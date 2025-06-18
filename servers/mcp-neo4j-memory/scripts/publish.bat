@echo off
setlocal enabledelayedexpansion

echo MCP Neo4j Memory - Docker Image Publisher
echo ========================================

REM Configuration
if "%DOCKER_REGISTRY%"=="" set DOCKER_REGISTRY=docker.io
if "%DOCKER_NAMESPACE%"=="" set DOCKER_NAMESPACE=lesykm
set IMAGE_NAME=mcp-neo4j-memory

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

echo Configuration:
echo Registry: %DOCKER_REGISTRY%
echo Namespace: %DOCKER_NAMESPACE%
echo Image: %IMAGE_NAME%
echo Version: %VERSION%
echo.

REM Check Docker
echo Checking Docker registry authentication...
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running
    exit /b 1
)

REM Parse arguments
if "%1"=="stdio" goto :stdio
if "%1"=="STDIO" goto :stdio
if "%1"=="sse" goto :sse
if "%1"=="SSE" goto :sse
if "%1"=="test" goto :test
if "%1"=="TEST" goto :test
if "%1"=="login" goto :login
if "%1"=="LOGIN" goto :login
if "%1"=="all" goto :all
if "%1"=="ALL" goto :all
if "%1"=="" goto :all

REM Default help
echo Usage: %0 [stdio^|sse^|test^|all^|login]
echo.
echo Commands:
echo   stdio  - Publish stdio variant (becomes latest)
echo   sse    - Publish SSE streaming variant
echo   test   - Publish test environment variant
echo   all    - Publish all variants (default)
echo   login  - Login to Docker registry
echo.
echo Environment Variables:
echo   DOCKER_REGISTRY  - Registry URL (default: docker.io)
echo   DOCKER_NAMESPACE - Namespace/username (default: your-username)
echo.
echo Examples:
echo   %0 login                              # Login first
echo   %0                                    # Publish all variants
echo   %0 stdio                             # Publish stdio only
echo   set DOCKER_NAMESPACE=myuser ^&^& %0   # Use custom namespace
goto :end

:login
echo Logging into Docker registry...
if "%DOCKER_REGISTRY%"=="docker.io" (
    docker login
) else (
    docker login "%DOCKER_REGISTRY%"
)
echo Login successful!
goto :end

:stdio
call :publish_variant "stdio" "mcp-neo4j-memory:stdio" "true"
goto :summary

:sse
call :publish_variant "sse" "mcp-neo4j-memory:sse" "false"
goto :summary

:test
call :publish_variant "test" "mcp-neo4j-memory:test" "false"
goto :summary

:all
echo Publishing all variants...
echo.

call :publish_variant "stdio" "mcp-neo4j-memory:stdio" "true"
call :publish_variant "sse" "mcp-neo4j-memory:sse" "false"
call :publish_variant "test" "mcp-neo4j-memory:test" "false"

echo All variants published successfully!
goto :summary

:publish_variant
set variant=%~1
set local_tag=%~2
set push_latest=%~3

echo Publishing %variant% variant...
echo ----------------------------------------

set remote_base=%DOCKER_REGISTRY%/%DOCKER_NAMESPACE%/%IMAGE_NAME%

REM Tag version-specific
echo Tagging: %local_tag% -^> %remote_base%:%VERSION%-%variant%
docker tag "%local_tag%" "%remote_base%:%VERSION%-%variant%"

REM Tag variant
echo Tagging: %local_tag% -^> %remote_base%:%variant%
docker tag "%local_tag%" "%remote_base%:%variant%"

REM Tag latest (only for stdio)
if "%push_latest%"=="true" (
    echo Tagging: %local_tag% -^> %remote_base%:%VERSION%
    docker tag "%local_tag%" "%remote_base%:%VERSION%"
    echo Tagging: %local_tag% -^> %remote_base%:latest
    docker tag "%local_tag%" "%remote_base%:latest"
)

REM Push all tags
echo Pushing %variant% images...
docker push "%remote_base%:%VERSION%-%variant%"
docker push "%remote_base%:%variant%"

if "%push_latest%"=="true" (
    docker push "%remote_base%:%VERSION%"
    docker push "%remote_base%:latest"
)

echo %variant% variant published successfully!
echo.
goto :eof

:summary
set remote_base=%DOCKER_REGISTRY%/%DOCKER_NAMESPACE%/%IMAGE_NAME%

echo.
echo Publication Summary
echo ==================
echo Registry: %DOCKER_REGISTRY%
echo Published tags:

if "%1"=="all" (
    echo   %remote_base%:latest
    echo   %remote_base%:%VERSION%
    echo   %remote_base%:stdio
    echo   %remote_base%:%VERSION%-stdio
    echo   %remote_base%:sse
    echo   %remote_base%:%VERSION%-sse
    echo   %remote_base%:test
    echo   %remote_base%:%VERSION%-test
) else if "%1"=="" (
    echo   %remote_base%:latest
    echo   %remote_base%:%VERSION%
    echo   %remote_base%:stdio
    echo   %remote_base%:%VERSION%-stdio
    echo   %remote_base%:sse
    echo   %remote_base%:%VERSION%-sse
    echo   %remote_base%:test
    echo   %remote_base%:%VERSION%-test
) else if "%1"=="stdio" (
    echo   %remote_base%:latest
    echo   %remote_base%:%VERSION%
    echo   %remote_base%:stdio
    echo   %remote_base%:%VERSION%-stdio
) else if "%1"=="sse" (
    echo   %remote_base%:sse
    echo   %remote_base%:%VERSION%-sse
) else if "%1"=="test" (
    echo   %remote_base%:test
    echo   %remote_base%:%VERSION%-test
)

echo.
echo Usage examples:
echo # Pull and run stdio (default):
echo docker run -it %remote_base%:latest
echo.
echo # Pull and run SSE server:
echo docker run -p 3001:3001 %remote_base%:sse
echo.
echo Publication complete!

:end
pause
