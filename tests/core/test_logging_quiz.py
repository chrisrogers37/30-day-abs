"""
Tests for quiz session logging functionality in core/logging.py.

This module tests the QuizLogger class and related functions for
structured quiz session logging.
"""

import pytest
import tempfile
from pathlib import Path
from core.logging import (
    QuizLogger, QuizSession, start_quiz_session, configure_quiz_logging,
    setup_logging, reset_logging
)


class TestQuizSession:
    """Test QuizSession dataclass."""
    
    @pytest.mark.unit
    def test_quiz_session_creation(self):
        """Test QuizSession can be created with required fields."""
        from datetime import datetime
        
        session = QuizSession(
            session_id="test123",
            start_time=datetime.now()
        )
        
        assert session.session_id == "test123"
        assert session.user_id is None
        assert session.scenario_title is None
        assert session.total_questions == 0
        assert session.questions_answered == 0
        assert session.score is None
        assert session.duration_seconds is None
    
    @pytest.mark.unit
    def test_quiz_session_with_optional_fields(self):
        """Test QuizSession with optional fields."""
        from datetime import datetime
        
        session = QuizSession(
            session_id="test456",
            start_time=datetime.now(),
            user_id="user123",
            scenario_title="E-commerce Test",
            total_questions=6,
            questions_answered=3,
            score=0.75,
            duration_seconds=120.5
        )
        
        assert session.user_id == "user123"
        assert session.scenario_title == "E-commerce Test"
        assert session.total_questions == 6
        assert session.questions_answered == 3
        assert session.score == 0.75
        assert session.duration_seconds == 120.5


class TestQuizLogger:
    """Test QuizLogger class functionality."""
    
    @pytest.mark.unit
    def test_quiz_logger_creation(self):
        """Test QuizLogger can be created."""
        reset_logging()
        
        logger = QuizLogger("test123")
        
        assert logger.session_id == "test123"
        assert isinstance(logger.session, QuizSession)
        assert logger.session.session_id == "test123"
        assert logger.logger.name == "quiz.session.test123"
    
    @pytest.mark.unit
    def test_log_user_action(self, tmp_path):
        """Test logging user actions."""
        log_file = tmp_path / "test.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        
        logger = QuizLogger("test123")
        logger.log_user_action("Button Clicked", "Generate Scenario")
        
        content = log_file.read_text()
        assert "USER ACTION: Button Clicked | Generate Scenario" in content
    
    @pytest.mark.unit
    def test_log_scenario_generated(self, tmp_path):
        """Test logging scenario generation."""
        log_file = tmp_path / "test.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        
        logger = QuizLogger("test123")
        
        scenario_data = {
            'scenario': {
                'title': 'E-commerce Checkout Test',
                'company': 'ShopFast',
                'industry': 'E-commerce',
                'baseline_conversion_rate': 0.025,
                'target_lift_pct': 0.20,
                'expected_daily_traffic': 10000,
                'business_context': 'Improve checkout conversion'
            }
        }
        
        logger.log_scenario_generated(scenario_data)
        
        content = log_file.read_text()
        assert "SCENARIO GENERATED" in content
        assert "Title: E-commerce Checkout Test" in content
        assert "Company: ShopFast" in content
        assert "Industry: E-commerce" in content
        assert "Baseline Conversion: 2.5%" in content
        assert "Target Lift: 20.0%" in content
        assert "Daily Traffic: 10,000" in content
        assert "Business Context: Improve checkout conversion" in content
    
    @pytest.mark.unit
    def test_log_question_answered(self, tmp_path):
        """Test logging question answers."""
        log_file = tmp_path / "test.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        
        logger = QuizLogger("test123")
        logger.log_question_answered(1, 2.5, 2.5, True, 0.1)
        
        content = log_file.read_text()
        assert "ANSWER RECEIVED for Question 1:" in content
        assert "User Answer: 2.5" in content
        assert "Correct Answer: 2.5" in content
        assert "Result: ✅ CORRECT" in content
        assert "Tolerance: ±10.0%" in content
    
    @pytest.mark.unit
    def test_log_question_answered_incorrect(self, tmp_path):
        """Test logging incorrect question answers."""
        log_file = tmp_path / "test.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        
        logger = QuizLogger("test123")
        logger.log_question_answered(2, 3.0, 2.5, False)
        
        content = log_file.read_text()
        assert "ANSWER RECEIVED for Question 2:" in content
        assert "User Answer: 3.0" in content
        assert "Correct Answer: 2.5" in content
        assert "Result: ❌ INCORRECT" in content
    
    @pytest.mark.unit
    def test_log_sample_size_calculation(self, tmp_path):
        """Test logging sample size calculations."""
        log_file = tmp_path / "test.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        
        logger = QuizLogger("test123")
        
        design_params = {
            'alpha': 0.05,
            'power': 0.80,
            'baseline_conversion_rate': 0.025,
            'target_lift_pct': 0.20
        }
        
        sample_size_result = {
            'per_arm': 5000,
            'total': 10000,
            'days_required': 10.0,
            'power_achieved': 0.80
        }
        
        logger.log_sample_size_calculation(design_params, sample_size_result)
        
        content = log_file.read_text()
        assert "SAMPLE SIZE CALCULATION" in content
        assert "Alpha: 0.050" in content
        assert "Power: 80.0%" in content
        assert "Baseline Rate: 2.5%" in content
        assert "Target Lift: 20.0%" in content
        assert "Per Arm: 5,000" in content
        assert "Total: 10,000" in content
        assert "Days Required: 10.0" in content
        assert "Power Achieved: 80.0%" in content
    
    @pytest.mark.unit
    def test_log_simulation_results(self, tmp_path):
        """Test logging simulation results."""
        log_file = tmp_path / "test.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        
        logger = QuizLogger("test123")
        
        sim_result = {
            'control_n': 5000,
            'control_conversions': 125,
            'control_rate': 0.025,
            'treatment_n': 5000,
            'treatment_conversions': 150,
            'treatment_rate': 0.030,
            'absolute_lift': 0.005,
            'relative_lift_pct': 0.20
        }
        
        logger.log_simulation_results(sim_result)
        
        content = log_file.read_text()
        assert "SIMULATION RESULTS" in content
        assert "Control Group: 5,000 users, 125 conversions (2.5%)" in content
        assert "Treatment Group: 5,000 users, 150 conversions (3.0%)" in content
        assert "Absolute Lift: 0.5%" in content
        assert "Relative Lift: 20.0%" in content
    
    @pytest.mark.unit
    def test_log_analysis_results(self, tmp_path):
        """Test logging analysis results."""
        log_file = tmp_path / "test.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        
        logger = QuizLogger("test123")
        
        analysis_result = {
            'p_value': 0.0234,
            'significant': True,
            'confidence_interval': "(0.001, 0.009)",
            'recommendation': 'Roll out treatment'
        }
        
        logger.log_analysis_results(analysis_result)
        
        content = log_file.read_text()
        assert "STATISTICAL ANALYSIS" in content
        assert "P-value: 0.0234" in content
        assert "Significant: Yes" in content
        assert "Confidence Interval: (0.001, 0.009)" in content
        assert "Recommendation: Roll out treatment" in content
    
    @pytest.mark.unit
    def test_log_quiz_completed(self, tmp_path):
        """Test logging quiz completion."""
        log_file = tmp_path / "test.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        
        logger = QuizLogger("test123")
        logger.session.scenario_title = "E-commerce Test"
        
        feedback = "Question 1: Correct\nQuestion 2: Incorrect\nQuestion 3: Correct"
        logger.log_quiz_completed(0.67, feedback, 3, 2)
        
        content = log_file.read_text()
        assert "QUIZ COMPLETED" in content
        assert "Score: 67.0% (2/3 correct)" in content
        assert "Session ID: test123" in content
        assert "Question 1: Correct" in content
        assert "Question 2: Incorrect" in content
        assert "Question 3: Correct" in content
        assert "SESSION SUMMARY:" in content
        assert "Scenario: E-commerce Test" in content
        assert "Questions: 2/3 correct" in content


class TestQuizSessionFunctions:
    """Test quiz session utility functions."""
    
    @pytest.mark.unit
    def test_start_quiz_session(self, tmp_path):
        """Test starting a quiz session."""
        reset_logging()
        
        # Test that start_quiz_session creates a QuizLogger
        session_logger = start_quiz_session(user_id="user123")
        
        assert isinstance(session_logger, QuizLogger)
        assert session_logger.session.user_id == "user123"
        assert session_logger.session_id is not None
        assert len(session_logger.session_id) == 8  # Short UUID
        
        # Test that the logger was created properly
        assert session_logger.logger.name.startswith("quiz.session.")
        assert session_logger.session.session_id == session_logger.session_id
    
    @pytest.mark.unit
    def test_configure_quiz_logging(self):
        """Test configuring quiz logging."""
        reset_logging()
        
        # This should not raise an exception
        configure_quiz_logging()
        
        # Verify logging is configured
        import logging
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
    
    @pytest.mark.unit
    def test_quiz_logger_session_tracking(self):
        """Test that QuizLogger properly tracks session state."""
        reset_logging()
        
        logger = QuizLogger("test123")
        
        # Initial state
        assert logger.session.questions_answered == 0
        assert logger.session.score is None
        
        # Log some questions
        logger.log_question_answered(1, 2.5, 2.5, True)
        logger.log_question_answered(2, 3.0, 2.5, False)
        
        assert logger.session.questions_answered == 2
        
        # Complete quiz
        logger.log_quiz_completed(0.5, "Test feedback", 2, 1)
        
        assert logger.session.score == 0.5
        assert logger.session.total_questions == 2
        assert logger.session.duration_seconds is not None
        assert logger.session.duration_seconds > 0
