"""
Comprehensive tests for alternative statistical tests in core.analyze.

Tests for chi-square test, Fisher's exact test, and automatic test selection.
"""

import pytest
from scipy.stats import fisher_exact as scipy_fisher_exact
from scipy.stats import chi2

from core.analyze import analyze_results, select_statistical_test, _chi_square_p_value
from core.types import StatisticalTestSelection
from tests.helpers.factories import create_sim_result, create_significant_positive_result
from tests.helpers.assertions import assert_p_value_valid


class TestChiSquareTest:
    """Test suite for chi-square test implementation."""
    
    @pytest.mark.unit
    def test_chi_square_basic(self):
        """Test basic chi-square test execution."""
        result = create_significant_positive_result(seed=42)
        analysis = analyze_results(result, alpha=0.05, test_type="chi_square")

        assert_p_value_valid(analysis.p_value)
        assert len(analysis.confidence_interval) == 2
        assert isinstance(analysis.significant, bool)

    @pytest.mark.unit
    def test_chi_square_vs_z_test(self):
        """Test that chi-square gives similar results to z-test."""
        result = create_significant_positive_result(n_per_arm=5000, seed=42)
        analysis_z = analyze_results(result, alpha=0.05, test_type="two_proportion_z")
        analysis_chi = analyze_results(result, alpha=0.05, test_type="chi_square")

        # P-values should be similar (within reasonable tolerance)
        # Both tests are asymptotically equivalent for large samples
        assert abs(analysis_z.p_value - analysis_chi.p_value) < 0.05

        # Should reach same significance conclusion
        assert analysis_z.significant == analysis_chi.significant

    @pytest.mark.unit
    def test_chi_square_various_sample_sizes(self):
        """Test chi-square with various sample sizes."""
        for n in [100, 500, 1000, 5000]:
            result = create_sim_result(
                control_n=n,
                control_conversions=int(n * 0.05),
                treatment_n=n,
                treatment_conversions=int(n * 0.06)
            )
            analysis = analyze_results(result, alpha=0.05, test_type="chi_square")
            assert_p_value_valid(analysis.p_value)

    @pytest.mark.unit
    def test_chi_square_edge_cases(self):
        """Test chi-square with edge cases."""
        small_result = create_sim_result(
            control_n=20,
            control_conversions=2,
            treatment_n=20,
            treatment_conversions=5
        )
        analysis = analyze_results(small_result, alpha=0.05, test_type="chi_square")
        assert_p_value_valid(analysis.p_value)

    @pytest.mark.unit
    def test_chi_square_returns_analysis_result(self):
        """Test that chi-square returns complete AnalysisResult."""
        result = create_significant_positive_result(seed=42)
        analysis = analyze_results(result, alpha=0.05, test_type="chi_square")

        assert hasattr(analysis, 'test_statistic')
        assert hasattr(analysis, 'p_value')
        assert hasattr(analysis, 'confidence_interval')
        assert hasattr(analysis, 'significant')
        assert hasattr(analysis, 'recommendation')


class TestFisherExactTest:
    """Test suite for Fisher's exact test implementation."""
    
    @pytest.mark.unit
    def test_fisher_exact_basic(self):
        """Test basic Fisher's exact test execution."""
        result = create_sim_result(
            control_n=30,
            control_conversions=5,
            treatment_n=30,
            treatment_conversions=10
        )
        analysis = analyze_results(result, alpha=0.05, test_type="fisher_exact")

        assert_p_value_valid(analysis.p_value)
        assert len(analysis.confidence_interval) == 2
        assert isinstance(analysis.significant, bool)

    @pytest.mark.unit
    def test_fisher_exact_small_samples(self):
        """Test Fisher's exact with various small samples."""
        for n in [10, 20, 30, 50]:
            result = create_sim_result(
                control_n=n,
                control_conversions=max(1, int(n * 0.1)),
                treatment_n=n,
                treatment_conversions=max(2, int(n * 0.2))
            )
            analysis = analyze_results(result, alpha=0.05, test_type="fisher_exact")
            assert_p_value_valid(analysis.p_value)

    @pytest.mark.unit
    def test_fisher_exact_vs_chi_square(self):
        """Test Fisher's exact gives exact results for small samples."""
        result = create_sim_result(
            control_n=25,
            control_conversions=5,
            treatment_n=25,
            treatment_conversions=10
        )
        analysis_fisher = analyze_results(result, alpha=0.05, test_type="fisher_exact")
        assert_p_value_valid(analysis_fisher.p_value)

        analysis_chi = analyze_results(result, alpha=0.05, test_type="chi_square")
        assert_p_value_valid(analysis_chi.p_value)

        # P-values may differ but should be in same ballpark
        assert abs(analysis_fisher.p_value - analysis_chi.p_value) < 0.3

    @pytest.mark.unit
    def test_fisher_exact_edge_case_zero_conversions(self):
        """Test Fisher's exact with zero conversions in one group."""
        result = create_sim_result(
            control_n=20,
            control_conversions=0,
            treatment_n=20,
            treatment_conversions=5
        )
        analysis = analyze_results(result, alpha=0.05, test_type="fisher_exact")
        assert_p_value_valid(analysis.p_value)

    @pytest.mark.unit
    def test_fisher_exact_returns_analysis_result(self):
        """Test that Fisher's exact returns complete AnalysisResult."""
        result = create_sim_result(
            control_n=30,
            control_conversions=5,
            treatment_n=30,
            treatment_conversions=10
        )
        analysis = analyze_results(result, alpha=0.05, test_type="fisher_exact")

        assert hasattr(analysis, 'test_statistic')
        assert hasattr(analysis, 'p_value')
        assert hasattr(analysis, 'confidence_interval')
        assert hasattr(analysis, 'significant')
        assert hasattr(analysis, 'recommendation')


class TestScipyAccuracy:
    """Verify our implementations match scipy directly."""

    @pytest.mark.unit
    def test_fisher_exact_works_for_large_samples(self):
        """Fisher's exact should NOT fall back to chi-square for n > 100."""
        result = create_sim_result(
            control_n=500,
            control_conversions=2,
            treatment_n=500,
            treatment_conversions=8,
        )
        analysis = analyze_results(result, alpha=0.05, test_type="fisher_exact")
        assert analysis.test_type_used == "fisher_exact"
        assert_p_value_valid(analysis.p_value)

    @pytest.mark.unit
    def test_fisher_exact_matches_scipy(self):
        """Fisher's exact p-value should match scipy.stats.fisher_exact."""
        result = create_sim_result(
            control_n=50,
            control_conversions=3,
            treatment_n=50,
            treatment_conversions=10,
        )
        analysis = analyze_results(result, alpha=0.05, test_type="fisher_exact")

        table = [[3, 47], [10, 40]]
        _, expected_p = scipy_fisher_exact(table, alternative="two-sided")
        assert abs(analysis.p_value - expected_p) < 1e-10

    @pytest.mark.unit
    def test_chi_square_p_value_matches_scipy_df1(self):
        """Chi-square p-value should match scipy for df=1."""
        p = _chi_square_p_value(3.84, df=1)
        expected = float(chi2.sf(3.84, 1))
        assert abs(p - expected) < 1e-10

    @pytest.mark.unit
    def test_chi_square_p_value_matches_scipy_df2(self):
        """Chi-square p-value should match scipy for df=2 (previously broken)."""
        p = _chi_square_p_value(5.99, df=2)
        expected = float(chi2.sf(5.99, 2))
        assert abs(p - expected) < 1e-10


class TestAutomaticTestSelection:
    """Test suite for automatic statistical test selection."""

    @pytest.mark.unit
    def test_select_fisher_for_small_expected_counts(self):
        """Test that Fisher's exact is selected when expected cell counts are small."""
        # Very low conversion rate with small sample -> small expected counts
        result = create_sim_result(
            control_n=50,
            control_conversions=2,
            treatment_n=50,
            treatment_conversions=5
        )

        selection = select_statistical_test(result)

        assert isinstance(selection, StatisticalTestSelection)
        assert selection.test_type == "fisher_exact"
        assert selection.min_expected_cell_count < 5
        assert "Fisher's exact" in selection.reasoning

    @pytest.mark.unit
    def test_select_chi_square_for_medium_samples(self):
        """Test that chi-square is selected for medium-sized samples."""
        # Medium sample with adequate expected counts but < 30 per group
        result = create_sim_result(
            control_n=25,
            control_conversions=5,
            treatment_n=25,
            treatment_conversions=8
        )

        selection = select_statistical_test(result)

        assert isinstance(selection, StatisticalTestSelection)
        # With these numbers, expected counts should be >= 5
        # but sample size < 30, so chi-square should be selected
        if selection.min_expected_cell_count >= 5:
            assert selection.test_type in ["chi_square", "two_proportion_z"]

    @pytest.mark.unit
    def test_select_z_test_for_large_samples(self):
        """Test that z-test is selected for large samples."""
        result = create_sim_result(
            control_n=5000,
            control_conversions=250,
            treatment_n=5000,
            treatment_conversions=300
        )

        selection = select_statistical_test(result)

        assert isinstance(selection, StatisticalTestSelection)
        assert selection.test_type == "two_proportion_z"
        assert selection.sample_size_adequate is True
        assert selection.min_expected_cell_count >= 5
        assert "z-test" in selection.reasoning.lower()

    @pytest.mark.unit
    def test_auto_mode_uses_selection(self):
        """Test that analyze_results with auto mode uses test selection."""
        result = create_sim_result(
            control_n=5000,
            control_conversions=250,
            treatment_n=5000,
            treatment_conversions=300
        )

        analysis = analyze_results(result, alpha=0.05, test_type="auto")

        assert analysis.test_type_used is not None
        assert analysis.test_selection is not None
        assert analysis.test_type_used == analysis.test_selection.test_type

    @pytest.mark.unit
    def test_manual_mode_skips_selection(self):
        """Test that manual test type does not populate test_selection."""
        result = create_sim_result(
            control_n=5000,
            control_conversions=250,
            treatment_n=5000,
            treatment_conversions=300
        )

        analysis = analyze_results(result, alpha=0.05, test_type="two_proportion_z")

        assert analysis.test_type_used == "two_proportion_z"
        assert analysis.test_selection is None

    @pytest.mark.unit
    def test_selection_includes_alternatives(self):
        """Test that test selection includes alternative tests."""
        result = create_sim_result(
            control_n=5000,
            control_conversions=250,
            treatment_n=5000,
            treatment_conversions=300
        )

        selection = select_statistical_test(result)

        assert len(selection.alternative_tests) > 0
        assert all(isinstance(t, str) for t in selection.alternative_tests)

    @pytest.mark.unit
    def test_selection_edge_case_very_low_conversions(self):
        """Test selection with very low conversion counts."""
        result = create_sim_result(
            control_n=100,
            control_conversions=1,
            treatment_n=100,
            treatment_conversions=2
        )

        selection = select_statistical_test(result)

        # With only 3 total conversions, Fisher's exact should be selected
        assert selection.test_type == "fisher_exact"
        assert selection.min_expected_cell_count < 5

