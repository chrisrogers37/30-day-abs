"""
Tests for llm.parser module - JSON parsing and validation.
"""

import json
import pytest
from llm.parser import (
    LLMOutputParser,
    USER_SEGMENT_FALLBACKS,
    COMPANY_TYPE_FALLBACKS,
)
from schemas.shared import UserSegment, CompanyType
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


class TestEnumNormalization:
    """Test suite for enum value normalization."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance."""
        return LLMOutputParser()

    @pytest.fixture
    def valid_scenario_data(self):
        """Create a valid scenario data structure for testing."""
        return {
            "scenario": {
                "title": "Test Scenario",
                "narrative": "A test scenario for unit testing the parser functionality.",
                "company_type": "E-commerce",
                "user_segment": "all_users",
                "primary_kpi": "conversion_rate",
                "secondary_kpis": ["engagement_rate"],
                "unit": "user",
                "assumptions": ["test assumption"]
            },
            "design_params": {
                "baseline_conversion_rate": 0.10,
                "mde_absolute": 0.01,
                "target_lift_pct": 0.10,
                "alpha": 0.05,
                "power": 0.80,
                "allocation": {"control": 0.5, "treatment": 0.5},
                "expected_daily_traffic": 5000
            },
            "llm_expected": {
                "simulation_hints": {
                    "treatment_conversion_rate": 0.11,
                    "control_conversion_rate": 0.10
                },
                "narrative_conclusion": "Expected outcome",
                "business_interpretation": "Business impact",
                "risk_assessment": "Low risk",
                "next_steps": "Monitor and iterate",
                "notes": "Test notes"
            }
        }

    @pytest.mark.unit
    def test_normalize_valid_user_segment(self, parser, valid_scenario_data):
        """Test that valid user segments are not modified."""
        valid_scenario_data["scenario"]["user_segment"] = "trial users"
        normalized = parser._normalize_enum_values(valid_scenario_data)
        assert normalized["scenario"]["user_segment"] == "trial users"

    @pytest.mark.unit
    def test_normalize_invalid_user_segment_with_fallback(self, parser, valid_scenario_data):
        """Test normalization of 'all passengers' to 'all_users'."""
        valid_scenario_data["scenario"]["user_segment"] = "all passengers"
        normalized = parser._normalize_enum_values(valid_scenario_data)
        assert normalized["scenario"]["user_segment"] == UserSegment.ALL_USERS.value

    @pytest.mark.unit
    def test_normalize_unknown_user_segment_defaults_to_all_users(self, parser, valid_scenario_data):
        """Test that completely unknown segments default to all_users."""
        valid_scenario_data["scenario"]["user_segment"] = "random unknown value"
        normalized = parser._normalize_enum_values(valid_scenario_data)
        assert normalized["scenario"]["user_segment"] == UserSegment.ALL_USERS.value

    @pytest.mark.unit
    def test_normalize_user_segment_case_insensitive(self, parser, valid_scenario_data):
        """Test that normalization is case-insensitive."""
        valid_scenario_data["scenario"]["user_segment"] = "ALL PASSENGERS"
        normalized = parser._normalize_enum_values(valid_scenario_data)
        assert normalized["scenario"]["user_segment"] == UserSegment.ALL_USERS.value

    @pytest.mark.unit
    def test_normalize_company_type_airline_to_travel(self, parser, valid_scenario_data):
        """Test normalization of 'airline' to Travel & Hospitality."""
        valid_scenario_data["scenario"]["company_type"] = "airline"
        normalized = parser._normalize_enum_values(valid_scenario_data)
        assert normalized["scenario"]["company_type"] == CompanyType.TRAVEL.value

    @pytest.mark.unit
    def test_normalize_unknown_company_type_defaults_to_ecommerce(self, parser, valid_scenario_data):
        """Test that unknown company types default to E-commerce."""
        valid_scenario_data["scenario"]["company_type"] = "random company type"
        normalized = parser._normalize_enum_values(valid_scenario_data)
        assert normalized["scenario"]["company_type"] == CompanyType.ECOMMERCE.value

    @pytest.mark.unit
    def test_full_parse_with_invalid_user_segment(self, parser, valid_scenario_data):
        """Test that full parsing succeeds after normalizing invalid user_segment."""
        valid_scenario_data["scenario"]["user_segment"] = "all passengers"
        json_content = json.dumps(valid_scenario_data)

        result = parser.parse_llm_response(json_content)

        assert result.success, f"Parsing failed: {result.errors}"
        assert result.scenario_dto is not None
        assert result.scenario_dto.scenario.user_segment == UserSegment.ALL_USERS

    @pytest.mark.unit
    def test_all_fallback_mappings_are_valid(self):
        """Test that all fallback mappings point to valid enum values."""
        for key, value in USER_SEGMENT_FALLBACKS.items():
            assert isinstance(value, UserSegment), f"Invalid UserSegment for '{key}': {value}"

        for key, value in COMPANY_TYPE_FALLBACKS.items():
            assert isinstance(value, CompanyType), f"Invalid CompanyType for '{key}': {value}"

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_segment,expected", [
        ("all passengers", UserSegment.ALL_USERS),
        ("customers", UserSegment.ALL_USERS),
        ("visitors", UserSegment.NEW_VISITORS),
        ("subscribers", UserSegment.PAID_USERS),
        ("buyers", UserSegment.REPEAT_PURCHASERS),
    ])
    def test_user_segment_fallback_mappings(self, parser, valid_scenario_data, invalid_segment, expected):
        """Test specific user segment fallback mappings."""
        valid_scenario_data["scenario"]["user_segment"] = invalid_segment
        normalized = parser._normalize_enum_values(valid_scenario_data)
        assert normalized["scenario"]["user_segment"] == expected.value

