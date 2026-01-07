"""
Neo4j Sizing Calculator

Calculates database sizes based on graph metrics using Neo4j sizing formulas.
"""

import math
from typing import Optional
from .models import Neo4jSizingCalculationResult
from .utils import get_logger

logger = get_logger(__name__)


class Neo4jSizingCalculator:
    """Calculator for Neo4j database sizing using standard formulas.
    
    Implements SizingCalculatorProtocol for consistent interface.
    """
    
    # Storage overhead constants (from Neo4j sizing sheet)
    BYTES_PER_NODE = 19  # Bytes per node (from sizing sheet)
    BYTES_PER_RELATIONSHIP = 37  # Bytes per relationship (from sizing sheet)
    BYTES_PER_PROPERTY = 41  # Bytes per property (from sizing sheet)
    BYTES_PER_LARGE_PROPERTY = 128  # Bytes per large property (128+ bytes, from sizing sheet)
    
    # Conversion constant
    BYTES_PER_GB = 1_073_741_824  # 1024^3
    
    # Operating system base requirement
    OS_BASE_SIZE_GB = 2.0  # Minimum 2GB for operating system overhead
    
    def calculate(
        self,
        num_nodes: int,
        num_relationships: int,
        avg_properties_per_node: int = 0,
        avg_properties_per_relationship: int = 0,
        total_num_large_node_properties: int = 0,
        total_num_large_reltype_properties: int = 0,
        vector_index_dimensions: int = 0,
        percentage_nodes_with_vector_properties: float = 0.0,
        number_of_vector_indexes: int = 0,
        quantization_enabled: bool = False,
        memory_to_storage_ratio: int = 1,
        concurrent_end_users: int = 0,
    ) -> Neo4jSizingCalculationResult:
        """
        Calculate database sizes based on graph metrics.
        
        Formulas inferred from typical Neo4j storage patterns:
        - Nodes: base node storage + properties
        - Relationships: base relationship storage + properties
        - Indexes: index entries for nodes and relationships
        - Vector indexes: calculated based on dimensions and node count
        
        Args:
            num_nodes: Number of nodes
            num_relationships: Number of relationships
            avg_properties_per_node: Average properties per node
            avg_properties_per_relationship: Average properties per relationship
            total_num_large_node_properties: Total number of large properties (128+ bytes) across all nodes
            total_num_large_reltype_properties: Total number of large properties (128+ bytes) across all relationships
            vector_index_dimensions: Vector index dimensions (0 if not using)
            percentage_nodes_with_vector_properties: Percentage of nodes with vector properties (0-100)
            number_of_vector_indexes: Number of vector indexes
            quantization_enabled: Enable scalar quantization (4x storage reduction for vectors)
            memory_to_storage_ratio: Memory-to-storage ratio denominator (1=1:1, 2=1:2, 4=1:4, 8=1:8). Default: 1.0
                                     If provided, calculates recommended_memory_gb based on total storage.
            concurrent_end_users: Number of concurrent end users. If provided, calculates recommended_vcpus (2 vCPU per user).
            
        Returns:
            Neo4jSizingCalculationResult with calculated sizes in GB, memory and vCPU recommendations
        """
        # Calculate node storage
        # Base node storage: nodes * bytes per node
        node_base_storage_bytes = num_nodes * Neo4jSizingCalculator.BYTES_PER_NODE
        
        # Node properties: nodes * avg properties * bytes per property
        node_properties_bytes = num_nodes * avg_properties_per_node * Neo4jSizingCalculator.BYTES_PER_PROPERTY
        
        # Large properties: total large node properties * bytes per large property
        large_properties_bytes = total_num_large_node_properties * Neo4jSizingCalculator.BYTES_PER_LARGE_PROPERTY
        
        # Total node storage
        size_of_nodes_gb = (node_base_storage_bytes + node_properties_bytes + large_properties_bytes) / Neo4jSizingCalculator.BYTES_PER_GB
        
        # Calculate relationship storage
        # Base relationship storage: relationships * bytes per relationship
        relationship_base_storage_bytes = num_relationships * Neo4jSizingCalculator.BYTES_PER_RELATIONSHIP
        
        # Relationship properties: relationships * avg properties * bytes per property
        relationship_properties_bytes = num_relationships * avg_properties_per_relationship * Neo4jSizingCalculator.BYTES_PER_PROPERTY
        
        # Large relationship properties: total large reltype properties * bytes per large property
        large_relationship_properties_bytes = total_num_large_reltype_properties * Neo4jSizingCalculator.BYTES_PER_LARGE_PROPERTY
        
        # Total relationship storage
        size_of_relationships_gb = (relationship_base_storage_bytes + relationship_properties_bytes + large_relationship_properties_bytes) / Neo4jSizingCalculator.BYTES_PER_GB
        
        # Total properties size (for reporting only - already included in node/relationship sizes)
        size_of_properties_gb = (node_properties_bytes + relationship_properties_bytes + large_properties_bytes + large_relationship_properties_bytes) / Neo4jSizingCalculator.BYTES_PER_GB
        
        # Total size without indexes
        # Note: properties are already included in size_of_nodes_gb and size_of_relationships_gb
        total_size_without_indexes_gb = size_of_nodes_gb + size_of_relationships_gb
        
        # Calculate non-vector indexes
        # Simple heuristic: 15% of total size without indexes (CEILING.MATH)
        # This is a standard estimate for index overhead in Neo4j
        size_of_non_vector_indexes_gb = math.ceil(total_size_without_indexes_gb * 0.15)
        
        # Calculate vector indexes
        size_of_vector_indexes_gb = 0.0
        if vector_index_dimensions > 0 and number_of_vector_indexes > 0 and percentage_nodes_with_vector_properties > 0:
            # Calculate: nodes * (percentage/100) * dimensions * (0.000000004 GB * 2) * number_of_vector_indexes
            # 0.000000004 GB = 4 bytes, * 2 = 8 bytes per dimension
            bytes_per_dimension = 8  # 4 bytes (float32) * 2 (overhead/structure)
            
            # Apply quantization reduction if enabled (4x reduction: int8 vs float32)
            if quantization_enabled:
                bytes_per_dimension = bytes_per_dimension / 4  # 4x reduction for scalar quantization
            
            size_per_dimension_gb = bytes_per_dimension / Neo4jSizingCalculator.BYTES_PER_GB
            
            size_of_vector_indexes_gb = (
                num_nodes * 
                (percentage_nodes_with_vector_properties / 100.0) * 
                vector_index_dimensions * 
                size_per_dimension_gb * 
                number_of_vector_indexes
            )
            # Apply CEILING.MATH (round up)
            size_of_vector_indexes_gb = math.ceil(size_of_vector_indexes_gb)
        
        # Total size with all indexes
        total_size_with_indexes_gb = (
            total_size_without_indexes_gb + 
            size_of_non_vector_indexes_gb + 
            size_of_vector_indexes_gb
        )
        
        # Apply OS base floor (minimum 2GB for operating system)
        total_size_with_indexes_gb = max(total_size_with_indexes_gb, Neo4jSizingCalculator.OS_BASE_SIZE_GB)
        
        # Calculate recommended memory (defaults to 1:1 ratio if not specified)
        # Use provided ratio or default to 1.0 (1:1 ratio)
        effective_memory_ratio = memory_to_storage_ratio if memory_to_storage_ratio is not None and memory_to_storage_ratio > 0 else 1.0
        recommended_memory_gb = math.ceil(total_size_with_indexes_gb / effective_memory_ratio)
        
        # Calculate recommended vCPUs (defaults to 1 if concurrent_end_users not provided)
        # 2 vCPU per concurrent end user, minimum 1
        if concurrent_end_users > 0:
            recommended_vcpus = concurrent_end_users * 2
        else:
            recommended_vcpus = 1  # Default to 1 vCPU (typical for small VM)
        
        # Build and return Pydantic model
        return Neo4jSizingCalculationResult(
            size_of_nodes_gb=round(size_of_nodes_gb, 2),
            size_of_relationships_gb=round(size_of_relationships_gb, 2),
            size_of_properties_gb=round(size_of_properties_gb, 2),
            size_of_vector_indexes_gb=round(size_of_vector_indexes_gb, 2),
            total_size_without_indexes_gb=round(total_size_without_indexes_gb, 2),
            size_of_non_vector_indexes_gb=round(size_of_non_vector_indexes_gb, 2),
            total_size_with_indexes_gb=round(total_size_with_indexes_gb, 2),
            recommended_memory_gb=recommended_memory_gb,
            recommended_vcpus=recommended_vcpus,
        )

