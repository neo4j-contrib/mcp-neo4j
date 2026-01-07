"""
Growth Projector

Projects database growth over multiple years using use-case-specific growth models.
Supports different growth patterns for transactional, analytical, and agentic/RAG use cases.
"""

from typing import List, Dict, Any, Optional
from .growth_models import (
    get_growth_model,
    GrowthModel,
    )
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
        growth_model: Optional[GrowthModel] = None,
        memory_to_storage_ratio: int = 1,
        **growth_model_kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Project database growth over multiple years.
        
        Args:
            base_size_gb: Base database size in GB (year 0)
            annual_growth_rate: Annual growth rate as percentage (e.g., 10.0 for 10%)
            projection_years: Number of years to project
            base_memory_gb: Base recommended memory in GB
            base_cores: Base recommended cores
            workloads: List of workload types (transactional, agentic, analytical, graph_data_science)
            domain: Graph domain (customer, product, etc.) - informational
            growth_model: Optional explicit growth model (overrides workloads)
            memory_to_storage_ratio: Memory-to-storage ratio denominator (1=1:1, 2=1:2, 4=1:4, 8=1:8). Default: 1 (1:1 ratio)
            **growth_model_kwargs: Additional parameters for growth models
                (e.g., carrying_capacity_multiplier for logistic, vector_growth_multiplier for RAG)
            
        Returns:
            List of year projections
        """
        # Select growth model
        if growth_model is None:
            growth_model = get_growth_model(workloads=workloads, domain=domain)
        
        projections = []
        previous_size = base_size_gb
        
        for year in range(1, projection_years + 1):
            # Calculate projected size using selected growth model
            current_size = growth_model.calculate(
                base_size_gb=base_size_gb,
                annual_growth_rate=annual_growth_rate,
                year=year,
                **growth_model_kwargs,
            )
            
            # Determine if scaling is needed
            # Scaling needed if size grows >50% from base or >20% from previous year
            scaling_needed = (
                current_size > (base_size_gb * 1.5) or
                current_size > (previous_size * 1.2)
            )
            
            # Calculate recommended memory based on projected size and memory-to-storage ratio
            # Ratio represents the denominator: 1 = 1:1, 2 = 1:2, 4 = 1:4, 8 = 1:8
            # Memory = Storage / ratio (e.g., with 1:8 ratio, 100GB storage = 12.5GB memory)
            # Memory should never go below base_memory_gb (can't shrink)
            import math
            calculated_memory = math.ceil(current_size / memory_to_storage_ratio)
            recommended_memory_gb = max(base_memory_gb, calculated_memory)
            
            # Keep cores static at base value
            recommended_cores = base_cores
            
            projections.append({
                "year": year,
                "total_size_gb": round(current_size, 2),
                "recommended_memory_gb": recommended_memory_gb,
                "recommended_cores": recommended_cores,
                "scaling_needed": scaling_needed,
            })
            
            previous_size = current_size
        
        return projections

