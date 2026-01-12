"""
Growth Projector

Projects database growth over multiple years using use-case-specific growth models.
Supports different growth patterns for transactional, analytical, and agentic/RAG use cases.
"""

from typing import List, Dict, Any, Optional
from .growth_models import get_component_growth_models
from .utils import get_logger

logger = get_logger(__name__)


class GrowthProjector:
    """Projects database growth and sizing over multiple years."""
    
    @staticmethod
    def project(
        base_size_gb: float,
        annual_growth_rate: float,
        projection_years: int,
        base_memory_gb: int,
        base_cores: int,
        workloads: Optional[List[str]] = None,
        domain: Optional[str] = None,
        memory_to_storage_ratio: int = 1,
        **growth_model_kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Project database growth over multiple years using component-based growth models.
        
        Each component (storage, memory, vcpu) grows independently according to its own growth model.
        The memory_to_storage_ratio is applied as a constraint (minimum floor) for memory.
        
        Args:
            base_size_gb: Base database size in GB (year 0)
            annual_growth_rate: Annual growth rate as percentage (e.g., 10.0 for 10%)
            projection_years: Number of years to project
            base_memory_gb: Base recommended memory in GB
            base_cores: Base recommended cores
            workloads: List of workload types (transactional, agentic, analytical)
            domain: Graph domain (customer, product, etc.) - primary driver if no workloads
            memory_to_storage_ratio: Memory-to-storage ratio denominator (1=1:1, 2=1:2, 4=1:4, 8=1:8). 
                                     Default: 1 (1:1 ratio). Applied as constraint/floor for memory.
            **growth_model_kwargs: Additional parameters for growth models
                (e.g., carrying_capacity_multiplier for logistic, vector_growth_multiplier for RAG)
            
        Returns:
            List of year projections with storage, memory, and vcpu projections
        """
        import math
        
        # Get component-based growth models
        component_models = get_component_growth_models(workloads=workloads, domain=domain)
        
        projections = []
        previous_size = base_size_gb
        previous_memory = base_memory_gb
        previous_cores = base_cores
        
        for year in range(1, projection_years + 1):
            # Project each component independently using its own growth model
            projected_storage = component_models["storage"].calculate(
                base_size_gb=base_size_gb,
                annual_growth_rate=annual_growth_rate,
                year=year,
                **growth_model_kwargs,
            )
            
            projected_memory = component_models["memory"].calculate(
                base_size_gb=base_memory_gb,  # Use base_memory_gb as base for memory growth
                annual_growth_rate=annual_growth_rate,
                year=year,
                **growth_model_kwargs,
            )
            
            projected_vcpu = component_models["vcpu"].calculate(
                base_size_gb=float(base_cores),  # Use base_cores as base for vcpu growth
                annual_growth_rate=annual_growth_rate,
                year=year,
                **growth_model_kwargs,
            )
            
            # Apply memory_to_storage_ratio as a constraint (minimum floor)
            # Memory must be at least: storage / ratio
            min_memory_from_ratio = math.ceil(projected_storage / memory_to_storage_ratio)
            projected_memory = max(projected_memory, min_memory_from_ratio)
            
            # Ensure no component shrinks (can't go below base values)
            recommended_memory_gb = max(base_memory_gb, math.ceil(projected_memory))
            recommended_cores = max(base_cores, math.ceil(projected_vcpu))
            
            # Determine if scaling is needed
            # Scaling needed if any component grows >50% from base or >20% from previous year
            scaling_needed = (
                projected_storage > (base_size_gb * 1.5) or
                projected_storage > (previous_size * 1.2) or
                recommended_memory_gb > (base_memory_gb * 1.5) or
                recommended_memory_gb > (previous_memory * 1.2) or
                recommended_cores > (base_cores * 1.5) or
                recommended_cores > (previous_cores * 1.2)
            )
            
            projections.append({
                "year": year,
                "total_size_gb": round(projected_storage, 2),
                "recommended_memory_gb": recommended_memory_gb,
                "recommended_cores": recommended_cores,
                "scaling_needed": scaling_needed,
            })
            
            previous_size = projected_storage
            previous_memory = recommended_memory_gb
            previous_cores = recommended_cores
        
        return projections

