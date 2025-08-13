"""
Gestor de paginación con cursors para MCP-Neo4j-Memory
"""
import base64
import json
from typing import Optional, Dict, Any, List


class PaginationManager:
    """Gestiona paginación con cursors"""
    
    @staticmethod
    def decode_cursor(cursor: Optional[str]) -> Dict[str, Any]:
        """Decodifica cursor de paginación"""
        if not cursor:
            return {"skip": 0, "page": 1}
        
        try:
            decoded = base64.b64decode(cursor).decode('utf-8')
            return json.loads(decoded)
        except:
            return {"skip": 0, "page": 1}
    
    @staticmethod
    def encode_cursor(skip: int, page: int) -> str:
        """Codifica cursor de paginación"""
        cursor_data = {
            "skip": skip,
            "page": page
        }
        cursor_json = json.dumps(cursor_data)
        return base64.b64encode(cursor_json.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def build_pagination_response(
        entities: List[Any],
        relations: List[Any],
        total_count: int,
        current_skip: int,
        page_size: int
    ) -> Dict[str, Any]:
        """Construye respuesta con información de paginación"""
        
        current_page = (current_skip // page_size) + 1
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        has_next = current_skip + page_size < total_count
        has_prev = current_skip > 0
        
        response = {
            "entities": entities,
            "relations": relations,
            "pagination": {
                "total_count": total_count,
                "page_size": page_size,
                "current_page": current_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
        
        if has_next:
            next_skip = current_skip + page_size
            response["pagination"]["next_cursor"] = PaginationManager.encode_cursor(
                next_skip, 
                current_page + 1
            )
        
        if has_prev:
            prev_skip = max(0, current_skip - page_size)
            response["pagination"]["prev_cursor"] = PaginationManager.encode_cursor(
                prev_skip,
                current_page - 1
            )
        
        return response
    
    @staticmethod
    def create_knowledge_graph_from_paginated_data(
        primary_nodes: List[Any],
        related_nodes: List[Any],
        relationships: List[Any]
    ) -> Dict[str, Any]:
        """Convierte datos paginados en formato KnowledgeGraph"""
        
        # Combinar todos los nodos
        all_entities = []
        
        # Procesar nodos primarios
        for node in primary_nodes:
            if hasattr(node, 'get'):
                # Es un dict-like object
                entity_data = {
                    "name": node.get("name", ""),
                    "type": node.get("type", ""),
                    "observations": node.get("observations", [])
                }
            else:
                # Es un objeto Neo4j Node
                entity_data = {
                    "name": node.get("name", ""),
                    "type": node.get("type", ""),
                    "observations": node.get("observations", [])
                }
            all_entities.append(entity_data)
        
        # Procesar nodos relacionados 
        for node in related_nodes:
            if node and hasattr(node, 'get'):
                entity_data = {
                    "name": node.get("name", ""),
                    "type": node.get("type", ""),
                    "observations": node.get("observations", [])
                }
                # Evitar duplicados por nombre
                if not any(e["name"] == entity_data["name"] for e in all_entities):
                    all_entities.append(entity_data)
        
        # Procesar relaciones
        all_relations = []
        for rel in relationships:
            if rel and hasattr(rel, 'type'):
                # Es una relación Neo4j
                relation_data = {
                    "source": rel.start_node.get("name", ""),
                    "target": rel.end_node.get("name", ""), 
                    "relationType": rel.type
                }
                all_relations.append(relation_data)
            elif isinstance(rel, dict):
                # Es un dict con datos de relación
                relation_data = {
                    "source": rel.get("source", ""),
                    "target": rel.get("target", ""),
                    "relationType": rel.get("relationType", "")
                }
                all_relations.append(relation_data)
        
        return {
            "entities": all_entities,
            "relations": all_relations
        }