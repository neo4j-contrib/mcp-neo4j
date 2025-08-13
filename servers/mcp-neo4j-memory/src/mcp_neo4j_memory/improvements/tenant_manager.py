"""
Gestor de multi-tenancy para MCP-Neo4j-Memory
"""
from typing import Optional, Dict, Any
from ..config import config


class TenantManager:
    """Gestiona multi-tenancy para todas las operaciones"""
    
    @staticmethod
    def get_tenant_id(tenant_id: Optional[str] = None) -> str:
        """Obtiene tenant_id o usa default"""
        if not config.enable_tenant:
            return "global"
        return tenant_id or config.default_tenant
    
    @staticmethod
    def inject_tenant_filter(query: str, tenant_var: str = "tenant") -> str:
        """Inyecta filtro de tenant en queries Cypher"""
        if not config.enable_tenant:
            return query
            
        # Buscar WHERE e inyectar tenant
        if "WHERE" in query.upper():
            # Insertar condición de tenant al principio del WHERE
            where_pos = query.upper().find("WHERE")
            before_where = query[:where_pos + 5]  # incluye "WHERE"
            after_where = query[where_pos + 5:].strip()
            
            # Si ya hay condiciones, agregar AND
            if after_where and not after_where.startswith("("):
                return f"{before_where} m.tenant_id = ${tenant_var} AND {after_where}"
            else:
                return f"{before_where} m.tenant_id = ${tenant_var} {after_where}"
        else:
            # Agregar WHERE después del MATCH
            import re
            match_pattern = r'(MATCH\s+.*?\))'
            match_obj = re.search(match_pattern, query, re.IGNORECASE | re.DOTALL)
            
            if match_obj:
                match_part = match_obj.group(1)
                rest_of_query = query[match_obj.end():].strip()
                return f"{match_part} WHERE m.tenant_id = ${tenant_var} {rest_of_query}"
            else:
                # Si no encuentra MATCH, agregar condición al final
                return f"{query} WHERE m.tenant_id = ${tenant_var}"
    
    @staticmethod
    def add_tenant_to_params(params: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Agrega tenant_id a los parámetros de la query"""
        if config.enable_tenant:
            params["tenant"] = TenantManager.get_tenant_id(tenant_id)
        return params
    
    @staticmethod
    def filter_results_by_tenant(results: list, tenant_id: str) -> list:
        """Filtra resultados por tenant (validación extra)"""
        if not config.enable_tenant:
            return results
            
        filtered = []
        for item in results:
            if hasattr(item, 'get') and item.get('tenant_id') == tenant_id:
                filtered.append(item)
            elif hasattr(item, 'tenant_id') and item.tenant_id == tenant_id:
                filtered.append(item)
            else:
                # Si no tiene tenant_id, incluir (retrocompatibilidad)
                filtered.append(item)
        return filtered