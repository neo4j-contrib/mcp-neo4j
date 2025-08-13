"""
Configuración centralizada para MCP-Neo4j-Memory v1.0
"""
import os
from typing import Optional


class MemoryConfig:
    """Configuración centralizada del MCP-Memory"""
    
    def __init__(self):
        # Neo4j Connection
        self.neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        # Multi-tenancy
        self.enable_tenant = os.getenv("ENABLE_TENANT", "true").lower() == "true"
        self.default_tenant = os.getenv("DEFAULT_TENANT", "default")
        
        # Search Limits
        self.default_max_level = int(os.getenv("DEFAULT_MAX_LEVEL", "2"))
        self.default_node_limit = int(os.getenv("DEFAULT_NODE_LIMIT", "100"))
        self.default_rel_limit = int(os.getenv("DEFAULT_REL_LIMIT", "200"))
        self.default_page_size = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
        
        # Performance
        self.query_timeout_ms = int(os.getenv("QUERY_TIMEOUT_MS", "5000"))
        self.enable_cache = os.getenv("ENABLE_CACHE", "false").lower() == "true"
        self.cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "300"))
        
        # Features
        self.enable_full_text = os.getenv("ENABLE_FULL_TEXT", "false").lower() == "true"
        self.auto_create_indexes = os.getenv("AUTO_CREATE_INDEXES", "true").lower() == "true"

    def model_dump(self):
        """For compatibility with Pydantic models"""
        return {
            "neo4j_url": self.neo4j_url,
            "neo4j_username": self.neo4j_username,
            "neo4j_database": self.neo4j_database,
            "enable_tenant": self.enable_tenant,
            "default_tenant": self.default_tenant,
            "default_max_level": self.default_max_level,
            "default_node_limit": self.default_node_limit,
            "default_rel_limit": self.default_rel_limit,
            "default_page_size": self.default_page_size,
            "query_timeout_ms": self.query_timeout_ms,
            "enable_cache": self.enable_cache,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "enable_full_text": self.enable_full_text,
            "auto_create_indexes": self.auto_create_indexes,
        }


# Singleton
config = MemoryConfig()