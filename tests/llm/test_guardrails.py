"""Tests for llm.guardrails module - Parameter validation and novelty scoring."""

import pytest
from unittest.mock import Mock, patch

from llm.guardrails import (
    ValidationResult,
    GuardrailError,
    LLMGuardrails,
    NoveltyScorer,
    get_novelty_scorer,
    score_scenario_novelty,
    record_generated_scenario,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scenario_dto(
    baseline=0.025,
    mde_absolute=0.005,
    target_lift_pct=0.20,
    alpha=0.05,
    power=0.80,
    traffic=5000,
    control_alloc=0.5,
    treatment_alloc=0.5,
    control_rate=0.025,
    treatment_rate=0.030,
    title="Checkout Button Color Change AB Test",
    narrative="Testing whether changing the checkout button from blue to green increases conversion rates for our e-commerce platform. This test targets all visitors.",
    company_type_value="E-commerce",
    user_segment_value="all_users",
    primary_kpi="conversion_rate",
):
    """Build a mock ScenarioResponseDTO for guardrail validation tests."""
    dto = Mock()

    # scenario sub-object
    dto.scenario.title = title
    dto.scenario.narrative = narrative
    dto.scenario.company_type.value = company_type_value
    dto.scenario.user_segment.value = user_segment_value
    dto.scenario.primary_kpi = primary_kpi

    # design_params sub-object
    dto.design_params.baseline_conversion_rate = baseline
    dto.design_params.mde_absolute = mde_absolute
    dto.design_params.target_lift_pct = target_lift_pct
    dto.design_params.alpha = alpha
    dto.design_params.power = power
    dto.design_params.expected_daily_traffic = traffic
    dto.design_params.allocation.control = control_alloc
    dto.design_params.allocation.treatment = treatment_alloc

    # llm_expected sub-object
    dto.llm_expected.simulation_hints.control_conversion_rate = control_rate
    dto.llm_expected.simulation_hints.treatment_conversion_rate = treatment_rate

    return dto


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_default_values(self):
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.quality_score == 0.0
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []
        assert result.clamped_values == {}

    def test_none_lists_initialized(self):
        result = ValidationResult(
            is_valid=False, errors=None, warnings=None, suggestions=None, clamped_values=None
        )
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []
        assert result.clamped_values == {}

    def test_provided_values_preserved(self):
        result = ValidationResult(
            is_valid=False,
            quality_score=0.75,
            errors=["err1"],
            warnings=["warn1"],
            suggestions=["sug1"],
            clamped_values={"alpha": (0.5, 0.2)},
        )
        assert result.quality_score == 0.75
        assert result.errors == ["err1"]
        assert result.clamped_values == {"alpha": (0.5, 0.2)}


class TestGuardrailError:
    def test_is_exception(self):
        err = GuardrailError("validation failed")
        assert isinstance(err, Exception)
        assert str(err) == "validation failed"


# ---------------------------------------------------------------------------
# LLMGuardrails.__init__
# ---------------------------------------------------------------------------


class TestLLMGuardrailsInit:
    def test_bounds_initialized(self):
        g = LLMGuardrails()
        assert "baseline_conversion_rate" in g.bounds
        assert "alpha" in g.bounds
        assert "power" in g.bounds
        assert "expected_daily_traffic" in g.bounds

    def test_bounds_are_tuples(self):
        g = LLMGuardrails()
        for key, val in g.bounds.items():
            assert isinstance(val, tuple), f"{key} bound is not a tuple"
            assert len(val) == 2
            assert val[0] < val[1], f"{key} lower bound >= upper bound"

    def test_traffic_tiers_initialized(self):
        g = LLMGuardrails()
        assert len(g.traffic_tiers) > 0

    def test_metric_baseline_ranges_initialized(self):
        g = LLMGuardrails()
        assert len(g.metric_baseline_ranges) > 0

    def test_effect_size_profiles_initialized(self):
        g = LLMGuardrails()
        assert len(g.effect_size_profiles) > 0


# ---------------------------------------------------------------------------
# _validate_design_params
# ---------------------------------------------------------------------------


class TestValidateDesignParams:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_valid_params_no_errors(self):
        dto = _make_scenario_dto()
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert len(result.errors) == 0

    def test_baseline_below_lower_bound(self):
        dto = _make_scenario_dto(baseline=0.0001)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Baseline conversion rate" in e for e in result.errors)

    def test_baseline_above_upper_bound(self):
        dto = _make_scenario_dto(baseline=0.9)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Baseline conversion rate" in e for e in result.errors)

    def test_mde_below_lower_bound(self):
        dto = _make_scenario_dto(mde_absolute=0.0001)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("MDE absolute" in e for e in result.errors)

    def test_mde_above_upper_bound(self):
        dto = _make_scenario_dto(mde_absolute=0.3)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("MDE absolute" in e for e in result.errors)

    def test_target_lift_below_lower_bound(self):
        dto = _make_scenario_dto(target_lift_pct=-0.6)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Target lift" in e for e in result.errors)

    def test_target_lift_above_upper_bound(self):
        dto = _make_scenario_dto(target_lift_pct=1.5)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Target lift" in e for e in result.errors)

    def test_alpha_below_lower_bound(self):
        dto = _make_scenario_dto(alpha=0.0001)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Alpha" in e for e in result.errors)

    def test_alpha_above_upper_bound(self):
        dto = _make_scenario_dto(alpha=0.3)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Alpha" in e for e in result.errors)

    def test_power_below_lower_bound(self):
        dto = _make_scenario_dto(power=0.3)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Power" in e for e in result.errors)

    def test_power_above_upper_bound(self):
        dto = _make_scenario_dto(power=1.0)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Power" in e for e in result.errors)

    def test_traffic_below_lower_bound(self):
        dto = _make_scenario_dto(traffic=50)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Daily traffic" in e for e in result.errors)

    def test_traffic_above_upper_bound(self):
        dto = _make_scenario_dto(traffic=20_000_000)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Daily traffic" in e for e in result.errors)

    def test_allocation_not_summing_to_one(self):
        dto = _make_scenario_dto(control_alloc=0.6, treatment_alloc=0.6)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        assert any("Allocation" in e for e in result.errors)

    def test_allocation_slight_rounding_ok(self):
        """Allocation within 0.001 tolerance should pass."""
        dto = _make_scenario_dto(control_alloc=0.4999, treatment_alloc=0.5001)
        result = ValidationResult(is_valid=True)
        self.g._validate_design_params(dto, result)
        alloc_errors = [e for e in result.errors if "Allocation" in e]
        assert len(alloc_errors) == 0


# ---------------------------------------------------------------------------
# _validate_business_context
# ---------------------------------------------------------------------------


class TestValidateBusinessContext:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_valid_context_no_warnings(self):
        dto = _make_scenario_dto()
        result = ValidationResult(is_valid=True)
        self.g._validate_business_context(dto, result)
        assert len(result.errors) == 0

    def test_short_title_warns(self):
        dto = _make_scenario_dto(title="Short")
        result = ValidationResult(is_valid=True)
        self.g._validate_business_context(dto, result)
        assert any("title" in w.lower() for w in result.warnings)

    def test_short_narrative_warns(self):
        dto = _make_scenario_dto(narrative="Too short.")
        result = ValidationResult(is_valid=True)
        self.g._validate_business_context(dto, result)
        assert any("narrative" in w.lower() for w in result.warnings)

    def test_invalid_company_type_errors(self):
        dto = _make_scenario_dto()
        # Make company_type.value raise AttributeError
        dto.scenario.company_type = "not_an_enum"
        result = ValidationResult(is_valid=True)
        self.g._validate_business_context(dto, result)
        assert any("Invalid company type" in e for e in result.errors)

    def test_short_kpi_warns(self):
        dto = _make_scenario_dto(primary_kpi="ab")
        result = ValidationResult(is_valid=True)
        self.g._validate_business_context(dto, result)
        assert any("KPI" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# _validate_parameter_consistency
# ---------------------------------------------------------------------------


class TestValidateParameterConsistency:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_consistent_params_no_warnings(self):
        dto = _make_scenario_dto(baseline=0.025, control_rate=0.025)
        result = ValidationResult(is_valid=True)
        self.g._validate_parameter_consistency(dto, result)
        baseline_warnings = [w for w in result.warnings if "Baseline" in w]
        assert len(baseline_warnings) == 0

    def test_baseline_control_mismatch_warns(self):
        dto = _make_scenario_dto(baseline=0.025, control_rate=0.050)
        result = ValidationResult(is_valid=True)
        self.g._validate_parameter_consistency(dto, result)
        assert any("Baseline" in w or "baseline" in w.lower() for w in result.warnings)

    def test_lift_mismatch_warns(self):
        """Target lift doesn't match computed actual lift."""
        dto = _make_scenario_dto(
            baseline=0.025, target_lift_pct=0.20,
            treatment_rate=0.050,  # actual lift = 100%, not 20%
        )
        result = ValidationResult(is_valid=True)
        self.g._validate_parameter_consistency(dto, result)
        assert any("lift" in w.lower() for w in result.warnings)

    def test_consistent_lift_no_warning(self):
        """Target lift matches actual lift (within tolerance)."""
        dto = _make_scenario_dto(
            baseline=0.025, target_lift_pct=0.20,
            control_rate=0.025, treatment_rate=0.030,
        )
        result = ValidationResult(is_valid=True)
        self.g._validate_parameter_consistency(dto, result)
        lift_warnings = [w for w in result.warnings if "lift" in w.lower()]
        assert len(lift_warnings) == 0

    def test_conversion_rate_out_of_bounds_errors(self):
        """Control/treatment rates outside bounds produce errors."""
        dto = _make_scenario_dto(control_rate=0.9, treatment_rate=0.95)
        result = ValidationResult(is_valid=True)
        self.g._validate_parameter_consistency(dto, result)
        assert any("control_conversion_rate" in e for e in result.errors)
        assert any("treatment_conversion_rate" in e for e in result.errors)


# ---------------------------------------------------------------------------
# _validate_metric_consistency
# ---------------------------------------------------------------------------


class TestValidateMetricConsistency:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_consistent_mde_and_lift(self):
        """No error when mde_absolute / baseline == target_lift_pct."""
        dto = _make_scenario_dto(baseline=0.025, mde_absolute=0.005, target_lift_pct=0.20)
        result = ValidationResult(is_valid=True)
        self.g._validate_metric_consistency(dto, result)
        math_errors = [e for e in result.errors if "Mathematical inconsistency" in e]
        assert len(math_errors) == 0

    def test_inconsistent_mde_and_lift_errors(self):
        """Error when mde_absolute / baseline != target_lift_pct."""
        dto = _make_scenario_dto(baseline=0.025, mde_absolute=0.005, target_lift_pct=0.50)
        result = ValidationResult(is_valid=True)
        self.g._validate_metric_consistency(dto, result)
        assert any("Mathematical inconsistency" in e for e in result.errors)

    def test_large_mde_relative_to_baseline_warns(self):
        """MDE > 50% of baseline triggers warning."""
        dto = _make_scenario_dto(baseline=0.01, mde_absolute=0.008, target_lift_pct=0.80)
        result = ValidationResult(is_valid=True)
        self.g._validate_metric_consistency(dto, result)
        assert any("MDE" in w for w in result.warnings)

    def test_non_proportion_kpi_warns(self):
        """Non-proportion KPI triggers warning."""
        dto = _make_scenario_dto(primary_kpi="revenue_per_user")
        result = ValidationResult(is_valid=True)
        self.g._validate_metric_consistency(dto, result)
        assert any("may not be appropriate" in w for w in result.warnings)

    def test_valid_proportion_kpi_no_warning(self):
        """Standard proportion KPI should not trigger warning."""
        dto = _make_scenario_dto(primary_kpi="conversion_rate")
        result = ValidationResult(is_valid=True)
        self.g._validate_metric_consistency(dto, result)
        kpi_warnings = [w for w in result.warnings if "may not be appropriate" in w]
        assert len(kpi_warnings) == 0


# ---------------------------------------------------------------------------
# _validate_realism
# ---------------------------------------------------------------------------


class TestValidateRealism:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_normal_values_no_warnings(self):
        dto = _make_scenario_dto()
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert len(result.warnings) == 0

    def test_very_high_baseline_warns(self):
        dto = _make_scenario_dto(baseline=0.85)
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert any("very high" in w.lower() for w in result.warnings)

    def test_very_low_baseline_warns(self):
        dto = _make_scenario_dto(baseline=0.0005)
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert any("very low" in w.lower() for w in result.warnings)

    def test_extreme_positive_lift_warns(self):
        dto = _make_scenario_dto(target_lift_pct=2.5)
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert any("ambitious" in w.lower() for w in result.warnings)

    def test_extreme_negative_lift_warns(self):
        dto = _make_scenario_dto(target_lift_pct=-0.6)
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert any("negative impact" in w.lower() for w in result.warnings)

    def test_very_high_traffic_warns(self):
        dto = _make_scenario_dto(traffic=15_000_000)
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert any("enterprise-scale" in w.lower() for w in result.warnings)

    def test_very_low_traffic_warns(self):
        dto = _make_scenario_dto(traffic=50)
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert any("very low" in w.lower() for w in result.warnings)

    def test_very_high_power_suggests(self):
        dto = _make_scenario_dto(power=0.96)
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert any("very high" in s.lower() for s in result.suggestions)

    def test_very_low_power_suggests(self):
        dto = _make_scenario_dto(power=0.55)
        result = ValidationResult(is_valid=True)
        self.g._validate_realism(dto, result)
        assert any("low" in s.lower() for s in result.suggestions)


# ---------------------------------------------------------------------------
# validate_scenario (full pipeline)
# ---------------------------------------------------------------------------


class TestValidateScenario:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_valid_scenario_passes(self):
        dto = _make_scenario_dto()
        result = self.g.validate_scenario(dto)
        assert result.is_valid is True
        assert result.quality_score > 0

    def test_invalid_params_fail(self):
        dto = _make_scenario_dto(baseline=0.0001, alpha=0.5)
        result = self.g.validate_scenario(dto)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_exception_sets_invalid(self):
        """If a validation sub-method raises, result is invalid."""
        dto = _make_scenario_dto()
        # Make an attribute access raise to trigger the except clause
        dto.design_params.baseline_conversion_rate = property(lambda self: 1 / 0)
        type(dto.design_params).baseline_conversion_rate = property(lambda self: (_ for _ in ()).throw(ValueError("boom")))
        result = self.g.validate_scenario(dto)
        assert result.is_valid is False
        assert any("Validation error" in e for e in result.errors)


# ---------------------------------------------------------------------------
# clamp_parameters
# ---------------------------------------------------------------------------


class TestClampParameters:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_in_range_values_not_clamped(self):
        dto = _make_scenario_dto()
        _, clamped_values = self.g.clamp_parameters(dto)
        assert len(clamped_values) == 0

    def test_low_baseline_clamped_up(self):
        # Value must differ from lower bound (0.001) by more than 0.001 tolerance
        dto = _make_scenario_dto(baseline=-0.1)
        clamped_dto, clamped_values = self.g.clamp_parameters(dto)
        assert "baseline_conversion_rate" in clamped_values
        original, clamped = clamped_values["baseline_conversion_rate"]
        assert original == -0.1
        assert clamped == self.g.bounds["baseline_conversion_rate"][0]

    def test_high_alpha_clamped_down(self):
        dto = _make_scenario_dto(alpha=0.5)
        _, clamped_values = self.g.clamp_parameters(dto)
        assert "alpha" in clamped_values
        _, clamped = clamped_values["alpha"]
        assert clamped == self.g.bounds["alpha"][1]

    def test_high_power_clamped_down(self):
        dto = _make_scenario_dto(power=1.0)
        _, clamped_values = self.g.clamp_parameters(dto)
        assert "power" in clamped_values

    def test_high_traffic_clamped_down(self):
        dto = _make_scenario_dto(traffic=20_000_000)
        _, clamped_values = self.g.clamp_parameters(dto)
        assert "expected_daily_traffic" in clamped_values

    def test_simulation_hints_clamped(self):
        # Values must differ from bounds by more than 0.001 tolerance
        dto = _make_scenario_dto(control_rate=-0.1, treatment_rate=0.9)
        _, clamped_values = self.g.clamp_parameters(dto)
        assert "control_conversion_rate" in clamped_values
        assert "treatment_conversion_rate" in clamped_values


# ---------------------------------------------------------------------------
# generate_regeneration_hints
# ---------------------------------------------------------------------------


class TestGenerateRegenerationHints:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_out_of_range_error_hint(self):
        result = ValidationResult(is_valid=False, errors=["Alpha 0.5 is outside valid range [0.001, 0.2]"])
        hints = self.g.generate_regeneration_hints(result)
        assert any("bounds" in h.lower() for h in hints)

    def test_allocation_error_hint(self):
        result = ValidationResult(is_valid=False, errors=["Allocation must sum to 1.0, got 1.2"])
        hints = self.g.generate_regeneration_hints(result)
        assert any("allocation" in h.lower() for h in hints)

    def test_mismatch_error_hint(self):
        result = ValidationResult(is_valid=False, errors=["Baseline doesn't match control rate"])
        hints = self.g.generate_regeneration_hints(result)
        assert any("consistency" in h.lower() for h in hints)

    def test_no_matching_patterns_gives_default_hint(self):
        result = ValidationResult(is_valid=False, errors=["Some unknown error"])
        hints = self.g.generate_regeneration_hints(result)
        assert len(hints) > 0
        assert any("review" in h.lower() for h in hints)


# ---------------------------------------------------------------------------
# get_quality_score
# ---------------------------------------------------------------------------


class TestGetQualityScore:
    def setup_method(self):
        self.g = LLMGuardrails()

    def test_normal_scenario_high_score(self):
        dto = _make_scenario_dto()
        score = self.g.get_quality_score(dto)
        assert 0.7 <= score <= 1.0

    def test_extreme_baseline_lowers_score(self):
        dto = _make_scenario_dto(baseline=0.96)
        score = self.g.get_quality_score(dto)
        assert score < 0.9

    def test_extreme_lift_lowers_score(self):
        dto = _make_scenario_dto(target_lift_pct=6.0)
        score = self.g.get_quality_score(dto)
        assert score < 0.9

    def test_inconsistent_baseline_control_lowers_score(self):
        dto = _make_scenario_dto(baseline=0.025, control_rate=0.100)
        score = self.g.get_quality_score(dto)
        normal_score = self.g.get_quality_score(_make_scenario_dto())
        assert score < normal_score

    def test_long_narrative_bonus(self):
        dto = _make_scenario_dto(
            narrative="A" * 250,
            title="A" * 35,
        )
        score = self.g.get_quality_score(dto)
        assert score >= 1.0  # base 1.0 + 0.05 + 0.05

    def test_short_narrative_penalty(self):
        dto = _make_scenario_dto(narrative="Short.", title="Short")
        score = self.g.get_quality_score(dto)
        assert score < 0.9

    def test_score_clamped_to_0_1(self):
        # Stack multiple penalties
        dto = _make_scenario_dto(
            baseline=0.96, target_lift_pct=6.0,
            control_rate=0.5, narrative="X", title="Y",
        )
        score = self.g.get_quality_score(dto)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# NoveltyScorer
# ---------------------------------------------------------------------------


class TestNoveltyScorer:
    def test_init_defaults(self):
        scorer = NoveltyScorer()
        assert scorer.history_size == 20
        assert scorer.recent_scenarios == []

    def test_init_custom_history(self):
        scorer = NoveltyScorer(history_size=5)
        assert scorer.history_size == 5


class TestExtractFeatures:
    def test_extracts_all_keys(self):
        scorer = NoveltyScorer()
        dto = _make_scenario_dto()
        features = scorer._extract_features(dto)
        assert "company_type" in features
        assert "user_segment" in features
        assert "primary_kpi" in features
        assert "traffic_tier" in features
        assert "baseline_tier" in features
        assert "effect_tier" in features
        assert "alpha" in features
        assert "power" in features

    def test_traffic_tiers(self):
        scorer = NoveltyScorer()
        cases = [
            (500, "early_stage"),
            (5000, "growth"),
            (50000, "scale"),
            (500000, "enterprise"),
        ]
        for traffic, expected_tier in cases:
            dto = _make_scenario_dto(traffic=traffic)
            features = scorer._extract_features(dto)
            assert features["traffic_tier"] == expected_tier, f"traffic={traffic}"

    def test_baseline_tiers(self):
        scorer = NoveltyScorer()
        cases = [
            (0.005, "very_low"),
            (0.025, "low"),
            (0.10, "medium"),
            (0.20, "high"),
            (0.40, "very_high"),
        ]
        for baseline, expected_tier in cases:
            dto = _make_scenario_dto(baseline=baseline)
            features = scorer._extract_features(dto)
            assert features["baseline_tier"] == expected_tier, f"baseline={baseline}"

    def test_effect_tiers(self):
        scorer = NoveltyScorer()
        cases = [
            (0.02, "incremental"),
            (0.10, "moderate"),
            (0.30, "significant"),
            (0.60, "transformational"),
        ]
        for lift, expected_tier in cases:
            dto = _make_scenario_dto(target_lift_pct=lift)
            features = scorer._extract_features(dto)
            assert features["effect_tier"] == expected_tier, f"lift={lift}"


class TestScoreNovelty:
    def test_first_scenario_is_novel(self):
        scorer = NoveltyScorer()
        dto = _make_scenario_dto()
        assert scorer.score_novelty(dto) == 1.0

    def test_identical_scenario_less_novel(self):
        scorer = NoveltyScorer()
        dto = _make_scenario_dto()
        scorer.record_scenario(dto)
        score = scorer.score_novelty(dto)
        assert score < 1.0

    def test_different_scenario_more_novel(self):
        scorer = NoveltyScorer()
        dto1 = _make_scenario_dto(company_type_value="E-commerce", primary_kpi="conversion_rate")
        scorer.record_scenario(dto1)

        dto2 = _make_scenario_dto(
            company_type_value="SaaS",
            user_segment_value="premium_users",
            primary_kpi="engagement_rate",
            traffic=50000,
            baseline=0.15,
            target_lift_pct=0.40,
        )
        score = scorer.score_novelty(dto2)
        assert score > 0.5

    def test_novelty_score_between_0_and_1(self):
        scorer = NoveltyScorer()
        dto = _make_scenario_dto()
        # Record many identical scenarios
        for _ in range(10):
            scorer.record_scenario(dto)
        score = scorer.score_novelty(dto)
        assert 0.0 <= score <= 1.0


class TestRecordScenario:
    def test_adds_to_history(self):
        scorer = NoveltyScorer()
        dto = _make_scenario_dto()
        scorer.record_scenario(dto)
        assert len(scorer.recent_scenarios) == 1

    def test_respects_history_size(self):
        scorer = NoveltyScorer(history_size=3)
        for i in range(5):
            dto = _make_scenario_dto(traffic=1000 * (i + 1))
            scorer.record_scenario(dto)
        assert len(scorer.recent_scenarios) == 3


class TestGetDiversitySuggestions:
    def test_no_history_no_suggestions(self):
        scorer = NoveltyScorer()
        dto = _make_scenario_dto()
        assert scorer.get_diversity_suggestions(dto) == []

    def test_repeated_company_type_suggests_alternatives(self):
        scorer = NoveltyScorer()
        for _ in range(4):
            scorer.record_scenario(_make_scenario_dto(company_type_value="E-commerce"))
        suggestions = scorer.get_diversity_suggestions(
            _make_scenario_dto(company_type_value="E-commerce")
        )
        assert any("Company type" in s or "company type" in s.lower() for s in suggestions)


class TestGetHistorySummary:
    def test_empty_history(self):
        scorer = NoveltyScorer()
        summary = scorer.get_history_summary()
        assert summary == {"total": 0}

    def test_with_history(self):
        scorer = NoveltyScorer()
        scorer.record_scenario(_make_scenario_dto())
        scorer.record_scenario(_make_scenario_dto(company_type_value="SaaS"))
        summary = scorer.get_history_summary()
        assert summary["total"] == 2
        assert "company_types" in summary
        assert len(summary["company_types"]) == 2


class TestClearHistory:
    def test_clears_all(self):
        scorer = NoveltyScorer()
        scorer.record_scenario(_make_scenario_dto())
        scorer.record_scenario(_make_scenario_dto())
        scorer.clear_history()
        assert scorer.recent_scenarios == []


# ---------------------------------------------------------------------------
# Module-level functions
# ---------------------------------------------------------------------------


class TestModuleLevelFunctions:
    def test_get_novelty_scorer_singleton(self):
        """get_novelty_scorer returns the same instance on repeated calls."""
        with patch("llm.guardrails._novelty_scorer", None):
            scorer1 = get_novelty_scorer()
            scorer2 = get_novelty_scorer()
            assert scorer1 is scorer2

    def test_score_scenario_novelty_returns_tuple(self):
        with patch("llm.guardrails._novelty_scorer", None):
            dto = _make_scenario_dto()
            novelty, suggestions = score_scenario_novelty(dto)
            assert isinstance(novelty, float)
            assert isinstance(suggestions, list)

    def test_record_generated_scenario_adds_to_history(self):
        with patch("llm.guardrails._novelty_scorer", None):
            scorer = get_novelty_scorer()
            scorer.clear_history()
            dto = _make_scenario_dto()
            record_generated_scenario(dto)
            assert len(scorer.recent_scenarios) == 1
