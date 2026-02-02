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
    get_component_growth_models,
    get_default_growth_rate,
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
    
    def test_get_component_growth_models_with_workloads(self):
        """Test getting component growth models based on workloads."""
        # Transactional should use log-linear for all components
        models = get_component_growth_models(workloads=["transactional"])
        assert isinstance(models["storage"], LogLinearGrowthModel)
        assert isinstance(models["memory"], LogLinearGrowthModel)
        assert isinstance(models["vcpu"], LogLinearGrowthModel)
        
        # Analytical should use compound for storage, linear for memory/vcpu
        models = get_component_growth_models(workloads=["analytical"])
        assert isinstance(models["storage"], CompoundGrowthModel)
        assert isinstance(models["memory"], LinearGrowthModel)
        assert isinstance(models["vcpu"], LinearGrowthModel)
        
        # Agentic should use compound for all components
        models = get_component_growth_models(workloads=["agentic"])
        assert isinstance(models["storage"], CompoundGrowthModel)
        assert isinstance(models["memory"], CompoundGrowthModel)
        assert isinstance(models["vcpu"], CompoundGrowthModel)
    
    def test_get_component_growth_models_with_domain(self):
        """Test getting component growth models based on domain."""
        # Customer domain (transactional+analytical) should use LogLinear (transactional is fastest)
        models = get_component_growth_models(domain="customer")
        assert isinstance(models["storage"], LogLinearGrowthModel)
        assert isinstance(models["memory"], LogLinearGrowthModel)
        assert isinstance(models["vcpu"], LogLinearGrowthModel)
        
        # Product domain (analytical) should use compound for storage, linear for memory/vcpu
        models = get_component_growth_models(domain="product")
        assert isinstance(models["storage"], CompoundGrowthModel)
        assert isinstance(models["memory"], LinearGrowthModel)
        assert isinstance(models["vcpu"], LinearGrowthModel)
        
        # Employee domain (analytical) should use compound for storage, linear for memory/vcpu
        models = get_component_growth_models(domain="employee")
        assert isinstance(models["storage"], CompoundGrowthModel)
        assert isinstance(models["memory"], LinearGrowthModel)
        assert isinstance(models["vcpu"], LinearGrowthModel)
        
        # Transaction domain should use log-linear for all components
        models = get_component_growth_models(domain="transaction")
        assert isinstance(models["storage"], LogLinearGrowthModel)
        assert isinstance(models["memory"], LogLinearGrowthModel)
        assert isinstance(models["vcpu"], LogLinearGrowthModel)
    
    def test_get_component_growth_models_workloads_override_domain(self):
        """Test that explicit workloads override domain-based growth models."""
        # Transaction domain would use LogLinear, but explicit workload overrides
        models = get_component_growth_models(workloads=["analytical"], domain="transaction")
        assert isinstance(models["storage"], CompoundGrowthModel)
        assert isinstance(models["memory"], LinearGrowthModel)
        assert isinstance(models["vcpu"], LinearGrowthModel)
        
        # Customer domain would use Compound, but explicit workload overrides
        models = get_component_growth_models(workloads=["transactional"], domain="customer")
        assert isinstance(models["storage"], LogLinearGrowthModel)
        assert isinstance(models["memory"], LogLinearGrowthModel)
        assert isinstance(models["vcpu"], LogLinearGrowthModel)
    
    def test_get_component_growth_models_default(self):
        """Test default growth models when no workload/domain specified."""
        models = get_component_growth_models()
        assert isinstance(models["storage"], CompoundGrowthModel)
        assert isinstance(models["memory"], CompoundGrowthModel)
        assert isinstance(models["vcpu"], CompoundGrowthModel)
    
    def test_multiple_workloads_uses_fastest(self):
        """Test that multiple workloads use the fastest-growing model for each component."""
        # Transactional (log-linear) + Analytical (compound/linear) should use log-linear for all
        models = get_component_growth_models(workloads=["analytical", "transactional"])
        assert isinstance(models["storage"], LogLinearGrowthModel)
        assert isinstance(models["memory"], LogLinearGrowthModel)
        assert isinstance(models["vcpu"], LogLinearGrowthModel)
        
        # Transactional (log-linear) should be fastest for all components
        models = get_component_growth_models(workloads=["analytical", "agentic", "transactional"])
        assert isinstance(models["storage"], LogLinearGrowthModel)
        assert isinstance(models["memory"], LogLinearGrowthModel)
        assert isinstance(models["vcpu"], LogLinearGrowthModel)


class TestDefaultGrowthRates:
    """Test smart default growth rate selection."""
    
    def test_default_growth_rate_with_workloads(self):
        """Test default growth rates for explicit workloads."""
        # Transactional should be 20%
        rate = get_default_growth_rate(workloads=["transactional"])
        assert rate == 20.0
        
        # Agentic should be 15%
        rate = get_default_growth_rate(workloads=["agentic"])
        assert rate == 15.0
        
        # Analytical should be 5%
        rate = get_default_growth_rate(workloads=["analytical"])
        assert rate == 5.0
    
    def test_default_growth_rate_with_domain(self):
        """Test default growth rates for domains."""
        # Customer domain (transactional+analytical) should use fastest: 20%
        rate = get_default_growth_rate(domain="customer")
        assert rate == 20.0
        
        # Transaction domain (transactional) should be 20%
        rate = get_default_growth_rate(domain="transaction")
        assert rate == 20.0
        
        # Product domain (analytical) should be 5%
        rate = get_default_growth_rate(domain="product")
        assert rate == 5.0
        
        # Employee domain (analytical) should be 5%
        rate = get_default_growth_rate(domain="employee")
        assert rate == 5.0
        
        # Security domain (transactional+analytical) should use fastest: 20%
        rate = get_default_growth_rate(domain="security")
        assert rate == 20.0
    
    def test_default_growth_rate_workloads_override_domain(self):
        """Test that explicit workloads override domain defaults."""
        # Customer domain defaults to 20% (transactional), but analytical override should be 5%
        rate = get_default_growth_rate(domain="customer", workloads=["analytical"])
        assert rate == 5.0
        
        # Product domain defaults to 5% (analytical), but transactional override should be 20%
        rate = get_default_growth_rate(domain="product", workloads=["transactional"])
        assert rate == 20.0
    
    def test_default_growth_rate_multiple_workloads(self):
        """Test that multiple workloads use the fastest growth rate."""
        # Transactional (20%) + Analytical (5%) should use 20%
        rate = get_default_growth_rate(workloads=["analytical", "transactional"])
        assert rate == 20.0
        
        # All three workloads should use 20% (transactional is fastest)
        rate = get_default_growth_rate(workloads=["analytical", "agentic", "transactional"])
        assert rate == 20.0
    
    def test_default_growth_rate_no_inputs(self):
        """Test default growth rate when no domain or workloads provided."""
        rate = get_default_growth_rate()
        assert rate == 10.0  # Generic default
    
    def test_default_growth_rate_domain_without_default_workloads(self):
        """Test default growth rate for domain without default workloads."""
        # Generic domain should use domain default (10%)
        rate = get_default_growth_rate(domain="generic")
        assert rate == 10.0

