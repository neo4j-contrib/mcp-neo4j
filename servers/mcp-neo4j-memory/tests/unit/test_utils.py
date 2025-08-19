import argparse
import os
from unittest.mock import patch
import pytest

from mcp_neo4j_memory.utils import process_config


@pytest.fixture
def clean_env():
    """Fixture to clean environment variables before each test."""
    env_vars = [
        "NEO4J_URL", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", 
        "NEO4J_DATABASE", "NEO4J_TRANSPORT", "NEO4J_MCP_SERVER_HOST", 
        "NEO4J_MCP_SERVER_PORT", "NEO4J_MCP_SERVER_PATH"
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
            "transport": None,
            "server_host": None,
            "server_port": None,
            "server_path": None,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)
    return _create_args


@pytest.fixture
def mock_logger():
    """Fixture to provide a mocked logger."""
    with patch('mcp_neo4j_memory.utils.logger') as mock:
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
        server_path="/test/"
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
        "NEO4J_MCP_SERVER_PATH": "/env/"
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
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password",
        "neo4j_database": "neo4j",
        "transport": "stdio",
        "host": None,
        "port": None,
        "path": None,
    }


def test_all_cli_args_provided(clean_env, sample_cli_args):
    """Test when all CLI arguments are provided."""
    config = process_config(sample_cli_args)
    
    assert config["neo4j_uri"] == "bolt://test:7687"
    assert config["neo4j_user"] == "testuser"
    assert config["neo4j_password"] == "testpass"
    assert config["neo4j_database"] == "testdb"
    assert config["transport"] == "http"
    assert config["host"] == "localhost"
    assert config["port"] == 9000
    assert config["path"] == "/test/"


def test_all_env_vars_provided(clean_env, set_env_vars, args_factory):
    """Test when all environment variables are provided."""
    args = args_factory()
    config = process_config(args)
    
    assert config["neo4j_uri"] == "bolt://env:7687"
    assert config["neo4j_user"] == "envuser"
    assert config["neo4j_password"] == "envpass"
    assert config["neo4j_database"] == "envdb"
    assert config["transport"] == "sse"
    assert config["host"] == "envhost"
    assert config["port"] == 8080
    assert config["path"] == "/env/"


def test_cli_args_override_env_vars(clean_env, args_factory):
    """Test that CLI arguments take precedence over environment variables."""
    os.environ["NEO4J_URL"] = "bolt://env:7687"
    os.environ["NEO4J_USERNAME"] = "envuser"
    
    args = args_factory(
        db_url="bolt://cli:7687",
        username="cliuser"
    )
    
    config = process_config(args)
    
    assert config["neo4j_uri"] == "bolt://cli:7687"
    assert config["neo4j_user"] == "cliuser"


def test_neo4j_uri_fallback(clean_env, args_factory):
    """Test NEO4J_URI fallback when NEO4J_URL is not set."""
    os.environ["NEO4J_URI"] = "bolt://uri:7687"
    
    args = args_factory()
    config = process_config(args)
    
    assert config["neo4j_uri"] == "bolt://uri:7687"


def test_default_values_with_warnings(clean_env, args_factory, expected_defaults, mock_logger):
    """Test default values are used and warnings are logged when nothing is provided."""
    args = args_factory()
    config = process_config(args)
    
    for key, expected_value in expected_defaults.items():
        assert config[key] == expected_value
    
    # Check that warnings were logged
    warning_calls = [call for call in mock_logger.warning.call_args_list]
    assert len(warning_calls) == 5  # 5 warnings: neo4j uri, user, password, database, transport


def test_stdio_transport_ignores_server_config(clean_env, args_factory, mock_logger):
    """Test that stdio transport ignores server host/port/path and logs warnings."""
    args = args_factory(
        transport="stdio",
        server_host="localhost",
        server_port=8000,
        server_path="/test/"
    )
    
    config = process_config(args)
    
    assert config["transport"] == "stdio"
    assert config["host"] == "localhost"  # Set but ignored
    assert config["port"] == 8000  # Set but ignored
    assert config["path"] == "/test/"  # Set but ignored
    
    # Check that warnings were logged for ignored server config
    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
    stdio_warnings = [msg for msg in warning_calls if "stdio" in msg and "ignored" in msg]
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
    stdio_warnings = [msg for msg in warning_calls if "stdio" in msg and "environment variable" in msg]
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
        transport="sse",
        server_host="myhost",
        server_port=9999,
        server_path="/mypath/"
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


@pytest.mark.parametrize("transport,expected_host,expected_port,expected_path,expected_warning_count", [
    ("stdio", None, None, None, 0),  # stdio with no server config
    ("http", "127.0.0.1", 8000, "/mcp/", 3),  # http with defaults
    ("sse", "127.0.0.1", 8000, "/mcp/", 3),   # sse with defaults
])
def test_mixed_transport_scenarios(clean_env, args_factory, mock_logger, transport, expected_host, expected_port, expected_path, expected_warning_count):
    """Test various combinations of transport with server config."""
    args = args_factory(transport=transport)
    config = process_config(args)
    
    assert config["transport"] == transport
    assert config["host"] == expected_host
    assert config["port"] == expected_port
    assert config["path"] == expected_path
    
    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
    server_warnings = [msg for msg in warning_calls if any(
        keyword in msg for keyword in ["server host", "server port", "server path"]
    )]
    assert len(server_warnings) == expected_warning_count, f"Transport {transport} warning count mismatch"


def test_info_logging_stdio_transport(clean_env, args_factory, mock_logger):
    """Test that info messages are logged for stdio transport when appropriate."""
    args = args_factory(transport="stdio")
    config = process_config(args)
    
    # Check for info messages about stdio transport
    info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
    stdio_info = [msg for msg in info_calls if "stdio" in msg]
    assert len(stdio_info) == 3  # host, port, path info messages