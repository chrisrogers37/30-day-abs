"""
Mock objects and helpers for testing.

This module provides mock implementations of external dependencies,
particularly for LLM clients and external APIs.
"""

from typing import Dict, Any, Optional, List
from unittest.mock import Mock, MagicMock
import json

from tests.fixtures.llm_responses import (
    ECOMMERCE_SCENARIO_RESPONSE,
    SAAS_SCENARIO_RESPONSE,
    create_openai_response
)


# ============================================================================
# Mock LLM Client
# ============================================================================

class MockLLMClient:
    """
    Mock LLM client for testing without making real API calls.
    
    This mock client provides deterministic responses for testing
    the LLM integration layer.
    """
    
    def __init__(
        self,
        response_content: Optional[str] = None,
        should_fail: bool = False,
        failure_type: str = "timeout"
    ):
        """
        Initialize mock LLM client.
        
        Args:
            response_content: Content to return (default: ecommerce scenario)
            should_fail: Whether to simulate failure
            failure_type: Type of failure (timeout, rate_limit, auth)
        """
        self.response_content = response_content or ECOMMERCE_SCENARIO_RESPONSE
        self.should_fail = should_fail
        self.failure_type = failure_type
        self.call_count = 0
        self.last_request = None
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Mock completion generation.
        
        Args:
            messages: List of messages
            **kwargs: Additional arguments
        
        Returns:
            Mock API response
        
        Raises:
            Exception: If should_fail is True
        """
        self.call_count += 1
        self.last_request = {
            "messages": messages,
            "kwargs": kwargs
        }
        
        if self.should_fail:
            if self.failure_type == "rate_limit":
                raise Exception("Rate limit exceeded")
            elif self.failure_type == "timeout":
                raise TimeoutError("Request timeout")
            elif self.failure_type == "auth":
                raise Exception("Authentication failed")
            else:
                raise Exception("Unknown error")
        
        return create_openai_response(self.response_content)
    
    def reset(self):
        """Reset call count and last request."""
        self.call_count = 0
        self.last_request = None


# ============================================================================
# Mock Scenario Generator
# ============================================================================

class MockScenarioGenerator:
    """Mock scenario generator for testing."""
    
    def __init__(
        self,
        scenario_content: Optional[str] = None,
        should_fail: bool = False
    ):
        """
        Initialize mock scenario generator.
        
        Args:
            scenario_content: Scenario JSON content
            should_fail: Whether generation should fail
        """
        self.scenario_content = scenario_content or ECOMMERCE_SCENARIO_RESPONSE
        self.should_fail = should_fail
        self.generation_count = 0
    
    async def generate_scenario(
        self,
        max_attempts: int = 3,
        min_quality_score: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Mock scenario generation.
        
        Args:
            max_attempts: Maximum retry attempts
            min_quality_score: Minimum quality threshold
            **kwargs: Additional arguments
        
        Returns:
            Generation result dictionary
        """
        self.generation_count += 1
        
        if self.should_fail:
            return {
                "success": False,
                "scenario_dto": None,
                "quality_score": 0.0,
                "errors": ["Generation failed"]
            }
        
        # Parse scenario content
        scenario_data = json.loads(
            self.scenario_content.strip().replace("```json", "").replace("```", "")
        )
        
        return {
            "success": True,
            "scenario_dto": scenario_data,
            "quality_score": 0.85,
            "errors": []
        }


# ============================================================================
# Mock Parser
# ============================================================================

class MockParser:
    """Mock LLM output parser for testing."""
    
    def __init__(
        self,
        should_fail_parsing: bool = False,
        should_fail_validation: bool = False
    ):
        """
        Initialize mock parser.
        
        Args:
            should_fail_parsing: Whether JSON parsing should fail
            should_fail_validation: Whether validation should fail
        """
        self.should_fail_parsing = should_fail_parsing
        self.should_fail_validation = should_fail_validation
        self.parse_count = 0
    
    def parse_llm_response(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Mock LLM response parsing.
        
        Args:
            content: LLM response content
        
        Returns:
            Parsing result dictionary
        """
        self.parse_count += 1
        
        if self.should_fail_parsing:
            return {
                "success": False,
                "scenario_dto": None,
                "errors": ["JSON parsing failed"]
            }
        
        if self.should_fail_validation:
            return {
                "success": False,
                "scenario_dto": None,
                "errors": ["Validation failed"]
            }
        
        # Parse and return scenario
        scenario_data = json.loads(
            content.strip().replace("```json", "").replace("```", "")
        )
        
        return {
            "success": True,
            "scenario_dto": scenario_data,
            "errors": []
        }


# ============================================================================
# Mock Guardrails
# ============================================================================

class MockGuardrails:
    """Mock guardrails for parameter validation testing."""
    
    def __init__(
        self,
        should_fail_validation: bool = False,
        quality_score: float = 0.85
    ):
        """
        Initialize mock guardrails.
        
        Args:
            should_fail_validation: Whether validation should fail
            quality_score: Quality score to return
        """
        self.should_fail_validation = should_fail_validation
        self.quality_score = quality_score
        self.validation_count = 0
    
    def validate_scenario(
        self,
        scenario_dto: Any
    ) -> Dict[str, Any]:
        """
        Mock scenario validation.
        
        Args:
            scenario_dto: Scenario to validate
        
        Returns:
            Validation result dictionary
        """
        self.validation_count += 1
        
        if self.should_fail_validation:
            return {
                "is_valid": False,
                "errors": ["Parameter out of bounds"],
                "quality_score": 0.3
            }
        
        return {
            "is_valid": True,
            "errors": [],
            "quality_score": self.quality_score
        }


# ============================================================================
# Mock Helper Functions
# ============================================================================

def create_mock_llm_client(
    response_content: Optional[str] = None,
    should_fail: bool = False
) -> MockLLMClient:
    """
    Create a mock LLM client.
    
    Args:
        response_content: Content to return
        should_fail: Whether to simulate failure
    
    Returns:
        MockLLMClient instance
    """
    return MockLLMClient(
        response_content=response_content,
        should_fail=should_fail
    )


def create_mock_scenario_generator(
    scenario_content: Optional[str] = None
) -> MockScenarioGenerator:
    """
    Create a mock scenario generator.
    
    Args:
        scenario_content: Scenario content to return
    
    Returns:
        MockScenarioGenerator instance
    """
    return MockScenarioGenerator(scenario_content=scenario_content)


def create_mock_streamlit_session_state() -> MagicMock:
    """
    Create a mock Streamlit session state.
    
    Returns:
        MagicMock configured to behave like st.session_state
    """
    mock_state = MagicMock()
    mock_state.__contains__ = lambda self, key: key in mock_state._data
    mock_state.__getitem__ = lambda self, key: mock_state._data[key]
    mock_state.__setitem__ = lambda self, key, value: mock_state._data.__setitem__(key, value)
    mock_state._data = {}
    return mock_state


def create_mock_openai_client() -> Mock:
    """
    Create a mock OpenAI client.
    
    Returns:
        Mock object configured like OpenAI client
    """
    mock_client = Mock()
    mock_completion = Mock()
    mock_completion.choices = [
        Mock(message=Mock(content=ECOMMERCE_SCENARIO_RESPONSE))
    ]
    mock_client.chat.completions.create.return_value = mock_completion
    return mock_client


# ============================================================================
# Response Builders
# ============================================================================

def build_mock_api_response(
    content: str,
    status_code: int = 200,
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Build a mock API response.
    
    Args:
        content: Response content
        status_code: HTTP status code
        model: Model name
    
    Returns:
        Mock API response dictionary
    """
    if status_code != 200:
        return {
            "error": {
                "message": "API error",
                "type": "api_error",
                "code": status_code
            }
        }
    
    return create_openai_response(content, model=model)


def build_mock_scenario_response(
    company_type: str = "E-commerce",
    baseline: float = 0.025,
    lift: float = 0.20
) -> str:
    """
    Build a mock scenario response with custom parameters.
    
    Args:
        company_type: Company type
        baseline: Baseline conversion rate
        lift: Target lift percentage
    
    Returns:
        JSON string representing scenario
    """
    scenario = {
        "scenario": {
            "title": f"{company_type} Test Scenario",
            "company_type": company_type,
            "user_segment": "all_users",
            "description": "Mock scenario for testing",
            "intervention_description": "Test intervention",
            "primary_metric": "Conversion rate",
            "hypothesis": f"Will improve conversion by {lift*100}%"
        },
        "design_params": {
            "baseline_conversion_rate": baseline,
            "mde_absolute": baseline * lift * 0.5,
            "target_lift_pct": lift,
            "alpha": 0.05,
            "power": 0.80,
            "allocation": {"control": 0.5, "treatment": 0.5},
            "expected_daily_traffic": 5000
        }
    }
    
    return f"```json\n{json.dumps(scenario, indent=2)}\n```"


# ============================================================================
# Assertion Helpers for Mocks
# ============================================================================

def assert_mock_called_with_content(
    mock_client: MockLLMClient,
    expected_content_substring: str
):
    """
    Assert that mock was called with expected content.
    
    Args:
        mock_client: Mock LLM client
        expected_content_substring: Expected substring in request
    
    Raises:
        AssertionError: If mock wasn't called with expected content
    """
    if mock_client.call_count == 0:
        raise AssertionError("Mock client was never called")
    
    if mock_client.last_request is None:
        raise AssertionError("No request recorded")
    
    messages = mock_client.last_request.get("messages", [])
    found = any(
        expected_content_substring in msg.get("content", "")
        for msg in messages
    )
    
    if not found:
        raise AssertionError(
            f"Expected substring '{expected_content_substring}' not found in messages"
        )


def assert_mock_call_count(
    mock_obj: Any,
    expected_count: int,
    obj_name: str = "Mock"
):
    """
    Assert that mock was called expected number of times.
    
    Args:
        mock_obj: Mock object with call_count attribute
        expected_count: Expected call count
        obj_name: Name of object for error message
    
    Raises:
        AssertionError: If call count doesn't match
    """
    actual_count = getattr(mock_obj, "call_count", 0)
    if actual_count != expected_count:
        raise AssertionError(
            f"{obj_name} called {actual_count} times, expected {expected_count}"
        )

