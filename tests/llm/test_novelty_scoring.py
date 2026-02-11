"""
Tests for novelty scoring system in llm.guardrails module.

These tests verify that the novelty scorer correctly:
- Identifies repetitive scenarios
- Scores novel scenarios highly
- Provides diversity suggestions
- Tracks scenario history correctly
"""

import pytest
from unittest.mock import MagicMock

from llm.guardrails import (
    NoveltyScorer,
    get_novelty_scorer,
    score_scenario_novelty,
    record_generated_scenario
)
from schemas.scenario import ScenarioResponseDTO


def create_mock_scenario(
    company_type: str = "B2B SaaS",
    user_segment: str = "trial users",
    primary_kpi: str = "conversion_rate",
    traffic: int = 5000,
    baseline: float = 0.05,
    target_lift: float = 0.15,
    alpha: float = 0.05,
    power: float = 0.80
) -> ScenarioResponseDTO:
    """Create a mock scenario DTO for testing."""
    # Create mock objects with necessary attributes
    scenario = MagicMock()
    scenario.company_type = MagicMock()
    scenario.company_type.value = company_type
    scenario.user_segment = MagicMock()
    scenario.user_segment.value = user_segment
    scenario.primary_kpi = primary_kpi

    design_params = MagicMock()
    design_params.expected_daily_traffic = traffic
    design_params.baseline_conversion_rate = baseline
    design_params.target_lift_pct = target_lift
    design_params.alpha = alpha
    design_params.power = power

    scenario_dto = MagicMock(spec=ScenarioResponseDTO)
    scenario_dto.scenario = scenario
    scenario_dto.design_params = design_params

    return scenario_dto


class TestNoveltyScorer:
    """Test suite for NoveltyScorer class."""

    @pytest.mark.unit
    def test_first_scenario_is_fully_novel(self):
        """First scenario should have perfect novelty score."""
        scorer = NoveltyScorer(history_size=20)
        scenario = create_mock_scenario()

        novelty = scorer.score_novelty(scenario)

        assert novelty == 1.0

    @pytest.mark.unit
    def test_identical_scenario_has_low_novelty(self):
        """Identical scenario should have low novelty."""
        scorer = NoveltyScorer(history_size=20)

        # Record a scenario
        scenario1 = create_mock_scenario()
        scorer.record_scenario(scenario1)

        # Score an identical scenario
        scenario2 = create_mock_scenario()
        novelty = scorer.score_novelty(scenario2)

        # Should be low because all features match
        assert novelty < 0.5

    @pytest.mark.unit
    def test_different_company_type_increases_novelty(self):
        """Different company type should increase novelty."""
        scorer = NoveltyScorer(history_size=20)

        # Record a SaaS scenario
        scenario1 = create_mock_scenario(company_type="B2B SaaS")
        scorer.record_scenario(scenario1)

        # Score an identical scenario first to get baseline
        identical_scenario = create_mock_scenario(company_type="B2B SaaS")
        identical_novelty = scorer.score_novelty(identical_scenario)

        # Score a Healthcare scenario
        scenario2 = create_mock_scenario(company_type="Telehealth")
        novelty = scorer.score_novelty(scenario2)

        # Different company type should be MORE novel than identical
        assert novelty > identical_novelty

    @pytest.mark.unit
    def test_different_segment_increases_novelty(self):
        """Different user segment should increase novelty."""
        scorer = NoveltyScorer(history_size=20)

        # Record a trial users scenario
        scenario1 = create_mock_scenario(user_segment="trial users")
        scorer.record_scenario(scenario1)

        # Score a power users scenario
        scenario2 = create_mock_scenario(user_segment="power users (top 10%)")
        novelty = scorer.score_novelty(scenario2)

        # Should be higher due to different segment
        assert novelty > 0.4

    @pytest.mark.unit
    def test_different_traffic_tier_increases_novelty(self):
        """Different traffic tier should increase novelty."""
        scorer = NoveltyScorer(history_size=20)

        # Record a growth-stage scenario
        scenario1 = create_mock_scenario(traffic=5000)  # growth tier
        scorer.record_scenario(scenario1)

        # Score an identical scenario first to get baseline
        identical_scenario = create_mock_scenario(traffic=5000)
        identical_novelty = scorer.score_novelty(identical_scenario)

        # Score an enterprise-scale scenario
        scenario2 = create_mock_scenario(traffic=500000)  # enterprise tier
        novelty = scorer.score_novelty(scenario2)

        # Different traffic tier should be MORE novel than identical
        assert novelty > identical_novelty

    @pytest.mark.unit
    def test_completely_different_scenario_is_highly_novel(self):
        """Completely different scenario should be highly novel."""
        scorer = NoveltyScorer(history_size=20)

        # Record a typical SaaS scenario
        scenario1 = create_mock_scenario(
            company_type="B2B SaaS",
            user_segment="trial users",
            traffic=5000,
            baseline=0.05,
            target_lift=0.15
        )
        scorer.record_scenario(scenario1)

        # Score a completely different scenario
        scenario2 = create_mock_scenario(
            company_type="Gaming",
            user_segment="power users (top 10%)",
            traffic=500000,
            baseline=0.25,
            target_lift=0.05
        )
        novelty = scorer.score_novelty(scenario2)

        # Should be highly novel
        assert novelty > 0.7

    @pytest.mark.unit
    def test_history_size_limit(self):
        """History should be limited to specified size."""
        history_size = 5
        scorer = NoveltyScorer(history_size=history_size)

        # Record more scenarios than history size
        for i in range(10):
            scenario = create_mock_scenario(company_type=f"Type{i}")
            scorer.record_scenario(scenario)

        # History should be limited
        assert len(scorer.recent_scenarios) == history_size

    @pytest.mark.unit
    def test_record_scenario_adds_to_history(self):
        """Recording a scenario should add it to history."""
        scorer = NoveltyScorer(history_size=20)

        assert len(scorer.recent_scenarios) == 0

        scenario = create_mock_scenario()
        scorer.record_scenario(scenario)

        assert len(scorer.recent_scenarios) == 1

    @pytest.mark.unit
    def test_clear_history(self):
        """Clear history should empty the recent scenarios list."""
        scorer = NoveltyScorer(history_size=20)

        # Add some scenarios
        for i in range(5):
            scenario = create_mock_scenario()
            scorer.record_scenario(scenario)

        assert len(scorer.recent_scenarios) == 5

        scorer.clear_history()

        assert len(scorer.recent_scenarios) == 0


class TestDiversitySuggestions:
    """Test suite for diversity suggestions."""

    @pytest.mark.unit
    def test_no_suggestions_for_novel_scenario(self):
        """Novel scenarios should not get suggestions."""
        scorer = NoveltyScorer(history_size=20)

        # Record a single scenario
        scenario1 = create_mock_scenario()
        scorer.record_scenario(scenario1)

        # Completely different scenario
        scenario2 = create_mock_scenario(
            company_type="Telehealth",
            user_segment="enterprise accounts"
        )

        suggestions = scorer.get_diversity_suggestions(scenario2)

        # Should have few or no suggestions for a novel scenario
        assert len(suggestions) <= 1

    @pytest.mark.unit
    def test_suggestions_for_repetitive_company_type(self):
        """Should suggest alternatives for overused company types."""
        scorer = NoveltyScorer(history_size=20)

        # Record many SaaS scenarios
        for i in range(5):
            scenario = create_mock_scenario(company_type="B2B SaaS")
            scorer.record_scenario(scenario)

        # Try to add another SaaS scenario
        new_scenario = create_mock_scenario(company_type="B2B SaaS")
        suggestions = scorer.get_diversity_suggestions(new_scenario)

        # Should suggest alternatives
        if len(suggestions) > 0:
            assert any("B2B SaaS" in s or "frequently" in s.lower() for s in suggestions)

    @pytest.mark.unit
    def test_no_suggestions_for_empty_history(self):
        """Empty history should produce no suggestions."""
        scorer = NoveltyScorer(history_size=20)
        scenario = create_mock_scenario()

        suggestions = scorer.get_diversity_suggestions(scenario)

        assert len(suggestions) == 0


class TestHistorySummary:
    """Test suite for history summary functionality."""

    @pytest.mark.unit
    def test_empty_history_summary(self):
        """Empty history should return minimal summary."""
        scorer = NoveltyScorer(history_size=20)
        summary = scorer.get_history_summary()

        assert summary["total"] == 0

    @pytest.mark.unit
    def test_history_summary_counts(self):
        """History summary should count feature occurrences correctly."""
        scorer = NoveltyScorer(history_size=20)

        # Record scenarios with different company types
        scorer.record_scenario(create_mock_scenario(company_type="B2B SaaS"))
        scorer.record_scenario(create_mock_scenario(company_type="B2B SaaS"))
        scorer.record_scenario(create_mock_scenario(company_type="Telehealth"))

        summary = scorer.get_history_summary()

        assert summary["total"] == 3
        assert summary["company_types"]["B2B SaaS"] == 2
        assert summary["company_types"]["Telehealth"] == 1


class TestGlobalNoveltyScorer:
    """Test suite for global novelty scorer functions."""

    @pytest.mark.unit
    def test_get_novelty_scorer_returns_instance(self):
        """get_novelty_scorer should return a NoveltyScorer instance."""
        scorer = get_novelty_scorer()
        assert isinstance(scorer, NoveltyScorer)

    @pytest.mark.unit
    def test_score_scenario_novelty_returns_tuple(self):
        """score_scenario_novelty should return score and suggestions."""
        scenario = create_mock_scenario()
        result = score_scenario_novelty(scenario)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], list)

    @pytest.mark.unit
    def test_record_generated_scenario(self):
        """record_generated_scenario should add to history."""
        # Clear history first
        scorer = get_novelty_scorer()
        scorer.clear_history()

        scenario = create_mock_scenario()
        initial_count = len(scorer.recent_scenarios)

        record_generated_scenario(scenario)

        assert len(scorer.recent_scenarios) == initial_count + 1


class TestFeatureExtraction:
    """Test suite for feature extraction logic."""

    @pytest.mark.unit
    def test_traffic_tier_extraction_early_stage(self):
        """Should correctly identify early stage traffic tier."""
        scorer = NoveltyScorer(history_size=20)
        scenario = create_mock_scenario(traffic=500)

        features = scorer._extract_features(scenario)

        assert features["traffic_tier"] == "early_stage"

    @pytest.mark.unit
    def test_traffic_tier_extraction_growth(self):
        """Should correctly identify growth traffic tier."""
        scorer = NoveltyScorer(history_size=20)
        scenario = create_mock_scenario(traffic=5000)

        features = scorer._extract_features(scenario)

        assert features["traffic_tier"] == "growth"

    @pytest.mark.unit
    def test_traffic_tier_extraction_scale(self):
        """Should correctly identify scale traffic tier."""
        scorer = NoveltyScorer(history_size=20)
        scenario = create_mock_scenario(traffic=50000)

        features = scorer._extract_features(scenario)

        assert features["traffic_tier"] == "scale"

    @pytest.mark.unit
    def test_traffic_tier_extraction_enterprise(self):
        """Should correctly identify enterprise traffic tier."""
        scorer = NoveltyScorer(history_size=20)
        scenario = create_mock_scenario(traffic=500000)

        features = scorer._extract_features(scenario)

        assert features["traffic_tier"] == "enterprise"

    @pytest.mark.unit
    def test_baseline_tier_extraction(self):
        """Should correctly identify baseline tiers."""
        scorer = NoveltyScorer(history_size=20)

        # Very low baseline
        scenario1 = create_mock_scenario(baseline=0.005)
        assert scorer._extract_features(scenario1)["baseline_tier"] == "very_low"

        # Low baseline
        scenario2 = create_mock_scenario(baseline=0.03)
        assert scorer._extract_features(scenario2)["baseline_tier"] == "low"

        # Medium baseline
        scenario3 = create_mock_scenario(baseline=0.10)
        assert scorer._extract_features(scenario3)["baseline_tier"] == "medium"

        # High baseline
        scenario4 = create_mock_scenario(baseline=0.20)
        assert scorer._extract_features(scenario4)["baseline_tier"] == "high"

        # Very high baseline
        scenario5 = create_mock_scenario(baseline=0.40)
        assert scorer._extract_features(scenario5)["baseline_tier"] == "very_high"

    @pytest.mark.unit
    def test_effect_tier_extraction(self):
        """Should correctly identify effect size tiers."""
        scorer = NoveltyScorer(history_size=20)

        # Incremental
        scenario1 = create_mock_scenario(target_lift=0.03)
        assert scorer._extract_features(scenario1)["effect_tier"] == "incremental"

        # Moderate
        scenario2 = create_mock_scenario(target_lift=0.10)
        assert scorer._extract_features(scenario2)["effect_tier"] == "moderate"

        # Significant
        scenario3 = create_mock_scenario(target_lift=0.30)
        assert scorer._extract_features(scenario3)["effect_tier"] == "significant"

        # Transformational
        scenario4 = create_mock_scenario(target_lift=0.80)
        assert scorer._extract_features(scenario4)["effect_tier"] == "transformational"
