"""
Interfaces for sizing calculator components.

Defines protocols/abstract base classes for extensible sizing calculator architecture.
"""

from typing import Protocol, Dict, Any

from .models import Neo4jSizingCalculationResult


class SizingCalculatorProtocol(Protocol):
    """Protocol defining the interface for sizing calculators.
    
    Any class implementing this protocol can be used as a sizing calculator.
    This allows for multiple calculator implementations with different input requirements.
    
    Calculators are free to accept any parameters they need via **kwargs, making the
    protocol flexible enough to support various calculation methods while maintaining
    a consistent output format.
    """
    
    def calculate(self, **kwargs: Any) -> Neo4jSizingCalculationResult:
        """
        Calculate database sizes based on graph metrics.
        
        Each calculator implementation can define its own required and optional parameters.
        The service layer is responsible for passing the appropriate parameters to each calculator.
        
        Args:
            **kwargs: Calculator-specific parameters. Common parameters may include:
                - num_nodes: Number of nodes
                - num_relationships: Number of relationships
                - avg_properties_per_node: Average properties per node
                - avg_properties_per_relationship: Average properties per relationship
                - total_num_large_node_properties: Total number of large properties (128+ bytes) across all nodes
                - total_num_large_reltype_properties: Total number of large properties (128+ bytes) across all relationships
                - vector_index_dimensions: Vector index dimensions
                - percentage_nodes_with_vector_properties: Percentage of nodes with vector properties (0-100)
                - number_of_vector_indexes: Number of vector indexes
                - quantization_enabled: Enable scalar quantization for vectors (4x storage reduction)
                - memory_to_storage_ratio: Memory-to-storage ratio denominator (1=1:1, 2=1:2, 4=1:4, 8=1:8)
                - concurrent_end_users: Number of concurrent end users (for vCPU calculation: 2 vCPU per user)
                - Any other calculator-specific parameters
            
        Returns:
            Dictionary with calculated sizes in GB. Must include at least the keys defined
            in Neo4jSizingCalculationResult. Additional calculator-specific keys are allowed.
            
            Required keys:
            - size_of_nodes_gb: float
            - size_of_relationships_gb: float
            - size_of_properties_gb: float
            - size_of_vector_indexes_gb: float
            - total_size_without_indexes_gb: float
            - size_of_non_vector_indexes_gb: float
            - total_size_with_indexes_gb: float
            - recommended_memory_gb: int (always calculated, defaults to 1:1 ratio)
            - recommended_vcpus: int (always calculated, defaults to 1)
        """
        ...

