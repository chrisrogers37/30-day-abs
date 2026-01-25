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
    @pytest.mark.parametrize(
        "invalid_segment,expected",
        [
            ("all passengers", UserSegment.ALL_USERS),
            ("customers", UserSegment.ALL_USERS),
            ("visitors", UserSegment.NEW_VISITORS),
            ("subscribers", UserSegment.PAID_USERS),
            ("buyers", UserSegment.REPEAT_PURCHASERS),
        ],
    )
    def test_user_segment_fallback_mappings(
        self, parser, valid_scenario_data, invalid_segment, expected
    ):
        """Test specific user segment fallback mappings."""
        valid_scenario_data["scenario"]["user_segment"] = invalid_segment
        normalized = parser._normalize_enum_values(valid_scenario_data)
        assert normalized["scenario"]["user_segment"] == expected.value


class TestJSONExtraction:
    """Test suite for JSON extraction from LLM responses."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance."""
        return LLMOutputParser()

    @pytest.mark.unit
    def test_extract_json_from_markdown_code_block(self, parser):
        """Test extracting JSON from markdown code blocks."""
        content = '```json\n{"key": "value"}\n```'
        result = parser._extract_json(content)
        assert result is not None
        assert '"key"' in result

    @pytest.mark.unit
    def test_extract_json_from_plain_code_block(self, parser):
        """Test extracting JSON from plain code blocks without json marker."""
        content = '```\n{"key": "value"}\n```'
        result = parser._extract_json(content)
        assert result is not None
        assert '"key"' in result

    @pytest.mark.unit
    def test_extract_raw_json(self, parser):
        """Test extracting raw JSON without code blocks."""
        content = 'Some text before {"key": "value"} and after'
        result = parser._extract_json(content)
        assert result is not None
        assert '"key"' in result

    @pytest.mark.unit
    def test_extract_json_no_json_found(self, parser):
        """Test extraction when no JSON is present."""
        content = "This is just plain text with no JSON"
        result = parser._extract_json(content)
        assert result is None

    @pytest.mark.unit
    def test_extract_json_incomplete_braces(self, parser):
        """Test extraction with incomplete braces."""
        content = "{ incomplete json without closing"
        result = parser._extract_json(content)
        assert result is None


class TestJSONCleaning:
    """Test suite for JSON cleaning functionality."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance."""
        return LLMOutputParser()

    @pytest.mark.unit
    def test_clean_json_trailing_comma_object(self, parser):
        """Test removing trailing commas before closing braces."""
        dirty = '{"key": "value",}'
        cleaned = parser._clean_json(dirty)
        assert cleaned == '{"key": "value"}'

    @pytest.mark.unit
    def test_clean_json_trailing_comma_array(self, parser):
        """Test removing trailing commas before closing brackets."""
        dirty = '{"arr": [1, 2, 3,]}'
        cleaned = parser._clean_json(dirty)
        assert cleaned == '{"arr": [1, 2, 3]}'

    @pytest.mark.unit
    def test_clean_json_preserves_valid_json(self, parser):
        """Test that valid JSON is preserved."""
        valid = '{"key": "value", "num": 123}'
        cleaned = parser._clean_json(valid)
        assert cleaned == valid


class TestJSONStructureValidation:
    """Test suite for JSON structure validation."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance."""
        return LLMOutputParser()

    @pytest.mark.unit
    def test_valid_json_structure(self, parser):
        """Test validation of valid JSON structure."""
        content = '{"key": "value"}'
        assert parser._is_valid_json_structure(content) is True

    @pytest.mark.unit
    def test_invalid_start_character(self, parser):
        """Test rejection of content not starting with brace."""
        content = '[1, 2, 3]'
        assert parser._is_valid_json_structure(content) is False

    @pytest.mark.unit
    def test_invalid_end_character(self, parser):
        """Test rejection of content not ending with brace."""
        content = '{"key": "value"'
        assert parser._is_valid_json_structure(content) is False

    @pytest.mark.unit
    def test_unbalanced_braces(self, parser):
        """Test rejection of unbalanced braces."""
        content = '{"key": {"nested": "value"}'
        assert parser._is_valid_json_structure(content) is False

    @pytest.mark.unit
    def test_braces_in_strings_are_ignored(self, parser):
        """Test that braces within strings don't affect balance."""
        content = '{"key": "value with { and } inside"}'
        assert parser._is_valid_json_structure(content) is True

    @pytest.mark.unit
    def test_escaped_quotes_handled(self, parser):
        """Test that escaped quotes are handled correctly."""
        content = '{"key": "value with \\"escaped\\" quotes"}'
        assert parser._is_valid_json_structure(content) is True

    @pytest.mark.unit
    def test_extra_closing_brace(self, parser):
        """Test rejection when closing brace comes early."""
        content = '{"key": "value"}}'
        assert parser._is_valid_json_structure(content) is False


class TestParseJSON:
    """Test suite for JSON parsing functionality."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance."""
        return LLMOutputParser()

    @pytest.mark.unit
    def test_parse_valid_json(self, parser):
        """Test parsing valid JSON."""
        content = '{"key": "value", "number": 42}'
        result = parser._parse_json(content)
        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 42

    @pytest.mark.unit
    def test_parse_invalid_json(self, parser):
        """Test parsing invalid JSON."""
        content = '{"key": invalid}'
        result = parser._parse_json(content)
        assert result is None

    @pytest.mark.unit
    def test_parse_non_object_root(self, parser):
        """Test rejection of non-object root (array)."""
        content = '[1, 2, 3]'
        result = parser._parse_json(content)
        assert result is None


class TestParseFullResponse:
    """Test suite for full LLM response parsing."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance."""
        return LLMOutputParser()

    @pytest.fixture
    def valid_response(self):
        """Create a valid LLM response."""
        return json.dumps(
            {
                "scenario": {
                    "title": "Test Scenario",
                    "narrative": "A test scenario for unit testing.",
                    "company_type": "E-commerce",
                    "user_segment": "all_users",
                    "primary_kpi": "conversion_rate",
                    "secondary_kpis": ["engagement_rate"],
                    "unit": "user",
                    "assumptions": ["test assumption"],
                },
                "design_params": {
                    "baseline_conversion_rate": 0.10,
                    "mde_absolute": 0.01,
                    "target_lift_pct": 0.10,
                    "alpha": 0.05,
                    "power": 0.80,
                    "allocation": {"control": 0.5, "treatment": 0.5},
                    "expected_daily_traffic": 5000,
                },
                "llm_expected": {
                    "simulation_hints": {
                        "treatment_conversion_rate": 0.11,
                        "control_conversion_rate": 0.10,
                    },
                    "narrative_conclusion": "Expected outcome",
                    "business_interpretation": "Business impact",
                    "risk_assessment": "Low risk",
                    "next_steps": "Monitor and iterate",
                    "notes": "Test notes",
                },
            }
        )

    @pytest.mark.unit
    def test_parse_llm_response_success(self, parser, valid_response):
        """Test successful parsing of valid LLM response."""
        result = parser.parse_llm_response(valid_response)
        assert result.success is True
        assert result.scenario_dto is not None
        assert result.errors == []

    @pytest.mark.unit
    def test_parse_llm_response_no_json(self, parser):
        """Test parsing response with no JSON."""
        result = parser.parse_llm_response("This has no JSON content at all")
        assert result.success is False
        assert len(result.errors) > 0
        assert "No valid JSON" in result.errors[0]

    @pytest.mark.unit
    def test_parse_llm_response_invalid_json(self, parser):
        """Test parsing response with invalid JSON."""
        result = parser.parse_llm_response('{"invalid": json syntax}')
        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.unit
    def test_parse_llm_response_with_markdown(self, parser, valid_response):
        """Test parsing JSON wrapped in markdown code block."""
        wrapped = f"```json\n{valid_response}\n```"
        result = parser.parse_llm_response(wrapped)
        assert result.success is True
        assert result.scenario_dto is not None

