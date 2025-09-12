import pytest
import tiktoken

from mcp_neo4j_cypher.utils import _truncate_string_to_tokens


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
        text = "This is a very long string that should definitely exceed the token limit. " * 10
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
    
    
