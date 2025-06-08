# MCP Neo4j Memory Project Refactoring Plan

## Overview

This document outlines the refactoring plan to reorganize the MCP Neo4j Memory project from its current messy structure into a clean, modular architecture using **Option 1: Separate Modules Within Same Project**.

## Current State Analysis

### Current File Structure:
```
src/mcp_neo4j_memory/
├── __init__.py           # Entry point with mode routing
├── __main__.py           # Module execution entry
├── server.py             # Original stdio MCP server with Neo4j logic
├── multi_server.py       # Multi-protocol server (stdio + HTTP + SSE)
├── http_server.py        # Incomplete HTTP server (should be deleted)
└── __pycache__/
```

### Current Problems:
1. **Code Duplication**: Tool definitions duplicated between `server.py` and `multi_server.py`
2. **Mixed Concerns**: Business logic mixed with protocol implementation
3. **Messy Structure**: No clear separation between core logic and transport protocols
4. **File Confusion**: `http_server.py` is incomplete, `multi_server.py` does everything
5. **Docker Files**: Docker configuration files scattered in root directory

## Target Structure (Option 1)

### New File Structure:
```
mcp-neo4j-memory/
├── src/mcp_neo4j_memory/
│   ├── __init__.py           # Main entry point & CLI routing
│   ├── __main__.py           # Module execution (unchanged)
│   ├── core/                 # Core business logic (extracted)
│   │   ├── __init__.py
│   │   ├── memory.py         # Neo4jMemory class (from server.py)
│   │   ├── models.py         # Data models (Entity, Relation, etc.)
│   │   └── tools.py          # MCP tool definitions (shared)
│   ├── protocols/            # Protocol implementations
│   │   ├── __init__.py
│   │   ├── stdio_server.py   # Clean stdio implementation
│   │   ├── http_server.py    # HTTP/REST endpoints
│   │   └── sse_server.py     # SSE streaming server
│   └── cli.py               # Command-line interface logic
├── docker/                  # Docker-related files (moved)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── examples/                # Configuration examples (new)
│   ├── librechat-stdio.yaml
│   ├── librechat-sse.yaml
│   └── claude-desktop.json
└── [existing files: README.md, pyproject.toml, etc.]
```

## Refactoring Steps

### Phase 1: Create New Directory Structure
1. Create `src/mcp_neo4j_memory/core/` directory
2. Create `src/mcp_neo4j_memory/protocols/` directory  
3. Create `docker/` directory in project root
4. Create `examples/` directory in project root

### Phase 2: Extract Core Business Logic

#### Step 2.1: Create `core/models.py`
Extract data models from `server.py`:
- `Entity` class
- `Relation` class  
- `KnowledgeGraph` class
- `ObservationAddition` class
- `ObservationDeletion` class

#### Step 2.2: Create `core/memory.py`
Extract `Neo4jMemory` class from `server.py`:
- All Neo4j database operations
- Graph manipulation methods
- Connection management
- Remove MCP-specific code (tool handlers)

#### Step 2.3: Create `core/tools.py`
Extract MCP tool definitions (shared between protocols):
- `get_mcp_tools()` function returning list of `types.Tool`
- Tool execution logic that calls `core/memory.py` methods
- Input validation and error handling

#### Step 2.4: Create `core/__init__.py`
Expose core components:
```python
from .memory import Neo4jMemory
from .models import Entity, Relation, KnowledgeGraph, ObservationAddition, ObservationDeletion
from .tools import get_mcp_tools, execute_tool

__all__ = ["Neo4jMemory", "Entity", "Relation", "KnowledgeGraph", 
           "ObservationAddition", "ObservationDeletion", "get_mcp_tools", "execute_tool"]
```

### Phase 3: Create Protocol Implementations

#### Step 3.1: Create `protocols/stdio_server.py`
Clean stdio implementation:
- Import from `core/` modules
- MCP server setup for stdio protocol
- Use shared tools from `core/tools.py`
- Remove duplicated business logic

#### Step 3.2: Create `protocols/http_server.py`  
Clean HTTP implementation:
- FastAPI setup with REST endpoints
- Use shared tools from `core/tools.py`
- Proper error handling and response formatting
- No SSE functionality (separate concern)

#### Step 3.3: Create `protocols/sse_server.py`
SSE-specific implementation:
- Server-Sent Events streaming
- LibreChat integration features
- Heartbeat and connection management
- Use shared core logic

#### Step 3.4: Create `protocols/__init__.py`
Expose protocol servers:
```python
from .stdio_server import run_stdio_server
from .http_server import run_http_server  
from .sse_server import run_sse_server

__all__ = ["run_stdio_server", "run_http_server", "run_sse_server"]
```

### Phase 4: Update Entry Points

#### Step 4.1: Create `cli.py`
Extract command-line interface logic from `__init__.py`:
- Argument parsing
- Environment variable handling
- Mode routing logic
- Configuration validation

#### Step 4.2: Update `__init__.py`
Simplify main entry point:
```python
from .cli import main
from . import core, protocols

__all__ = ["main", "core", "protocols"]
```

### Phase 5: Move Configuration Files

#### Step 5.1: Move Docker files to `docker/`
- `Dockerfile` → `docker/Dockerfile`
- `docker-compose.yml` → `docker/docker-compose.yml`
- `docker-compose.prod.yml` → `docker/docker-compose.prod.yml`
- Update paths in compose files accordingly

#### Step 5.2: Create example configurations in `examples/`
- `librechat-stdio.yaml` - LibreChat stdio configuration
- `librechat-sse.yaml` - LibreChat SSE configuration  
- `claude-desktop.json` - Claude Desktop configuration example

### Phase 6: Clean Up and Remove

#### Step 6.1: Delete obsolete files
- Delete `http_server.py` (incomplete implementation)
- Delete original `server.py` (logic moved to core/)
- Delete original `multi_server.py` (split into protocols/)

#### Step 6.2: Update imports throughout project
- Fix all import statements to use new module structure
- Update tests to import from new locations
- Update documentation references

### Phase 7: Update Configuration and Documentation

#### Step 7.1: Update build scripts
- Update `build.sh` and `run.sh` to use `docker/` directory
- Update Docker build context paths

#### Step 7.2: Update documentation
- Update README.md with new structure
- Update usage examples
- Document the modular architecture benefits

## Key Benefits After Refactoring

### 1. **No Code Duplication**
- Tool definitions in one place (`core/tools.py`)
- Business logic in one place (`core/memory.py`)
- Each protocol focuses only on transport concerns

### 2. **Clear Separation of Concerns**
- **Core**: Business logic, data models, Neo4j operations
- **Protocols**: Transport/communication protocols (stdio, HTTP, SSE)
- **CLI**: Command-line interface and configuration

### 3. **Easier Testing**
- Test core business logic independently
- Test each protocol implementation separately
- Mock interfaces between modules

### 4. **Better Maintainability**
- Changes to Neo4j logic only affect `core/` modules
- Adding new protocols doesn't require touching core logic
- Clear module boundaries and responsibilities

### 5. **Improved Documentation**
- Each module has a clear, single purpose
- Examples directory provides clear usage patterns
- Docker files organized and easy to find

## Migration Notes for Users

### Backward Compatibility
- Entry point remains the same: `mcp-neo4j-memory`
- Command-line arguments unchanged
- Docker image interface unchanged
- Configuration file formats unchanged

### For Developers
- Import paths change: `from mcp_neo4j_memory.core import Neo4jMemory`
- Clear module structure for extending functionality
- Easier to contribute protocol-specific improvements

## Implementation Priority

1. **High Priority**: Core logic extraction (Phase 2) - removes code duplication
2. **Medium Priority**: Protocol separation (Phase 3) - improves maintainability  
3. **Low Priority**: File organization (Phase 5) - improves project navigation

## Success Criteria

✅ **No code duplication** between protocol implementations  
✅ **Clear module boundaries** - core vs protocols vs CLI  
✅ **All existing functionality works** after refactoring  
✅ **Easier to add new protocols** without touching core logic  
✅ **Better test coverage** possible with modular structure  
✅ **Cleaner project structure** - easy to navigate and understand

---

## Notes for Future Claude Sessions

When continuing this refactoring:

1. **Current state**: Project has stdio MCP working + HTTP/SSE added but structure is messy
2. **Goal**: Reorganize into clean modular structure without breaking functionality
3. **Key files to refactor**: `server.py`, `multi_server.py` (delete `http_server.py`)
4. **Don't change**: Entry point behavior, CLI arguments, Docker interface
5. **Priority**: Extract shared core logic first to eliminate code duplication

This refactoring will make the project much more maintainable and professional without breaking existing functionality.