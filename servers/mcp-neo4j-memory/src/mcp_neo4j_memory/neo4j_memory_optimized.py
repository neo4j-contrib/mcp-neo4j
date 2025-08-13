"""
Versión optimizada de Neo4jMemory con mejoras de producción
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from neo4j import AsyncDriver, RoutingControl
from pydantic import BaseModel

from .config import config
from .improvements.tenant_manager import TenantManager
from .improvements.query_optimizer import QueryOptimizer
from .improvements.pagination import PaginationManager


# Set up logging
logger = logging.getLogger('mcp_neo4j_memory_optimized')
logger.setLevel(logging.INFO)


# Modelos extendidos con tenant support
class EntityOptimized(BaseModel):
    name: str
    type: str
    observations: List[str]
    tenant_id: Optional[str] = None
    created_at: Optional[str] = None


class RelationOptimized(BaseModel):
    source: str
    target: str
    relationType: str
    tenant_id: Optional[str] = None


class KnowledgeGraphOptimized(BaseModel):
    entities: List[EntityOptimized]
    relations: List[RelationOptimized]
    pagination: Optional[Dict[str, Any]] = None


class ObservationAdditionOptimized(BaseModel):
    entityName: str
    observations: List[str]
    tenant_id: Optional[str] = None


class ObservationDeletionOptimized(BaseModel):
    entityName: str
    observations: List[str]
    tenant_id: Optional[str] = None


class Neo4jMemoryOptimized:
    """Versión optimizada de Neo4jMemory con multi-tenancy, paginación y límites"""
    
    def __init__(self, neo4j_driver: AsyncDriver):
        self.driver = neo4j_driver

    async def create_indexes(self):
        """Crea índices necesarios para performance"""
        async with self.driver.session() as session:
            try:
                # Índice para tenant_id
                if config.enable_tenant:
                    await session.run("""
                        CREATE INDEX memory_tenant_idx IF NOT EXISTS
                        FOR (m:Memory) ON (m.tenant_id)
                    """)
                    logger.info("Created tenant index")
                
                # Índice compuesto para búsquedas
                await session.run("""
                    CREATE INDEX memory_search_idx IF NOT EXISTS
                    FOR (m:Memory) ON (m.name, m.type)
                """)
                
                # Índice fulltext
                await session.run("""
                    CREATE FULLTEXT INDEX search IF NOT EXISTS 
                    FOR (m:Memory) ON EACH [m.name, m.type, m.observations]
                """)
                
                logger.info("Indexes created/verified")
                
            except Exception as e:
                logger.debug(f"Index creation: {e}")

    async def search_memories_optimized(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        max_level: Optional[int] = None,
        node_limit: Optional[int] = None,
        rel_limit: Optional[int] = None,
        props_keep: Optional[List[str]] = None,
        cursor: Optional[str] = None,
        page_size: Optional[int] = None,
        simple_mode: bool = False
    ) -> KnowledgeGraphOptimized:
        """
        Búsqueda optimizada con multi-tenancy, paginación y límites
        """
        
        # Aplicar defaults desde config
        tenant_id = TenantManager.get_tenant_id(tenant_id)
        max_level = max_level or config.default_max_level
        node_limit = node_limit or config.default_node_limit
        rel_limit = rel_limit or config.default_rel_limit
        page_size = page_size or config.default_page_size
        
        # Decodificar cursor para paginación
        pagination_info = PaginationManager.decode_cursor(cursor)
        skip = pagination_info["skip"]
        
        logger.info(f"Searching memories: query='{query}', tenant='{tenant_id}', skip={skip}, page_size={page_size}")
        
        try:
            # Elegir query según el modo
            if simple_mode or max_level <= 1:
                cypher = QueryOptimizer.build_simple_search_query(
                    query=query,
                    tenant_id=tenant_id,
                    skip=skip,
                    page_size=page_size
                )
            else:
                cypher = QueryOptimizer.build_search_query(
                    query=query,
                    tenant_id=tenant_id,
                    max_level=max_level,
                    node_limit=node_limit,
                    rel_limit=rel_limit,
                    skip=skip,
                    page_size=page_size
                )
            
            # Ejecutar query con timeout
            async with self.driver.session() as session:
                result = await session.run(cypher, {
                    "query": query,
                    "tenant": tenant_id
                })
                
                record = await result.single()
                
                if not record:
                    return KnowledgeGraphOptimized(
                        entities=[],
                        relations=[],
                        pagination={
                            "total_count": 0,
                            "page_size": page_size,
                            "current_page": 1,
                            "total_pages": 0,
                            "has_next": False,
                            "has_prev": False
                        }
                    )
                
                # Procesar resultados
                primary_nodes = record.get("primary_nodes", [])
                related_nodes = record.get("related_nodes", [])
                relationships = record.get("relationships", [])
                total_count = record.get("total_count", 0)
                
                # Convertir a formato KnowledgeGraph
                graph_data = PaginationManager.create_knowledge_graph_from_paginated_data(
                    primary_nodes, related_nodes, relationships
                )
                
                # Filtrar propiedades si se especifica
                if props_keep:
                    graph_data["entities"] = QueryOptimizer.filter_node_properties(
                        graph_data["entities"], props_keep
                    )
                
                # Crear entidades y relaciones optimizadas
                entities = []
                for entity_data in graph_data["entities"]:
                    entities.append(EntityOptimized(
                        name=entity_data.get("name", ""),
                        type=entity_data.get("type", ""),
                        observations=entity_data.get("observations", []),
                        tenant_id=tenant_id
                    ))
                
                relations = []
                for rel_data in graph_data["relations"]:
                    relations.append(RelationOptimized(
                        source=rel_data.get("source", ""),
                        target=rel_data.get("target", ""),
                        relationType=rel_data.get("relationType", ""),
                        tenant_id=tenant_id
                    ))
                
                # Construir respuesta con paginación
                paginated_response = PaginationManager.build_pagination_response(
                    entities=entities,
                    relations=relations[:rel_limit],  # Aplicar límite
                    total_count=total_count,
                    current_skip=skip,
                    page_size=page_size
                )
                
                return KnowledgeGraphOptimized(
                    entities=paginated_response["entities"],
                    relations=paginated_response["relations"],
                    pagination=paginated_response["pagination"]
                )
                
        except Exception as e:
            logger.error(f"Error in optimized search: {e}")
            # Fallback a búsqueda simple
            return await self._fallback_search(query, tenant_id)

    async def _fallback_search(self, query: str, tenant_id: str) -> KnowledgeGraphOptimized:
        """Búsqueda de respaldo en caso de error"""
        try:
            # Query muy simple como fallback
            simple_query = """
            MATCH (m:Memory)
            WHERE m.name CONTAINS $query OR m.type CONTAINS $query
            AND (m.tenant_id = $tenant OR $tenant = 'global')
            RETURN m
            LIMIT 10
            """
            
            async with self.driver.session() as session:
                result = await session.run(simple_query, {
                    "query": query,
                    "tenant": tenant_id
                })
                
                entities = []
                async for record in result:
                    node = record["m"]
                    entities.append(EntityOptimized(
                        name=node.get("name", ""),
                        type=node.get("type", ""),
                        observations=node.get("observations", []),
                        tenant_id=tenant_id
                    ))
                
                return KnowledgeGraphOptimized(
                    entities=entities,
                    relations=[],
                    pagination={
                        "total_count": len(entities),
                        "page_size": 10,
                        "current_page": 1,
                        "total_pages": 1,
                        "has_next": False,
                        "has_prev": False
                    }
                )
                
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return KnowledgeGraphOptimized(entities=[], relations=[], pagination=None)

    async def create_entities_optimized(
        self, 
        entities: List[EntityOptimized],
        tenant_id: Optional[str] = None
    ) -> List[EntityOptimized]:
        """Crear entidades con soporte de tenant"""
        
        tenant_id = TenantManager.get_tenant_id(tenant_id)
        created = []
        
        async with self.driver.session() as session:
            for entity in entities:
                # Agregar tenant_id y timestamp
                entity_data = {
                    "name": entity.name,
                    "type": entity.type,
                    "observations": entity.observations,
                    "tenant_id": tenant_id,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                result = await session.run("""
                    MERGE (m:Memory {name: $name, tenant_id: $tenant_id})
                    SET m += $properties
                    RETURN m
                """, {
                    "name": entity.name,
                    "tenant_id": tenant_id,
                    "properties": entity_data
                })
                
                record = await result.single()
                if record:
                    node = record["m"]
                    created.append(EntityOptimized(
                        name=node.get("name", ""),
                        type=node.get("type", ""),
                        observations=node.get("observations", []),
                        tenant_id=tenant_id,
                        created_at=node.get("created_at")
                    ))
        
        logger.info(f"Created {len(created)} entities for tenant '{tenant_id}'")
        return created

    async def create_relations_optimized(
        self,
        relations: List[RelationOptimized],
        tenant_id: Optional[str] = None
    ) -> List[RelationOptimized]:
        """Crear relaciones con soporte de tenant"""
        
        tenant_id = TenantManager.get_tenant_id(tenant_id)
        created = []
        
        async with self.driver.session() as session:
            for relation in relations:
                result = await session.run(f"""
                    MATCH (source:Memory {{name: $source, tenant_id: $tenant_id}})
                    MATCH (target:Memory {{name: $target, tenant_id: $tenant_id}})
                    MERGE (source)-[r:{relation.relationType}]->(target)
                    SET r.tenant_id = $tenant_id
                    SET r.created_at = $created_at
                    RETURN r, source.name as source_name, target.name as target_name
                """, {
                    "source": relation.source,
                    "target": relation.target,
                    "tenant_id": tenant_id,
                    "created_at": datetime.utcnow().isoformat()
                })
                
                record = await result.single()
                if record:
                    created.append(RelationOptimized(
                        source=record["source_name"],
                        target=record["target_name"],
                        relationType=relation.relationType,
                        tenant_id=tenant_id
                    ))
        
        logger.info(f"Created {len(created)} relations for tenant '{tenant_id}'")
        return created

    async def read_graph_optimized(
        self,
        tenant_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> KnowledgeGraphOptimized:
        """Leer grafo completo con límites y tenant"""
        
        tenant_id = TenantManager.get_tenant_id(tenant_id)
        limit = limit or config.default_node_limit
        
        # Query optimizada para leer grafo completo
        query = """
        MATCH (m:Memory)
        WHERE m.tenant_id = $tenant OR $tenant = 'global'
        WITH m
        LIMIT $limit
        
        OPTIONAL MATCH (m)-[r]-(other:Memory)
        WHERE other.tenant_id = $tenant OR $tenant = 'global'
        
        RETURN collect(DISTINCT m) as nodes,
               collect(DISTINCT r) as relations
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {
                "tenant": tenant_id,
                "limit": limit
            })
            
            record = await result.single()
            if not record:
                return KnowledgeGraphOptimized(entities=[], relations=[])
            
            # Procesar nodos
            entities = []
            for node in record.get("nodes", []):
                entities.append(EntityOptimized(
                    name=node.get("name", ""),
                    type=node.get("type", ""),
                    observations=node.get("observations", []),
                    tenant_id=tenant_id
                ))
            
            # Procesar relaciones
            relations = []
            for rel in record.get("relations", []):
                if rel:
                    relations.append(RelationOptimized(
                        source=rel.start_node.get("name", ""),
                        target=rel.end_node.get("name", ""),
                        relationType=rel.type,
                        tenant_id=tenant_id
                    ))
            
            return KnowledgeGraphOptimized(
                entities=entities,
                relations=relations
            )