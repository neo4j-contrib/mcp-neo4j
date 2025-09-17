import argparse
import os
from unittest.mock import patch

import pytest
import tiktoken

from mcp_neo4j_cypher.utils import (
    _truncate_string_to_tokens,
    parse_boolean_safely,
    process_config,
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
        "NEO4J_READ_ONLY",
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
            "read_only": None,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    return _create_args


@pytest.fixture
def mock_logger():
    """Fixture to provide a mocked logger."""
    with patch("mcp_neo4j_cypher.utils.logger") as mock:
        yield mock


@pytest.fixture
def sample_cli_args(args_factory):
    """Fixture providing sample CLI arguments."""
    return args_factory(
        db_url="bolt://test:7687",
        username="testuser",
        password="testpass",
        database="testdb",
        transport="http",
        server_host="localhost",
        server_port=9000,
        server_path="/test/",
        namespace="testnamespace",
        read_timeout=120,
    )


@pytest.fixture
def sample_env_vars():
    """Fixture providing sample environment variables."""
    return {
        "NEO4J_URL": "bolt://env:7687",
        "NEO4J_USERNAME": "envuser",
        "NEO4J_PASSWORD": "envpass",
        "NEO4J_DATABASE": "envdb",
        "NEO4J_TRANSPORT": "sse",
        "NEO4J_MCP_SERVER_HOST": "envhost",
        "NEO4J_MCP_SERVER_PORT": "8080",
        "NEO4J_MCP_SERVER_PATH": "/env/",
        "NEO4J_NAMESPACE": "envnamespace",
        "NEO4J_READ_TIMEOUT": "45",
    }


@pytest.fixture
def set_env_vars(sample_env_vars):
    """Fixture to set environment variables and clean up after test."""
    for key, value in sample_env_vars.items():
        os.environ[key] = value
    yield sample_env_vars
    # Cleanup handled by clean_env fixture


@pytest.fixture
def expected_defaults():
    """Fixture providing expected default configuration values."""
    return {
        "db_url": "bolt://localhost:7687",
        "username": "neo4j",
        "password": "password",
        "database": "neo4j",
        "transport": "stdio",
        "host": None,
        "port": None,
        "path": None,
        "namespace": "",
        "read_timeout": 30,
    }


def test_all_cli_args_provided(clean_env, sample_cli_args):
    """Test when all CLI arguments are provided."""
    config = process_config(sample_cli_args)

    assert config["db_url"] == "bolt://test:7687"
    assert config["username"] == "testuser"
    assert config["password"] == "testpass"
    assert config["database"] == "testdb"
    assert config["transport"] == "http"
    assert config["host"] == "localhost"
    assert config["port"] == 9000
    assert config["path"] == "/test/"
    assert config["namespace"] == "testnamespace"
    assert config["read_timeout"] == 120


def test_all_env_vars_provided(clean_env, set_env_vars, args_factory):
    """Test when all environment variables are provided."""
    args = args_factory()
    config = process_config(args)

    assert config["db_url"] == "bolt://env:7687"
    assert config["username"] == "envuser"
    assert config["password"] == "envpass"
    assert config["database"] == "envdb"
    assert config["transport"] == "sse"
    assert config["host"] == "envhost"
    assert config["port"] == 8080
    assert config["path"] == "/env/"
    assert config["namespace"] == "envnamespace"
    assert config["read_timeout"] == 45


def test_cli_args_override_env_vars(clean_env, args_factory):
    """Test that CLI arguments take precedence over environment variables."""
    os.environ["NEO4J_URL"] = "bolt://env:7687"
    os.environ["NEO4J_USERNAME"] = "envuser"

    args = args_factory(db_url="bolt://cli:7687", username="cliuser")

    config = process_config(args)

    assert config["db_url"] == "bolt://cli:7687"
    assert config["username"] == "cliuser"


def test_neo4j_uri_fallback(clean_env, args_factory):
    """Test NEO4J_URI fallback when NEO4J_URL is not set."""
    os.environ["NEO4J_URI"] = "bolt://uri:7687"

    args = args_factory()
    config = process_config(args)

    assert config["db_url"] == "bolt://uri:7687"


def test_default_values_with_warnings(
    clean_env, args_factory, expected_defaults, mock_logger
):
    """Test default values are used and warnings are logged when nothing is provided."""
    args = args_factory()
    config = process_config(args)

    for key, expected_value in expected_defaults.items():
        assert config[key] == expected_value

    # Check that warnings were logged
    warning_calls = [call for call in mock_logger.warning.call_args_list]
    assert (
        len(warning_calls) == 5
    )  # 5 warnings: neo4j uri, user, password, database, transport


def test_stdio_transport_ignores_server_config(clean_env, args_factory, mock_logger):
    """Test that stdio transport ignores server host/port/path and logs warnings."""
    args = args_factory(
        transport="stdio",
        server_host="localhost",
        server_port=8000,
        server_path="/test/",
    )

    config = process_config(args)

    assert config["transport"] == "stdio"
    assert config["host"] == "localhost"  # Set but ignored
    assert config["port"] == 8000  # Set but ignored
    assert config["path"] == "/test/"  # Set but ignored

    # Check that warnings were logged for ignored server config
    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
    stdio_warnings = [
        msg for msg in warning_calls if "stdio" in msg and "ignored" in msg
    ]
    assert len(stdio_warnings) == 3  # host, port, path warnings


def test_stdio_transport_env_vars_ignored(clean_env, args_factory, mock_logger):
    """Test that stdio transport ignores environment variables for server config."""
    os.environ["NEO4J_TRANSPORT"] = "stdio"
    os.environ["NEO4J_MCP_SERVER_HOST"] = "envhost"
    os.environ["NEO4J_MCP_SERVER_PORT"] = "9000"
    os.environ["NEO4J_MCP_SERVER_PATH"] = "/envpath/"

    args = args_factory()
    config = process_config(args)

    assert config["transport"] == "stdio"
    assert config["host"] == "envhost"  # Set but ignored
    assert config["port"] == 9000  # Set but ignored
    assert config["path"] == "/envpath/"  # Set but ignored

    # Check that warnings were logged for ignored env vars
    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
    stdio_warnings = [
        msg for msg in warning_calls if "stdio" in msg and "environment variable" in msg
    ]
    assert len(stdio_warnings) == 3


def test_non_stdio_transport_uses_defaults(clean_env, args_factory, mock_logger):
    """Test that non-stdio transport uses default server config when not provided."""
    args = args_factory(transport="http")
    config = process_config(args)

    assert config["transport"] == "http"
    assert config["host"] == "127.0.0.1"
    assert config["port"] == 8000
    assert config["path"] == "/mcp/"

    # Check that warnings were logged for using defaults
    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
    default_warnings = [msg for msg in warning_calls if "Using default" in msg]
    assert len(default_warnings) >= 3  # host, port, path defaults


def test_non_stdio_transport_with_server_config(clean_env, args_factory, mock_logger):
    """Test that non-stdio transport uses provided server config without warnings."""
    args = args_factory(
        transport="sse", server_host="myhost", server_port=9999, server_path="/mypath/"
    )

    config = process_config(args)

    assert config["transport"] == "sse"
    assert config["host"] == "myhost"
    assert config["port"] == 9999
    assert config["path"] == "/mypath/"

    # Should not have warnings about stdio transport
    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
    stdio_warnings = [msg for msg in warning_calls if "stdio" in msg]
    assert len(stdio_warnings) == 0


def test_env_var_port_conversion(clean_env, args_factory, mock_logger):
    """Test that environment variable port is converted to int."""
    os.environ["NEO4J_MCP_SERVER_PORT"] = "8080"
    os.environ["NEO4J_TRANSPORT"] = "http"

    args = args_factory()
    config = process_config(args)

    assert config["port"] == 8080
    assert isinstance(config["port"], int)


@pytest.mark.parametrize(
    "transport,expected_host,expected_port,expected_path,expected_warning_count",
    [
        ("stdio", None, None, None, 0),  # stdio with no server config
        ("http", "127.0.0.1", 8000, "/mcp/", 3),  # http with defaults
        ("sse", "127.0.0.1", 8000, "/mcp/", 3),  # sse with defaults
    ],
)
def test_mixed_transport_scenarios(
    clean_env,
    args_factory,
    mock_logger,
    transport,
    expected_host,
    expected_port,
    expected_path,
    expected_warning_count,
):
    """Test various combinations of transport with server config."""
    args = args_factory(transport=transport)
    config = process_config(args)

    assert config["transport"] == transport
    assert config["host"] == expected_host
    assert config["port"] == expected_port
    assert config["path"] == expected_path

    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
    server_warnings = [
        msg
        for msg in warning_calls
        if any(
            keyword in msg for keyword in ["server host", "server port", "server path"]
        )
    ]
    assert len(server_warnings) == expected_warning_count, (
        f"Transport {transport} warning count mismatch"
    )


def test_info_logging_stdio_transport(clean_env, args_factory, mock_logger):
    """Test that info messages are logged for stdio transport when appropriate."""
    args = args_factory(transport="stdio")
    process_config(args)

    # Check for info messages about stdio transport
    info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
    stdio_info = [msg for msg in info_calls if "stdio" in msg]
    assert len(stdio_info) == 3  # host, port, path info messages


# CORS allow_origins tests


def test_allow_origins_cli_args(clean_env, args_factory):
    """Test allow_origins configuration from CLI arguments."""
    origins = "http://localhost:3000,https://trusted-site.com"
    expected_origins = ["http://localhost:3000", "https://trusted-site.com"]
    args = args_factory(allow_origins=origins)
    config = process_config(args)

    assert config["allow_origins"] == expected_origins


def test_allow_origins_env_var(clean_env, args_factory):
    """Test allow_origins configuration from environment variable."""
    origins_str = "http://localhost:3000,https://trusted-site.com"
    expected_origins = ["http://localhost:3000", "https://trusted-site.com"]
    os.environ["NEO4J_MCP_SERVER_ALLOW_ORIGINS"] = origins_str

    args = args_factory()
    config = process_config(args)

    assert config["allow_origins"] == expected_origins


def test_allow_origins_defaults(clean_env, args_factory, mock_logger):
    """Test allow_origins uses empty list as default when not provided."""
    args = args_factory()
    config = process_config(args)

    assert config["allow_origins"] == []

    # Check that info message was logged about using defaults
    info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
    allow_origins_info = [
        msg
        for msg in info_calls
        if "allow origins" in msg and "Defaulting to no" in msg
    ]
    assert len(allow_origins_info) == 1


def test_allow_origins_cli_overrides_env(clean_env, args_factory):
    """Test that CLI allow_origins takes precedence over environment variable."""
    os.environ["NEO4J_MCP_SERVER_ALLOW_ORIGINS"] = "http://env-site.com"

    cli_origins = "http://cli-site.com,https://cli-secure.com"
    expected_origins = ["http://cli-site.com", "https://cli-secure.com"]
    args = args_factory(allow_origins=cli_origins)
    config = process_config(args)

    assert config["allow_origins"] == expected_origins


def test_allow_origins_empty_list(clean_env, args_factory):
    """Test allow_origins with empty list from CLI."""
    args = args_factory(allow_origins="")
    config = process_config(args)

    assert config["allow_origins"] == []


def test_allow_origins_single_origin(clean_env, args_factory):
    """Test allow_origins with single origin."""
    single_origin = "https://single-site.com"
    args = args_factory(allow_origins=single_origin)
    config = process_config(args)

    assert config["allow_origins"] == [single_origin]


def test_allow_origins_wildcard(clean_env, args_factory):
    """Test allow_origins with wildcard."""
    wildcard_origins = "*"
    args = args_factory(allow_origins=wildcard_origins)
    config = process_config(args)

    assert config["allow_origins"] == [wildcard_origins]


def test_read_timeout_cli_arg(clean_env, args_factory):
    """Test that read_timeout CLI argument is properly processed."""
    args = args_factory(read_timeout=60)
    config = process_config(args)

    assert config["read_timeout"] == 60


def test_read_timeout_env_var(clean_env, args_factory):
    """Test that NEO4J_READ_TIMEOUT environment variable is properly processed."""
    os.environ["NEO4J_READ_TIMEOUT"] = "90"

    args = args_factory()
    config = process_config(args)

    assert config["read_timeout"] == 90


def test_token_limit_cli_arg(clean_env, args_factory):
    """Test that token_limit CLI argument is processed correctly."""
    args = args_factory(token_limit=5000)
    config = process_config(args)

    assert config["token_limit"] == 5000


def test_token_limit_env_var(clean_env, args_factory):
    """Test that token_limit environment variable is processed correctly."""
    os.environ["NEO4J_RESPONSE_TOKEN_LIMIT"] = "3000"

    args = args_factory()
    config = process_config(args)

    assert config["token_limit"] == 3000


def test_read_timeout_cli_overrides_env(clean_env, args_factory):
    """Test that CLI read_timeout argument overrides environment variable."""
    os.environ["NEO4J_READ_TIMEOUT"] = "90"

    args = args_factory(read_timeout=120)
    config = process_config(args)

    assert config["read_timeout"] == 120


def test_read_timeout_invalid_env_var(clean_env, args_factory, mock_logger):
    """Test that invalid read_timeout environment variable is handled."""
    os.environ["NEO4J_READ_TIMEOUT"] = "a"

    args = args_factory()
    config = process_config(args)

    assert config["read_timeout"] == 30

    # Check that warning message was logged about invalid value
    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
    invalid_timeout_warning = [
        msg for msg in warning_calls if "Invalid read timeout" in msg
    ]
    assert len(invalid_timeout_warning) == 1


def test_read_timeout_default_value(clean_env, args_factory, mock_logger):
    """Test that default read_timeout is used when not specified."""
    args = args_factory()
    config = process_config(args)

    assert config["read_timeout"] == 30

    # Check that info message was logged about default
    info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
    timeout_info = [
        msg for msg in info_calls if "read timeout" in msg and "default" in msg
    ]
    assert len(timeout_info) == 1
    assert config["read_timeout"] == 30


def test_token_limit_default_none(clean_env, args_factory, mock_logger):
    """Test that token_limit defaults to None when not provided."""
    args = args_factory()
    config = process_config(args)

    assert config["token_limit"] is None

    # Check info message
    info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
    token_limit_info = [msg for msg in info_calls if "token limit" in msg]
    assert len(token_limit_info) == 1


def test_token_limit_cli_overrides_env(clean_env, args_factory):
    """Test that CLI token_limit takes precedence over environment variable."""
    os.environ["NEO4J_RESPONSE_TOKEN_LIMIT"] = "2000"

    args = args_factory(token_limit=4000)
    config = process_config(args)

    assert config["token_limit"] == 4000


# Token truncation tests


class TestTruncateStringToTokens:
    """Test cases for _truncate_string_to_tokens function."""

    def test_short_string_not_truncated(self):
        """Test that strings below token limit are not truncated."""
        text = "Hello, world!"
        token_limit = 100

        result = _truncate_string_to_tokens(text, token_limit)

        assert result == text

    def test_string_exactly_at_limit_not_truncated(self):
        """Test that strings exactly at token limit are not truncated."""
        text = "This is a test string."
        encoding = tiktoken.encoding_for_model("gpt-4")
        tokens = encoding.encode(text)
        token_limit = len(tokens)

        result = _truncate_string_to_tokens(text, token_limit)

        assert result == text

    def test_long_string_truncated(self):
        """Test that strings exceeding token limit are truncated."""
        text = (
            "This is a very long string that should definitely exceed the token limit. "
            * 10
        )
        token_limit = 20

        result = _truncate_string_to_tokens(text, token_limit)

        # Verify it's shorter than original
        assert len(result) < len(text)

        # Verify it's within token limit
        encoding = tiktoken.encoding_for_model("gpt-4")
        result_tokens = encoding.encode(result)
        assert len(result_tokens) <= token_limit

    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        text = ""
        token_limit = 10

        result = _truncate_string_to_tokens(text, token_limit)

        assert result == ""

    def test_single_character_handling(self):
        """Test handling of single characters."""
        text = "A"
        token_limit = 10

        result = _truncate_string_to_tokens(text, token_limit)

        assert result == "A"

    def test_zero_token_limit(self):
        """Test behavior with zero token limit."""
        text = "Hello, world!"
        token_limit = 0

        result = _truncate_string_to_tokens(text, token_limit)

        # Should return empty string when limit is 0
        assert result == ""

    def test_json_data_truncation(self):
        """Test truncation of JSON-like data typical of Neo4j responses."""
        json_data = """[
            {"name": "Alice", "age": 30, "city": "New York", "occupation": "Engineer"},
            {"name": "Bob", "age": 25, "city": "San Francisco", "occupation": "Designer"},
            {"name": "Charlie", "age": 35, "city": "Chicago", "occupation": "Manager"},
            {"name": "Diana", "age": 28, "city": "Seattle", "occupation": "Developer"}
        ]"""
        token_limit = 30

        result = _truncate_string_to_tokens(json_data, token_limit)

        # Verify truncation occurred
        assert len(result) < len(json_data)

        # Verify token limit respected
        encoding = tiktoken.encoding_for_model("gpt-4")
        result_tokens = encoding.encode(result)
        assert len(result_tokens) <= token_limit

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        text = "Hello 🌍! This has unicode: café, naïve, 北京"
        token_limit = 10

        result = _truncate_string_to_tokens(text, token_limit)

        # Should handle unicode properly
        encoding = tiktoken.encoding_for_model("gpt-4")
        result_tokens = encoding.encode(result)
        assert len(result_tokens) <= token_limit

        # Result should be valid unicode
        assert isinstance(result, str)

    def test_large_token_limit_no_truncation(self):
        """Test with token limit much larger than text."""
        text = "Short text."
        token_limit = 10000  # Very large limit

        result = _truncate_string_to_tokens(text, token_limit)

        assert result == text


# Boolean parsing tests


class TestParseBooleanSafely:
    """Test cases for parse_boolean_safely function."""

    def test_bool_inputs(self):
        """Test boolean inputs."""
        assert parse_boolean_safely(True) is True
        assert parse_boolean_safely(False) is False

    def test_string_true_variations(self):
        """Test string 'true' variations."""
        assert parse_boolean_safely("true") is True
        assert parse_boolean_safely("TRUE") is True
        assert parse_boolean_safely("  true  ") is True

    def test_string_false_variations(self):
        """Test string 'false' variations."""
        assert parse_boolean_safely("false") is False
        assert parse_boolean_safely("FALSE") is False
        assert parse_boolean_safely("  false  ") is False

    def test_invalid_strings(self):
        """Test invalid string values raise ValueError."""
        invalid_values = ["yes", "no", "1", "0", "", "random"]
        for value in invalid_values:
            with pytest.raises(ValueError, match="Invalid boolean value"):
                parse_boolean_safely(value)

    def test_invalid_types(self):
        """Test invalid types raise ValueError."""
        invalid_values = [None, 1, [], {}]
        for value in invalid_values:
            with pytest.raises(ValueError, match="Invalid boolean value"):
                parse_boolean_safely(value)


# Read-only configuration tests


def test_read_only_cli_args(clean_env, args_factory):
    """Test read-only mode via CLI arguments."""
    # CLI arguments are boolean flags (store_true action)
    assert process_config(args_factory(read_only=True))["read_only"] is True
    assert process_config(args_factory(read_only=False))["read_only"] is False


def test_read_only_env_vars(clean_env, args_factory):
    """Test read-only mode via environment variables."""
    os.environ["NEO4J_READ_ONLY"] = "true"
    assert process_config(args_factory())["read_only"] is True

    os.environ["NEO4J_READ_ONLY"] = "FALSE"
    assert process_config(args_factory())["read_only"] is False


def test_read_only_invalid_values(clean_env, args_factory):
    """Test read-only mode with invalid environment values raises ValueError."""
    # Environment invalid values should raise ValueError
    os.environ["NEO4J_READ_ONLY"] = "yes"
    with pytest.raises(ValueError):
        process_config(args_factory())

    os.environ["NEO4J_READ_ONLY"] = "1"
    with pytest.raises(ValueError):
        process_config(args_factory())

    os.environ["NEO4J_READ_ONLY"] = ""
    with pytest.raises(ValueError):
        process_config(args_factory())


def test_read_only_defaults_and_precedence(clean_env, args_factory):
    """Test read-only defaults and CLI precedence."""
    # Default is False when no args and no env var
    assert process_config(args_factory())["read_only"] is False

    # CLI overrides environment - when CLI flag is present (True), it takes precedence
    os.environ["NEO4J_READ_ONLY"] = "false"
    assert process_config(args_factory(read_only=True))["read_only"] is True

    # When CLI flag is absent (False), env var is used
    os.environ["NEO4J_READ_ONLY"] = "true"
    assert process_config(args_factory(read_only=False))["read_only"] is True
