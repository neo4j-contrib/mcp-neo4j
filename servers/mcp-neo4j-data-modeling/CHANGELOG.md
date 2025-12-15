## Next

### Fixed

### Changed

### Added

## v0.8.0

### Fixed
* Remove `stateless_http` flag on MCP server constructor and move to the appropriate `run_...` function for http and sse transport. The constructor flag is deprecated by FastMCP.
* Removed `dependencies=...` from server constructor. This was removed from FastMCP.

### Changed
* Make node corners rounded for Mermaid visualization

### Added
* Add methods to export schema as string representations of Pydantic models for `Node`, `Relationship` and `DataModel`
* Add tool that exports data model as a string representation of a Python file containing imports and Pydantic models
* Add methods to import and export as Neo4j GraphRAG Python Package schema JSON for `Node`, `Relationship` and `DataModel`
* Add tools that import and export data model as Neo4j GraphRAG Python Package schema JSON
* Add `description` field to `Node` and `Relationship` classes
* Add docstring to generated Pydantic nodes and relationships based on `description` field

## v0.7.0

### Fixed
* Fix bug in Dockerfile where build would fail due to `LABEL` statement coming before `FROM` statement

### Changed
* Tools that received Pydantic objects as arguments now also accept JSON strings as input. This is for client applications that send JSON strings instead of objects for tool arguments. This is a workaround for client applications that don't adhere to the defined tool schemas and will be removed in the future once it is not needed.

### Added
* Added JSON string parsing utils function. This is for client applications that send JSON strings instead of objects for tool arguments. This is a workaround for client applications that don't adhere to the defined tool schemas and will be removed in the future once it is not needed.

## v0.6.1

### Added
* Add config and Github workflow to add server to Github MCP Registry

## v0.6.0

### Added
* Add import and export methods to `DataModel` for turtle OWL strings
* Add MCP tools for loading and exporting turtle OWL files

## v0.5.1

### Added
* Add namespacing support for multi-tenant deployments with `--namespace` CLI argument and `NEO4J_NAMESPACE` environment variable

## v0.5.0

### Fixed
* Fix bug where MCP server could only be deployed with stdio transport

### Changed
* Update README with link to data modeling demo repo and workflow image
* Update Dockerfile for Docker Hub deployment
* Change default transport to `stdio` in Dockerfile

### Added
* Add security middleware (CORS and TrustedHost) for HTTP and SSE transports
* Add CLI  support for `--allow-origins` and `--allowed-hosts` configuration
* Add environment variable for `NEO4J_MCP_SERVER_ALLOW_ORIGINS` and `NEO4J_MCP_SERVER_ALLOWED_HOSTS` configuration
* Add detailed logging for configuration parameter parsing

## v0.4.0

### Added
* Add `create_new_data_model` prompt that provides a structured prompt for generating a graph data model

## v0.3.0

### Fixed
* Remove back slashes from f-string in Mermaid config generation

### Added
* Update PR workflow to iterate over Python 3.10 to 3.13
* Add example data model resources 
* Add tools to list and retrieve example data models and their Mermaid configurations

## v0.2.0

### Added
* Add HTTP transport option
* Migrate to FastMCP v2.x

## v0.1.1

### Fixed
* Shorten tool names to comply with Cursor name length restrictions

### Changed
* Removed NVL visualization due to compatibility issues

### Added
* Code generation tools for ingestion queries
* Resource that explains the recommended process of ingesting data into Neo4j
* Mermaid visualization configuration generation

## v0.1.0

* Basic functionality 
  * Expose schemas for Data Model, Node, Relationship and Property
  * Validation tools
* Visualize data model in interactive browser window   
* Import / Export from Arrows web application