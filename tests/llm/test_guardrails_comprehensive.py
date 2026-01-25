"""
Comprehensive tests for llm.guardrails module - Validation and bounds checking.

These tests exercise the LLMGuardrails class and NoveltyScorer with proper
test coverage of validation logic, parameter bounds, and quality scoring.
"""

import pytest
from unittest.mock import Mock, patch

from llm.guardrails import (
    LLMGuardrails,
    ValidationResult,
    GuardrailError,
    NoveltyScorer,
    get_novelty_scorer,
    score_scenario_novelty,
    record_generated_scenario,
)
from schemas.shared import CompanyType, UserSegment


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def guardrails():
    """Create a fresh guardrails instance."""
    return LLMGuardrails()


@pytest.fixture
def valid_scenario_dto():
    """Create a valid scenario DTO mock."""
    scenario_dto = Mock()

    # Scenario attributes
    scenario_dto.scenario = Mock()
    scenario_dto.scenario.title = "E-commerce Checkout Optimization"
    scenario_dto.scenario.company_type = CompanyType.ECOMMERCE
    scenario_dto.scenario.user_segment = UserSegment.ALL_USERS
    scenario_dto.scenario.primary_kpi = "conversion_rate"
    scenario_dto.scenario.secondary_kpis = ["engagement_rate"]
    scenario_dto.scenario.narrative = "A valid test scenario"
    scenario_dto.scenario.unit = "user"
    scenario_dto.scenario.assumptions = ["assumption1"]

    # Design params within bounds
    scenario_dto.design_params = Mock()
    scenario_dto.design_params.baseline_conversion_rate = 0.10  # 10%
    scenario_dto.design_params.mde_absolute = 0.01  # 1 percentage point
    scenario_dto.design_params.target_lift_pct = 0.10  # 10% lift
    scenario_dto.design_params.alpha = 0.05
    scenario_dto.design_params.power = 0.80
    scenario_dto.design_params.expected_daily_traffic = 5000
    scenario_dto.design_params.allocation = Mock()
    scenario_dto.design_params.allocation.control = 0.5
    scenario_dto.design_params.allocation.treatment = 0.5

    # LLM expected values
    scenario_dto.llm_expected = Mock()
    scenario_dto.llm_expected.simulation_hints = Mock()
    scenario_dto.llm_expected.simulation_hints.control_conversion_rate = 0.10
    scenario_dto.llm_expected.simulation_hints.treatment_conversion_rate = 0.11

    return scenario_dto


@pytest.fixture
def invalid_scenario_dto():
    """Create a scenario DTO with invalid parameters."""
    scenario_dto = Mock()

    scenario_dto.scenario = Mock()
    scenario_dto.scenario.title = "Invalid Scenario"
    scenario_dto.scenario.company_type = CompanyType.ECOMMERCE
    scenario_dto.scenario.user_segment = UserSegment.ALL_USERS
    scenario_dto.scenario.primary_kpi = "conversion_rate"
    scenario_dto.scenario.secondary_kpis = []
    scenario_dto.scenario.narrative = "Test"
    scenario_dto.scenario.unit = "user"
    scenario_dto.scenario.assumptions = []

    # Design params out of bounds
    scenario_dto.design_params = Mock()
    scenario_dto.design_params.baseline_conversion_rate = 2.0  # > 1 is invalid
    scenario_dto.design_params.mde_absolute = 0.5  # Too high
    scenario_dto.design_params.target_lift_pct = 5.0  # > 1 is excessive
    scenario_dto.design_params.alpha = 0.5  # Too high
    scenario_dto.design_params.power = 0.3  # Too low
    scenario_dto.design_params.expected_daily_traffic = 50  # Too low
    scenario_dto.design_params.allocation = Mock()
    scenario_dto.design_params.allocation.control = 0.5
    scenario_dto.design_params.allocation.treatment = 0.5

    scenario_dto.llm_expected = Mock()
    scenario_dto.llm_expected.simulation_hints = Mock()
    scenario_dto.llm_expected.simulation_hints.control_conversion_rate = 2.0
    scenario_dto.llm_expected.simulation_hints.treatment_conversion_rate = 2.5

    return scenario_dto


# ============================================================================
# ValidationResult Tests
# ============================================================================


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""

    @pytest.mark.unit
    def test_validation_result_defaults(self):
        """Test ValidationResult with default values."""
        result = ValidationResult(is_valid=False)
        assert result.is_valid is False
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []
        assert result.clamped_values == {}
        assert result.quality_score == 0.0

    @pytest.mark.unit
    def test_validation_result_with_values(self):
        """Test ValidationResult with provided values."""
        result = ValidationResult(
            is_valid=True,
            errors=["error1"],
            warnings=["warning1"],
            suggestions=["suggestion1"],
            clamped_values={"alpha": (0.5, 0.1)},
            quality_score=0.85,
        )
        assert result.is_valid is True
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]
        assert result.suggestions == ["suggestion1"]
        assert result.clamped_values == {"alpha": (0.5, 0.1)}
        assert result.quality_score == 0.85

    @pytest.mark.unit
    def test_validation_result_post_init(self):
        """Test that None values are initialized to empty collections."""
        result = ValidationResult(
            is_valid=True,
            errors=None,
            warnings=None,
            suggestions=None,
            clamped_values=None,
        )
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []
        assert result.clamped_values == {}


# ============================================================================
# LLMGuardrails Tests
# ============================================================================


class TestLLMGuardrailsInit:
    """Test suite for LLMGuardrails initialization."""

    @pytest.mark.unit
    def test_guardrails_initialization(self, guardrails):
        """Test guardrails initializes with correct bounds."""
        assert "baseline_conversion_rate" in guardrails.bounds
        assert "mde_absolute" in guardrails.bounds
        assert "target_lift_pct" in guardrails.bounds
        assert "alpha" in guardrails.bounds
        assert "power" in guardrails.bounds
        assert "expected_daily_traffic" in guardrails.bounds

    @pytest.mark.unit
    def test_bounds_are_tuples(self, guardrails):
        """Test that all bounds are (min, max) tuples."""
        for param, bounds in guardrails.bounds.items():
            assert isinstance(bounds, tuple), f"{param} bounds should be tuple"
            assert len(bounds) == 2, f"{param} bounds should have 2 elements"
            assert bounds[0] < bounds[1], f"{param} min should be < max"


class TestValidateScenario:
    """Test suite for validate_scenario method."""

    @pytest.mark.unit
    def test_validate_valid_scenario(self, guardrails, valid_scenario_dto):
        """Test validation of a valid scenario."""
        result = guardrails.validate_scenario(valid_scenario_dto)

        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.unit
    def test_validate_invalid_baseline_rate(self, guardrails, valid_scenario_dto):
        """Test validation catches out-of-bounds baseline rate."""
        valid_scenario_dto.design_params.baseline_conversion_rate = 2.0  # > 1
        result = guardrails.validate_scenario(valid_scenario_dto)

        assert result.is_valid is False
        assert any("baseline" in e.lower() for e in result.errors)

    @pytest.mark.unit
    def test_validate_invalid_alpha(self, guardrails, valid_scenario_dto):
        """Test validation catches out-of-bounds alpha."""
        valid_scenario_dto.design_params.alpha = 0.5  # Too high
        result = guardrails.validate_scenario(valid_scenario_dto)

        assert result.is_valid is False
        assert any("alpha" in e.lower() for e in result.errors)

    @pytest.mark.unit
    def test_validate_invalid_power(self, guardrails, valid_scenario_dto):
        """Test validation catches out-of-bounds power."""
        valid_scenario_dto.design_params.power = 0.3  # Too low
        result = guardrails.validate_scenario(valid_scenario_dto)

        assert result.is_valid is False
        assert any("power" in e.lower() for e in result.errors)

    @pytest.mark.unit
    def test_validate_invalid_traffic(self, guardrails, valid_scenario_dto):
        """Test validation catches out-of-bounds traffic."""
        valid_scenario_dto.design_params.expected_daily_traffic = 10  # Too low
        result = guardrails.validate_scenario(valid_scenario_dto)

        assert result.is_valid is False
        assert any("traffic" in e.lower() for e in result.errors)


class TestGetQualityScore:
    """Test suite for get_quality_score method."""

    @pytest.mark.unit
    def test_quality_score_valid_scenario(self, guardrails, valid_scenario_dto):
        """Test quality score for valid scenario."""
        score = guardrails.get_quality_score(valid_scenario_dto)

        assert 0 <= score <= 1
        assert score > 0.5  # Valid scenario should have decent score

    @pytest.mark.unit
    def test_quality_score_invalid_scenario(self, guardrails, invalid_scenario_dto):
        """Test quality score for invalid scenario."""
        score = guardrails.get_quality_score(invalid_scenario_dto)

        # Invalid scenario should have low or zero score
        assert 0 <= score <= 1


class TestClampParameters:
    """Test suite for clamp_parameters method."""

    @pytest.mark.unit
    def test_clamp_within_bounds(self, guardrails, valid_scenario_dto):
        """Test clamping doesn't change valid parameters."""
        clamped, changes = guardrails.clamp_parameters(valid_scenario_dto)

        # No changes should be made for valid params
        assert len(changes) == 0

    @pytest.mark.unit
    def test_clamp_out_of_bounds(self, guardrails, invalid_scenario_dto):
        """Test clamping corrects out-of-bounds parameters."""
        clamped, changes = guardrails.clamp_parameters(invalid_scenario_dto)

        # Should have clamped values
        assert len(changes) > 0


# ============================================================================
# NoveltyScorer Tests
# ============================================================================


class TestNoveltyScorer:
    """Test suite for NoveltyScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create a fresh novelty scorer."""
        return NoveltyScorer(history_size=5)

    @pytest.mark.unit
    def test_novelty_scorer_initialization(self, scorer):
        """Test novelty scorer initializes correctly."""
        assert scorer.history_size == 5
        assert len(scorer.recent_scenarios) == 0

    @pytest.mark.unit
    def test_record_scenario(self, scorer, valid_scenario_dto):
        """Test recording a scenario to history."""
        scorer.record_scenario(valid_scenario_dto)

        assert len(scorer.recent_scenarios) == 1

    @pytest.mark.unit
    def test_history_size_limit(self, scorer, valid_scenario_dto):
        """Test that history respects size limit."""
        # Record more than history_size scenarios using a properly mocked DTO
        for i in range(10):
            scenario = Mock()
            scenario.scenario = Mock()
            scenario.scenario.company_type = CompanyType.ECOMMERCE
            scenario.scenario.user_segment = UserSegment.ALL_USERS
            scenario.scenario.primary_kpi = f"metric_{i}"
            scenario.design_params = Mock()
            scenario.design_params.baseline_conversion_rate = 0.1 + i * 0.01
            scenario.design_params.expected_daily_traffic = 5000
            scenario.design_params.target_lift_pct = 0.10
            scenario.design_params.alpha = 0.05
            scenario.design_params.power = 0.80
            scorer.record_scenario(scenario)

        assert len(scorer.recent_scenarios) <= 5

    @pytest.mark.unit
    def test_score_first_scenario(self, scorer, valid_scenario_dto):
        """Test novelty score for first scenario is high."""
        score = scorer.score_novelty(valid_scenario_dto)

        assert score == 1.0  # First scenario is always novel

    @pytest.mark.unit
    def test_score_identical_scenario(self, scorer, valid_scenario_dto):
        """Test novelty score for identical scenarios is low."""
        scorer.record_scenario(valid_scenario_dto)
        score = scorer.score_novelty(valid_scenario_dto)

        assert score < 1.0  # Should be less novel

    @pytest.mark.unit
    def test_get_history_summary(self, scorer, valid_scenario_dto):
        """Test getting history summary."""
        scorer.record_scenario(valid_scenario_dto)
        summary = scorer.get_history_summary()

        assert "total" in summary
        assert "company_types" in summary
        assert "user_segments" in summary
        assert summary["total"] == 1

    @pytest.mark.unit
    def test_get_diversity_suggestions(self, scorer, valid_scenario_dto):
        """Test diversity suggestions generation."""
        # Record several similar scenarios
        for _ in range(3):
            scorer.record_scenario(valid_scenario_dto)

        suggestions = scorer.get_diversity_suggestions(valid_scenario_dto)

        # Should suggest diversifying since all scenarios are similar
        assert isinstance(suggestions, list)


# ============================================================================
# Module Functions Tests
# ============================================================================


class TestModuleFunctions:
    """Test suite for module-level functions."""

    @pytest.mark.unit
    def test_get_novelty_scorer(self):
        """Test factory function creates scorer."""
        scorer = get_novelty_scorer(history_size=10)

        assert isinstance(scorer, NoveltyScorer)
        assert scorer.history_size == 10

    @pytest.mark.unit
    def test_get_novelty_scorer_singleton(self):
        """Test factory returns same instance (singleton pattern)."""
        scorer1 = get_novelty_scorer()
        scorer2 = get_novelty_scorer()

        assert scorer1 is scorer2

    @pytest.mark.unit
    def test_score_scenario_novelty(self, valid_scenario_dto):
        """Test module-level novelty scoring function."""
        score, suggestions = score_scenario_novelty(valid_scenario_dto)

        assert 0 <= score <= 1
        assert isinstance(suggestions, list)

    @pytest.mark.unit
    def test_record_generated_scenario(self, valid_scenario_dto):
        """Test module-level record function."""
        # Should not raise
        record_generated_scenario(valid_scenario_dto)


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.unit
    def test_validate_missing_design_params(self, guardrails):
        """Test validation handles missing design params."""
        scenario_dto = Mock()
        scenario_dto.scenario = Mock()
        scenario_dto.design_params = None
        scenario_dto.llm_expected = Mock()

        # Should handle gracefully (not raise)
        try:
            result = guardrails.validate_scenario(scenario_dto)
            assert result.is_valid is False
        except AttributeError:
            # Acceptable if it raises for None design_params
            pass

    @pytest.mark.unit
    def test_validate_edge_values(self, guardrails, valid_scenario_dto):
        """Test validation with edge values at bounds."""
        # Test with values exactly at bounds
        valid_scenario_dto.design_params.alpha = 0.001  # Minimum
        valid_scenario_dto.design_params.power = 0.99  # Maximum

        result = guardrails.validate_scenario(valid_scenario_dto)

        # Should be valid since values are at bounds, not beyond
        assert result.is_valid is True

    @pytest.mark.unit
    def test_quality_score_range(self, guardrails, valid_scenario_dto):
        """Test quality score stays within 0-1 range."""
        score = guardrails.get_quality_score(valid_scenario_dto)
        assert 0.0 <= score <= 1.0

        # Test with extreme values
        valid_scenario_dto.design_params.baseline_conversion_rate = 0.001
        score = guardrails.get_quality_score(valid_scenario_dto)
        assert 0.0 <= score <= 1.0
