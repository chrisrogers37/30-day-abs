"""
API schemas and DTOs for AB Test Simulator.

This package contains Pydantic models for API boundaries, JSON serialization,
and validation. These are separate from core domain types to maintain
clean separation of concerns.
"""

# Import all schemas
from .shared import *
from .scenario import *
from .design import *
from .simulate import *
from .analyze import *
from .evaluation import *

# Rebuild models to resolve forward references
try:
    from .scenario import ScenarioResponseDTO
    ScenarioResponseDTO.model_rebuild()
except Exception:
    # If rebuild fails, it's not critical for basic functionality
    pass