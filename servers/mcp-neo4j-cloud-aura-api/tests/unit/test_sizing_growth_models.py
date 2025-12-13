"""
Unit tests for growth models.
"""

import pytest
from mcp_neo4j_aura_manager.sizing.growth_models import (
    CompoundGrowthModel,
    LinearGrowthModel,
    LogLinearGrowthModel,
    LogisticGrowthModel,
    ExponentialWithVectorGrowthModel,
    get_growth_model,
    GraphDomain,
    WorkloadType,
)


class TestGrowthModels:
    """Test growth model calculations."""
    
    def test_compound_growth_model(self):
        """Test compound growth model."""
        model = CompoundGrowthModel()
        
        # 10% growth over 1 year: 100 * 1.1 = 110
        result = model.calculate(base_size_gb=100.0, annual_growth_rate=10.0, year=1)
        assert abs(result - 110.0) < 0.01
        
        # 10% growth over 2 years: 100 * 1.1^2 = 121
        result = model.calculate(base_size_gb=100.0, annual_growth_rate=10.0, year=2)
        assert abs(result - 121.0) < 0.01
    
    def test_linear_growth_model(self):
        """Test linear growth model."""
        model = LinearGrowthModel()
        
        # 10% growth over 1 year: 100 + (100 * 0.1 * 1) = 110
        result = model.calculate(base_size_gb=100.0, annual_growth_rate=10.0, year=1)
        assert abs(result - 110.0) < 0.01
        
        # 10% growth over 2 years: 100 + (100 * 0.1 * 2) = 120
        result = model.calculate(base_size_gb=100.0, annual_growth_rate=10.0, year=2)
        assert abs(result - 120.0) < 0.01
    
    def test_log_linear_growth_model(self):
        """Test log-linear growth model (faster than linear)."""
        model = LogLinearGrowthModel()
        
        result = model.calculate(base_size_gb=100.0, annual_growth_rate=10.0, year=1)
        # Log-linear should be faster than linear
        linear_result = LinearGrowthModel().calculate(base_size_gb=100.0, annual_growth_rate=10.0, year=1)
        assert result > linear_result
    
    def test_exponential_with_vector_growth_model(self):
        """Test exponential growth model for vector/RAG workloads."""
        model = ExponentialWithVectorGrowthModel()
        
        result = model.calculate(base_size_gb=100.0, annual_growth_rate=10.0, year=1)
        # Should be exponential growth
        assert result > 110.0  # Faster than compound
    
    def test_logistic_growth_model(self):
        """Test logistic growth model with carrying capacity."""
        model = LogisticGrowthModel()
        
        # With default carrying capacity (2x base)
        result = model.calculate(
            base_size_gb=100.0,
            annual_growth_rate=10.0,
            year=1,
            carrying_capacity_multiplier=2.0,
        )
        
        # Should grow but be bounded
        assert 100.0 < result < 200.0
    
    def test_get_growth_model_with_workloads(self):
        """Test getting growth model based on workloads."""
        # Transactional should use log-linear (fast growth)
        model = get_growth_model(workloads=["transactional"])
        assert isinstance(model, LogLinearGrowthModel)
        
        # Analytical should use compound (moderate growth)
        model = get_growth_model(workloads=["analytical"])
        assert isinstance(model, CompoundGrowthModel)
        
        # Agentic should use exponential (fastest growth)
        model = get_growth_model(workloads=["agentic"])
        assert isinstance(model, ExponentialWithVectorGrowthModel)
        
        # Graph Data Science should use linear (slowest)
        model = get_growth_model(workloads=["graph_data_science"])
        assert isinstance(model, LinearGrowthModel)
    
    def test_get_growth_model_with_domain(self):
        """Test getting growth model based on domain."""
        # Customer domain defaults to transactional + analytical
        model = get_growth_model(domain="customer")
        # Should use fastest-growing workload (transactional -> log-linear)
        assert isinstance(model, LogLinearGrowthModel)
        
        # Product domain defaults to analytical
        model = get_growth_model(domain="product")
        assert isinstance(model, CompoundGrowthModel)
    
    def test_get_growth_model_workloads_override_domain(self):
        """Test that explicit workloads override domain defaults."""
        # Domain would suggest log-linear, but explicit workload overrides
        model = get_growth_model(workloads=["analytical"], domain="customer")
        assert isinstance(model, CompoundGrowthModel)
    
    def test_get_growth_model_default(self):
        """Test default growth model when no workload/domain specified."""
        model = get_growth_model()
        assert isinstance(model, CompoundGrowthModel)
    
    def test_multiple_workloads_uses_fastest(self):
        """Test that multiple workloads use the fastest-growing model."""
        # Transactional (log-linear) + Analytical (compound) should use log-linear
        model = get_growth_model(workloads=["analytical", "transactional"])
        assert isinstance(model, LogLinearGrowthModel)
        
        # Agentic (exponential) should be fastest
        model = get_growth_model(workloads=["analytical", "agentic"])
        assert isinstance(model, ExponentialWithVectorGrowthModel)

