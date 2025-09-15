## Next

### Fixed

### Changed

### Added

## v0.4.0

### Changed
* Change default transport in Dockerfile to `stdio`
* Split client, service and MCP classes into separate files
* Create centralized logger config in `utils.py`

### Added
* Add tool annotations to tools to better describe their effects
* Add security middleware (CORS and TrustedHost protection) for HTTP transport
* Add `--allow-origins` and `--allowed-hosts` command line arguments
* Add security environment variables: `NEO4J_MCP_SERVER_ALLOW_ORIGINS` and `NEO4J_MCP_SERVER_ALLOWED_HOSTS`
* Update config parsing functions 
* Add clear logging for config declaration via cli and env variables

## v0.3.0

### Changed
* Migrate to FastMCP v2.x

### Added
* Add HTTP transport option

## v0.2.2
...