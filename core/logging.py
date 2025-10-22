"""
Centralized logging configuration for 30 Day A/Bs.

This module provides consistent logging across all application modules
with proper configuration, formatting, and log level management.

Features:
- Single source of truth for logging configuration
- Console and file logging support
- Environment-aware log levels
- Structured log format
- Log rotation support
- Per-module logger creation
- Testing-friendly configuration

Usage:
    Basic usage in any module:
        from core.logging import get_logger
        
        logger = get_logger(__name__)
        logger.info("This is a log message")
    
    Configure at application startup:
        from core.logging import setup_logging
        
        setup_logging(level="DEBUG", log_file="app.log")
    
    Streamlit-specific configuration:
        from core.logging import configure_for_streamlit
        
        configure_for_streamlit(debug=False)

Environment Variables:
    LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FILE: Log file path (relative to logs/ or absolute)
    LOG_CONSOLE: Enable console logging (true/false)
"""

import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Default log formats
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEBUG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

# Global state
_logging_configured = False
_log_level = "INFO"


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
    format_string: Optional[str] = None,
    max_bytes: int = 10_485_760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure centralized logging for the application.
    
    This should be called once at application startup. Subsequent calls
    will update the configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path (relative to logs/ or absolute)
        console: Whether to log to console (default: True)
        format_string: Custom format string (default: based on level)
        max_bytes: Maximum log file size before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)
    
    Returns:
        Configured root logger
    
    Examples:
        Basic setup (console only):
            setup_logging(level="INFO")
        
        With file logging:
            setup_logging(level="DEBUG", log_file="app.log")
        
        Production setup:
            setup_logging(
                level="WARNING",
                log_file="production.log",
                console=False
            )
    """
    global _logging_configured, _log_level
    
    _log_level = level.upper()
    log_level = getattr(logging, _log_level)
    
    # Use DEBUG format if debug level
    if format_string is None:
        format_string = DEBUG_FORMAT if _log_level == "DEBUG" else DEFAULT_FORMAT
    
    # Get root logger and clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Make path relative to logs/ unless absolute
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = LOGS_DIR / log_file
        
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    _logging_configured = True
    
    # Log the configuration
    root_logger.info(f"Logging configured: level={_log_level}, file={log_file}, console={console}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    This is the preferred way to get a logger in any module.
    If logging hasn't been configured yet, it will use default configuration.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance for the module
    
    Examples:
        In any module:
            from core.logging import get_logger
            
            logger = get_logger(__name__)
            logger.info("This is a log message")
            logger.debug("Debug information")
            logger.warning("Warning message")
            logger.error("Error message")
    """
    global _logging_configured
    
    # Ensure logging is configured
    if not _logging_configured:
        setup_logging()
    
    return logging.getLogger(name)


def get_log_level() -> str:
    """
    Get the current log level.
    
    Returns:
        Current log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    return _log_level


def set_log_level(level: str):
    """
    Change the log level for all loggers.
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Examples:
        Enable debug logging:
            set_log_level("DEBUG")
        
        Reduce noise in production:
            set_log_level("WARNING")
    """
    global _log_level
    _log_level = level.upper()
    log_level = getattr(logging, _log_level)
    
    # Update root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Update all handlers
    for handler in root_logger.handlers:
        handler.setLevel(log_level)
    
    root_logger.info(f"Log level changed to {_log_level}")


def disable_module_logging(module_name: str):
    """
    Disable logging for a specific module.
    
    Useful for silencing noisy third-party libraries.
    
    Args:
        module_name: Name of the module to silence
    
    Examples:
        Silence httpx logs:
            disable_module_logging("httpx")
        
        Silence urllib3 warnings:
            disable_module_logging("urllib3")
    """
    logging.getLogger(module_name).setLevel(logging.CRITICAL + 1)


def configure_for_streamlit(debug: bool = False):
    """
    Configure logging optimized for Streamlit application.
    
    Sets up console and file logging with appropriate levels and
    silences noisy third-party libraries.
    
    Args:
        debug: Whether to enable debug logging (default: False)
    
    Examples:
        In streamlit_app.py:
            from core.logging import configure_for_streamlit
            
            # Production mode
            configure_for_streamlit(debug=False)
            
            # Debug mode
            configure_for_streamlit(debug=True)
    """
    level = "DEBUG" if debug else "INFO"
    
    setup_logging(
        level=level,
        log_file="streamlit.log",
        console=True
    )
    
    # Silence noisy libraries
    disable_module_logging("httpx")
    disable_module_logging("urllib3")
    disable_module_logging("openai._base_client")


def configure_for_testing():
    """
    Configure logging optimized for testing.
    
    Reduces noise during test runs by setting WARNING level
    and disabling console output.
    
    Examples:
        In conftest.py:
            from core.logging import configure_for_testing
            
            @pytest.fixture(scope="session", autouse=True)
            def setup_test_logging():
                configure_for_testing()
    """
    setup_logging(
        level="WARNING",
        console=False  # Don't clutter test output
    )


def reset_logging():
    """
    Reset logging configuration to default state.
    
    Useful for testing to ensure clean state between tests.
    """
    global _logging_configured, _log_level
    
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    _logging_configured = False
    _log_level = "INFO"


# Quiz Session Logging
@dataclass
class QuizSession:
    """Represents a complete quiz session."""
    session_id: str
    start_time: datetime
    user_id: Optional[str] = None
    scenario_title: Optional[str] = None
    total_questions: int = 0
    questions_answered: int = 0
    score: Optional[float] = None
    duration_seconds: Optional[float] = None


class QuizLogger:
    """
    Specialized logger for quiz sessions with clean, structured output.
    
    Provides methods for logging each step of the quiz process in a
    consistent, readable format perfect for reviewing user sessions.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_logger(f"quiz.session.{session_id}")
        self.start_time = time.time()
        self.session = QuizSession(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        # Log session start
        self._log_separator("QUIZ SESSION STARTED")
        self.logger.info(f"Session ID: {session_id}")
        self.logger.info(f"Started at: {self.session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self._log_separator()
    
    def _log_separator(self, title: str = ""):
        """Log a visual separator for better readability."""
        if title:
            self.logger.info("=" * 60)
            self.logger.info(f" {title}")
            self.logger.info("=" * 60)
        else:
            self.logger.info("-" * 60)
    
    def log_user_action(self, action: str, details: str = ""):
        """Log a user action with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if details:
            self.logger.info(f"[{timestamp}] USER ACTION: {action} | {details}")
        else:
            self.logger.info(f"[{timestamp}] USER ACTION: {action}")
    
    def log_scenario_generated(self, scenario_data: Dict[str, Any]):
        """Log when a scenario is generated."""
        self._log_separator("SCENARIO GENERATED")
        
        scenario = scenario_data.get('scenario', {})
        self.session.scenario_title = scenario.get('title', 'Unknown')
        
        self.logger.info(f"Title: {self.session.scenario_title}")
        self.logger.info(f"Company: {scenario.get('company', 'Unknown')}")
        self.logger.info(f"Industry: {scenario.get('industry', 'Unknown')}")
        self.logger.info(f"Baseline Conversion: {scenario.get('baseline_conversion_rate', 0):.1%}")
        self.logger.info(f"Target Lift: {scenario.get('target_lift_pct', 0):.1%}")
        self.logger.info(f"Daily Traffic: {scenario.get('expected_daily_traffic', 0):,}")
        
        # Log business context
        context = scenario.get('business_context', '')
        if context:
            self.logger.info(f"Business Context: {context}")
        
        self._log_separator()
    
    def log_question_answered(self, question_num: int, user_answer: Any, 
                            correct_answer: Any, is_correct: bool, 
                            tolerance: Optional[float] = None):
        """Log when a user answers a question."""
        self.session.questions_answered += 1
        
        self.logger.info(f"ANSWER RECEIVED for Question {question_num}:")
        self.logger.info(f"  User Answer: {user_answer}")
        self.logger.info(f"  Correct Answer: {correct_answer}")
        self.logger.info(f"  Result: {'✅ CORRECT' if is_correct else '❌ INCORRECT'}")
        
        if tolerance is not None:
            self.logger.info(f"  Tolerance: ±{tolerance:.1%}")
        
        self.logger.info("")
    
    def log_sample_size_calculation(self, design_params: Dict[str, Any], 
                                  sample_size_result: Dict[str, Any]):
        """Log sample size calculation details."""
        self._log_separator("SAMPLE SIZE CALCULATION")
        
        self.logger.info("Design Parameters:")
        self.logger.info(f"  Alpha: {design_params.get('alpha', 0):.3f}")
        self.logger.info(f"  Power: {design_params.get('power', 0):.1%}")
        self.logger.info(f"  Baseline Rate: {design_params.get('baseline_conversion_rate', 0):.1%}")
        self.logger.info(f"  Target Lift: {design_params.get('target_lift_pct', 0):.1%}")
        
        self.logger.info("")
        self.logger.info("Sample Size Results:")
        self.logger.info(f"  Per Arm: {sample_size_result.get('per_arm', 0):,}")
        self.logger.info(f"  Total: {sample_size_result.get('total', 0):,}")
        self.logger.info(f"  Days Required: {sample_size_result.get('days_required', 0):.1f}")
        self.logger.info(f"  Power Achieved: {sample_size_result.get('power_achieved', 0):.1%}")
        
        self._log_separator()
    
    def log_simulation_results(self, sim_result: Dict[str, Any]):
        """Log simulation results."""
        self._log_separator("SIMULATION RESULTS")
        
        self.logger.info("Trial Data:")
        self.logger.info(f"  Control Group: {sim_result.get('control_n', 0):,} users, "
                        f"{sim_result.get('control_conversions', 0):,} conversions "
                        f"({sim_result.get('control_rate', 0):.1%})")
        self.logger.info(f"  Treatment Group: {sim_result.get('treatment_n', 0):,} users, "
                        f"{sim_result.get('treatment_conversions', 0):,} conversions "
                        f"({sim_result.get('treatment_rate', 0):.1%})")
        
        self.logger.info("")
        self.logger.info("Performance Metrics:")
        self.logger.info(f"  Absolute Lift: {sim_result.get('absolute_lift', 0):.1%}")
        self.logger.info(f"  Relative Lift: {sim_result.get('relative_lift_pct', 0):.1%}")
        
        self._log_separator()
    
    def log_analysis_results(self, analysis_result: Dict[str, Any]):
        """Log statistical analysis results."""
        self._log_separator("STATISTICAL ANALYSIS")
        
        self.logger.info("Test Results:")
        self.logger.info(f"  P-value: {analysis_result.get('p_value', 0):.4f}")
        self.logger.info(f"  Significant: {'Yes' if analysis_result.get('significant', False) else 'No'}")
        self.logger.info(f"  Confidence Interval: {analysis_result.get('confidence_interval', 'N/A')}")
        
        recommendation = analysis_result.get('recommendation', '')
        if recommendation:
            self.logger.info(f"  Recommendation: {recommendation}")
        
        self._log_separator()
    
    def log_quiz_completed(self, score: float, feedback: str, 
                         total_questions: int, correct_answers: int):
        """Log quiz completion with final results."""
        self.session.score = score
        self.session.total_questions = total_questions
        self.session.duration_seconds = time.time() - self.start_time
        
        self._log_separator("QUIZ COMPLETED")
        
        self.logger.info("Final Results:")
        self.logger.info(f"  Score: {score:.1%} ({correct_answers}/{total_questions} correct)")
        self.logger.info(f"  Duration: {self.session.duration_seconds:.1f} seconds")
        self.logger.info(f"  Session ID: {self.session_id}")
        
        self.logger.info("")
        self.logger.info("Feedback:")
        for line in feedback.split('\n'):
            if line.strip():
                self.logger.info(f"  {line.strip()}")
        
        self._log_separator("SESSION END")
        
        # Log session summary
        self.logger.info("SESSION SUMMARY:")
        self.logger.info(f"  Scenario: {self.session.scenario_title}")
        self.logger.info(f"  Questions: {correct_answers}/{total_questions} correct")
        self.logger.info(f"  Score: {score:.1%}")
        self.logger.info(f"  Duration: {self.session.duration_seconds:.1f}s")
        self.logger.info(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def start_quiz_session(user_id: Optional[str] = None) -> QuizLogger:
    """
    Start a new quiz session with structured logging.
    
    Args:
        user_id: Optional user identifier
    
    Returns:
        QuizLogger instance for the session
    
    Example:
        session_logger = start_quiz_session(user_id="user123")
        session_logger.log_scenario_generated(scenario_data)
    """
    session_id = str(uuid.uuid4())[:8]  # Short session ID
    
    # Configure logging for quiz sessions
    setup_logging(
        level="INFO",
        log_file=f"quiz_session_{session_id}.log",
        console=True
    )
    
    logger = QuizLogger(session_id)
    if user_id:
        logger.session.user_id = user_id
        logger.logger.info(f"User ID: {user_id}")
    
    return logger


def configure_quiz_logging():
    """
    Configure logging specifically for quiz sessions.
    
    This should be called at application startup to ensure
    clean, structured logging for quiz sessions.
    """
    setup_logging(
        level="INFO",
        log_file="quiz_sessions.log",
        console=True
    )
    
    # Silence noisy libraries during quiz sessions
    disable_module_logging("httpx")
    disable_module_logging("urllib3")
    disable_module_logging("openai._base_client")


