"""
Integration tests for sizing calculator MCP tools.
"""

import pytest
from mcp_neo4j_aura_manager.aura_manager import AuraManager
from mcp_neo4j_aura_manager.sizing.service import AuraSizingService


class TestSizingToolsIntegration:
    """Integration tests for sizing tools through AuraManager."""
    
    @pytest.fixture
    def aura_manager(self):
        """Create an AuraManager instance for testing."""
        # Use dummy credentials - we're not making real API calls
        return AuraManager("dummy-id", "dummy-secret")
    
    @pytest.mark.asyncio
    async def test_calculate_database_sizing_integration(self, aura_manager):
        """Test calculate_database_sizing through AuraManager."""
        result = await aura_manager.calculate_database_sizing(
            num_nodes=100000,
            num_relationships=500000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
        )
        
        assert "calculations" in result
        assert "metadata" in result
        assert result["calculations"]["total_size_with_indexes_gb"] > 0
        assert result["metadata"]["calculator_type"] == "Neo4jSizingCalculator"
        # Verify new required fields are present
        assert "recommended_memory_gb" in result["calculations"]
        assert "recommended_vcpus" in result["calculations"]
        assert result["calculations"]["recommended_memory_gb"] >= 2  # At least OS floor
        assert result["calculations"]["recommended_vcpus"] == 1  # Default
    
    @pytest.mark.asyncio
    async def test_calculate_database_sizing_with_vectors(self, aura_manager):
        """Test calculate_database_sizing with vector indexes."""
        result = await aura_manager.calculate_database_sizing(
            num_nodes=100000,
            num_relationships=500000,
            avg_properties_per_node=5,
            avg_properties_per_relationship=2,
            vector_index_dimensions=768,
            percentage_nodes_with_vector_properties=50.0,
            number_of_vector_indexes=1,
            quantization_enabled=True,
        )
        
        assert result["calculations"]["size_of_vector_indexes_gb"] > 0
        assert "vector_index_dimensions" in result["metadata"]["calculation_config"]
        # Verify memory and vCPUs are present
        assert "recommended_memory_gb" in result["calculations"]
        assert "recommended_vcpus" in result["calculations"]
    
    @pytest.mark.asyncio
    async def test_forecast_database_size_integration(self, aura_manager):
        """Test forecast_database_size through AuraManager."""
        result = await aura_manager.forecast_database_size(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            domain="customer",
            annual_growth_rate=10.0,
            projection_years=3,
        )
        
        assert "base_size_gb" in result
        assert "projections" in result
        assert len(result["projections"]) == 3
        assert result["growth_model_used"] is not None
    
    @pytest.mark.asyncio
    async def test_forecast_with_workloads(self, aura_manager):
        """Test forecast with workload types."""
        result = await aura_manager.forecast_database_size(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            domain="generic",
            annual_growth_rate=10.0,
            projection_years=3,
            workloads=["transactional"],
        )
        
        # Transactional should use LogLinearGrowthModel
        assert "LogLinear" in result["growth_model_used"]
    
    @pytest.mark.asyncio
    async def test_forecast_with_domain(self, aura_manager):
        """Test forecast with domain."""
        result = await aura_manager.forecast_database_size(
            base_size_gb=100.0,
            base_memory_gb=64,
            base_cores=8,
            annual_growth_rate=10.0,
            projection_years=3,
            domain="customer",
        )
        
        # Customer domain defaults to transactional + analytical -> LogLinear
        assert "LogLinear" in result["growth_model_used"]
    
    @pytest.mark.asyncio
    async def test_error_handling_negative_values(self, aura_manager):
        """Test that negative values raise appropriate errors."""
        with pytest.raises(ValueError, match="num_nodes must be non-negative"):
            await aura_manager.calculate_database_sizing(
                num_nodes=-1,
                num_relationships=100,
                avg_properties_per_node=5,
                avg_properties_per_relationship=2,
            )
        
        with pytest.raises(ValueError, match="base_size_gb must be non-negative"):
            await aura_manager.forecast_database_size(
                base_size_gb=-1.0,
                base_memory_gb=64,
                base_cores=8,
                domain="customer",
            )

