## Next

### Fixed

### Changed

### Added

## v0.4.1

### Changed
* Updated tool docstrings to better describe their function, inputs and outputs

### Added
* Add namespacing support for multi-tenant deployments with `--namespace` CLI argument and `NEO4J_NAMESPACE` environment variable

## v0.4.0

### Changed
* Change default transport to `stdio` in Dockerfile

### Added
* Add env variable `NEO4J_MCP_SERVER_ALLOW_ORIGINS` and cli variable `--allow-origins` to configure CORS Middleware for remote deployments
* Add env variable `NEO4J_MCP_SERVER_ALLOWED_HOSTS` and cli variable `--allowed-hosts` to configure Trusted Hosts Middleware for remote deployments
* Update HTTP and SSE transports to use security middleware
* Add comprehensive HTTP transport integration tests with security middleware testing

## v0.3.0

### Changed
* Update tool return type hints for structured output
* Move `Neo4jMemory` class and related classes to separate file
* Change tool responses to return the `ToolResponse` object
* Updated tool argument types with Pydantic models

### Added
* Add structured output to tool responses
* Add error handling to catch Neo4j specific errors and improve error responses
* Implement `ToolError` class from FastMCP
* Add tool annotations
* Add clear warnings for config declaration via cli and env variables

## v0.2.0

### Fixed
* Fix bug in `search_nodes` method where query arg wasn't passed properly
* Fix bug where stdio transport was always selected
* Fixed argument parsing in server init

### Changed
* Implement FastMCP with function decorators to simplify server code
* Add HTTP transport option
* Migrate to FastMCP v2.x
* rename tools to be more clear - `search_nodes` into `search_memories` and `find_nodes` into `find_memories_by_name`
* Update underlying Pydantic class `ObservationAddition` to have `observations` field to be consistent with `ObservationDeletion` class
* Update Dockerfile to include `NEO4J_DATABASE`, `NEO4J_TRANSPORT`, `NEO4J_MCP_SERVER_HOST`, `NEO4J_MCP_SERVER_PORT` and `NEO4J_MCP_SERVER_PATH` env variables

### Added
* Add compatibility for NEO4J_URI and NEO4J_URL env variables
* Command in Makefile to easily build and deploy Docker image locally

## v0.1.5

### Fixed
* Remove use of dynamic node labels and relationship types to be compatible with Neo4j versions < 5.26

## v0.1.4

* Create, Read, Update and Delete semantic memories