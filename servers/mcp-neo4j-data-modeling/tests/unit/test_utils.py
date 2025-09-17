import os
from unittest.mock import patch

import pytest

from mcp_neo4j_data_modeling.utils import (
    parse_allow_origins,
    parse_allowed_hosts,
    parse_namespace,
    parse_server_host,
    parse_server_path,
    parse_server_port,
    parse_transport,
    process_config,
)


class TestParseTransport:
    def test_parse_transport_from_cli_args(self, clean_env, args_factory):
        """Test parsing transport from CLI arguments."""
        for transport in ["stdio", "http", "sse"]:
            args = args_factory(transport=transport)
            result = parse_transport(args)
            assert result == transport

    def test_parse_transport_from_env_var(self, clean_env, args_factory):
        """Test parsing transport from environment variable."""
        for transport in ["stdio", "http", "sse"]:
            os.environ["NEO4J_TRANSPORT"] = transport
            args = args_factory()
            result = parse_transport(args)
            assert result == transport
            del os.environ["NEO4J_TRANSPORT"]

    def test_parse_transport_cli_overrides_env(self, clean_env, args_factory):
        """Test that CLI argument takes precedence over environment variable."""
        os.environ["NEO4J_TRANSPORT"] = "http"
        args = args_factory(transport="sse")
        result = parse_transport(args)
        assert result == "sse"

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_transport_default_stdio(self, mock_logger, clean_env, args_factory):
        """Test that transport defaults to stdio when not provided."""
        args = args_factory()
        result = parse_transport(args)
        assert result == "stdio"

        # Check that info message was logged
        mock_logger.info.assert_called_once_with(
            "Info: No transport type provided. Using default: stdio"
        )

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_transport_invalid_cli_raises_error(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that invalid transport in CLI raises ValueError."""
        args = args_factory(transport="invalid")
        with pytest.raises(ValueError, match="Invalid transport: invalid"):
            parse_transport(args)

        # Check that error was logged
        mock_logger.error.assert_called_once()

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_transport_invalid_env_raises_error(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that invalid transport in env var raises ValueError."""
        os.environ["NEO4J_TRANSPORT"] = "invalid"
        args = args_factory()
        with pytest.raises(ValueError, match="Invalid transport: invalid"):
            parse_transport(args)

        # Check that error was logged
        mock_logger.error.assert_called_once()


class TestParseServerHost:
    def test_parse_server_host_from_cli_args(self, clean_env, args_factory):
        """Test parsing server_host from CLI arguments."""
        args = args_factory(server_host="test-host")
        result = parse_server_host(args, "http")
        assert result == "test-host"

    def test_parse_server_host_from_env_var(self, clean_env, args_factory):
        """Test parsing server_host from environment variable."""
        os.environ["NEO4J_MCP_SERVER_HOST"] = "env-host"
        args = args_factory()
        result = parse_server_host(args, "http")
        assert result == "env-host"

    def test_parse_server_host_cli_overrides_env(self, clean_env, args_factory):
        """Test that CLI argument takes precedence over environment variable."""
        os.environ["NEO4J_MCP_SERVER_HOST"] = "env-host"
        args = args_factory(server_host="cli-host")
        result = parse_server_host(args, "http")
        assert result == "cli-host"

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_host_default_for_non_stdio(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that server_host defaults to 127.0.0.1 for non-stdio transport."""
        args = args_factory()
        result = parse_server_host(args, "http")
        assert result == "127.0.0.1"

        # Check that warning was logged
        mock_logger.warning.assert_called_once()

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_host_none_for_stdio(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that server_host returns None for stdio transport when not provided."""
        args = args_factory()
        result = parse_server_host(args, "stdio")
        assert result is None

        # Check that info message was logged
        mock_logger.info.assert_called_once()

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_host_stdio_warning_cli(
        self, mock_logger, clean_env, args_factory
    ):
        """Test warning when server_host provided with stdio transport via CLI."""
        args = args_factory(server_host="test-host")
        result = parse_server_host(args, "stdio")
        assert result == "test-host"

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        assert (
            "server_host` argument will be set, but ignored"
            in mock_logger.warning.call_args[0][0]
        )

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_host_stdio_warning_env(
        self, mock_logger, clean_env, args_factory
    ):
        """Test warning when server_host provided with stdio transport via env var."""
        os.environ["NEO4J_MCP_SERVER_HOST"] = "env-host"
        args = args_factory()
        result = parse_server_host(args, "stdio")
        assert result == "env-host"

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        assert (
            "NEO4J_MCP_SERVER_HOST` environment variable will be set, but ignored"
            in mock_logger.warning.call_args[0][0]
        )


class TestParseServerPort:
    def test_parse_server_port_from_cli_args(self, clean_env, args_factory):
        """Test parsing server_port from CLI arguments."""
        args = args_factory(server_port=9000)
        result = parse_server_port(args, "http")
        assert result == 9000

    def test_parse_server_port_from_env_var(self, clean_env, args_factory):
        """Test parsing server_port from environment variable."""
        os.environ["NEO4J_MCP_SERVER_PORT"] = "9000"
        args = args_factory()
        result = parse_server_port(args, "http")
        assert result == 9000

    def test_parse_server_port_cli_overrides_env(self, clean_env, args_factory):
        """Test that CLI argument takes precedence over environment variable."""
        os.environ["NEO4J_MCP_SERVER_PORT"] = "8080"
        args = args_factory(server_port=9000)
        result = parse_server_port(args, "http")
        assert result == 9000

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_port_default_for_non_stdio(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that server_port defaults to 8000 for non-stdio transport."""
        args = args_factory()
        result = parse_server_port(args, "http")
        assert result == 8000

        # Check that warning was logged
        mock_logger.warning.assert_called_once()

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_port_none_for_stdio(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that server_port returns None for stdio transport when not provided."""
        args = args_factory()
        result = parse_server_port(args, "stdio")
        assert result is None

        # Check that info message was logged
        mock_logger.info.assert_called_once()

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_port_stdio_warning_cli(
        self, mock_logger, clean_env, args_factory
    ):
        """Test warning when server_port provided with stdio transport via CLI."""
        args = args_factory(server_port=9000)
        result = parse_server_port(args, "stdio")
        assert result == 9000

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        assert (
            "server_port` argument will be set, but ignored"
            in mock_logger.warning.call_args[0][0]
        )

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_port_stdio_warning_env(
        self, mock_logger, clean_env, args_factory
    ):
        """Test warning when server_port provided with stdio transport via env var."""
        os.environ["NEO4J_MCP_SERVER_PORT"] = "9000"
        args = args_factory()
        result = parse_server_port(args, "stdio")
        assert result == 9000

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        assert (
            "NEO4J_MCP_SERVER_PORT` environment variable will be set, but ignored"
            in mock_logger.warning.call_args[0][0]
        )


class TestParseServerPath:
    def test_parse_server_path_from_cli_args(self, clean_env, args_factory):
        """Test parsing server_path from CLI arguments."""
        args = args_factory(server_path="/test/")
        result = parse_server_path(args, "http")
        assert result == "/test/"

    def test_parse_server_path_from_env_var(self, clean_env, args_factory):
        """Test parsing server_path from environment variable."""
        os.environ["NEO4J_MCP_SERVER_PATH"] = "/env/"
        args = args_factory()
        result = parse_server_path(args, "http")
        assert result == "/env/"

    def test_parse_server_path_cli_overrides_env(self, clean_env, args_factory):
        """Test that CLI argument takes precedence over environment variable."""
        os.environ["NEO4J_MCP_SERVER_PATH"] = "/env/"
        args = args_factory(server_path="/cli/")
        result = parse_server_path(args, "http")
        assert result == "/cli/"

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_path_default_for_non_stdio(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that server_path defaults to /mcp/ for non-stdio transport."""
        args = args_factory()
        result = parse_server_path(args, "http")
        assert result == "/mcp/"

        # Check that warning was logged
        mock_logger.warning.assert_called_once()

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_path_none_for_stdio(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that server_path returns None for stdio transport when not provided."""
        args = args_factory()
        result = parse_server_path(args, "stdio")
        assert result is None

        # Check that info message was logged
        mock_logger.info.assert_called_once()

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_path_stdio_warning_cli(
        self, mock_logger, clean_env, args_factory
    ):
        """Test warning when server_path provided with stdio transport via CLI."""
        args = args_factory(server_path="/test/")
        result = parse_server_path(args, "stdio")
        assert result == "/test/"

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        assert (
            "server_path` argument will be set, but ignored"
            in mock_logger.warning.call_args[0][0]
        )

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_server_path_stdio_warning_env(
        self, mock_logger, clean_env, args_factory
    ):
        """Test warning when server_path provided with stdio transport via env var."""
        os.environ["NEO4J_MCP_SERVER_PATH"] = "/env/"
        args = args_factory()
        result = parse_server_path(args, "stdio")
        assert result == "/env/"

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        assert (
            "NEO4J_MCP_SERVER_PATH` environment variable will be set, but ignored"
            in mock_logger.warning.call_args[0][0]
        )


class TestParseAllowOrigins:
    def test_parse_allow_origins_from_cli_args(self, clean_env, args_factory):
        """Test parsing allow_origins from CLI arguments."""
        origins = "http://localhost:3000,https://trusted-site.com"
        expected_origins = ["http://localhost:3000", "https://trusted-site.com"]
        args = args_factory(allow_origins=origins)
        result = parse_allow_origins(args)
        assert result == expected_origins

    def test_parse_allow_origins_from_env_var(self, clean_env, args_factory):
        """Test parsing allow_origins from environment variable."""
        origins_str = "http://localhost:3000,https://trusted-site.com"
        expected_origins = ["http://localhost:3000", "https://trusted-site.com"]
        os.environ["NEO4J_MCP_SERVER_ALLOW_ORIGINS"] = origins_str

        args = args_factory()
        result = parse_allow_origins(args)
        assert result == expected_origins

    def test_parse_allow_origins_cli_overrides_env(self, clean_env, args_factory):
        """Test that CLI allow_origins takes precedence over environment variable."""
        os.environ["NEO4J_MCP_SERVER_ALLOW_ORIGINS"] = "http://env-site.com"

        cli_origins = "http://cli-site.com,https://cli-secure.com"
        expected_origins = ["http://cli-site.com", "https://cli-secure.com"]
        args = args_factory(allow_origins=cli_origins)
        result = parse_allow_origins(args)
        assert result == expected_origins

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_allow_origins_defaults_empty(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that allow_origins defaults to empty list when not provided."""
        args = args_factory()
        result = parse_allow_origins(args)
        assert result == []

        # Check that info message was logged
        mock_logger.info.assert_called_once_with(
            "Info: No allow origins provided. Defaulting to no allowed origins."
        )

    def test_parse_allow_origins_empty_string(self, clean_env, args_factory):
        """Test allow_origins with empty string from CLI."""
        args = args_factory(allow_origins="")
        result = parse_allow_origins(args)
        assert result == []

    def test_parse_allow_origins_single_origin(self, clean_env, args_factory):
        """Test allow_origins with single origin."""
        single_origin = "https://single-site.com"
        args = args_factory(allow_origins=single_origin)
        result = parse_allow_origins(args)
        assert result == [single_origin]

    def test_parse_allow_origins_with_spaces(self, clean_env, args_factory):
        """Test allow_origins with spaces around origins."""
        origins = " http://localhost:3000 , https://trusted-site.com "
        expected_origins = ["http://localhost:3000", "https://trusted-site.com"]
        args = args_factory(allow_origins=origins)
        result = parse_allow_origins(args)
        assert result == expected_origins

    def test_parse_allow_origins_wildcard(self, clean_env, args_factory):
        """Test allow_origins with wildcard."""
        wildcard_origins = "*"
        args = args_factory(allow_origins=wildcard_origins)
        result = parse_allow_origins(args)
        assert result == [wildcard_origins]


class TestParseAllowedHosts:
    def test_parse_allowed_hosts_from_cli_args(self, clean_env, args_factory):
        """Test parsing allowed_hosts from CLI arguments."""
        hosts = "example.com,www.example.com"
        expected_hosts = ["example.com", "www.example.com"]
        args = args_factory(allowed_hosts=hosts)
        result = parse_allowed_hosts(args)
        assert result == expected_hosts

    def test_parse_allowed_hosts_from_env_var(self, clean_env, args_factory):
        """Test parsing allowed_hosts from environment variable."""
        hosts_str = "example.com,www.example.com"
        expected_hosts = ["example.com", "www.example.com"]
        os.environ["NEO4J_MCP_SERVER_ALLOWED_HOSTS"] = hosts_str

        args = args_factory()
        result = parse_allowed_hosts(args)
        assert result == expected_hosts

    def test_parse_allowed_hosts_cli_overrides_env(self, clean_env, args_factory):
        """Test that CLI allowed_hosts takes precedence over environment variable."""
        os.environ["NEO4J_MCP_SERVER_ALLOWED_HOSTS"] = "env-host.com"

        cli_hosts = "cli-host.com,cli-secure.com"
        expected_hosts = ["cli-host.com", "cli-secure.com"]
        args = args_factory(allowed_hosts=cli_hosts)
        result = parse_allowed_hosts(args)
        assert result == expected_hosts

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_allowed_hosts_defaults_secure(
        self, mock_logger, clean_env, args_factory
    ):
        """Test that allowed_hosts defaults to secure localhost/127.0.0.1 when not provided."""
        args = args_factory()
        result = parse_allowed_hosts(args)
        assert result == ["localhost", "127.0.0.1"]

        # Check that info message was logged
        mock_logger.info.assert_called_once()
        assert "Defaulting to secure mode" in mock_logger.info.call_args[0][0]

    def test_parse_allowed_hosts_empty_string(self, clean_env, args_factory):
        """Test allowed_hosts with empty string from CLI."""
        args = args_factory(allowed_hosts="")
        result = parse_allowed_hosts(args)
        assert result == []

    def test_parse_allowed_hosts_single_host(self, clean_env, args_factory):
        """Test allowed_hosts with single host."""
        single_host = "example.com"
        args = args_factory(allowed_hosts=single_host)
        result = parse_allowed_hosts(args)
        assert result == [single_host]

    def test_parse_allowed_hosts_with_spaces(self, clean_env, args_factory):
        """Test allowed_hosts with spaces around hosts."""
        hosts = " example.com , www.example.com "
        expected_hosts = ["example.com", "www.example.com"]
        args = args_factory(allowed_hosts=hosts)
        result = parse_allowed_hosts(args)
        assert result == expected_hosts


class TestProcessConfig:
    def test_process_config_all_provided(self, clean_env, args_factory):
        """Test process_config when all arguments are provided."""
        args = args_factory(
            transport="http",
            server_host="test-host",
            server_port=9000,
            server_path="/test/",
            allow_origins="http://localhost:3000",
            allowed_hosts="example.com,www.example.com",
        )

        config = process_config(args)

        assert config["transport"] == "http"
        assert config["host"] == "test-host"
        assert config["port"] == 9000
        assert config["path"] == "/test/"
        assert config["allow_origins"] == ["http://localhost:3000"]
        assert config["allowed_hosts"] == ["example.com", "www.example.com"]

    def test_process_config_env_vars(self, clean_env, args_factory):
        """Test process_config when using environment variables."""
        os.environ["NEO4J_TRANSPORT"] = "sse"
        os.environ["NEO4J_MCP_SERVER_HOST"] = "env-host"
        os.environ["NEO4J_MCP_SERVER_PORT"] = "8080"
        os.environ["NEO4J_MCP_SERVER_PATH"] = "/env/"
        os.environ["NEO4J_MCP_SERVER_ALLOW_ORIGINS"] = "http://env.com,https://env.com"
        os.environ["NEO4J_MCP_SERVER_ALLOWED_HOSTS"] = "env.com,www.env.com"

        args = args_factory()
        config = process_config(args)

        assert config["transport"] == "sse"
        assert config["host"] == "env-host"
        assert config["port"] == 8080
        assert config["path"] == "/env/"
        assert config["allow_origins"] == ["http://env.com", "https://env.com"]
        assert config["allowed_hosts"] == ["env.com", "www.env.com"]

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_process_config_defaults(self, mock_logger, clean_env, args_factory):
        """Test process_config with minimal arguments (defaults applied)."""
        args = args_factory()

        config = process_config(args)

        assert config["transport"] == "stdio"  # default
        assert config["host"] is None  # None for stdio
        assert config["port"] is None  # None for stdio
        assert config["path"] is None  # None for stdio
        assert config["allow_origins"] == []  # default empty
        assert config["allowed_hosts"] == ["localhost", "127.0.0.1"]  # default secure

    @pytest.mark.parametrize(
        "transport,expected_host,expected_port,expected_path",
        [
            ("stdio", None, None, None),
            ("http", "127.0.0.1", 8000, "/mcp/"),
            ("sse", "127.0.0.1", 8000, "/mcp/"),
        ],
    )
    def test_process_config_transport_scenarios(
        self,
        clean_env,
        args_factory,
        transport,
        expected_host,
        expected_port,
        expected_path,
    ):
        """Test process_config with different transport modes."""
        args = args_factory(transport=transport)

        config = process_config(args)

        assert config["transport"] == transport
        assert config["host"] == expected_host
        assert config["port"] == expected_port
        assert config["path"] == expected_path


class TestParseNamespace:
    """Test namespace parsing functionality."""

    def test_parse_namespace_from_cli_args(self, clean_env, args_factory):
        """Test parsing namespace from CLI arguments."""
        args = args_factory(namespace="test-cli")
        result = parse_namespace(args)
        assert result == "test-cli"

    def test_parse_namespace_from_env_var(self, clean_env, args_factory):
        """Test parsing namespace from environment variable."""
        os.environ["NEO4J_NAMESPACE"] = "test-env"
        args = args_factory()
        result = parse_namespace(args)
        assert result == "test-env"

    def test_parse_namespace_cli_overrides_env(self, clean_env, args_factory):
        """Test that CLI argument takes precedence over environment variable."""
        os.environ["NEO4J_NAMESPACE"] = "test-env"
        args = args_factory(namespace="test-cli")
        result = parse_namespace(args)
        assert result == "test-cli"

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_namespace_default_empty(self, mock_logger, clean_env, args_factory):
        """Test that namespace defaults to empty string when not provided."""
        args = args_factory()
        result = parse_namespace(args)
        assert result == ""

        # Check that info message was logged
        mock_logger.info.assert_called_once_with("Info: No namespace provided for tools. No namespace will be used.")

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_namespace_logs_cli_value(self, mock_logger, clean_env, args_factory):
        """Test that namespace value is logged when provided via CLI."""
        args = args_factory(namespace="my-app")
        result = parse_namespace(args)
        assert result == "my-app"

        # Check that info message was logged
        mock_logger.info.assert_called_once_with("Info: Namespace provided for tools: my-app")

    @patch("mcp_neo4j_data_modeling.utils.logger")
    def test_parse_namespace_logs_env_value(self, mock_logger, clean_env, args_factory):
        """Test that namespace value is logged when provided via environment."""
        os.environ["NEO4J_NAMESPACE"] = "env-app"
        args = args_factory()
        result = parse_namespace(args)
        assert result == "env-app"

        # Check that info message was logged
        mock_logger.info.assert_called_once_with("Info: Namespace provided for tools: env-app")


class TestNamespaceConfigProcessing:
    """Test namespace configuration processing in process_config."""

    def test_process_config_namespace_cli(self, clean_env, args_factory):
        """Test process_config when namespace provided via CLI."""
        args = args_factory(namespace="test-cli")
        config = process_config(args)
        assert config["namespace"] == "test-cli"

    def test_process_config_namespace_env_var(self, clean_env, args_factory):
        """Test process_config when namespace provided via environment variable."""
        os.environ["NEO4J_NAMESPACE"] = "test-env"
        args = args_factory()
        config = process_config(args)
        assert config["namespace"] == "test-env"

    def test_process_config_namespace_cli_overrides_env(self, clean_env, args_factory):
        """Test that CLI namespace takes precedence over environment variable."""
        os.environ["NEO4J_NAMESPACE"] = "test-env"
        args = args_factory(namespace="test-cli")
        config = process_config(args)
        assert config["namespace"] == "test-cli"

    def test_process_config_namespace_default_empty(self, clean_env, args_factory):
        """Test that namespace defaults to empty string when not provided."""
        args = args_factory()
        config = process_config(args)
        assert config["namespace"] == ""

    def test_process_config_includes_namespace_in_output(self, clean_env, args_factory):
        """Test that process_config output includes namespace key."""
        args = args_factory(namespace="test")
        config = process_config(args)
        assert "namespace" in config
