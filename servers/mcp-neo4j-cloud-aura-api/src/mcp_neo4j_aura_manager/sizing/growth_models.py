from __future__ import annotations

from enum import Enum
from typing import Optional, List, Set, Dict
import math


# ============================================================================
# Enums
# ============================================================================

class GraphDomain(str, Enum):
    """The 7 Graphs of the Enterprise - high-level business domains.
    
    Domains are categorized into three types that influence growth patterns:
    - Graphs of Things: Static entities (product, employee, supplier)
    - Graphs of Transactions: High volume events (transaction)
    - Graphs of Behaviors: Activity-based (customer, process, security)
    
    Domain is the primary driver for growth model selection. Workloads can override domain defaults.
    """
    CUSTOMER = "customer"  # Customer interactions, preferences, journeys (Graphs of Behaviors)
    PRODUCT = "product"  # Relationships between products, components, services (Graphs of Things)
    EMPLOYEE = "employee"  # Team structures, skills, collaborations (Graphs of Things)
    SUPPLIER = "supplier"  # Supply chain, dependencies, risk (Graphs of Things)
    TRANSACTION = "transaction"  # Fraud detection, payment flows (Graphs of Transactions)
    PROCESS = "process"  # Business workflows, dependencies, bottlenecks (Graphs of Behaviors)
    SECURITY = "security"  # Access, threats, compliance (Graphs of Behaviors)
    GENERIC = "generic"  # Unknown or mixed domain


class WorkloadType(str, Enum):
    """Workload types that determine growth patterns and core scaling.
    
    Workloads can override domain-based growth models when explicitly provided.
    
    Storage Growth (fastest to slowest):
    - Transactional: Fast growth (Log-linear) - high read/write volume, real-time queries
    - Agentic: Medium growth (Compound) - RAG, vector search, knowledge bases
    - Analytical: Moderate growth (Compound) - reporting, BI, aggregations, ad-hoc queries
    
    Core Scaling (high to low):
    - Transactional: High - needs more cores for concurrent writes
    - Agentic: Medium - queries hitting DB
    - Analytical: Low - mostly reads, batch writes don't need many cores
    """
    TRANSACTIONAL = "transactional"
    AGENTIC = "agentic"
    ANALYTICAL = "analytical"


# ============================================================================
# Configuration Mappings
# ============================================================================

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

WORKLOAD_DEFAULT_GROWTH_RATES: Dict[WorkloadType, float] = {
    WorkloadType.TRANSACTIONAL: 20.0,  # High-volume transactional systems grow fast
    WorkloadType.AGENTIC: 15.0,        # agentic workloads grow moderately fast (with the potential to grow faster yet)
    WorkloadType.ANALYTICAL: 5.0,      # Analytical/reporting workloads grow slowly
}

DOMAIN_DEFAULT_GROWTH_RATES: Dict[GraphDomain, float] = {
    GraphDomain.CUSTOMER: 15.0,      # Customer 360: moderate growth
    GraphDomain.PRODUCT: 5.0,        # Product catalogs: slow growth
    GraphDomain.EMPLOYEE: 3.0,       # Org charts: very slow growth
    GraphDomain.SUPPLIER: 5.0,       # Supply chain: slow growth
    GraphDomain.TRANSACTION: 20.0,   # Transaction graphs: fast growth
    GraphDomain.PROCESS: 5.0,        # Process workflows: slow growth
    GraphDomain.SECURITY: 10.0,      # Security: moderate growth
    GraphDomain.GENERIC: 10.0,       # Generic: moderate default
}


# ============================================================================
# Growth Model Classes
# ============================================================================

class GrowthModel:
    """Base class for growth models."""
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        **kwargs
    ) -> float:
        """Calculate projected size for a given year.
        
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
    """Exponential growth with additional vector index growth.
    
    Good for agentic/RAG workloads where vector indexes grow separately.
    Assumes chunk size + vector index size >> entity size.
    
    Vector index size formula:
    (1.1 * (4 * dimension + 8 * 16) * num_vectors) / 1,048,576,000
    
    Reference: https://neo4j.com/docs/operations-manual/current/performance/vector-index-memory-configuration/
    """
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        vector_growth_multiplier: float = 1.2,
        vector_proportion: float = 0.7,
        **kwargs
    ) -> float:
        """Calculate growth with vector component growing faster.
        
        Args:
            base_size_gb: Base size in GB (year 0), includes entity + vector data
            annual_growth_rate: Annual growth rate as percentage
            year: Year number (1, 2, 3, etc.)
            vector_growth_multiplier: Additional growth multiplier for vectors (default 1.2)
            vector_proportion: Proportion of base size that is vector-related (default 0.7)
        """
        vector_base = base_size_gb * vector_proportion
        non_vector_base = base_size_gb * (1 - vector_proportion)
        
        vector_growth = vector_base * ((1 + annual_growth_rate / 100.0) * vector_growth_multiplier) ** year
        non_vector_growth = non_vector_base * ((1 + annual_growth_rate / 100.0) ** year)
        
        return vector_growth + non_vector_growth


class LogisticGrowthModel(GrowthModel):
    """Logistic growth: S-curve that levels off.
    
    Fast early growth that slows down. Good for workloads that reach saturation.
    Formula: base * (K / (1 + (K - 1) * e^(-r * t)))
    """
    
    @staticmethod
    def calculate(
        base_size_gb: float,
        annual_growth_rate: float,
        year: int,
        carrying_capacity_multiplier: float = 5.0,
        **kwargs
    ) -> float:
        """Calculate logistic growth.
        
        Args:
            carrying_capacity_multiplier: Maximum size as multiple of base (default 5x)
        """
        K = carrying_capacity_multiplier
        r = annual_growth_rate / 100.0
        t = year
        
        return base_size_gb * (K / (1 + (K - 1) * math.exp(-r * t)))


# ============================================================================
# Component Growth Model Mappings
# ============================================================================

WORKLOAD_COMPONENT_GROWTH_MODELS: Dict[WorkloadType, Dict[str, type[GrowthModel]]] = {
    WorkloadType.TRANSACTIONAL: {
        "storage": LogLinearGrowthModel,
        "memory": LogLinearGrowthModel,
        "vcpu": LogLinearGrowthModel,
    },
    WorkloadType.AGENTIC: {
        "storage": CompoundGrowthModel,
        "memory": CompoundGrowthModel,
        "vcpu": CompoundGrowthModel,
    },
    WorkloadType.ANALYTICAL: {
        "storage": CompoundGrowthModel,
        "memory": LinearGrowthModel,
        "vcpu": LinearGrowthModel,
    },
}

DOMAIN_COMPONENT_GROWTH_MODELS: Dict[GraphDomain, Dict[str, type[GrowthModel]]] = {
    GraphDomain.PRODUCT: {
        "storage": CompoundGrowthModel,
        "memory": CompoundGrowthModel,
        "vcpu": LinearGrowthModel,
    },
    GraphDomain.EMPLOYEE: {
        "storage": LinearGrowthModel,
        "memory": LinearGrowthModel,
        "vcpu": LinearGrowthModel,
    },
    GraphDomain.SUPPLIER: {
        "storage": CompoundGrowthModel,
        "memory": CompoundGrowthModel,
        "vcpu": LinearGrowthModel,
    },
    GraphDomain.TRANSACTION: {
        "storage": LogLinearGrowthModel,
        "memory": LogLinearGrowthModel,
        "vcpu": LogLinearGrowthModel,
    },
    GraphDomain.CUSTOMER: {
        "storage": CompoundGrowthModel,
        "memory": CompoundGrowthModel,
        "vcpu": CompoundGrowthModel,
    },
    GraphDomain.PROCESS: {
        "storage": CompoundGrowthModel,
        "memory": CompoundGrowthModel,
        "vcpu": CompoundGrowthModel,
    },
    GraphDomain.SECURITY: {
        "storage": CompoundGrowthModel,
        "memory": CompoundGrowthModel,
        "vcpu": CompoundGrowthModel,
    },
    GraphDomain.GENERIC: {
        "storage": CompoundGrowthModel,
        "memory": CompoundGrowthModel,
        "vcpu": CompoundGrowthModel,
    },
}


# ============================================================================
# Growth Model Selection Functions
# ============================================================================

def get_default_growth_rate(
    workloads: Optional[List[str]] = None,
    domain: Optional[str] = None
) -> float:
    """Get default growth rate based on workloads or domain.
    
    Priority:
    1. If workloads provided → use fastest workload's default rate
    2. If domain provided → infer default workloads for domain, then use fastest workload's rate
    3. Otherwise → 10.0% (generic default)
    
    Args:
        workloads: List of workload types (transactional, agentic, analytical)
        domain: Graph domain (customer, product, etc.)
        
    Returns:
        Default annual growth rate percentage
    """
    # Determine which workloads to use
    workload_enums: List[WorkloadType] = []
    
    if workloads:
        try:
            workload_enums = [WorkloadType(w) for w in workloads]
        except ValueError:
            pass
    elif domain:
        # If no workloads provided but domain is, use default workloads for that domain
        try:
            domain_enum = GraphDomain(domain)
            default_workloads = DOMAIN_DEFAULT_WORKLOADS.get(domain_enum, [])
            workload_enums = default_workloads
        except ValueError:
            pass
    
    # Use the fastest-growing workload's default rate
    if workload_enums:
        workload_set = set(workload_enums)
        if WorkloadType.TRANSACTIONAL in workload_set:
            return WORKLOAD_DEFAULT_GROWTH_RATES[WorkloadType.TRANSACTIONAL]
        elif WorkloadType.AGENTIC in workload_set:
            return WORKLOAD_DEFAULT_GROWTH_RATES[WorkloadType.AGENTIC]
        elif WorkloadType.ANALYTICAL in workload_set:
            return WORKLOAD_DEFAULT_GROWTH_RATES[WorkloadType.ANALYTICAL]
    
    # Fallback: if domain provided but has no default workloads, use domain rate
    if domain:
        try:
            domain_enum = GraphDomain(domain)
            return DOMAIN_DEFAULT_GROWTH_RATES.get(domain_enum, 10.0)
        except ValueError:
            pass
    
    return 10.0  # Generic default


def get_component_growth_models(
    workloads: Optional[List[str]] = None,
    domain: Optional[str] = None
) -> Dict[str, GrowthModel]:
    """Get component-based growth models for storage, memory, and vcpu.
    
    Each component can have its own growth model. When multiple workloads are provided,
    uses the fastest-growing model for each component.
    
    Priority:
    1. If workloads provided → use workload-based component models (override)
    2. If domain provided → infer default workloads for domain, then use workload-based models
    3. If domain provided but no default workloads → use domain-based component models
    4. Otherwise → CompoundGrowthModel for all components (default)
    """
    # Determine which workloads to use
    workload_enums: List[WorkloadType] = []
    
    if workloads:
        try:
            workload_enums = [WorkloadType(w) for w in workloads]
        except ValueError:
            pass
    elif domain:
        # If no workloads provided but domain is, use default workloads for that domain
        try:
            domain_enum = GraphDomain(domain)
            default_workloads = DOMAIN_DEFAULT_WORKLOADS.get(domain_enum, [])
            workload_enums = default_workloads
        except ValueError:
            pass
    
    # Use workload-based models if we have workloads
    if workload_enums:
        try:
            workload_set = set(workload_enums)
            component_models = {}
            
            if WorkloadType.TRANSACTIONAL in workload_set:
                component_models["storage"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.TRANSACTIONAL]["storage"]()
                component_models["memory"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.TRANSACTIONAL]["memory"]()
                component_models["vcpu"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.TRANSACTIONAL]["vcpu"]()
            elif WorkloadType.AGENTIC in workload_set:
                component_models["storage"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.AGENTIC]["storage"]()
                component_models["memory"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.AGENTIC]["memory"]()
                component_models["vcpu"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.AGENTIC]["vcpu"]()
            elif WorkloadType.ANALYTICAL in workload_set:
                component_models["storage"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.ANALYTICAL]["storage"]()
                component_models["memory"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.ANALYTICAL]["memory"]()
                component_models["vcpu"] = WORKLOAD_COMPONENT_GROWTH_MODELS[WorkloadType.ANALYTICAL]["vcpu"]()
            else:
                default = CompoundGrowthModel()
                component_models = {"storage": default, "memory": default, "vcpu": default}
            
            return component_models
        except (ValueError, KeyError):
            pass
    
    # Fallback: if domain provided but has no default workloads, use domain models
    if domain:
        try:
            domain_enum = GraphDomain(domain)
            component_models = DOMAIN_COMPONENT_GROWTH_MODELS.get(domain_enum)
            if component_models:
                return {
                    component: model_class()
                    for component, model_class in component_models.items()
                }
        except ValueError:
            pass
    
    # Final fallback: default compound growth for all components
    default_model = CompoundGrowthModel()
    return {
        "storage": default_model,
        "memory": default_model,
        "vcpu": default_model,
    }
