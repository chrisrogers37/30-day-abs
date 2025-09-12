"""
Core domain logic for AB Test Simulator.

This module contains pure, deterministic domain logic with no HTTP, no LLM calls,
and no global state. All mathematical calculations are performed here.
"""

from .types import (
    Allocation,
    DesignParams,
    SampleSize,
    SimResult,
    AnalysisResult,
    BusinessImpact,
    TestQuality,
)

__all__ = [
    "Allocation",
    "DesignParams", 
    "SampleSize",
    "SimResult",
    "AnalysisResult",
    "BusinessImpact",
    "TestQuality",
]
