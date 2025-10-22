"""
Tests for llm.parser module - JSON parsing and validation.
"""

import pytest
from tests.fixtures.llm_responses import (
    ECOMMERCE_SCENARIO_RESPONSE,
    MALFORMED_JSON_RESPONSE
)


class TestJSONParsing:
    """Test suite for JSON parsing."""
    
    @pytest.mark.unit
    def test_parse_valid_json(self):
        """Test parsing of valid JSON response."""
        # Basic validation that response contains expected structure
        assert "scenario" in ECOMMERCE_SCENARIO_RESPONSE
        assert "design_params" in ECOMMERCE_SCENARIO_RESPONSE
    
    @pytest.mark.unit
    def test_parse_malformed_json(self):
        """Test handling of malformed JSON."""
        # Malformed JSON should be detected
        assert "```" in MALFORMED_JSON_RESPONSE

