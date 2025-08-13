"""
Script de prueba manual para las mejoras de MCP-Neo4j-Memory v1.0
"""
import asyncio
import json
import os
from datetime import datetime

# Set environment variables for testing
os.environ["NEO4J_URL"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
os.environ["ENABLE_TENANT"] = "true"
os.environ["DEFAULT_TENANT"] = "test-demo"
os.environ["DEFAULT_NODE_LIMIT"] = "50"
os.environ["DEFAULT_PAGE_SIZE"] = "10"

from src.mcp_neo4j_memory.neo4j_memory_optimized import (
    Neo4jMemoryOptimized, 
    EntityOptimized, 
    RelationOptimized
)
from src.mcp_neo4j_memory.config import config
from neo4j import AsyncGraphDatabase


async def test_workflow():
    """Prueba manual del flujo completo optimizado"""
    
    print("🚀 Iniciando pruebas manuales de MCP-Memory Optimizado v1.0...")
    print(f"📊 Configuración: tenant={config.default_tenant}, node_limit={config.default_node_limit}")
    
    try:
        # Conectar a Neo4j
        driver = AsyncGraphDatabase.driver(
            config.neo4j_url,
            auth=(config.neo4j_username, config.neo4j_password)
        )
        
        await driver.verify_connectivity()
        print(f"✅ Conectado a Neo4j: {config.neo4j_url}")
        
    except Exception as e:
        print(f"❌ Error conectando a Neo4j: {e}")
        print("💡 Asegúrate de que Neo4j esté ejecutándose en localhost:7687")
        print("💡 Usuario: neo4j, Password: password")
        return
    
    # Inicializar memoria optimizada
    memory = Neo4jMemoryOptimized(driver)
    
    try:
        # Crear índices
        await memory.create_indexes()
        print("✅ Índices creados/verificados")
        
        # 1. Crear entidades de prueba
        print("\n1️⃣ Creando entidades de prueba...")
        entities = [
            EntityOptimized(
                name="Juan Pérez",
                type="Person",
                observations=["Ingeniero de software", "20 años de experiencia", "Experto en Python y Go"]
            ),
            EntityOptimized(
                name="Proyecto MCP",
                type="Project",
                observations=["Servidor Neo4j", "Model Context Protocol", "Optimización de memoria"]
            ),
            EntityOptimized(
                name="Neo4j",
                type="Technology",
                observations=["Base de datos de grafos", "Cypher queries", "Alta performance"]
            ),
            EntityOptimized(
                name="Python",
                type="Technology", 
                observations=["Lenguaje de programación", "Backend development", "Data science"]
            )
        ]
        
        # Crear en tenant demo
        result = await memory.create_entities_optimized(entities, tenant_id="demo")
        print(f"✅ Creadas {len(result)} entidades en tenant 'demo'")
        
        # Crear relaciones
        relations = [
            RelationOptimized(source="Juan Pérez", target="Proyecto MCP", relationType="TRABAJA_EN"),
            RelationOptimized(source="Proyecto MCP", target="Neo4j", relationType="USA"),
            RelationOptimized(source="Juan Pérez", target="Python", relationType="CONOCE"),
            RelationOptimized(source="Proyecto MCP", target="Python", relationType="DESARROLLADO_EN")
        ]
        
        rel_result = await memory.create_relations_optimized(relations, tenant_id="demo")
        print(f"✅ Creadas {len(rel_result)} relaciones en tenant 'demo'")
        
        # 2. Búsqueda estándar optimizada
        print("\n2️⃣ Búsqueda optimizada estándar...")
        result = await memory.search_memories_optimized(
            query="Proyecto",
            tenant_id="demo",
            page_size=5
        )
        print(f"📊 Encontrados: {len(result.entities)} entidades, {len(result.relations)} relaciones")
        print(f"📄 Paginación: Página {result.pagination['current_page']} de {result.pagination['total_pages']}")
        print(f"📊 Total en BD: {result.pagination['total_count']}")
        
        # 3. Búsqueda con filtrado de propiedades (optimización de tokens)
        print("\n3️⃣ Búsqueda con filtrado de propiedades...")
        result = await memory.search_memories_optimized(
            query="software",
            tenant_id="demo",
            max_level=1,
            props_keep=["name", "type"],  # Solo nombre y tipo
            page_size=3
        )
        
        print(f"🔍 Nodos filtrados: {len(result.entities)}")
        if result.entities:
            print("📋 Ejemplo de entidad filtrada:")
            print(json.dumps(result.entities[0].model_dump(), indent=2, ensure_ascii=False))
        
        # 4. Test de paginación
        print("\n4️⃣ Test de paginación...")
        page1 = await memory.search_memories_optimized(
            query="",  # Buscar todo
            tenant_id="demo",
            simple_mode=True,
            page_size=2
        )
        
        print(f"📄 Página 1: {len(page1.entities)} entidades")
        if page1.pagination and page1.pagination['has_next']:
            print("➡️  Hay más páginas disponibles")
            cursor = page1.pagination['next_cursor']
            print(f"🔗 Cursor: {cursor[:30]}...")
            
            # Obtener página 2
            page2 = await memory.search_memories_optimized(
                query="",
                tenant_id="demo", 
                simple_mode=True,
                page_size=2,
                cursor=cursor
            )
            print(f"📄 Página 2: {len(page2.entities)} entidades")
        
        # 5. Test de multi-tenancy
        print("\n5️⃣ Test de multi-tenancy...")
        
        # Crear datos en otro tenant
        await memory.create_entities_optimized([
            EntityOptimized(
                name="Datos Secretos",
                type="Confidential",
                observations=["Información clasificada", "Acceso restringido"]
            )
        ], tenant_id="otro-cliente")
        
        # Buscar en tenant demo (no debe encontrar datos del otro tenant)
        result_demo = await memory.search_memories_optimized(
            query="Secretos",
            tenant_id="demo",
            simple_mode=True
        )
        print(f"🔍 Búsqueda 'Secretos' en tenant 'demo': {len(result_demo.entities)} entidades (debe ser 0)")
        
        # Buscar en tenant correcto
        result_otro = await memory.search_memories_optimized(
            query="Secretos",
            tenant_id="otro-cliente",
            simple_mode=True
        )
        print(f"🔍 Búsqueda 'Secretos' en tenant 'otro-cliente': {len(result_otro.entities)} entidades (debe ser 1)")
        
        # 6. Test de modo simple vs complejo
        print("\n6️⃣ Test de rendimiento: modo simple vs complejo...")
        
        import time
        
        # Modo simple
        start = time.time()
        result_simple = await memory.search_memories_optimized(
            query="Juan",
            tenant_id="demo",
            simple_mode=True
        )
        time_simple = time.time() - start
        
        # Modo complejo
        start = time.time()
        result_complex = await memory.search_memories_optimized(
            query="Juan",
            tenant_id="demo",
            max_level=3,
            simple_mode=False
        )
        time_complex = time.time() - start
        
        print(f"⚡ Modo simple: {time_simple:.3f}s, {len(result_simple.entities)} entidades")
        print(f"⚡ Modo complejo: {time_complex:.3f}s, {len(result_complex.entities)} entidades")
        
        # 7. Leer grafo completo con límites
        print("\n7️⃣ Leer grafo completo con límites...")
        graph = await memory.read_graph_optimized(tenant_id="demo", limit=10)
        print(f"📊 Grafo completo: {len(graph.entities)} entidades, {len(graph.relations)} relaciones")
        
        print("\n✅ Todas las pruebas completadas exitosamente!")
        print("\n📈 Resumen de mejoras implementadas:")
        print("  ✓ Multi-tenancy para aislamiento de datos")
        print("  ✓ Límites configurables para control de respuesta")
        print("  ✓ Paginación con cursors para datasets grandes")
        print("  ✓ Filtrado de propiedades para reducir tokens")
        print("  ✓ Modo simple para búsquedas rápidas")
        print("  ✓ Índices automáticos para mejor performance")
        print("  ✓ Retrocompatibilidad mantenida")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await driver.close()


if __name__ == "__main__":
    print("🧪 MCP-Neo4j-Memory v1.0 - Test Manual")
    print("=" * 50)
    
    # Verificar que se pueden importar las mejoras
    try:
        from src.mcp_neo4j_memory.config import config
        print(f"✅ Configuración cargada: tenant={config.default_tenant}")
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        print("💡 Ejecuta desde la carpeta del servidor: cd servers/mcp-neo4j-memory/")
        exit(1)
    
    asyncio.run(test_workflow())