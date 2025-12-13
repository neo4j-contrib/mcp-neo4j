"""
Unit tests for the growth projector.
"""

import pytest
from mcp_neo4j_aura_manager.sizing.projector import GrowthProjector
from mcp_neo4j_aura_manager.sizing.growth_models import CompoundGrowthModel


class TestGrowthProjector:
    """Test the GrowthProjector class."""
    
    def test_project_basic(self):
        """Test basic projection."""
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=10.0,
            projection_years=3,
            base_memory_gb=64,
            base_cores=8,
        )
        
        assert len(projections) == 3
        assert projections[0]["year"] == 1
        assert projections[1]["year"] == 2
        assert projections[2]["year"] == 3
        
        # Each year should show growth
        assert projections[0]["total_size_gb"] > 100.0
        assert projections[1]["total_size_gb"] > projections[0]["total_size_gb"]
        assert projections[2]["total_size_gb"] > projections[1]["total_size_gb"]
    
    def test_project_with_workloads(self):
        """Test projection with workload types."""
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=10.0,
            projection_years=3,
            base_memory_gb=64,
            base_cores=8,
            workloads=["transactional"],
        )
        
        assert len(projections) == 3
        # Transactional should grow faster than default
        assert projections[0]["total_size_gb"] > 110.0
    
    def test_project_scaling_needed(self):
        """Test that scaling_needed flag is set correctly."""
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=50.0,  # High growth rate
            projection_years=3,
            base_memory_gb=64,
            base_cores=8,
        )
        
        # With 50% growth, year 1 should trigger scaling (>50% from base)
        assert projections[0]["scaling_needed"] is True
    
    def test_project_memory_scales_with_storage(self):
        """Test that memory scales with storage based on ratio, cores remain static."""
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=10.0,
            projection_years=3,
            base_memory_gb=64,
            base_cores=8,
            memory_to_storage_ratio=1.0,  # 1:1 ratio
        )
        
        # Memory should scale with storage (1:1 ratio), cores should stay static
        for projection in projections:
            # With 1:1 ratio, memory should approximately equal storage (rounded up)
            assert projection["recommended_memory_gb"] >= projection["total_size_gb"]
            assert projection["recommended_cores"] == 8  # Cores stay static
    
    def test_project_memory_with_different_ratios(self):
        """Test memory scaling with different ratios."""
        # Test 1:8 ratio
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=10.0,
            projection_years=1,
            base_memory_gb=10,  # Low base to see scaling
            base_cores=8,
            memory_to_storage_ratio=8.0,  # 1:8 ratio
        )
        
        # With 1:8 ratio, memory should be storage / 8 (but not below base)
        # Year 1: 110GB storage / 8 = 13.75GB → 14GB memory
        assert projections[0]["recommended_memory_gb"] == 14
        
        # Test 1:4 ratio
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=10.0,
            projection_years=1,
            base_memory_gb=10,
            base_cores=8,
            memory_to_storage_ratio=4.0,  # 1:4 ratio
        )
        
        # Year 1: 110GB storage / 4 = 27.5GB → 28GB memory
        assert projections[0]["recommended_memory_gb"] == 28
    
    def test_project_with_custom_model(self):
        """Test projection with custom growth model."""
        custom_model = CompoundGrowthModel()
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=10.0,
            projection_years=2,
            base_memory_gb=64,
            base_cores=8,
            growth_model=custom_model,
        )
        
        assert len(projections) == 2
    
    def test_project_scaling_threshold(self):
        """Test scaling threshold logic."""
        # Growth >50% from base should trigger scaling
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=60.0,  # 60% growth
            projection_years=1,
            base_memory_gb=64,
            base_cores=8,
        )
        
        assert projections[0]["scaling_needed"] is True
        
        # Growth <50% from base should not trigger scaling
        projections = GrowthProjector.project(
            base_size_gb=100.0,
            annual_growth_rate=10.0,  # 10% growth
            projection_years=1,
            base_memory_gb=64,
            base_cores=8,
        )
        
        assert projections[0]["scaling_needed"] is False

