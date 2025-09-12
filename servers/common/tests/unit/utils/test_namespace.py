"""
Tests for namespace utilities.
"""

from common.utils.namespace import format_namespace


class TestFormatNamespace:
    """Test cases for format_namespace function."""
    
    def test_empty_namespace(self):
        """Test with empty namespace string."""
        result = format_namespace("")
        assert result == ""
    
    def test_namespace_without_suffix(self):
        """Test namespace without hyphen suffix."""
        result = format_namespace("test")
        assert result == "test-"
    
    def test_namespace_with_suffix(self):
        """Test namespace that already has hyphen suffix."""
        result = format_namespace("test-")
        assert result == "test-"
    
    def test_namespace_with_multiple_parts(self):
        """Test namespace with multiple parts."""
        result = format_namespace("my-namespace")
        assert result == "my-namespace-"
    
    def test_namespace_with_multiple_parts_and_suffix(self):
        """Test namespace with multiple parts that already has suffix."""
        result = format_namespace("my-namespace-")
        assert result == "my-namespace-"
    
    def test_single_char_namespace(self):
        """Test with single character namespace."""
        result = format_namespace("a")
        assert result == "a-"
    
    def test_single_hyphen_namespace(self):
        """Test with single hyphen as namespace."""
        result = format_namespace("-")
        assert result == "-"
    
    def test_namespace_with_numbers(self):
        """Test namespace with numbers."""
        result = format_namespace("v1")
        assert result == "v1-"
    
    def test_namespace_with_numbers_and_suffix(self):
        """Test namespace with numbers that already has suffix."""
        result = format_namespace("v1-")
        assert result == "v1-"