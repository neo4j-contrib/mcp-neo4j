"""
Optimizador de queries para reducir tokens y mejorar performance
"""
from typing import Optional, List, Dict, Any
import base64
import json
from ..config import config


class QueryOptimizer:
    """Optimiza queries para reducir tokens y mejorar performance"""
    
    @staticmethod
    def build_search_query(
        query: str,
        tenant_id: str,
        max_level: int,
        node_limit: int,
        rel_limit: int,
        skip: int = 0,
        page_size: int = 50
    ) -> str:
        """Construye query optimizada para search_memories"""
        
        # Si multi-tenancy está deshabilitado, no usar filtro de tenant
        tenant_filter = ""
        if config.enable_tenant:
            tenant_filter = "AND m.tenant_id = $tenant"
        
        return f"""
        // Fase 1: Búsqueda inicial con límites y paginación
        CALL db.index.fulltext.queryNodes('search', $query) YIELD node as m, score
        WHERE 1=1 {tenant_filter}
        WITH m, score
        ORDER BY score DESC, m.name ASC
        SKIP {skip}
        LIMIT {page_size}
        
        // Fase 2: Expandir grafo con nivel controlado
        OPTIONAL MATCH path = (m)-[*1..{max_level}]-(connected:Memory)
        WHERE connected.tenant_id = $tenant OR $tenant = 'global'
        WITH m, 
             collect(DISTINCT connected)[0..{node_limit}] as connected_nodes,
             collect(DISTINCT relationships(path))[0..{rel_limit}] as path_rels
        
        // Fase 3: Contar total para paginación
        WITH m, connected_nodes, path_rels,
             size([(total:Memory) WHERE 
               (total.name CONTAINS $query OR 
                total.type CONTAINS $query OR
                any(obs IN total.observations WHERE obs CONTAINS $query))
               AND (total.tenant_id = $tenant OR $tenant = 'global')
             | total]) as total_count
        
        // Fase 4: Retornar estructura optimizada
        RETURN 
            collect(DISTINCT m) as primary_nodes,
            apoc.coll.flatten(collect(connected_nodes)) as related_nodes,
            apoc.coll.flatten(collect(path_rels)) as relationships,
            max(total_count) as total_count,
            {skip} as current_skip,
            {page_size} as page_size
        """
    
    @staticmethod
    def build_simple_search_query(
        query: str,
        tenant_id: str,
        skip: int = 0,
        page_size: int = 50
    ) -> str:
        """Query simple sin expansión de grafo para mejor performance"""
        
        tenant_filter = ""
        if config.enable_tenant:
            tenant_filter = "AND m.tenant_id = $tenant"
        
        return f"""
        // Búsqueda directa con fulltext index
        CALL db.index.fulltext.queryNodes('search', $query) YIELD node as m, score
        WHERE 1=1 {tenant_filter}
        WITH m, score
        ORDER BY score DESC, m.name ASC
        SKIP {skip}
        LIMIT {page_size}
        
        // Obtener relaciones directas únicamente
        OPTIONAL MATCH (m)-[r]-(other:Memory)
        WHERE other.tenant_id = $tenant OR $tenant = 'global'
        
        // Contar total
        WITH m, collect(DISTINCT r) as relations, collect(DISTINCT other) as others,
             size([(total:Memory) WHERE 
               (total.name CONTAINS $query OR 
                total.type CONTAINS $query OR
                any(obs IN total.observations WHERE obs CONTAINS $query))
               AND (total.tenant_id = $tenant OR $tenant = 'global')
             | total]) as total_count
        
        RETURN 
            collect(DISTINCT m) as primary_nodes,
            apoc.coll.flatten(collect(others)) as related_nodes,
            apoc.coll.flatten(collect(relations)) as relationships,
            max(total_count) as total_count
        """
    
    @staticmethod
    def filter_node_properties(
        nodes: List[Dict],
        props_keep: Optional[List[str]] = None
    ) -> List[Dict]:
        """Filtra propiedades de nodos para reducir tokens"""
        
        if not props_keep:
            # Propiedades default para minimizar tokens
            props_keep = ["name", "type", "tenant_id"]
        
        filtered_nodes = []
        for node in nodes:
            if isinstance(node, dict):
                filtered_node = {
                    prop: node.get(prop) 
                    for prop in props_keep 
                    if prop in node
                }
                # Agregar summary si observations es muy largo
                if "observations" in node and "observations" not in props_keep:
                    obs = node.get("observations", [])
                    if isinstance(obs, list) and len(obs) > 0:
                        # Solo el primer observation y truncado
                        filtered_node["observations_summary"] = obs[0][:100] + "..." if len(obs[0]) > 100 else obs[0]
                        filtered_node["observations_count"] = len(obs)
                
                filtered_nodes.append(filtered_node)
            else:
                # Si es un objeto Neo4j, convertir a dict primero
                try:
                    node_dict = dict(node)
                    filtered_node = {
                        prop: node_dict.get(prop) 
                        for prop in props_keep 
                        if prop in node_dict
                    }
                    filtered_nodes.append(filtered_node)
                except:
                    # Si no se puede convertir, agregar tal como está
                    filtered_nodes.append(node)
        
        return filtered_nodes
    
    @staticmethod
    def optimize_response_size(response: Dict[str, Any], max_tokens: int = 2000) -> Dict[str, Any]:
        """Optimiza el tamaño de la respuesta para mantenerse bajo límite de tokens"""
        
        # Estimación básica: ~4 caracteres por token
        estimated_chars = len(str(response)) 
        estimated_tokens = estimated_chars / 4
        
        if estimated_tokens <= max_tokens:
            return response
        
        # Si es muy grande, reducir progresivamente
        optimized = response.copy()
        
        # 1. Limitar observations a resumen
        if "entities" in optimized:
            for entity in optimized["entities"]:
                if "observations" in entity and len(entity["observations"]) > 1:
                    entity["observations"] = [entity["observations"][0][:50] + "..."]
        
        # 2. Limitar número de relaciones
        if "relations" in optimized and len(optimized["relations"]) > 50:
            optimized["relations"] = optimized["relations"][:50]
            optimized["_truncated"] = True
        
        # 3. Limitar número de entidades  
        if "entities" in optimized and len(optimized["entities"]) > 25:
            optimized["entities"] = optimized["entities"][:25]
            optimized["_truncated"] = True
        
        return optimized