"""
Unit tests for the Aura sizing service.
"""

import pytest
from mcp_neo4j_aura_manager.sizing.service import AuraSizingService
from mcp_neo4j_aura_manager.sizing.calculator import Neo4jSizingCalculator


class TestAuraSizingService:
    """Test the AuraSizingService class."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return AuraSizingService()
    
    def test_calculate_sizing_basic(self, service):
        """Test basic sizing calculation."""
        result = service.calculate_sizing(
            num_nodes=1000,
            num_relationships=5000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
        )
        
        assert result.calculations.total_size_with_indexes_gb > 0
        assert result.metadata.calculator_type == "Neo4jSizingCalculator"
        assert "quantization_enabled" in result.metadata.calculation_config
    
    def test_calculate_sizing_with_optional_params(self, service):
        """Test sizing with all optional parameters."""
        result = service.calculate_sizing(
            num_nodes=10000,
            num_relationships=50000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
            total_num_large_node_properties=1000,
            total_num_large_reltype_properties=500,
            vector_index_dimensions=768,
            percentage_nodes_with_vector_properties=50.0,
            number_of_vector_indexes=1,
            quantization_enabled=True,
        )
        
        assert result.calculations.total_size_with_indexes_gb > 0
        assert result.metadata.calculation_config["quantization_enabled"] is True
        assert result.metadata.calculation_config["vector_index_dimensions"] == 768
    
    def test_calculate_sizing_none_defaults(self, service):
        """Test that None values for optional parameters are converted to defaults."""
        result = service.calculate_sizing(
            num_nodes=100,
            num_relationships=200,
            avg_properties_per_node=3,
            avg_properties_per_relationship=1,
            total_num_large_node_properties=None,
            total_num_large_reltype_properties=None,
            vector_index_dimensions=None,
            percentage_nodes_with_vector_properties=None,
            number_of_vector_indexes=None,
        )
        
        # Should work without errors and use defaults for optional params
        assert result.calculations.total_size_with_indexes_gb >= 0
        assert result.calculations.size_of_vector_indexes_gb == 0
    
    def test_calculate_sizing_validation_negative_nodes(self, service):
        """Test validation rejects negative nodes."""
        with pytest.raises(ValueError, match="num_nodes must be non-negative"):
            service.calculate_sizing(
                num_nodes=-1,
                num_relationships=100,
                avg_properties_per_node=5,
                avg_properties_per_relationship=2,
            )
    
    def test_calculate_sizing_validation_negative_relationships(self, service):
        """Test validation rejects negative relationships."""
        with pytest.raises(ValueError, match="num_relationships must be non-negative"):
            service.calculate_sizing(
                num_nodes=100,
                num_relationships=-1,
                avg_properties_per_node=5,
                avg_properties_per_relationship=2,
            )
    
    def test_calculate_sizing_validation_negative_properties(self, service):
        """Test validation rejects negative property counts."""
        with pytest.raises(ValueError, match="avg_properties_per_node must be non-negative"):
            service.calculate_sizing(
                num_nodes=100,
                num_relationships=200,
                avg_properties_per_node=-1,
                avg_properties_per_relationship=2,
            )
    
    def test_calculate_sizing_validation_percentage_range(self, service):
        """Test validation for percentage range."""
        with pytest.raises(ValueError, match="percentage_nodes_with_vector_properties must be between 0 and 100"):
            service.calculate_sizing(
                num_nodes=100,
                num_relationships=200,
                avg_properties_per_node=5,
                avg_properties_per_relationship=2,
                percentage_nodes_with_vector_properties=150.0,
            )
        
        with pytest.raises(ValueError, match="percentage_nodes_with_vector_properties must be between 0 and 100"):
            service.calculate_sizing(
                num_nodes=100,
                num_relationships=200,
                avg_properties_per_node=5,
                avg_properties_per_relationship=2,
                percentage_nodes_with_vector_properties=-10.0,
            )
    
    def test_calculate_sizing_custom_calculator(self):
        """Test service with custom calculator."""
        custom_calculator = Neo4jSizingCalculator()
        service = AuraSizingService(calculator=custom_calculator)
        
        result = service.calculate_sizing(
            num_nodes=1000,
            num_relationships=5000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
        )
        
        assert result.metadata.calculator_type == "Neo4jSizingCalculator"
    
    def test_forecast_sizing_basic(self, service):
        """Test basic forecast calculation."""
        result = service.forecast_sizing(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            domain="customer",
            annual_growth_rate=10.0,
            projection_years=3,
        )
        
        assert len(result.projections) == 3
        assert result.base_size_gb == 100.0
        assert result.base_memory_gb == 64
        assert result.base_cores == 8
        assert result.growth_model_used is not None
        
        # Projections should show growth
        assert result.projections[0].total_size_gb > result.base_size_gb
        assert result.projections[1].total_size_gb > result.projections[0].total_size_gb
    
    def test_forecast_sizing_with_workloads(self, service):
        """Test forecast with workload types."""
        result = service.forecast_sizing(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            domain="generic",
            annual_growth_rate=10.0,
            projection_years=3,
            workloads=["transactional"],
        )
        
        assert result.growth_model_used is not None
        assert len(result.projections) == 3
    
    def test_forecast_sizing_with_domain(self, service):
        """Test forecast with domain."""
        result = service.forecast_sizing(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            annual_growth_rate=10.0,
            projection_years=3,
            domain="customer",
        )
        
        assert result.growth_model_used is not None
        assert len(result.projections) == 3
    
    def test_forecast_sizing_smart_default_growth_rate_with_domain(self, service):
        """Test that forecast uses smart default growth rate when annual_growth_rate is None."""
        # Customer domain should use 20% (transactional is fastest default workload)
        result = service.forecast_sizing(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            annual_growth_rate=None,  # Should use smart default
            projection_years=3,
            domain="customer",
        )
        
        assert result.growth_model_used is not None
        assert len(result.projections) == 3
        # Customer domain with transactional workload should grow faster than 10%
        assert result.projections[0].total_size_gb > 110.0  # More than 10% growth
    
    def test_forecast_sizing_smart_default_growth_rate_with_workloads(self, service):
        """Test that forecast uses smart default growth rate based on workloads."""
        # Analytical workload should use 5% default
        result = service.forecast_sizing(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            annual_growth_rate=None,  # Should use smart default
            projection_years=3,
            domain="generic",
            workloads=["analytical"],
        )
        
        assert result.growth_model_used is not None
        assert len(result.projections) == 3
        # Analytical with 5% growth should be slower
        assert result.projections[0].total_size_gb < 110.0  # Less than 10% growth
    
    def test_forecast_sizing_smart_default_growth_rate_no_inputs(self, service):
        """Test that forecast uses generic default when domain has no default workloads."""
        # Generic domain has no default workloads, so should use domain default (10%)
        result = service.forecast_sizing(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            annual_growth_rate=None,  # Should use generic default (10%)
            projection_years=3,
            domain="generic",
        )
        
        assert result.growth_model_used is not None
        assert len(result.projections) == 3
        # Generic default should be around 10% growth
        assert 105.0 < result.projections[0].total_size_gb < 115.0
    
    def test_forecast_sizing_validation(self, service):
        """Test forecast validation."""
        with pytest.raises(ValueError, match="base_size_gb must be non-negative"):
            service.forecast_sizing(
                base_size_gb=-1.0,
                base_memory_gb=64,
                base_cores=8,
                domain="customer",
            )
        
        with pytest.raises(ValueError, match="projection_years must be at least 1"):
            service.forecast_sizing(
                base_size_gb=100.0,
                base_memory_gb=64,
                base_cores=8,
                domain="customer",
                projection_years=0,
            )
        
        with pytest.raises(ValueError, match="projection_years exceeds reasonable limit"):
            service.forecast_sizing(
                base_size_gb=100.0,
                base_memory_gb=64,
                base_cores=8,
                domain="customer",
                projection_years=25,
            )

