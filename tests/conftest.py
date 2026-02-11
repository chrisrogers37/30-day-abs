"""
Shared pytest fixtures for all tests.

This module contains reusable fixtures that are available to all test modules.
Fixtures include standard test data, mock objects, and common configurations.
"""

import os
import sys
from typing import Dict, Any
import pytest
import numpy as np

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.types import Allocation, DesignParams, SimResult
from schemas.shared import AllocationDTO


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    Test configuration dictionary.
    
    Returns:
        Dictionary containing test configuration values
    """
    return {
        "environment": "test",
        "llm_provider": "mock",
        "random_seed": 42,
        "tolerance_percentage": 0.05,
        "tolerance_absolute": 0.001,
    }


@pytest.fixture(scope="function")
def reset_random_seed():
    """Reset numpy random seed before each test for reproducibility."""
    np.random.seed(42)
    yield
    np.random.seed(None)


# ============================================================================
# Core Module Fixtures
# ============================================================================

@pytest.fixture
def standard_allocation() -> Allocation:
    """
    Standard 50/50 allocation for testing.
    
    Returns:
        Allocation object with equal split
    """
    return Allocation(control=0.5, treatment=0.5)


@pytest.fixture
def unbalanced_allocation() -> Allocation:
    """
    Unbalanced 70/30 allocation for testing.
    
    Returns:
        Allocation object with unbalanced split
    """
    return Allocation(control=0.7, treatment=0.3)


@pytest.fixture
def standard_design_params(standard_allocation) -> DesignParams:
    """
    Standard design parameters for testing.
    
    Args:
        standard_allocation: 50/50 allocation fixture
    
    Returns:
        DesignParams with typical test values
    """
    return DesignParams(
        baseline_conversion_rate=0.05,
        target_lift_pct=0.15,
        alpha=0.05,
        power=0.8,
        allocation=standard_allocation,
        expected_daily_traffic=10000
    )


@pytest.fixture
def high_baseline_design_params(standard_allocation) -> DesignParams:
    """
    Design parameters with high baseline conversion rate.
    
    Args:
        standard_allocation: 50/50 allocation fixture
    
    Returns:
        DesignParams with high baseline rate
    """
    return DesignParams(
        baseline_conversion_rate=0.25,
        target_lift_pct=0.10,
        alpha=0.05,
        power=0.8,
        allocation=standard_allocation,
        expected_daily_traffic=10000
    )


@pytest.fixture
def low_baseline_design_params(standard_allocation) -> DesignParams:
    """
    Design parameters with low baseline conversion rate.
    
    Args:
        standard_allocation: 50/50 allocation fixture
    
    Returns:
        DesignParams with low baseline rate
    """
    return DesignParams(
        baseline_conversion_rate=0.01,
        target_lift_pct=0.20,
        alpha=0.05,
        power=0.8,
        allocation=standard_allocation,
        expected_daily_traffic=10000
    )


@pytest.fixture
def simple_sim_result() -> SimResult:
    """
    Simple simulation result for testing analysis functions.
    
    Returns:
        SimResult with predetermined values
    """
    return SimResult(
        control_n=1000,
        control_conversions=50,
        treatment_n=1000,
        treatment_conversions=60
    )


@pytest.fixture
def significant_sim_result() -> SimResult:
    """
    Simulation result with statistically significant difference.
    
    Returns:
        SimResult with significant treatment effect
    """
    return SimResult(
        control_n=5000,
        control_conversions=250,
        treatment_n=5000,
        treatment_conversions=325
    )


@pytest.fixture
def non_significant_sim_result() -> SimResult:
    """
    Simulation result without statistically significant difference.
    
    Returns:
        SimResult with minimal treatment effect
    """
    return SimResult(
        control_n=500,
        control_conversions=25,
        treatment_n=500,
        treatment_conversions=27
    )


# ============================================================================
# Schema/DTO Fixtures
# ============================================================================

@pytest.fixture
def standard_allocation_dto() -> AllocationDTO:
    """
    Standard 50/50 allocation DTO for testing.
    
    Returns:
        AllocationDTO with equal split
    """
    return AllocationDTO(control=0.5, treatment=0.5)


@pytest.fixture
def sample_scenario_dict() -> Dict[str, Any]:
    """
    Sample scenario dictionary for LLM testing.
    
    Returns:
        Dictionary representing a complete scenario
    """
    return {
        "scenario": {
            "title": "E-commerce Product Page Redesign",
            "company_type": "E-commerce",
            "user_segment": "all_users",
            "description": "Testing a new product page layout to improve conversion rates.",
            "intervention_description": "Redesigned product page with larger images and clearer CTA",
            "primary_metric": "Purchase conversion rate",
            "hypothesis": "New design will increase purchase rate by 15%",
        },
        "design_params": {
            "baseline_conversion_rate": 0.025,
            "mde_absolute": 0.00375,
            "target_lift_pct": 0.15,
            "alpha": 0.05,
            "power": 0.80,
            "allocation": {"control": 0.5, "treatment": 0.5},
            "expected_daily_traffic": 5000,
        },
        "business_context": {
            "business_target_absolute": 0.005,
            "business_target_relative_pct": 0.20,
            "revenue_per_conversion": 50.0,
            "implementation_cost": 5000.0,
            "risk_tolerance": "medium",
        },
    }


@pytest.fixture
def mock_llm_response_json() -> str:
    """
    Mock LLM response as JSON string.
    
    Returns:
        JSON string representing LLM scenario output
    """
    return """
    {
        "scenario": {
            "title": "Mobile App Onboarding Flow Optimization",
            "company_type": "SaaS",
            "user_segment": "new_users",
            "description": "Testing simplified onboarding to increase activation",
            "intervention_description": "Reduced onboarding from 5 steps to 3 steps",
            "primary_metric": "Activation rate",
            "hypothesis": "Simpler onboarding will increase activation by 20%"
        },
        "design_params": {
            "baseline_conversion_rate": 0.15,
            "mde_absolute": 0.03,
            "target_lift_pct": 0.20,
            "alpha": 0.05,
            "power": 0.80,
            "allocation": {"control": 0.5, "treatment": 0.5},
            "expected_daily_traffic": 2000
        },
        "business_context": {
            "business_target_absolute": 0.02,
            "business_target_relative_pct": 0.133,
            "revenue_per_conversion": 100.0,
            "implementation_cost": 10000.0,
            "risk_tolerance": "medium"
        }
    }
    """


# ============================================================================
# Parametrize Data Fixtures
# ============================================================================

@pytest.fixture(params=[
    (0.05, 0.10, 0.05, 0.80),
    (0.05, 0.15, 0.05, 0.80),
    (0.05, 0.20, 0.05, 0.80),
    (0.10, 0.15, 0.05, 0.80),
    (0.15, 0.20, 0.05, 0.80),
])
def sample_size_params(request, standard_allocation):
    """
    Parametrized design parameters for sample size testing.
    
    Args:
        request: Pytest request object with parameters
        standard_allocation: 50/50 allocation fixture
    
    Returns:
        DesignParams with various parameter combinations
    """
    baseline, lift, alpha, power = request.param
    return DesignParams(
        baseline_conversion_rate=baseline,
        target_lift_pct=lift,
        alpha=alpha,
        power=power,
        allocation=standard_allocation,
        expected_daily_traffic=10000
    )


# ============================================================================
# Mock and Spy Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_response():
    """
    Mock OpenAI API response for testing.
    
    Returns:
        Dictionary mimicking OpenAI API response structure
    """
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"scenario": {"title": "Test Scenario"}}'
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


# ============================================================================
# File and Path Fixtures
# ============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Temporary directory for test outputs.
    
    Args:
        tmp_path: Pytest temporary path fixture
    
    Returns:
        Path to temporary directory
    """
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_csv_data() -> str:
    """
    Sample CSV data for testing data export.
    
    Returns:
        CSV string with sample user data
    """
    return """user_id,group,converted,timestamp,session_duration,page_views,device_type,traffic_source
user_1,control,true,2024-01-15T10:30:00,120,5,mobile,organic
user_2,control,false,2024-01-15T10:35:00,45,2,desktop,paid
user_3,treatment,true,2024-01-15T10:40:00,150,7,mobile,organic
user_4,treatment,false,2024-01-15T10:45:00,30,1,desktop,direct
"""


# ============================================================================
# Tolerance and Comparison Fixtures
# ============================================================================

@pytest.fixture
def tolerance_percentage() -> float:
    """
    Standard percentage tolerance for floating-point comparisons.
    
    Returns:
        Tolerance value (5%)
    """
    return 0.05


@pytest.fixture
def tolerance_absolute() -> float:
    """
    Standard absolute tolerance for floating-point comparisons.
    
    Returns:
        Tolerance value (0.001)
    """
    return 0.001


# ============================================================================
# Environment and Configuration
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup test environment variables.
    
    This fixture runs once per test session and sets up the test environment.
    """
    # Set environment to test mode
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LLM_PROVIDER"] = "mock"
    
    # Disable any external API calls
    os.environ["DISABLE_EXTERNAL_CALLS"] = "true"
    
    yield
    
    # Cleanup after all tests
    os.environ.pop("ENVIRONMENT", None)
    os.environ.pop("LLM_PROVIDER", None)
    os.environ.pop("DISABLE_EXTERNAL_CALLS", None)


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """
    Pytest configuration hook.
    
    Registers custom markers and configures the test environment.
    """
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "requires_api: mark test as requiring real API calls"
    )

