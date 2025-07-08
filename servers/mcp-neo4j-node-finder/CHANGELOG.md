## Next

### Fixed

### Changed

### Added


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
