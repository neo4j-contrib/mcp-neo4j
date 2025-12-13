"""
Pydantic models for Aura sizing calculations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Neo4jSizingCalculationResult(BaseModel):
    """Standard structure for Neo4j sizing calculation results.
    
    This is the result structure returned by Neo4jSizingCalculator.
    All calculators should return this structure.
    """
    size_of_nodes_gb: float = Field(..., description="Size of nodes in GB")
    size_of_relationships_gb: float = Field(..., description="Size of relationships in GB")
    size_of_properties_gb: float = Field(..., description="Size of properties in GB")
    size_of_vector_indexes_gb: float = Field(..., description="Size of vector indexes in GB")
    total_size_without_indexes_gb: float = Field(..., description="Total size without indexes in GB")
    size_of_non_vector_indexes_gb: float = Field(..., description="Size of non-vector indexes in GB")
    total_size_with_indexes_gb: float = Field(..., description="Total size with all indexes in GB")
    recommended_memory_gb: int = Field(..., description="Recommended memory in GB (defaults to 1:1 ratio if memory_to_storage_ratio not provided)")
    recommended_vcpus: int = Field(..., description="Recommended vCPUs (defaults to 1, or 2 vCPU per concurrent_end_users if provided)")


class YearProjection(BaseModel):
    """Projection for a specific year."""
    year: int = Field(..., description="Year number (1, 2, 3, etc.)")
    total_size_gb: float = Field(..., description="Total database size in GB for this year")
    recommended_memory_gb: int = Field(..., description="Recommended memory in GB")
    recommended_cores: int = Field(..., description="Recommended number of cores")
    scaling_needed: bool = Field(..., description="Whether scaling is needed compared to previous year")


class SizingCalculations(BaseModel):
    """Detailed sizing calculations."""
    size_of_nodes_gb: float = Field(..., description="Size of nodes in GB")
    size_of_relationships_gb: float = Field(..., description="Size of relationships in GB")
    size_of_properties_gb: float = Field(..., description="Size of properties in GB")
    size_of_vector_indexes_gb: float = Field(..., description="Size of vector indexes in GB")
    total_size_without_indexes_gb: float = Field(..., description="Total size without indexes in GB")
    size_of_non_vector_indexes_gb: float = Field(..., description="Size of non-vector indexes in GB")
    total_size_with_indexes_gb: float = Field(..., description="Total size with all indexes in GB")
    recommended_memory_gb: int = Field(..., description="Recommended memory in GB (defaults to 1:1 ratio with storage)")
    recommended_vcpus: int = Field(..., description="Recommended vCPUs (defaults to 1, or 2 vCPU per concurrent_end_users if provided)")


class SizingMetadata(BaseModel):
    """Metadata about how the sizing was calculated."""
    calculator_type: str = Field(..., description="Type of calculator used (e.g., 'Neo4jSizingCalculator')")
    calculation_config: dict = Field(..., description="Key configuration used (e.g., quantization_enabled, vector_dimensions)")


class SizingResult(BaseModel):
    """Complete sizing calculation result (current size only, no projections)."""
    calculations: SizingCalculations = Field(..., description="Detailed calculations")
    metadata: SizingMetadata = Field(..., description="Calculation metadata")


class ForecastResult(BaseModel):
    """Forecast result with multi-year projections."""
    base_size_gb: float = Field(..., description="Base database size in GB")
    base_memory_gb: int = Field(..., description="Base recommended memory in GB")
    base_cores: int = Field(..., description="Base recommended number of cores")
    projections: List[YearProjection] = Field(..., description="Multi-year projections")
    growth_model_used: str = Field(..., description="Growth model used for projections")
