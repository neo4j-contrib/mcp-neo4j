## Next

### Fixed

### Changed
* Security upgrade python from 3.11-slim to 3.13.8-slim
* Lock FastMCP version to <3.x

### Added

## v0.4.7

### Fixed
* Removed `dependencies=...` from server constructor. This was removed from FastMCP.

## v0.4.6

### Fixed
* Fix bug in Dockerfile where build would fail due to `LABEL` statement coming before `FROM` statement

### Added
* Add `NEO4J_MCP_SERVER_STATELESS` environment variable and `--stateless` cli flag to configure stateless http deployment options when using http or sse transport

## v0.4.5

### Fixed
* Fix server name in MCP Registry config
* Update Github action to deploy to MCP Registry

## v0.4.4

### Added
* Add config and Github workflow to add server to Github MCP Registry

## v0.4.3

### Added
* Add namespacing support for multi-tenant deployments with `--namespace` CLI argument and `NEO4J_NAMESPACE` environment variable

## v0.4.2

### Fixed
* fix bug where config logging wasn't being used

### Changed
* Use `stateless_http=False` when using `http` or `sse` transport to be consistent with previous configuration

## v0.4.1

### Fixed
* f-string bug in utils.py patched for earlier Python versions

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