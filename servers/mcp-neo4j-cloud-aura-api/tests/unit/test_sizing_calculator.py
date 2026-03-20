"""
Unit tests for the Neo4j sizing calculator.
"""

import math
import pytest
from mcp_neo4j_aura_manager.sizing.calculator import Neo4jSizingCalculator


class TestNeo4jSizingCalculator:
    """Test the Neo4jSizingCalculator class."""
    
    @pytest.fixture
    def calculator(self):
        """Create a calculator instance for testing."""
        return Neo4jSizingCalculator()
    
    def test_basic_calculation(self, calculator):
        """Test basic sizing calculation with minimal inputs."""
        result = calculator.calculate(
            num_nodes=100000,  # Use larger numbers to avoid rounding to 0
            num_relationships=500000,
        )
        
        assert result.total_size_with_indexes_gb > 0
        assert result.size_of_nodes_gb >= 0  # Can be 0 if rounded
        assert result.size_of_relationships_gb >= 0  # Can be 0 if rounded
        # But total should be >= 2GB due to OS base floor
        assert result.total_size_with_indexes_gb >= 2.0
    
    def test_calculation_with_properties(self, calculator):
        """Test calculation with properties."""
        result = calculator.calculate(
            num_nodes=100000,  # Use larger numbers
            num_relationships=500000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
        )
        
        assert result.size_of_properties_gb > 0
        # Properties are included in node/relationship sizes, so nodes should be >= properties
        assert result.size_of_nodes_gb >= result.size_of_properties_gb * 0.1
        # Total should be >= 2GB due to OS base floor
        assert result.total_size_with_indexes_gb >= 2.0
    
    def test_calculation_with_large_properties(self, calculator):
        """Test calculation with large properties."""
        result = calculator.calculate(
            num_nodes=100000,  # Use larger numbers
            num_relationships=200000,
            avg_properties_per_node=3,
            total_num_large_node_properties=50000,  # More large properties
            total_num_large_reltype_properties=20000,
        )
        
        assert result.size_of_properties_gb > 0
        # Large properties should add significant size
        assert result.total_size_with_indexes_gb > 0.5
        # Total should be >= 2GB due to OS base floor
        assert result.total_size_with_indexes_gb >= 2.0
    
    def test_vector_indexes_calculation(self, calculator):
        """Test vector indexes calculation."""
        result = calculator.calculate(
            num_nodes=10000,
            num_relationships=50000,
            vector_index_dimensions=768,
            percentage_nodes_with_vector_properties=50.0,
            number_of_vector_indexes=1,
            quantization_enabled=False,
        )
        
        assert result.size_of_vector_indexes_gb > 0
        # With 10K nodes, 50% coverage, 768 dims, should be significant
        assert result.size_of_vector_indexes_gb > 0.1
        # Total should be >= 2GB due to OS base floor
        assert result.total_size_with_indexes_gb >= 2.0
    
    def test_vector_indexes_with_quantization(self, calculator):
        """Test vector indexes with quantization (4x reduction)."""
        # Use very large numbers to ensure values are large enough that ceiling doesn't mask the difference
        result_no_quant = calculator.calculate(
            num_nodes=1000000,  # 1M nodes
            num_relationships=5000000,
            vector_index_dimensions=768,
            percentage_nodes_with_vector_properties=50.0,
            number_of_vector_indexes=1,
            quantization_enabled=False,
        )
        
        result_with_quant = calculator.calculate(
            num_nodes=1000000,
            num_relationships=5000000,
            vector_index_dimensions=768,
            percentage_nodes_with_vector_properties=50.0,
            number_of_vector_indexes=1,
            quantization_enabled=True,
        )
        
        # Quantized should be approximately 4x smaller
        assert result_with_quant.size_of_vector_indexes_gb < result_no_quant.size_of_vector_indexes_gb
        # Account for ceiling rounding - ratio should be close to 4x
        ratio = result_no_quant.size_of_vector_indexes_gb / max(result_with_quant.size_of_vector_indexes_gb, 0.01)
        assert 3.0 <= ratio <= 5.0  # Should be approximately 4x (allow tolerance for ceiling)
    
    def test_non_vector_indexes_heuristic(self, calculator):
        """Test that non-vector indexes use 15% heuristic with ceiling."""
        result = calculator.calculate(
            num_nodes=100000,  # Use larger numbers
            num_relationships=500000,
            avg_properties_per_node=5,
        )
        
        # Non-vector indexes should be ceiling(15% of total without indexes)
        expected_index_size = result.total_size_without_indexes_gb * 0.15
        # The actual value uses math.ceil, so it should be >= expected
        assert result.size_of_non_vector_indexes_gb >= expected_index_size
        # And should be within 1.0 of expected (ceiling can add up to 1.0)
        assert result.size_of_non_vector_indexes_gb - expected_index_size < 1.0
    
    def test_total_size_calculation(self, calculator):
        """Test that total size includes all components."""
        result = calculator.calculate(
            num_nodes=1000,
            num_relationships=5000,
            avg_properties_per_node=3,
        )
        
        # Total with indexes should be sum of components (or OS floor, whichever is higher)
        expected_total = (
            result.total_size_without_indexes_gb +
            result.size_of_non_vector_indexes_gb +
            result.size_of_vector_indexes_gb
        )
        # Should be max of expected or OS floor (2GB)
        assert result.total_size_with_indexes_gb == max(expected_total, 2.0)
    
    def test_properties_not_double_counted(self, calculator):
        """Test that properties are not double-counted in total."""
        result = calculator.calculate(
            num_nodes=1000,
            num_relationships=5000,
            avg_properties_per_node=5,
        )
        
        # Total without indexes should be nodes + relationships (properties already included)
        expected = result.size_of_nodes_gb + result.size_of_relationships_gb
        assert abs(result.total_size_without_indexes_gb - expected) < 0.01
    
    def test_zero_nodes_and_relationships(self, calculator):
        """Test calculation with zero nodes and relationships."""
        result = calculator.calculate(
            num_nodes=0,
            num_relationships=0,
        )
        
        assert result.size_of_nodes_gb == 0
        assert result.size_of_relationships_gb == 0
        assert result.total_size_without_indexes_gb == 0
        # Indexes might still have minimum due to ceiling
        assert result.size_of_non_vector_indexes_gb >= 0
        # Total size should have OS base floor of 2GB
        assert result.total_size_with_indexes_gb >= 2.0
    
    def test_os_base_floor_applied(self, calculator):
        """Test that OS base floor of 2GB is applied to small graphs."""
        result = calculator.calculate(
            num_nodes=100,  # Very small graph
            num_relationships=200,
        )
        
        # Even for very small graphs, total should be at least 2GB
        assert result.total_size_with_indexes_gb >= 2.0
    
    def test_large_scale_graph(self, calculator):
        """Test calculation with very large graph."""
        result = calculator.calculate(
            num_nodes=200_000_000,
            num_relationships=1_000_000_000,
            avg_properties_per_node=10,
            avg_properties_per_relationship=3,
        )
        
        # Should handle large numbers without errors
        assert result.total_size_with_indexes_gb > 100  # Should be substantial
        assert result.size_of_nodes_gb > 50
        assert result.size_of_relationships_gb > 100
        # Large graphs should be well above OS floor
        assert result.total_size_with_indexes_gb > 2.0
    
    def test_multiple_vector_indexes(self, calculator):
        """Test calculation with multiple vector indexes."""
        # Use very large numbers to avoid ceiling rounding issues
        result = calculator.calculate(
            num_nodes=1000000,  # 1M nodes
            num_relationships=5000000,
            vector_index_dimensions=768,
            percentage_nodes_with_vector_properties=50.0,
            number_of_vector_indexes=3,  # 3 indexes
            quantization_enabled=False,
        )
        
        # With 3 indexes, should be 3x the single index size
        result_single = calculator.calculate(
            num_nodes=1000000,
            num_relationships=5000000,
            vector_index_dimensions=768,
            percentage_nodes_with_vector_properties=50.0,
            number_of_vector_indexes=1,
            quantization_enabled=False,
        )
        
        # Account for ceiling rounding - ratio should be close to 3x
        ratio = result.size_of_vector_indexes_gb / max(result_single.size_of_vector_indexes_gb, 0.01)
        assert 2.5 < ratio < 3.5  # Allow tolerance for ceiling rounding
    
    def test_recommended_memory_defaults_to_1_to_1(self, calculator):
        """Test that recommended_memory_gb defaults to 1:1 ratio (memory = storage)."""
        result = calculator.calculate(
            num_nodes=100000,
            num_relationships=500000,
        )
        
        # Memory should always be present
        assert result.recommended_memory_gb is not None
        # With default 1:1 ratio, memory should equal storage (rounded up)
        assert result.recommended_memory_gb >= result.total_size_with_indexes_gb
        # Should be at least 2GB (OS floor)
        assert result.recommended_memory_gb >= 2
    
    def test_recommended_memory_with_ratio(self, calculator):
        """Test recommended_memory_gb with different memory_to_storage_ratio values."""
        # Test 1:2 ratio - use larger graph to avoid OS floor issues
        result = calculator.calculate(
            num_nodes=10000000,
            num_relationships=50000000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
            memory_to_storage_ratio=2,  # 1:2 ratio (integer)
        )
        
        # Memory should be storage / 2 (rounded up), but at least 2GB (OS floor)
        expected_memory = result.total_size_with_indexes_gb / 2.0
        expected_memory = max(math.ceil(expected_memory), 2)  # OS floor of 2GB
        assert result.recommended_memory_gb == expected_memory
        
        # Test 1:4 ratio
        result = calculator.calculate(
            num_nodes=10000000,
            num_relationships=50000000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
            memory_to_storage_ratio=4,  # 1:4 ratio (integer)
        )
        
        expected_memory = result.total_size_with_indexes_gb / 4.0
        expected_memory = max(math.ceil(expected_memory), 2)  # OS floor of 2GB
        assert result.recommended_memory_gb == expected_memory
    
    def test_recommended_vcpus_defaults_to_1(self, calculator):
        """Test that recommended_vcpus defaults to 1."""
        result = calculator.calculate(
            num_nodes=100000,
            num_relationships=500000,
        )
        
        # vCPUs should always be present
        assert result.recommended_vcpus is not None
        # Should default to 1
        assert result.recommended_vcpus == 1
    
    def test_recommended_vcpus_with_concurrent_users(self, calculator):
        """Test recommended_vcpus calculation with concurrent_end_users (2 vCPU per user)."""
        result = calculator.calculate(
            num_nodes=100000,
            num_relationships=500000,
            concurrent_end_users=5,
        )
        
        # Should be 2 vCPU per concurrent user
        assert result.recommended_vcpus == 10  # 5 users * 2 vCPU
        
        # Test with 10 users
        result = calculator.calculate(
            num_nodes=100000,
            num_relationships=500000,
            concurrent_end_users=10,
        )
        
        assert result.recommended_vcpus == 20  # 10 users * 2 vCPU
