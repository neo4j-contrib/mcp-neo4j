## Next

### Fixed

### Changed

### Added

## v0.4.1

### Added
* Add env variable `NEO4J_READ_ONLY` and cli variable `--read-only` to configure tool availability

## v0.4.0

### Changed
* Change default transport to `stdio` in Dockerfile

### Added
* Added Cypher result sanitation function from Neo4j GraphRAG that removes embedding values from the result
* Add env variable `NEO4J_MCP_SERVER_ALLOW_ORIGINS` and cli variable `--allow-origins` to configure CORS Middleware for remote deployments
* Add env variable `NEO4J_MCP_SERVER_ALLOWED_HOSTS` and cli variable `--allowed-hosts` to configure Trusted Hosts Middleware for remote deployments
* Update HTTP and SSE transports to use security middleware
* Added `read_neo4j_cypher` query timeout configuration via `--read-timeout` CLI parameter and `NEO4J_READ_TIMEOUT` environment variable (defaults to 30 seconds)
* Add response token limit for read Cypher responses

## v0.3.1

### Changed
* Update Neo4j Driver syntax to use `driver.execute_query(...)`. This cleans the driver code.

### Added
* Add clear warnings for config declaration via cli and env variables

## v0.3.0

### Fixed
* Updated the `get_neo4j_schema` tool to include Relationship properties as well
* Fix bug where `params` arg wouldn't be parsed correctly

### Changed
* Update error handling in read and write tools
* Update `get_neo4j_schema` tool description
* Update `get_neo4j_schema` tool to catch missing apoc plugin error explicitly and provide guidance to client and user
* Update error handling for tools to explicitly catch and return Neo4j based errors with details

### Added
* Add .dxt file for Cypher MCP server
* Add .dxt file generation to Cypher MCP Publish GitHub action
* Add HTTP transport option
* Migrate to FastMCP v2.x
* Add tool annotations
* Update Dockerfile for http configuration

## v0.2.4

### Fixed
* Fixed Cypher MCP Docker deployments by allowing user to declare NEO4J_MCP_SERVER_HOST and NEO4J_MCP_SERVER_PORT. Can now declare NEO4J_MCP_SERVER_HOST=0.0.0.0 to use Docker hosted Cypher MCP server.

### Added
* NEO4J_MCP_SERVER_HOST and NEO4J_MCP_SERVER_PORT env variables
* --server-host and --server-port cli variables

## v0.2.3

### Added
* Namespace option via CLI or env variables. This allows many Cypher MCP servers to be used at once.
* Allow transport to be specified via env variables

## v0.2.2 

### Fixed

* IT no longer has risk of affecting locally deployed Neo4j instances
* Env config now supports NEO4J_URI and NEO4J_URL variables
* Fixed async issues with main server function not being async

### Changed

* IT now uses Testcontainers library instead of Docker scripts 
* Remove healthcheck from main function

### Added
* Support for transport config in cli args

## v0.2.1

### Fixed

* Fixed MCP version notation for declaration in config files - README

## v0.2.0

### Changed

* Refactor mcp-neo4j-cypher to use the FastMCP class
* Implement Neo4j async driver
* Tool responses now return JSON serialized results
* Update README with new config options 
* Update integration tests

### Added

* Add support for environment variables
* Add Github workflow to test and format mcp-neo4j-cypher


## v0.1.1

...
