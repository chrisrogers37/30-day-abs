"""
Comprehensive tests for core.analyze business functions.

Tests for calculate_business_impact and assess_test_quality functions.
"""

import pytest
from core.analyze import calculate_business_impact, assess_test_quality
from tests.helpers.factories import (
    create_design_params,
    create_significant_positive_result,
    create_sim_result
)


class TestCalculateBusinessImpact:
    """Test suite for calculate_business_impact function."""
    
    @pytest.mark.unit
    def test_business_impact_basic(self):
        """Test basic business impact calculation."""
        sim_result = create_significant_positive_result(seed=42)
        
        impact = calculate_business_impact(
            sim_result=sim_result,
            revenue_per_conversion=50.0,
            monthly_traffic=30000
        )
        
        assert impact is not None
        assert impact.absolute_lift > 0
        assert impact.relative_lift_pct > 0
        assert isinstance(impact.rollout_recommendation, str)
        assert impact.risk_level in ["low", "medium", "high"]
    
    @pytest.mark.unit
    def test_business_impact_revenue_calculations(self):
        """Test revenue impact calculations."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,  # 5%
            treatment_n=1000,
            treatment_conversions=60  # 6%, +1% absolute lift
        )
        
        impact = calculate_business_impact(
            sim_result=sim_result,
            revenue_per_conversion=100.0,
            monthly_traffic=30000
        )
        
        # With 1% lift and 30k monthly traffic: 300 additional conversions
        # 300 * $100 = $30,000 monthly revenue impact
        assert impact.revenue_impact_monthly is not None
        assert impact.revenue_impact_monthly > 0
        assert 25000 < impact.revenue_impact_monthly < 35000  # Rough range
    
    @pytest.mark.unit
    def test_business_impact_without_revenue(self):
        """Test business impact without revenue data."""
        sim_result = create_significant_positive_result(seed=42)
        
        impact = calculate_business_impact(sim_result=sim_result)
        
        # Should still calculate lift and recommendation
        assert impact.absolute_lift > 0
        assert impact.rollout_recommendation in [
            "proceed_with_confidence",
            "proceed_with_caution",
            "do_not_proceed"
        ]
        # Revenue fields may be None
        assert impact.revenue_impact_monthly is None or isinstance(impact.revenue_impact_monthly, float)
    
    @pytest.mark.unit
    def test_business_impact_rollout_recommendations(self):
        """Test rollout recommendation logic."""
        # Large positive lift
        large_lift_result = create_sim_result(
            control_n=5000,
            control_conversions=250,  # 5%
            treatment_n=5000,
            treatment_conversions=350  # 7%, +2% absolute lift
        )
        
        impact_large = calculate_business_impact(large_lift_result)
        
        # Should recommend proceeding with confidence for large lift
        assert impact_large.rollout_recommendation in ["proceed_with_confidence", "proceed_with_caution"]
        assert impact_large.risk_level in ["low", "medium"]
    
    @pytest.mark.unit
    def test_business_impact_risk_levels(self):
        """Test risk level assessment."""
        # Small lift
        small_lift_result = create_sim_result(
            control_n=1000,
            control_conversions=50,  # 5%
            treatment_n=1000,
            treatment_conversions=52  # 5.2%, +0.2% absolute lift
        )
        
        impact_small = calculate_business_impact(small_lift_result)
        
        # Small lift should have higher risk
        assert impact_small.risk_level in ["medium", "high"]
    
    @pytest.mark.unit
    def test_business_impact_confidence_in_revenue(self):
        """Test confidence in revenue calculation."""
        sim_result = create_significant_positive_result(seed=42)
        
        impact = calculate_business_impact(
            sim_result=sim_result,
            revenue_per_conversion=50.0,
            monthly_traffic=30000
        )
        
        # Confidence should be a probability if calculated
        if impact.confidence_in_revenue is not None:
            assert 0 <= impact.confidence_in_revenue <= 1


class TestAssessTestQuality:
    """Test suite for assess_test_quality function."""
    
    @pytest.mark.unit
    def test_assess_test_quality_basic(self):
        """Test basic test quality assessment."""
        params = create_design_params()
        sim_result = create_significant_positive_result(n_per_arm=5000, seed=42)
        
        quality = assess_test_quality(sim_result, params)
        
        assert quality is not None
        assert quality.early_stopping_risk in ["low", "medium", "high"]
        assert quality.novelty_effect_potential in ["low", "medium", "high"]
        assert isinstance(quality.sample_size_adequacy, bool)
    
    @pytest.mark.unit
    def test_early_stopping_risk_assessment(self):
        """Test early stopping risk assessment."""
        params = create_design_params()
        
        # Small sample - high risk
        small_sample = create_sim_result(control_n=500, control_conversions=25,
                                        treatment_n=500, treatment_conversions=30)
        quality_small = assess_test_quality(small_sample, params)
        assert quality_small.early_stopping_risk == "high"
        
        # Large sample - low risk
        large_sample = create_sim_result(control_n=10000, control_conversions=500,
                                        treatment_n=10000, treatment_conversions=600)
        quality_large = assess_test_quality(large_sample, params)
        assert quality_large.early_stopping_risk == "low"
    
    @pytest.mark.unit
    def test_novelty_effect_assessment(self):
        """Test novelty effect potential assessment."""
        # High lift - high novelty risk
        params_high_lift = create_design_params(target_lift_pct=0.30)
        sim_result = create_significant_positive_result(seed=42)
        
        quality = assess_test_quality(sim_result, params_high_lift)
        assert quality.novelty_effect_potential in ["medium", "high"]
        
        # Low lift - low novelty risk
        params_low_lift = create_design_params(target_lift_pct=0.05)
        quality_low = assess_test_quality(sim_result, params_low_lift)
        assert quality_low.novelty_effect_potential in ["low", "medium"]
    
    @pytest.mark.unit
    def test_sample_size_adequacy(self):
        """Test sample size adequacy assessment."""
        params = create_design_params()
        
        # Adequate sample
        adequate = create_sim_result(control_n=5000, control_conversions=250,
                                    treatment_n=5000, treatment_conversions=300)
        quality = assess_test_quality(adequate, params)
        assert quality.sample_size_adequacy == True
        
        # Inadequate sample
        inadequate = create_sim_result(control_n=100, control_conversions=5,
                                      treatment_n=100, treatment_conversions=6)
        quality_small = assess_test_quality(inadequate, params)
        assert quality_small.sample_size_adequacy == False
    
    @pytest.mark.unit
    def test_allocation_balance(self):
        """Test allocation balance calculation."""
        params = create_design_params()
        
        # Balanced allocation
        balanced = create_sim_result(control_n=1000, control_conversions=50,
                                    treatment_n=1000, treatment_conversions=60)
        quality = assess_test_quality(balanced, params)
        
        # Allocation balance should be close to 0.5 for balanced split
        assert 0.45 <= quality.allocation_balance <= 0.55

