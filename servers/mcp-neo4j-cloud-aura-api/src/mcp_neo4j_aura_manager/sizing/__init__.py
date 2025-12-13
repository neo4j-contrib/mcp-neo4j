"""
Aura Sizing Module

Provides tools for calculating Neo4j database sizing based on graph metrics.
"""

from .calculator import Neo4jSizingCalculator
from .interfaces import SizingCalculatorProtocol
from .models import Neo4jSizingCalculationResult
from .projector import GrowthProjector
from .service import AuraSizingService
from .models import (
    SizingResult,
    ForecastResult,
    SizingCalculations,
    YearProjection,
    SizingMetadata,
)

__all__ = [
    "Neo4jSizingCalculator",
    "SizingCalculator",  # Backward compatibility alias
    "SizingCalculatorProtocol",
    "Neo4jSizingCalculationResult",
    "GrowthProjector",
    "AuraSizingService",
    "SizingResult",
    "ForecastResult",
    "SizingCalculations",
    "YearProjection",
    "SizingMetadata",
]
