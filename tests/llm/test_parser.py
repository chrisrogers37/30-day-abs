"""Tests for llm.parser module - JSON parsing and validation."""

import json
import pytest

from llm.parser import LLMOutputParser, ParsingResult


@pytest.fixture
def parser():
    """Create a fresh parser instance."""
    return LLMOutputParser()


# A valid scenario JSON that matches the ScenarioResponseDTO schema
VALID_SCENARIO_JSON = {
    "scenario": {
        "title": "Checkout Button Color Test",
        "narrative": "Testing green vs blue checkout button.",
        "company_type": "E-commerce",
        "user_segment": "all_users",
        "primary_kpi": "conversion_rate",
        "secondary_kpis": ["revenue_per_visitor"],
        "unit": "visitor",
        "assumptions": ["steady traffic"],
    },
    "design_params": {
        "baseline_conversion_rate": 0.025,
        "mde_absolute": 0.005,
        "target_lift_pct": 0.20,
        "alpha": 0.05,
        "power": 0.80,
        "allocation": {"control": 0.5, "treatment": 0.5},
        "expected_daily_traffic": 5000,
    },
    "llm_expected": {
        "simulation_hints": {
            "treatment_conversion_rate": 0.030,
            "control_conversion_rate": 0.025,
        },
        "narrative_conclusion": "Expected 20% lift.",
        "business_interpretation": "Significant revenue impact.",
        "risk_assessment": "Low risk.",
        "next_steps": "Monitor for 2 weeks.",
        "notes": "Test notes.",
    },
}


class TestParsingResult:
    """Tests for the ParsingResult dataclass."""

    def test_default_values(self):
        result = ParsingResult(success=False)
        assert result.success is False
        assert result.errors == []
        assert result.warnings == []
        assert result.scenario_dto is None

    def test_none_lists_initialized(self):
        result = ParsingResult(success=True, errors=None, warnings=None)
        assert result.errors == []
        assert result.warnings == []


class TestExtractJson:
    """Tests for JSON extraction from various LLM response formats."""

    def test_extract_from_markdown_code_block(self, parser):
        content = '```json\n{"key": "value"}\n```'
        result = parser._extract_json(content)
        assert result is not None
        assert '"key"' in result

    def test_extract_from_generic_code_block(self, parser):
        content = '```\n{"key": "value"}\n```'
        result = parser._extract_json(content)
        assert result is not None

    def test_extract_raw_json(self, parser):
        content = '{"key": "value"}'
        result = parser._extract_json(content)
        assert result is not None

    def test_extract_json_with_surrounding_text(self, parser):
        content = 'Here is the result:\n{"key": "value"}\nThat is the JSON.'
        result = parser._extract_json(content)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_no_json_returns_none(self, parser):
        content = "This is just plain text with no JSON at all."
        result = parser._extract_json(content)
        assert result is None

    def test_empty_string(self, parser):
        result = parser._extract_json("")
        assert result is None


class TestCleanJson:
    """Tests for JSON cleanup."""

    def test_removes_trailing_commas(self, parser):
        content = '{"a": 1, "b": 2,}'
        cleaned = parser._clean_json(content)
        assert cleaned == '{"a": 1, "b": 2}'

    def test_removes_trailing_comma_in_array(self, parser):
        content = '{"a": [1, 2,]}'
        cleaned = parser._clean_json(content)
        assert cleaned == '{"a": [1, 2]}'

    def test_strips_whitespace(self, parser):
        content = '  {"a": 1}  '
        cleaned = parser._clean_json(content)
        assert cleaned == '{"a": 1}'


class TestIsValidJsonStructure:
    """Tests for JSON structure validation."""

    def test_valid_json_object(self, parser):
        assert parser._is_valid_json_structure('{"key": "value"}') is True

    def test_empty_object(self, parser):
        assert parser._is_valid_json_structure('{}') is True

    def test_nested_object(self, parser):
        assert parser._is_valid_json_structure('{"a": {"b": 1}}') is True

    def test_not_starting_with_brace(self, parser):
        assert parser._is_valid_json_structure('[1, 2, 3]') is False

    def test_unbalanced_braces(self, parser):
        assert parser._is_valid_json_structure('{"a": 1') is False

    def test_empty_string(self, parser):
        assert parser._is_valid_json_structure('') is False


class TestParseJson:
    """Tests for JSON parsing."""

    def test_parse_valid_json(self, parser):
        result = parser._parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_invalid_json(self, parser):
        result = parser._parse_json('{invalid}')
        assert result is None
        assert len(parser.parsing_errors) > 0

    def test_parse_non_object(self, parser):
        """JSON arrays should be rejected (root must be object)."""
        result = parser._parse_json('[1, 2, 3]')
        assert result is None

    def test_parse_nested_json(self, parser):
        data = '{"a": {"b": [1, 2]}, "c": true}'
        result = parser._parse_json(data)
        assert result["a"]["b"] == [1, 2]
        assert result["c"] is True


class TestValidateSchema:
    """Tests for Pydantic schema validation."""

    def test_valid_scenario_passes(self, parser):
        result = parser._validate_schema(VALID_SCENARIO_JSON)
        assert result is not None
        assert result.scenario.title == "Checkout Button Color Test"

    def test_missing_scenario_key_fails(self, parser):
        data = {
            "design_params": VALID_SCENARIO_JSON["design_params"],
            "llm_expected": VALID_SCENARIO_JSON["llm_expected"],
        }
        result = parser._validate_schema(data)
        assert result is None

    def test_missing_design_params_fails(self, parser):
        data = {
            "scenario": VALID_SCENARIO_JSON["scenario"],
            "llm_expected": VALID_SCENARIO_JSON["llm_expected"],
        }
        result = parser._validate_schema(data)
        assert result is None

    def test_missing_llm_expected_fails(self, parser):
        data = {
            "scenario": VALID_SCENARIO_JSON["scenario"],
            "design_params": VALID_SCENARIO_JSON["design_params"],
        }
        result = parser._validate_schema(data)
        assert result is None

    def test_invalid_design_params_fails(self, parser):
        data = dict(VALID_SCENARIO_JSON)
        data["design_params"] = {
            "baseline_conversion_rate": 5.0,  # out of range
            "mde_absolute": 0.005,
            "target_lift_pct": 0.20,
            "alpha": 0.05,
            "power": 0.80,
            "allocation": {"control": 0.5, "treatment": 0.5},
            "expected_daily_traffic": 5000,
        }
        result = parser._validate_schema(data)
        assert result is None


class TestValidateBusinessLogic:
    """Tests for business logic validation."""

    def test_consistent_data_no_warnings(self, parser):
        data = {
            "design_params": {
                "baseline_conversion_rate": 0.025,
                "target_lift_pct": 0.20,
                "allocation": {"control": 0.5, "treatment": 0.5},
                "expected_daily_traffic": 5000,
            },
            "llm_expected": {
                "simulation_hints": {
                    "control_conversion_rate": 0.025,
                    "treatment_conversion_rate": 0.030,
                },
            },
        }
        result = ParsingResult(success=True)
        parser._validate_business_logic(data, result)
        # No warnings for baseline mismatch
        baseline_warnings = [w for w in result.warnings if "Baseline" in w]
        assert len(baseline_warnings) == 0

    def test_mismatched_baseline_warns(self, parser):
        data = {
            "design_params": {
                "baseline_conversion_rate": 0.025,
                "allocation": {"control": 0.5, "treatment": 0.5},
                "expected_daily_traffic": 5000,
            },
            "llm_expected": {
                "simulation_hints": {
                    "control_conversion_rate": 0.050,  # mismatch
                },
            },
        }
        result = ParsingResult(success=True)
        parser._validate_business_logic(data, result)
        assert any("Baseline" in w or "baseline" in w.lower() for w in result.warnings)

    def test_low_traffic_warns(self, parser):
        data = {
            "design_params": {
                "expected_daily_traffic": 100,
                "allocation": {},
            },
            "llm_expected": {"simulation_hints": {}},
        }
        result = ParsingResult(success=True)
        parser._validate_business_logic(data, result)
        assert any("traffic" in w.lower() for w in result.warnings)

    def test_allocation_sum_mismatch_warns(self, parser):
        data = {
            "design_params": {
                "allocation": {"control": 0.6, "treatment": 0.6},
                "expected_daily_traffic": 5000,
            },
            "llm_expected": {"simulation_hints": {}},
        }
        result = ParsingResult(success=True)
        parser._validate_business_logic(data, result)
        assert any("Allocation" in w or "allocation" in w.lower() for w in result.warnings)


class TestParseLLMResponse:
    """Integration tests for the full parse_llm_response pipeline."""

    def test_parse_valid_json_in_markdown(self, parser):
        content = f"```json\n{json.dumps(VALID_SCENARIO_JSON)}\n```"
        result = parser.parse_llm_response(content)
        assert result.success is True
        assert result.scenario_dto is not None
        assert result.scenario_dto.scenario.title == "Checkout Button Color Test"

    def test_parse_raw_json(self, parser):
        content = json.dumps(VALID_SCENARIO_JSON)
        result = parser.parse_llm_response(content)
        assert result.success is True

    def test_parse_empty_response(self, parser):
        result = parser.parse_llm_response("")
        assert result.success is False
        assert len(result.errors) > 0

    def test_parse_malformed_json(self, parser):
        content = "```json\n{invalid json}\n```"
        result = parser.parse_llm_response(content)
        assert result.success is False

    def test_parse_missing_required_keys(self, parser):
        content = json.dumps({"scenario": {"title": "Test"}})
        result = parser.parse_llm_response(content)
        assert result.success is False

    def test_raw_content_preserved(self, parser):
        content = "some raw content"
        result = parser.parse_llm_response(content)
        assert result.raw_content == content


class TestCreateFallbackScenario:
    """Tests for fallback scenario creation."""

    def test_fallback_returns_valid_dto(self, parser):
        scenario = parser.create_fallback_scenario()
        assert scenario is not None
        assert scenario.scenario.title == "Fallback E-commerce Checkout Test"

    def test_fallback_has_valid_design_params(self, parser):
        scenario = parser.create_fallback_scenario()
        dp = scenario.design_params
        assert 0 < dp.baseline_conversion_rate < 1
        assert dp.expected_daily_traffic > 0


class TestGetParsingSuggestions:
    """Tests for parsing error suggestions."""

    def test_json_error_suggestion(self, parser):
        suggestions = parser.get_parsing_suggestions(["JSON parsing error: unexpected token"])
        assert len(suggestions) > 0
        assert any("quotes" in s.lower() or "comma" in s.lower() for s in suggestions)

    def test_missing_keys_suggestion(self, parser):
        suggestions = parser.get_parsing_suggestions(["Missing required keys: ['scenario']"])
        assert len(suggestions) > 0

    def test_no_json_found_suggestion(self, parser):
        suggestions = parser.get_parsing_suggestions(["No valid JSON found"])
        assert len(suggestions) > 0
