# Phase 08: Add Test Coverage for 0% Modules

**PR Title**: `test: add coverage for 0% modules`
**Risk Level**: Low (adds tests only — no source changes)
**Effort**: 12-16 hours
**Depends On**: All previous phases (run last so tests target stable code)
**Blocks**: None

---

## Problem Statement

Four modules totaling ~2,050 lines of code have 0% test coverage:

| Module | Lines | Reason | Priority |
|--------|-------|--------|----------|
| `llm/generator.py` | 546 | No test file exists | High |
| `llm/integration.py` | 464 | No test file exists | High |
| `schemas/complications.py` | 263 | No test file exists | Medium |
| `ui/streamlit_app.py` | 1830 | Cannot be tested via pytest directly | Low (defer) |

Additionally, two modules have very low coverage:

| Module | Lines | Coverage | Priority |
|--------|-------|----------|----------|
| `llm/parser.py` | 532 | 17% | High |
| `llm/guardrails.py` | 1044 | 46% | Medium |

---

## Strategy

### Testing Approach for LLM Modules

The LLM modules make external API calls to OpenAI. All tests should use **mocked clients** — never real API calls. The project already has patterns for this in `tests/llm/test_client.py`.

Key mocking pattern:
```python
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = Mock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content='{"key": "value"}'))]
    )
    return client
```

### Testing Approach for UI Module

`ui/streamlit_app.py` uses Streamlit's session state and rendering functions, which are difficult to test with pytest. **Defer this to a separate effort** using Streamlit's testing utilities or integration tests. This phase focuses on the testable modules.

---

## Implementation Plan

### Module 1: `llm/generator.py` (High Priority)

**Create**: `tests/llm/test_generator.py`

**Key classes/functions to test**:
- `LLMScenarioGenerator` class
  - `__init__()` — verify default configuration
  - `generate()` — happy path with mocked client
  - `generate()` — retry logic when first attempt fails
  - `generate()` — fallback scenario when all attempts fail
  - `generate()` — quality threshold rejection and re-attempt
- `GenerationResult` dataclass
  - Verify fields and defaults
- `create_generator()` factory function
  - Default configuration
  - Custom configuration

**Test outline** (~15-20 tests):

```python
class TestLLMScenarioGenerator:
    def test_generate_success_returns_scenario(self, mock_openai_client):
        """Happy path: valid JSON response is parsed and returned."""

    def test_generate_retries_on_api_error(self, mock_openai_client):
        """API errors trigger retry up to max_retries."""

    def test_generate_returns_fallback_on_all_failures(self, mock_openai_client):
        """When all retries fail, a fallback scenario is returned."""

    def test_generate_rejects_low_quality_scenario(self, mock_openai_client):
        """Scenarios below quality threshold are regenerated."""

    def test_generate_accepts_high_quality_scenario(self, mock_openai_client):
        """Scenarios above quality threshold are accepted on first try."""

    def test_generate_with_custom_request(self, mock_openai_client):
        """Custom generation requests modify the prompt."""

    def test_generate_parallel_generates_multiple(self, mock_openai_client):
        """Parallel generation returns multiple scenarios."""


class TestGenerationResult:
    def test_success_result_has_scenario(self):
        """Successful result includes scenario data."""

    def test_failure_result_has_error(self):
        """Failed result includes error message."""


class TestCreateGenerator:
    def test_default_configuration(self):
        """Factory creates generator with sensible defaults."""

    def test_custom_configuration(self):
        """Factory respects custom configuration."""
```

### Module 2: `llm/integration.py` (High Priority)

**Create**: `tests/llm/test_integration.py`

**Key functions to test**:
- `run_generation_pipeline()` — end-to-end with mocked LLM
- `convert_dto_to_design_params()` — DTO conversion (if Phase 06 hasn't moved this)
- Pipeline error handling — each step's failure mode

**Test outline** (~10-12 tests):

```python
class TestGenerationPipeline:
    def test_pipeline_success_returns_complete_result(self, mock_generator):
        """Full pipeline produces scenario, design params, and answer keys."""

    def test_pipeline_handles_generation_failure(self, mock_generator):
        """Pipeline returns error result when generation fails."""

    def test_pipeline_handles_parsing_failure(self, mock_generator):
        """Pipeline returns error result when parsing fails."""

    def test_pipeline_handles_validation_failure(self, mock_generator):
        """Pipeline returns error result when guardrails reject scenario."""

    def test_dto_to_design_params_conversion(self):
        """DTO is correctly converted to core DesignParams."""

    def test_dto_to_design_params_with_defaults(self):
        """Missing DTO fields use correct defaults."""
```

### Module 3: `schemas/complications.py` (Medium Priority)

**Create**: `tests/schemas/test_complications.py`

First, read the module to understand what it contains (complication types, enums, models).

**Key items to test**:
- All Pydantic models validate correctly with valid data
- All Pydantic models reject invalid data with clear errors
- Enum values are complete and correct
- Serialization round-trip (model → dict → model)

**Test outline** (~8-10 tests):

```python
class TestComplicationModels:
    def test_valid_complication_data_parses(self):
        """Valid complication data creates model successfully."""

    def test_invalid_complication_data_raises(self):
        """Invalid data raises ValidationError with helpful message."""

    def test_serialization_roundtrip(self):
        """Model can be serialized to dict and deserialized back."""

    def test_all_complication_types_have_descriptions(self):
        """Every ComplicationType enum has a non-empty description."""
```

### Module 4: `llm/parser.py` (Increase from 17% → 60%+)

**Existing file**: `tests/llm/test_parser.py` (already exists but sparse)

**Key functions needing tests**:
- `parse_llm_response()` — various JSON formats (clean, wrapped in markdown, nested)
- `extract_json_from_text()` — edge cases (no JSON, multiple JSON blocks, malformed)
- `validate_scenario_fields()` — required vs optional fields
- `_convert_field_types()` — type coercion edge cases

**Test outline** (~15-20 additional tests):

```python
class TestParseLLMResponse:
    def test_parse_clean_json(self):
        """Clean JSON string is parsed correctly."""

    def test_parse_json_in_markdown_code_block(self):
        """JSON wrapped in ```json ... ``` is extracted."""

    def test_parse_json_with_trailing_text(self):
        """JSON followed by explanation text is extracted."""

    def test_parse_empty_response(self):
        """Empty string returns None."""

    def test_parse_invalid_json(self):
        """Malformed JSON returns None."""


class TestExtractJsonFromText:
    def test_extract_from_mixed_content(self):
        """JSON is extracted from text with surrounding prose."""

    def test_no_json_in_text(self):
        """Text with no JSON returns None."""

    def test_multiple_json_blocks(self):
        """First valid JSON block is returned."""


class TestValidateScenarioFields:
    def test_all_required_fields_present(self):
        """Scenario with all required fields passes validation."""

    def test_missing_required_field_fails(self):
        """Scenario missing a required field fails validation."""

    def test_extra_fields_ignored(self):
        """Extra fields in the JSON don't cause failure."""
```

### Module 5: `llm/guardrails.py` (Increase from 46% → 70%+)

**Existing file**: `tests/llm/test_guardrails.py` (exists but incomplete)

**Key areas needing tests**:
- Boundary validation for each parameter (test at bounds, just inside, just outside)
- Cross-parameter consistency checks
- NoveltyScorer (if it has meaningful logic)

**Test outline** (~10-15 additional tests):

```python
class TestParameterBounds:
    @pytest.mark.parametrize("param,value,expected", [
        ("baseline_conversion_rate", 0.001, True),   # Lower bound
        ("baseline_conversion_rate", 0.8, True),     # Upper bound
        ("baseline_conversion_rate", 0.0001, False),  # Below lower bound
        ("baseline_conversion_rate", 0.9, False),    # Above upper bound
        ("expected_daily_traffic", 100, True),
        ("expected_daily_traffic", 10_000_000, True),
        ("expected_daily_traffic", 50, False),
    ])
    def test_parameter_bounds(self, param, value, expected):
        """Parameter values at and beyond bounds are validated correctly."""
```

---

## Test File Structure

```
tests/
├── llm/
│   ├── test_generator.py      # NEW (Phase 08)
│   ├── test_integration.py    # NEW (Phase 08)
│   ├── test_parser.py         # EXPANDED (Phase 08)
│   ├── test_guardrails.py     # EXPANDED (Phase 08)
│   └── test_client.py         # Existing
├── schemas/
│   ├── test_complications.py  # NEW (Phase 08)
│   └── ...                    # Existing
└── ...
```

---

## Verification Checklist

- [ ] `tests/llm/test_generator.py` exists with 15+ tests
- [ ] `tests/llm/test_integration.py` exists with 10+ tests
- [ ] `tests/schemas/test_complications.py` exists with 8+ tests
- [ ] `tests/llm/test_parser.py` has 15+ additional tests
- [ ] `tests/llm/test_guardrails.py` has 10+ additional tests
- [ ] All new tests pass: `pytest tests/llm/ tests/schemas/ -v`
- [ ] Full suite passes: `pytest` — 500+ tests, 0 failures
- [ ] Coverage report shows:
  - `llm/generator.py` ≥ 50%
  - `llm/integration.py` ≥ 50%
  - `schemas/complications.py` ≥ 80%
  - `llm/parser.py` ≥ 50%
  - `llm/guardrails.py` ≥ 65%
- [ ] No tests make real API calls (all use mocks)
- [ ] No tests depend on `.env` or environment variables

---

## What NOT To Do

- **Do NOT modify source code** in this phase — tests only. If a bug is found during testing, note it and file a separate issue.
- **Do NOT write tests for `ui/streamlit_app.py`** in this phase — Streamlit testing requires a different framework.
- **Do NOT use `@pytest.mark.requires_api`** for any new test — all tests must work offline.
- **Do NOT copy test patterns from `test_basic.py`** or `test_streamlit_app.py` at the project root — those are legacy smoke tests. Follow the patterns in `tests/core/` instead.
- **Do NOT aim for 100% coverage** on LLM modules — focus on the critical paths and error handling. 50-70% is a good target for modules that wrap external APIs.

---

## Coverage Target Summary

| Module | Current | Target | Delta |
|--------|---------|--------|-------|
| `llm/generator.py` | 0% | 50%+ | +50% |
| `llm/integration.py` | 0% | 50%+ | +50% |
| `schemas/complications.py` | 0% | 80%+ | +80% |
| `llm/parser.py` | 17% | 50%+ | +33% |
| `llm/guardrails.py` | 46% | 65%+ | +19% |
| **Overall project** | **54%** | **62%+** | **+8%** |
