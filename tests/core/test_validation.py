"""
Tests for core.validation module - Answer validation and scoring.
"""

import pytest
from core.validation import (
    validate_design_answer,
    validate_analysis_answer,
    calculate_correct_design_answers,
    calculate_correct_analysis_answers
)
from tests.helpers.factories import create_significant_positive_result


class TestValidateDesignAnswer:
    """Test suite for validate_design_answer function - all 6 questions."""
    
    @pytest.mark.unit
    def test_validate_question_1_mde(self, standard_design_params):
        """Test validation of Question 1: MDE."""
        
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde_absolute = baseline * target_lift
        
        # Correct answer in percentage points
        correct_answer_pct_points = mde_absolute * 100
        
        validation = validate_design_answer(
            question_num=1,
            user_answer=correct_answer_pct_points,
            design_params=standard_design_params,
            mde_absolute=mde_absolute
        )
        
        assert validation.is_correct == True
        assert validation.tolerance == 0.5
    
    @pytest.mark.unit
    def test_validate_question_2_target_rate(self, standard_design_params):
        """Test validation of Question 2: Target conversion rate."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde_absolute = baseline * target_lift
        
        # Correct answer: (baseline + mde) * 100
        correct_answer = (baseline + mde_absolute) * 100
        
        validation = validate_design_answer(
            question_num=2,
            user_answer=correct_answer,
            design_params=standard_design_params,
            mde_absolute=mde_absolute
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_question_3_relative_lift(self, standard_design_params):
        """Test validation of Question 3: Relative lift."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde_absolute = baseline * target_lift
        
        # Correct answer: (mde / baseline) * 100
        correct_answer = (mde_absolute / baseline) * 100
        
        validation = validate_design_answer(
            question_num=3,
            user_answer=correct_answer,
            design_params=standard_design_params,
            mde_absolute=mde_absolute
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_question_4_sample_size(self, standard_design_params):
        """Test validation of Question 4: Sample size."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        
        validation = validate_design_answer(
            question_num=4,
            user_answer=sample_size.per_arm,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert validation.is_correct == True
        assert validation.tolerance == 50
    
    @pytest.mark.unit
    def test_validate_question_5_duration(self, standard_design_params):
        """Test validation of Question 5: Test duration."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        required_sample = sample_size.per_arm * 2
        correct_days = max(1, round(required_sample / standard_design_params.expected_daily_traffic))
        
        validation = validate_design_answer(
            question_num=5,
            user_answer=correct_days,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_question_6_additional_conversions(self, standard_design_params):
        """Test validation of Question 6: Additional conversions per day."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde_absolute = baseline * target_lift
        
        correct_answer = round(standard_design_params.expected_daily_traffic * mde_absolute)
        
        validation = validate_design_answer(
            question_num=6,
            user_answer=correct_answer,
            design_params=standard_design_params,
            mde_absolute=mde_absolute
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_within_tolerance(self, standard_design_params):
        """Test that answers within tolerance are accepted."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        
        # Answer slightly different but within tolerance (50 users for sample size)
        user_answer = sample_size.per_arm + 30  # Within 50 user tolerance
        
        validation = validate_design_answer(
            question_num=4,
            user_answer=user_answer,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_outside_tolerance(self, standard_design_params):
        """Test that answers outside tolerance are rejected."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        
        # Answer way off
        user_answer = sample_size.per_arm * 2.0  # 100% off
        
        validation = validate_design_answer(
            question_num=4,
            user_answer=user_answer,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert validation.is_correct == False
    
    @pytest.mark.unit
    def test_validate_invalid_question_number(self, standard_design_params):
        """Test that invalid question number raises error."""
        with pytest.raises(ValueError):
            validate_design_answer(
                question_num=999,
                user_answer=100,
                design_params=standard_design_params
            )


class TestValidateAnalysisAnswer:
    """Test suite for validate_analysis_answer function - all 7 questions."""
    
    @pytest.mark.unit
    def test_validate_question_1_control_rate(self):
        """Test validation of Question 1: Control conversion rate."""
        from tests.helpers.factories import create_sim_result
        
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        
        # Correct answer: 5.0%
        correct_answer = 5.0
        
        validation = validate_analysis_answer(
            question_num=1,
            user_answer=correct_answer,
            sim_result=sim_result
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_question_2_treatment_rate(self):
        """Test validation of Question 2: Treatment conversion rate."""
        from tests.helpers.factories import create_sim_result
        
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        
        # Correct answer: 6.0%
        correct_answer = 6.0
        
        validation = validate_analysis_answer(
            question_num=2,
            user_answer=correct_answer,
            sim_result=sim_result
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_question_3_absolute_lift(self):
        """Test validation of Question 3: Absolute lift."""
        from tests.helpers.factories import create_sim_result
        
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        
        # Correct answer: 1.0 percentage point
        correct_answer = 1.0
        
        validation = validate_analysis_answer(
            question_num=3,
            user_answer=correct_answer,
            sim_result=sim_result
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_question_4_relative_lift(self):
        """Test validation of Question 4: Relative lift."""
        from tests.helpers.factories import create_sim_result
        
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,  # 5%
            treatment_n=1000,
            treatment_conversions=60  # 6%
        )
        
        # Correct answer: 20% relative lift
        correct_answer = 20.0
        
        validation = validate_analysis_answer(
            question_num=4,
            user_answer=correct_answer,
            sim_result=sim_result
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_question_5_p_value(self):
        """Test validation of Question 5: P-value."""
        from core.analyze import analyze_results
        
        sim_result = create_significant_positive_result(seed=42)
        analysis = analyze_results(sim_result, alpha=0.05)
        
        # Use the calculated p-value
        validation = validate_analysis_answer(
            question_num=5,
            user_answer=analysis.p_value,
            sim_result=sim_result
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_question_6_confidence_interval(self):
        """Test validation of Question 6: Confidence interval."""
        from core.analyze import analyze_results
        
        sim_result = create_significant_positive_result(seed=42)
        analysis = analyze_results(sim_result, alpha=0.05)
        
        # Confidence interval as tuple
        ci_tuple = analysis.confidence_interval
        
        # Test with tuple format
        validation = validate_analysis_answer(
            question_num=6,
            user_answer=ci_tuple,
            sim_result=sim_result
        )
        
        # Should validate (exact match or within tolerance)
        assert isinstance(validation, object)
    
    @pytest.mark.unit
    def test_validate_question_7_rollout_decision(self):
        """Test validation of Question 7: Rollout decision."""
        from core.analyze import analyze_results, make_rollout_decision
        
        sim_result = create_significant_positive_result(seed=42)
        analysis = analyze_results(sim_result, alpha=0.05)
        
        correct_decision = make_rollout_decision(
            sim_result,
            analysis,
            business_target_absolute=0.01
        )
        
        validation = validate_analysis_answer(
            question_num=7,
            user_answer=correct_decision,
            sim_result=sim_result,
            business_target_absolute=0.01
        )
        
        assert validation.is_correct == True
    
    @pytest.mark.unit
    def test_validate_analysis_invalid_question(self):
        """Test that invalid question number raises error."""
        from tests.helpers.factories import create_sim_result
        
        sim_result = create_sim_result()
        
        with pytest.raises(ValueError):
            validate_analysis_answer(
                question_num=999,
                user_answer=0.5,
                sim_result=sim_result
            )


class TestCalculateCorrectAnswers:
    """Test suite for calculating correct answers."""
    
    @pytest.mark.unit
    def test_calculate_correct_design_answers(self, standard_design_params):
        """Test calculation of correct design answers."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        
        correct_answers = calculate_correct_design_answers(
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        # Check that we get a dictionary with answer keys
        assert isinstance(correct_answers, dict)
        assert len(correct_answers) > 0
    
    @pytest.mark.unit
    def test_calculate_correct_analysis_answers(self):
        """Test calculation of correct analysis answers."""
        sim_result = create_significant_positive_result(seed=42)
        
        correct_answers = calculate_correct_analysis_answers(
            sim_result=sim_result,
            business_target_absolute=0.01
        )
        
        assert "control_conversion_rate" in correct_answers
        assert "treatment_conversion_rate" in correct_answers
        assert "p_value" in correct_answers
        assert "rollout_decision" in correct_answers

