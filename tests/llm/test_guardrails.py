"""
Tests for llm.guardrails module - Parameter validation.
"""

import pytest
from tests.helpers.mocks import MockGuardrails


class TestGuardrails:
    """Test suite for guardrails validation."""
    
    @pytest.mark.unit
    def test_validate_scenario_success(self):
        """Test successful validation."""
        guardrails = MockGuardrails()
        
        result = guardrails.validate_scenario({"test": "scenario"})
        
        assert result["is_valid"] == True
        assert result["quality_score"] > 0
    
    @pytest.mark.unit
    def test_validate_scenario_failure(self):
        """Test failed validation."""
        guardrails = MockGuardrails(should_fail_validation=True)
        
        result = guardrails.validate_scenario({"test": "scenario"})
        
        assert result["is_valid"] == False

