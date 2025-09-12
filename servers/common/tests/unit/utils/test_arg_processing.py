import argparse
import os
from unittest.mock import patch

import pytest

from common.utils.arg_processing import (
    process_allow_origins,
    process_allowed_hosts,
    process_database,
    process_db_url,
    process_namespace,
    process_password,
    process_read_timeout,
    process_server_host,
    process_server_path,
    process_server_port,
    process_token_limit,
    process_transport,
    process_username,
)


@pytest.fixture
def clean_env():
    """Fixture to clean environment variables before each test."""
    env_vars = [
        "NEO4J_URL",
        "NEO4J_URI",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
        "NEO4J_DATABASE",
        "NEO4J_TRANSPORT",
        "NEO4J_MCP_SERVER_HOST",
        "NEO4J_MCP_SERVER_PORT",
        "NEO4J_MCP_SERVER_PATH",
        "NEO4J_MCP_SERVER_ALLOW_ORIGINS",
        "NEO4J_MCP_SERVER_ALLOWED_HOSTS",
        "NEO4J_NAMESPACE",
        "NEO4J_READ_TIMEOUT",
        "NEO4J_RESPONSE_TOKEN_LIMIT",
    ]
    # Store original values
    original_values = {}
    for var in env_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        os.environ[var] = value


@pytest.fixture
def args_factory():
    """Factory fixture to create argparse.Namespace objects with default None values."""

    def _create_args(**kwargs):
        defaults = {
            "db_url": None,
            "username": None,
            "password": None,
            "database": None,
            "namespace": None,
            "transport": None,
            "server_host": None,
            "server_port": None,
            "server_path": None,
            "allow_origins": None,
            "allowed_hosts": None,
            "read_timeout": None,
            "token_limit": None,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    return _create_args


@pytest.fixture
def mock_logger():
    """Fixture to provide a mocked logger."""
    with patch("common.utils.arg_processing.logger") as mock:
        yield mock


# Individual function tests


class TestProcessDbUrl:
    """Test cases for process_db_url function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        args = args_factory(db_url="bolt://test:7687")
        result = process_db_url(args)
        assert result == "bolt://test:7687"

    def test_neo4j_url_env_var(self, clean_env, args_factory):
        """Test NEO4J_URL environment variable."""
        os.environ["NEO4J_URL"] = "bolt://env:7687"
        args = args_factory()
        result = process_db_url(args)
        assert result == "bolt://env:7687"

    def test_neo4j_uri_fallback(self, clean_env, args_factory):
        """Test NEO4J_URI fallback when NEO4J_URL is not set."""
        os.environ["NEO4J_URI"] = "bolt://uri:7687"
        args = args_factory()
        result = process_db_url(args)
        assert result == "bolt://uri:7687"

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_db_url(args)
        assert result == "bolt://localhost:7687"
        mock_logger.warning.assert_called_once()


class TestProcessUsername:
    """Test cases for process_username function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        args = args_factory(username="testuser")
        result = process_username(args)
        assert result == "testuser"

    def test_env_var_provided(self, clean_env, args_factory):
        """Test when environment variable is provided."""
        os.environ["NEO4J_USERNAME"] = "envuser"
        args = args_factory()
        result = process_username(args)
        assert result == "envuser"

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_username(args)
        assert result == "neo4j"
        mock_logger.warning.assert_called_once()


class TestProcessPassword:
    """Test cases for process_password function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        args = args_factory(password="testpass")
        result = process_password(args)
        assert result == "testpass"

    def test_env_var_provided(self, clean_env, args_factory):
        """Test when environment variable is provided."""
        os.environ["NEO4J_PASSWORD"] = "envpass"
        args = args_factory()
        result = process_password(args)
        assert result == "envpass"

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_password(args)
        assert result == "password"
        mock_logger.warning.assert_called_once()


class TestProcessDatabase:
    """Test cases for process_database function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        args = args_factory(database="testdb")
        result = process_database(args)
        assert result == "testdb"

    def test_env_var_provided(self, clean_env, args_factory):
        """Test when environment variable is provided."""
        os.environ["NEO4J_DATABASE"] = "envdb"
        args = args_factory()
        result = process_database(args)
        assert result == "envdb"

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_database(args)
        assert result == "neo4j"
        mock_logger.warning.assert_called_once()


class TestProcessNamespace:
    """Test cases for process_namespace function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        args = args_factory(namespace="testns")
        result = process_namespace(args)
        assert result == "testns"

    def test_env_var_provided(self, clean_env, args_factory):
        """Test when environment variable is provided."""
        os.environ["NEO4J_NAMESPACE"] = "envns"
        args = args_factory()
        result = process_namespace(args)
        assert result == "envns"

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_namespace(args)
        assert result == ""
        mock_logger.info.assert_called_once()


class TestProcessTransport:
    """Test cases for process_transport function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        args = args_factory(transport="http")
        result = process_transport(args)
        assert result == "http"

    def test_env_var_provided(self, clean_env, args_factory):
        """Test when environment variable is provided."""
        os.environ["NEO4J_TRANSPORT"] = "sse"
        args = args_factory()
        result = process_transport(args)
        assert result == "sse"

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_transport(args)
        assert result == "stdio"
        mock_logger.warning.assert_called_once()


class TestProcessServerHost:
    """Test cases for process_server_host function."""

    def test_cli_arg_provided_non_stdio(self, clean_env, args_factory):
        """Test when CLI argument is provided for non-stdio transport."""
        args = args_factory(server_host="testhost")
        result = process_server_host(args, "http")
        assert result == "testhost"

    def test_cli_arg_provided_stdio(self, clean_env, args_factory, mock_logger):
        """Test when CLI argument is provided for stdio transport."""
        args = args_factory(server_host="testhost")
        result = process_server_host(args, "stdio")
        assert result == "testhost"
        mock_logger.warning.assert_called_once()

    def test_env_var_provided_non_stdio(self, clean_env, args_factory):
        """Test when environment variable is provided for non-stdio transport."""
        os.environ["NEO4J_MCP_SERVER_HOST"] = "envhost"
        args = args_factory()
        result = process_server_host(args, "http")
        assert result == "envhost"

    def test_env_var_provided_stdio(self, clean_env, args_factory, mock_logger):
        """Test when environment variable is provided for stdio transport."""
        os.environ["NEO4J_MCP_SERVER_HOST"] = "envhost"
        args = args_factory()
        result = process_server_host(args, "stdio")
        assert result == "envhost"
        mock_logger.warning.assert_called_once()

    def test_default_non_stdio(self, clean_env, args_factory, mock_logger):
        """Test default value for non-stdio transport."""
        args = args_factory()
        result = process_server_host(args, "http")
        assert result == "127.0.0.1"
        mock_logger.warning.assert_called_once()

    def test_default_stdio(self, clean_env, args_factory, mock_logger):
        """Test default value for stdio transport."""
        args = args_factory()
        result = process_server_host(args, "stdio")
        assert result is None
        mock_logger.info.assert_called_once()


class TestProcessServerPort:
    """Test cases for process_server_port function."""

    def test_cli_arg_provided_non_stdio(self, clean_env, args_factory):
        """Test when CLI argument is provided for non-stdio transport."""
        args = args_factory(server_port=9000)
        result = process_server_port(args, "http")
        assert result == 9000

    def test_cli_arg_provided_stdio(self, clean_env, args_factory, mock_logger):
        """Test when CLI argument is provided for stdio transport."""
        args = args_factory(server_port=9000)
        result = process_server_port(args, "stdio")
        assert result == 9000
        mock_logger.warning.assert_called_once()

    def test_env_var_provided_non_stdio(self, clean_env, args_factory):
        """Test when environment variable is provided for non-stdio transport."""
        os.environ["NEO4J_MCP_SERVER_PORT"] = "8080"
        args = args_factory()
        result = process_server_port(args, "http")
        assert result == 8080
        assert isinstance(result, int)

    def test_env_var_provided_stdio(self, clean_env, args_factory, mock_logger):
        """Test when environment variable is provided for stdio transport."""
        os.environ["NEO4J_MCP_SERVER_PORT"] = "8080"
        args = args_factory()
        result = process_server_port(args, "stdio")
        assert result == 8080
        mock_logger.warning.assert_called_once()

    def test_default_non_stdio(self, clean_env, args_factory, mock_logger):
        """Test default value for non-stdio transport."""
        args = args_factory()
        result = process_server_port(args, "http")
        assert result == 8000
        mock_logger.warning.assert_called_once()

    def test_default_stdio(self, clean_env, args_factory, mock_logger):
        """Test default value for stdio transport."""
        args = args_factory()
        result = process_server_port(args, "stdio")
        assert result is None
        mock_logger.info.assert_called_once()


class TestProcessServerPath:
    """Test cases for process_server_path function."""

    def test_cli_arg_provided_non_stdio(self, clean_env, args_factory):
        """Test when CLI argument is provided for non-stdio transport."""
        args = args_factory(server_path="/test/")
        result = process_server_path(args, "http")
        assert result == "/test/"

    def test_cli_arg_provided_stdio(self, clean_env, args_factory, mock_logger):
        """Test when CLI argument is provided for stdio transport."""
        args = args_factory(server_path="/test/")
        result = process_server_path(args, "stdio")
        assert result == "/test/"
        mock_logger.warning.assert_called_once()

    def test_env_var_provided_non_stdio(self, clean_env, args_factory):
        """Test when environment variable is provided for non-stdio transport."""
        os.environ["NEO4J_MCP_SERVER_PATH"] = "/env/"
        args = args_factory()
        result = process_server_path(args, "http")
        assert result == "/env/"

    def test_env_var_provided_stdio(self, clean_env, args_factory, mock_logger):
        """Test when environment variable is provided for stdio transport."""
        os.environ["NEO4J_MCP_SERVER_PATH"] = "/env/"
        args = args_factory()
        result = process_server_path(args, "stdio")
        assert result == "/env/"
        mock_logger.warning.assert_called_once()

    def test_default_non_stdio(self, clean_env, args_factory, mock_logger):
        """Test default value for non-stdio transport."""
        args = args_factory()
        result = process_server_path(args, "http")
        assert result == "/mcp/"
        mock_logger.warning.assert_called_once()

    def test_default_stdio(self, clean_env, args_factory, mock_logger):
        """Test default value for stdio transport."""
        args = args_factory()
        result = process_server_path(args, "stdio")
        assert result is None
        mock_logger.info.assert_called_once()


class TestProcessAllowOrigins:
    """Test cases for process_allow_origins function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        origins = "http://localhost:3000,https://trusted-site.com"
        expected_origins = ["http://localhost:3000", "https://trusted-site.com"]
        args = args_factory(allow_origins=origins)
        result = process_allow_origins(args)
        assert result == expected_origins

    def test_env_var_provided(self, clean_env, args_factory):
        """Test when environment variable is provided."""
        origins_str = "http://localhost:3000,https://trusted-site.com"
        expected_origins = ["http://localhost:3000", "https://trusted-site.com"]
        os.environ["NEO4J_MCP_SERVER_ALLOW_ORIGINS"] = origins_str
        args = args_factory()
        result = process_allow_origins(args)
        assert result == expected_origins

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_allow_origins(args)
        assert result == []
        mock_logger.info.assert_called_once()

    def test_empty_string(self, clean_env, args_factory):
        """Test with empty string."""
        args = args_factory(allow_origins="")
        result = process_allow_origins(args)
        assert result == []

    def test_single_origin(self, clean_env, args_factory):
        """Test with single origin."""
        single_origin = "https://single-site.com"
        args = args_factory(allow_origins=single_origin)
        result = process_allow_origins(args)
        assert result == [single_origin]

    def test_wildcard(self, clean_env, args_factory):
        """Test with wildcard."""
        wildcard_origins = "*"
        args = args_factory(allow_origins=wildcard_origins)
        result = process_allow_origins(args)
        assert result == [wildcard_origins]


class TestProcessAllowedHosts:
    """Test cases for process_allowed_hosts function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        hosts = "host1.com,host2.com"
        expected_hosts = ["host1.com", "host2.com"]
        args = args_factory(allowed_hosts=hosts)
        result = process_allowed_hosts(args)
        assert result == expected_hosts

    def test_env_var_provided(self, clean_env, args_factory):
        """Test when environment variable is provided."""
        hosts_str = "env1.com,env2.com"
        expected_hosts = ["env1.com", "env2.com"]
        os.environ["NEO4J_MCP_SERVER_ALLOWED_HOSTS"] = hosts_str
        args = args_factory()
        result = process_allowed_hosts(args)
        assert result == expected_hosts

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_allowed_hosts(args)
        assert result == ["localhost", "127.0.0.1"]
        mock_logger.info.assert_called_once()


class TestProcessTokenLimit:
    """Test cases for process_token_limit function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        args = args_factory(token_limit=5000)
        result = process_token_limit(args)
        assert result == 5000

    def test_env_var_provided(self, clean_env, args_factory, mock_logger):
        """Test when environment variable is provided."""
        os.environ["NEO4J_RESPONSE_TOKEN_LIMIT"] = "3000"
        args = args_factory()
        result = process_token_limit(args)
        assert result == 3000
        mock_logger.info.assert_called_once()

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_token_limit(args)
        assert result is None
        mock_logger.info.assert_called_once()


class TestProcessReadTimeout:
    """Test cases for process_read_timeout function."""

    def test_cli_arg_provided(self, clean_env, args_factory):
        """Test when CLI argument is provided."""
        args = args_factory(read_timeout=60)
        result = process_read_timeout(args)
        assert result == 60

    def test_env_var_provided(self, clean_env, args_factory, mock_logger):
        """Test when environment variable is provided."""
        os.environ["NEO4J_READ_TIMEOUT"] = "90"
        args = args_factory()
        result = process_read_timeout(args)
        assert result == 90
        mock_logger.info.assert_called_once()

    def test_invalid_env_var(self, clean_env, args_factory, mock_logger):
        """Test when environment variable is invalid."""
        os.environ["NEO4J_READ_TIMEOUT"] = "invalid"
        args = args_factory()
        result = process_read_timeout(args)
        assert result == 30
        mock_logger.warning.assert_called_once()

    def test_default_value(self, clean_env, args_factory, mock_logger):
        """Test default value when nothing is provided."""
        args = args_factory()
        result = process_read_timeout(args)
        assert result == 30
        mock_logger.info.assert_called_once()


# Integration tests (similar to original process_config tests but using individual functions)


class TestIntegration:
    """Integration tests using multiple argument processing functions."""

    def test_full_config_from_cli(self, clean_env, args_factory):
        """Test full configuration from CLI arguments."""
        args = args_factory(
            db_url="bolt://test:7687",
            username="testuser",
            password="testpass",
            database="testdb",
            namespace="testns",
            transport="http",
            server_host="localhost",
            server_port=9000,
            server_path="/test/",
            allow_origins="http://localhost:3000",
            allowed_hosts="host1.com,host2.com",
            token_limit=5000,
            read_timeout=120,
        )

        config = {
            "db_url": process_db_url(args),
            "username": process_username(args),
            "password": process_password(args),
            "database": process_database(args),
            "namespace": process_namespace(args),
            "transport": process_transport(args),
        }

        transport = config["transport"]
        config.update(
            {
                "host": process_server_host(args, transport),
                "port": process_server_port(args, transport),
                "path": process_server_path(args, transport),
                "allow_origins": process_allow_origins(args),
                "allowed_hosts": process_allowed_hosts(args),
                "token_limit": process_token_limit(args),
                "read_timeout": process_read_timeout(args),
            }
        )

        assert config["db_url"] == "bolt://test:7687"
        assert config["username"] == "testuser"
        assert config["password"] == "testpass"
        assert config["database"] == "testdb"
        assert config["namespace"] == "testns"
        assert config["transport"] == "http"
        assert config["host"] == "localhost"
        assert config["port"] == 9000
        assert config["path"] == "/test/"
        assert config["allow_origins"] == ["http://localhost:3000"]
        assert config["allowed_hosts"] == ["host1.com", "host2.com"]
        assert config["token_limit"] == 5000
        assert config["read_timeout"] == 120

    def test_stdio_transport_behavior(self, clean_env, args_factory, mock_logger):
        """Test that stdio transport handles server config appropriately."""
        args = args_factory(
            transport="stdio",
            server_host="ignored_host",
            server_port=9999,
            server_path="/ignored/",
        )

        transport = process_transport(args)
        host = process_server_host(args, transport)
        port = process_server_port(args, transport)
        path = process_server_path(args, transport)

        assert transport == "stdio"
        assert host == "ignored_host"  # Set but should be ignored
        assert port == 9999  # Set but should be ignored
        assert path == "/ignored/"  # Set but should be ignored

        # Should have logged warnings about ignored values
        assert mock_logger.warning.call_count >= 3
