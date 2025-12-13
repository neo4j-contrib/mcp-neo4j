"""
Aura Sizing Service

Service that performs sizing calculations and growth projections.
"""

from typing import Optional, List
from .calculator import Neo4jSizingCalculator
from .interfaces import SizingCalculatorProtocol
from .projector import GrowthProjector
from .growth_models import get_growth_model
from .models import (
    SizingResult,
    ForecastResult,
    SizingCalculations,
    YearProjection,
    SizingMetadata,
)
from .utils import get_logger

logger = get_logger(__name__)


class AuraSizingService:
    """Service for database sizing calculations and forecasting."""
    
    def __init__(self, calculator: Optional[SizingCalculatorProtocol] = None):
        """
        Initialize the sizing service.
        
        Args:
            calculator: Sizing calculator implementation. If None, uses Neo4jSizingCalculator by default.
        """
        self._calculator = calculator or Neo4jSizingCalculator()
    
    def calculate_sizing(
        self,
        # Graph metrics
        num_nodes: int,
        num_relationships: int,
        avg_properties_per_node: int,
        avg_properties_per_relationship: int,
        total_num_large_node_properties: Optional[int] = None,
        total_num_large_reltype_properties: Optional[int] = None,
        
        # Vector metrics
        vector_index_dimensions: Optional[int] = None,
        percentage_nodes_with_vector_properties: Optional[float] = None,
        number_of_vector_indexes: Optional[int] = None,
        
        # Optional overrides
        quantization_enabled: bool = False,
        memory_to_storage_ratio: Optional[float] = None,
        concurrent_end_users: Optional[int] = None,
    ) -> SizingResult:
        """
        Calculate current database sizing based on graph metrics.
        
        Args:
            num_nodes: Number of nodes
            num_relationships: Number of relationships
            avg_properties_per_node: Average properties per node (REQUIRED)
            avg_properties_per_relationship: Average properties per relationship (REQUIRED)
            total_num_large_node_properties: Total number of large properties (128+ bytes) across all nodes (default: 0)
            total_num_large_reltype_properties: Total number of large properties (128+ bytes) across all relationships (default: 0)
            vector_index_dimensions: Vector index dimensions (default: 0 if not using)
            percentage_nodes_with_vector_properties: Percentage of nodes with vector properties 0-100 (default: 0.0)
            number_of_vector_indexes: Number of vector indexes (default: 0)
            quantization_enabled: Enable scalar quantization for vectors (4x storage reduction)
            memory_to_storage_ratio: Memory-to-storage ratio denominator (1=1:1, 2=1:2, 4=1:4, 8=1:8). 
                                     If provided, calculates recommended_memory_gb. Default: None (no memory calculation)
            concurrent_end_users: Number of concurrent end users. If provided, calculates recommended_vcpus (2 vCPU per user).
                                  Default: None (no vCPU calculation)
            
        Returns:
            Sizing result with calculations and metadata (no projections)
        """
        # Convert None to sensible defaults for optional parameters
        # Note: avg_properties_per_node and avg_properties_per_relationship are now required
        total_num_large_node_properties = total_num_large_node_properties if total_num_large_node_properties is not None else 0
        total_num_large_reltype_properties = total_num_large_reltype_properties if total_num_large_reltype_properties is not None else 0
        
        # Vector metrics default to 0 (not using vectors)
        vector_index_dimensions = vector_index_dimensions if vector_index_dimensions is not None else 0
        percentage_nodes_with_vector_properties = percentage_nodes_with_vector_properties if percentage_nodes_with_vector_properties is not None else 0.0
        number_of_vector_indexes = number_of_vector_indexes if number_of_vector_indexes is not None else 0
        
        # Validate required parameters (after None conversion)
        if num_nodes < 0:
            raise ValueError("num_nodes must be non-negative")
        if num_relationships < 0:
            raise ValueError("num_relationships must be non-negative")
        
        # Validate property counts
        if avg_properties_per_node < 0:
            raise ValueError("avg_properties_per_node must be non-negative")
        if avg_properties_per_relationship < 0:
            raise ValueError("avg_properties_per_relationship must be non-negative")
        if total_num_large_node_properties < 0:
            raise ValueError("total_num_large_node_properties must be non-negative")
        if total_num_large_reltype_properties < 0:
            raise ValueError("total_num_large_reltype_properties must be non-negative")
        
        # Validate vector parameters
        if vector_index_dimensions < 0:
            raise ValueError("vector_index_dimensions must be non-negative")
        if vector_index_dimensions > 0:
            # Common vector dimensions: 384, 512, 768, 1024, 1536
            if vector_index_dimensions not in [384, 512, 768, 1024, 1536]:
                logger.warning(f"Unusual vector dimension: {vector_index_dimensions}. Common values are 384, 512, 768, 1024, 1536")
        if percentage_nodes_with_vector_properties < 0 or percentage_nodes_with_vector_properties > 100:
            raise ValueError("percentage_nodes_with_vector_properties must be between 0 and 100")
        if number_of_vector_indexes < 0:
            raise ValueError("number_of_vector_indexes must be non-negative")
        
        # Validate memory_to_storage_ratio if provided
        if memory_to_storage_ratio is not None:
            if memory_to_storage_ratio not in [1.0, 2.0, 4.0, 8.0]:
                raise ValueError("memory_to_storage_ratio must be 1.0 (1:1), 2.0 (1:2), 4.0 (1:4), or 8.0 (1:8)")
        
        # Validate concurrent_end_users if provided
        if concurrent_end_users is not None and concurrent_end_users < 0:
            raise ValueError("concurrent_end_users must be non-negative")
        
        # Calculate database sizes using the injected calculator
        calculation_result = self._calculator.calculate(
            num_nodes=num_nodes,
            num_relationships=num_relationships,
            avg_properties_per_node=avg_properties_per_node,
            avg_properties_per_relationship=avg_properties_per_relationship,
            total_num_large_node_properties=total_num_large_node_properties,
            total_num_large_reltype_properties=total_num_large_reltype_properties,
            vector_index_dimensions=vector_index_dimensions,
            percentage_nodes_with_vector_properties=percentage_nodes_with_vector_properties,
            number_of_vector_indexes=number_of_vector_indexes,
            quantization_enabled=quantization_enabled,
            memory_to_storage_ratio=memory_to_storage_ratio if memory_to_storage_ratio is not None else 1.0,
            concurrent_end_users=concurrent_end_users if concurrent_end_users is not None else 0,
        )
        
        # Convert Neo4jSizingCalculationResult to SizingCalculations
        calculations = SizingCalculations(**calculation_result.model_dump())
        
        # Get calculator type name for metadata
        calculator_type = self._calculator.__class__.__name__
        
        # Extract key configuration that affects the calculation
        calculation_config = {
            "quantization_enabled": quantization_enabled,
        }
        if vector_index_dimensions > 0:
            calculation_config["vector_index_dimensions"] = vector_index_dimensions
            calculation_config["number_of_vector_indexes"] = number_of_vector_indexes
            calculation_config["percentage_nodes_with_vector_properties"] = percentage_nodes_with_vector_properties
        if memory_to_storage_ratio is not None:
            calculation_config["memory_to_storage_ratio"] = memory_to_storage_ratio
        if concurrent_end_users is not None:
            calculation_config["concurrent_end_users"] = concurrent_end_users
        
        return SizingResult(
            calculations=calculations,
            metadata=SizingMetadata(
                calculator_type=calculator_type,
                calculation_config=calculation_config,
            ),
        )
    
    def forecast_sizing(
        self,
        base_size_gb: float,
        base_memory_gb: int,
        base_cores: int,
        annual_growth_rate: float = 10.0,
        projection_years: int = 3,
        workloads: Optional[List[str]] = None,
        domain: Optional[str] = None,
        memory_to_storage_ratio: float = 1.0,
    ) -> ForecastResult:
        """
        Forecast database growth over multiple years.
        
        Args:
            base_size_gb: Current database size in GB
            base_memory_gb: Current recommended memory in GB
            base_cores: Current recommended number of cores
            annual_growth_rate: Annual growth rate percentage (default: 10%)
            projection_years: Number of years to project (default: 3)
            workloads: List of workload types (transactional, agentic, analytical, graph_data_science)
                      If provided, overrides domain defaults
            domain: Graph domain (customer, product, etc.) - used to infer default workloads if workloads not provided
            memory_to_storage_ratio: Memory-to-storage ratio denominator (1=1:1, 2=1:2, 4=1:4, 8=1:8). Default: 1 (1:1 ratio)
            
        Returns:
            Forecast result with multi-year projections
        """
        # Validate inputs
        if base_size_gb < 0:
            raise ValueError("base_size_gb must be non-negative")
        if base_memory_gb < 0:
            raise ValueError("base_memory_gb must be non-negative")
        if base_cores < 0:
            raise ValueError("base_cores must be non-negative")
        if annual_growth_rate < 0:
            raise ValueError("annual_growth_rate must be non-negative")
        if annual_growth_rate > 1000:
            raise ValueError("annual_growth_rate seems unreasonably high (>1000%). Please verify the value.")
        if projection_years < 1:
            raise ValueError("projection_years must be at least 1")
        if projection_years > 20:
            raise ValueError("projection_years exceeds reasonable limit (20 years). Please use a value <= 20")
        # Validate memory_to_storage_ratio
        if memory_to_storage_ratio not in [1.0, 2.0, 4.0, 8.0]:
            raise ValueError("memory_to_storage_ratio must be 1.0 (1:1), 2.0 (1:2), 4.0 (1:4), or 8.0 (1:8)")
        
        # Project growth using workload-based model
        projections_list = GrowthProjector.project(
            base_size_gb=base_size_gb,
            annual_growth_rate=annual_growth_rate,
            projection_years=projection_years,
            base_memory_gb=base_memory_gb,
            base_cores=base_cores,
            workloads=workloads,
            domain=domain,
            memory_to_storage_ratio=memory_to_storage_ratio,
        )
        projections = [YearProjection(**p) for p in projections_list]
        
        # Get the growth model name for reference
        growth_model = get_growth_model(workloads=workloads, domain=domain)
        growth_model_name = growth_model.__class__.__name__
        
        return ForecastResult(
            base_size_gb=base_size_gb,
            base_memory_gb=base_memory_gb,
            base_cores=base_cores,
            projections=projections,
            growth_model_used=growth_model_name,
        )
