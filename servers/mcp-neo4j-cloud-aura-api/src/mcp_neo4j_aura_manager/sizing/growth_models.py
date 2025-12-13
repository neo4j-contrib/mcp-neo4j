"""
Growth Models for Different Use Cases

Neo4j use cases can be characterized by:
1. Domain (7 Graphs of the Enterprise): Customer, Product, Employee, Supplier, Transaction, Process, Security
2. Workload Type: Transactional, Agentic, Analytical, Graph Data Science
3. Growth Pattern: Based on workload type (Transactional/Agentic grow faster than Analytical/GDS)
"""

from enum import Enum
from typing import Literal, Optional, List, Set, Dict
import math


class GraphDomain(str, Enum):
    """The 7 Graphs of the Enterprise - high-level business domains.
    
    Each domain can support any combination of workload types.
    Domain defaults are just suggestions - users can override with any workload combination.
    """
    CUSTOMER = "customer"  # Customer interactions, preferences, journeys
    PRODUCT = "product"  # Relationships between products, components, services
    EMPLOYEE = "employee"  # Team structures, skills, collaborations
    SUPPLIER = "supplier"  # Supply chain, dependencies, risk
    TRANSACTION = "transaction"  # Fraud detection, payment flows
    PROCESS = "process"  # Business workflows, dependencies, bottlenecks
    SECURITY = "security"  # Access, threats, compliance
    GENERIC = "generic"  # Unknown or mixed domain


class WorkloadType(str, Enum):
    """Workload types that determine growth patterns.
    
    Growth speed (fastest to slowest):
    - Transactional: Fast growth - high write volume, real-time queries
    - Agentic: Fast growth - RAG, vector search, knowledge bases
    - Analytical: Moderate growth - reporting, BI, aggregations
    - Graph Data Science: Slowest growth - algorithms, analytics, batch processing
    
    Any graph domain can use any combination of these workload types.
    """
    TRANSACTIONAL = "transactional"
    AGENTIC = "agentic"
    ANALYTICAL = "analytical"
    GRAPH_DATA_SCIENCE = "graph_data_science"


# Default workload type suggestions for each GraphDomain
# These are just common defaults - any domain can use any workload combination
# Users can override by explicitly providing workloads
DOMAIN_DEFAULT_WORKLOADS: Dict[GraphDomain, List[WorkloadType]] = {
    GraphDomain.CUSTOMER: [WorkloadType.TRANSACTIONAL, WorkloadType.ANALYTICAL],  # Customer 360: commonly transactional + analytical
    GraphDomain.PRODUCT: [WorkloadType.ANALYTICAL],  # Product graph: commonly analytical
    GraphDomain.EMPLOYEE: [WorkloadType.ANALYTICAL],  # Employee graph: commonly analytical
    GraphDomain.SUPPLIER: [WorkloadType.ANALYTICAL],  # Supply chain: commonly analytical
    GraphDomain.TRANSACTION: [WorkloadType.TRANSACTIONAL],  # Transaction graph: commonly high-volume transactional
    GraphDomain.PROCESS: [WorkloadType.ANALYTICAL],  # Process graph: commonly analytical
    GraphDomain.SECURITY: [WorkloadType.TRANSACTIONAL, WorkloadType.ANALYTICAL],  # Security: commonly transactional + analytical
    GraphDomain.GENERIC: [],  # No default - user must specify or use generic growth
}


class GrowthModel:
    """Base class for growth models."""
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        **kwargs
    ) -> float:
        """
        Calculate projected size for a given year.
        
        Args:
            base_size_gb: Base size in GB (year 0)
            annual_growth_rate: Annual growth rate as percentage
            year: Year number (1, 2, 3, etc.)
            **kwargs: Additional parameters for specific models
            
        Returns:
            Projected size in GB
        """
        raise NotImplementedError


class CompoundGrowthModel(GrowthModel):
    """Simple compound growth: size = base * (1 + rate)^year
    
    Standard exponential growth - good default for most use cases.
    """
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        **kwargs
    ) -> float:
        return base_size_gb * ((1 + annual_growth_rate / 100.0) ** year)


class LogLinearGrowthModel(GrowthModel):
    """Log-linear growth: size = base * e^(rate * year)
    
    Very fast early growth. Good for high-volume transactional and agentic workloads.
    """
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        **kwargs
    ) -> float:
        # Log-linear: exponential growth using e^(r*t)
        r = annual_growth_rate / 100.0
        return base_size_gb * math.exp(r * year)


class LinearGrowthModel(GrowthModel):
    """Linear growth: size = base * (1 + rate * year)
    
    Constant absolute growth per year. Slower than exponential.
    Good for steady, predictable workloads.
    """
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        **kwargs
    ) -> float:
        return base_size_gb * (1 + (annual_growth_rate / 100.0) * year)


class ExponentialWithVectorGrowthModel(GrowthModel):
    """Exponential growth with additional vector index growth
    
    Good for agentic/RAG workloads where vector indexes grow separately.
    """
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        vector_growth_multiplier: float = 1.2,
        vector_proportion: float = 0.3,
        **kwargs
    ) -> float:
        """
        Exponential growth with vector component growing faster.
        
        Args:
            vector_growth_multiplier: Additional growth multiplier for vector indexes
            vector_proportion: Proportion of base size that is vector-related (default 30%)
        """
        vector_base = base_size_gb * vector_proportion
        non_vector_base = base_size_gb * (1 - vector_proportion)
        
        # Vector grows faster
        vector_growth = vector_base * ((1 + annual_growth_rate / 100.0) * vector_growth_multiplier) ** year
        non_vector_growth = non_vector_base * ((1 + annual_growth_rate / 100.0) ** year)
        
        return vector_growth + non_vector_growth


class LogisticGrowthModel(GrowthModel):
    """Logistic growth: S-curve that levels off
    
    Fast early growth that slows down. Good for workloads that reach saturation.
    """
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        carrying_capacity_multiplier: float = 5.0,
        **kwargs
    ) -> float:
        """
        Logistic growth: base * (K / (1 + (K - 1) * e^(-r * t)))
        
        Args:
            carrying_capacity_multiplier: Maximum size as multiple of base (default 5x)
        """
        K = carrying_capacity_multiplier
        r = annual_growth_rate / 100.0
        t = year
        
        size = base_size_gb * (K / (1 + (K - 1) * math.exp(-r * t)))
        return size


def get_growth_model_for_workloads(workloads: List[WorkloadType]) -> GrowthModel:
    """
    Determine growth model based on workload types.
    
    Priority (fastest growth wins):
    1. Transactional or Agentic → LogLinearGrowthModel (fastest)
    2. Analytical → CompoundGrowthModel (moderate)
    3. Graph Data Science → LinearGrowthModel (slowest)
    
    If multiple workloads, use the fastest-growing one.
    If Agentic is present, use ExponentialWithVectorGrowthModel.
    
    Args:
        workloads: List of workload types
        
    Returns:
        Appropriate growth model
    """
    if not workloads:
        return CompoundGrowthModel()
    
    workload_set: Set[WorkloadType] = set(workloads)
    
    # Agentic workloads get special treatment (vector growth)
    if WorkloadType.AGENTIC in workload_set:
        # If also transactional, use log-linear with vectors
        if WorkloadType.TRANSACTIONAL in workload_set:
            return LogLinearGrowthModel()
        return ExponentialWithVectorGrowthModel()
    
    # Transactional workloads grow fast
    if WorkloadType.TRANSACTIONAL in workload_set:
        return LogLinearGrowthModel()
    
    # Analytical workloads use compound growth
    if WorkloadType.ANALYTICAL in workload_set:
        return CompoundGrowthModel()
    
    # Graph Data Science grows slowest
    if WorkloadType.GRAPH_DATA_SCIENCE in workload_set:
        return LinearGrowthModel()
    
    # Default to compound
    return CompoundGrowthModel()


def get_growth_model(
    workloads: Optional[List[str]] = None,
    domain: Optional[str] = None
) -> GrowthModel:
    """
    Get the appropriate growth model based on workload types or domain.
    
    Priority:
    1. If workloads are explicitly provided, use those
    2. If domain is provided, use default workloads for that domain
    3. Otherwise, use generic compound growth
    
    Args:
        workloads: List of workload types (transactional, agentic, analytical, graph_data_science)
                  If provided, overrides domain defaults
        domain: Graph domain (customer, product, etc.) - used to infer default workloads if workloads not provided
        
    Returns:
        Growth model instance
    """
    # If workloads explicitly provided, use them
    if workloads:
        try:
            workload_enums = [WorkloadType(w) for w in workloads]
            return get_growth_model_for_workloads(workload_enums)
        except ValueError:
            # Invalid workload type, fall through to domain-based selection
            pass
    
    # If domain provided, use default workloads for that domain
    if domain:
        try:
            domain_enum = GraphDomain(domain)
            default_workloads = DOMAIN_DEFAULT_WORKLOADS.get(domain_enum, [])
            if default_workloads:
                return get_growth_model_for_workloads(default_workloads)
        except ValueError:
            # Invalid domain, fall through to default
            pass
    
    # Default to compound growth
    return CompoundGrowthModel()


def get_default_workloads_for_domain(domain: str) -> List[str]:
    """
    Get default workload types for a graph domain.
    
    Args:
        domain: Graph domain (customer, product, etc.)
        
    Returns:
        List of default workload type strings for the domain
    """
    try:
        domain_enum = GraphDomain(domain)
        default_workloads = DOMAIN_DEFAULT_WORKLOADS.get(domain_enum, [])
        return [w.value for w in default_workloads]
    except ValueError:
        return []
