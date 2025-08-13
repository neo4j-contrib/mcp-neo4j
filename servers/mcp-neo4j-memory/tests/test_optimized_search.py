"""
Tests para las funciones optimizadas de búsqueda
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

# Mock de Neo4j para tests unitarios
pytest_plugins = ('pytest_asyncio',)


def test_pagination_manager():
    """Test del gestor de paginación"""
    from mcp_neo4j_memory.improvements.pagination import PaginationManager
    
    # Test encode/decode cursor
    cursor = PaginationManager.encode_cursor(skip=20, page=3)
    decoded = PaginationManager.decode_cursor(cursor)
    
    assert decoded["skip"] == 20
    assert decoded["page"] == 3
    
    # Test decode cursor inválido
    decoded_invalid = PaginationManager.decode_cursor("invalid_cursor")
    assert decoded_invalid["skip"] == 0
    assert decoded_invalid["page"] == 1


def test_tenant_manager():
    """Test del gestor de multi-tenancy"""
    from mcp_neo4j_memory.improvements.tenant_manager import TenantManager
    
    # Test get_tenant_id
    tenant_id = TenantManager.get_tenant_id("test-tenant")
    assert tenant_id == "test-tenant"
    
    tenant_id_default = TenantManager.get_tenant_id(None)
    assert tenant_id_default == "default"  # Del config
    
    # Test add_tenant_to_params
    params = {"query": "test"}
    params_with_tenant = TenantManager.add_tenant_to_params(params, "test-tenant")
    assert "tenant" in params_with_tenant
    assert params_with_tenant["tenant"] == "test-tenant"


def test_query_optimizer():
    """Test del optimizador de queries"""
    from mcp_neo4j_memory.improvements.query_optimizer import QueryOptimizer
    
    # Test filter_node_properties
    nodes = [
        {
            "name": "Test Node",
            "type": "TestType", 
            "observations": ["obs1", "obs2", "obs3"],
            "extra_data": "should be filtered",
            "metadata": {"key": "value"}
        }
    ]
    
    filtered = QueryOptimizer.filter_node_properties(nodes, ["name", "type"])
    
    assert len(filtered) == 1
    assert "name" in filtered[0]
    assert "type" in filtered[0]
    assert "extra_data" not in filtered[0]
    assert "observations_summary" in filtered[0]  # Debe agregar summary


def test_config():
    """Test de la configuración"""
    from mcp_neo4j_memory.config import config
    
    # Test valores por defecto
    assert config.default_tenant == "default"
    assert config.default_max_level == 2
    assert config.default_node_limit == 100
    assert config.enable_tenant == True


class MockNeo4jDriver:
    """Mock driver de Neo4j para tests"""
    
    def __init__(self):
        self.session_mock = AsyncMock()
        self.result_mock = AsyncMock()
        
    def session(self):
        return self.session_mock
    
    async def verify_connectivity(self):
        return True


@pytest.mark.asyncio
async def test_optimized_memory_creation():
    """Test de creación de Neo4jMemoryOptimized"""
    from mcp_neo4j_memory.neo4j_memory_optimized import Neo4jMemoryOptimized
    
    mock_driver = MockNeo4jDriver()
    memory = Neo4jMemoryOptimized(mock_driver)
    
    assert memory.driver == mock_driver


@pytest.mark.asyncio  
async def test_search_with_pagination():
    """Test de búsqueda con paginación simulada"""
    from mcp_neo4j_memory.improvements.pagination import PaginationManager
    
    # Datos simulados
    entities = [{"name": f"Entity {i}", "type": "Test"} for i in range(25)]
    relations = []
    
    # Test paginación
    paginated = PaginationManager.build_pagination_response(
        entities=entities,
        relations=relations,
        total_count=100,
        current_skip=0,
        page_size=10
    )
    
    assert paginated["pagination"]["total_count"] == 100
    assert paginated["pagination"]["page_size"] == 10
    assert paginated["pagination"]["current_page"] == 1
    assert paginated["pagination"]["has_next"] == True
    assert "next_cursor" in paginated["pagination"]


@pytest.mark.asyncio
async def test_fallback_search():
    """Test de búsqueda de respaldo"""
    from mcp_neo4j_memory.neo4j_memory_optimized import Neo4jMemoryOptimized
    
    # Mock driver que siempre falla
    mock_driver = AsyncMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    # Simular fallo en query principal
    mock_session.run.side_effect = Exception("Query failed")
    
    memory = Neo4jMemoryOptimized(mock_driver)
    
    # El fallback debe manejarse sin errores
    result = await memory._fallback_search("test query", "test-tenant")
    
    assert result.entities == []
    assert result.relations == []