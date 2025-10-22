"""
Tests for centralized logging configuration.

Tests cover:
- Default logging setup
- Custom log levels
- File logging with rotation
- Console logging
- Logger retrieval
- Log level changes
- Module-specific configuration
- Streamlit configuration
- Testing configuration
"""

import pytest
import logging
from pathlib import Path
import tempfile
from core.logging import (
    setup_logging,
    get_logger,
    get_log_level,
    set_log_level,
    configure_for_streamlit,
    configure_for_testing,
    disable_module_logging,
    reset_logging,
    LOGS_DIR
)


@pytest.fixture(autouse=True)
def reset_logging_state():
    """Reset logging state before each test."""
    reset_logging()
    yield
    reset_logging()


class TestLoggingSetup:
    """Test logging setup and configuration."""
    
    @pytest.mark.unit
    def test_setup_logging_default(self):
        """Test default logging setup."""
        logger = setup_logging()
        
        assert isinstance(logger, logging.Logger)
        assert get_log_level() == "INFO"
        assert len(logger.handlers) > 0
    
    @pytest.mark.unit
    def test_setup_logging_custom_level(self):
        """Test logging setup with custom level."""
        setup_logging(level="DEBUG")
        
        assert get_log_level() == "DEBUG"
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    @pytest.mark.unit
    def test_setup_logging_warning_level(self):
        """Test logging setup with WARNING level."""
        setup_logging(level="WARNING")
        
        assert get_log_level() == "WARNING"
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
    
    @pytest.mark.unit
    def test_setup_logging_console_only(self):
        """Test logging with console output only."""
        logger = setup_logging(level="INFO", console=True)
        
        # Should have console handler
        handlers = logger.handlers
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)
    
    @pytest.mark.unit
    def test_setup_logging_no_console(self):
        """Test logging without console output."""
        logger = setup_logging(level="INFO", console=False, log_file="test.log")
        
        # Should have file handler but no console
        from logging.handlers import RotatingFileHandler
        handlers = logger.handlers
        
        # Check file handler exists
        file_handlers = [h for h in handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) > 0
        
        # No console handlers
        console_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler) 
                           and not isinstance(h, RotatingFileHandler)]
        assert len(console_handlers) == 0
    
    @pytest.mark.unit
    def test_setup_logging_with_file(self, tmp_path):
        """Test logging with file output."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(level="INFO", log_file=str(log_file))
        logger.info("Test message")
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
    
    @pytest.mark.unit
    def test_setup_logging_file_in_logs_dir(self):
        """Test that relative log files go to logs/ directory."""
        setup_logging(level="INFO", log_file="app.log")
        
        expected_path = LOGS_DIR / "app.log"
        root_logger = logging.getLogger()
        
        from logging.handlers import RotatingFileHandler
        file_handlers = [h for h in root_logger.handlers 
                        if isinstance(h, RotatingFileHandler)]
        
        if file_handlers:
            handler = file_handlers[0]
            assert Path(handler.baseFilename) == expected_path.resolve()
    
    @pytest.mark.unit
    def test_setup_logging_custom_format(self):
        """Test logging with custom format."""
        custom_format = "%(levelname)s: %(message)s"
        logger = setup_logging(level="INFO", format_string=custom_format)
        
        # Check that a handler has the custom format
        for handler in logger.handlers:
            if handler.formatter:
                assert custom_format in handler.formatter._fmt


class TestGetLogger:
    """Test logger retrieval."""
    
    @pytest.mark.unit
    def test_get_logger_basic(self):
        """Test getting a basic logger."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    @pytest.mark.unit
    def test_get_logger_multiple(self):
        """Test getting multiple loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 is not logger2
    
    @pytest.mark.unit
    def test_get_logger_same_name(self):
        """Test that getting same logger returns same instance."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        
        assert logger1 is logger2
    
    @pytest.mark.unit
    def test_get_logger_auto_configures(self):
        """Test that get_logger auto-configures if not configured."""
        # Don't call setup_logging first
        logger = get_logger("test")
        
        # Should still work
        assert isinstance(logger, logging.Logger)
        assert get_log_level() == "INFO"


class TestLogLevelManagement:
    """Test log level management."""
    
    @pytest.mark.unit
    def test_get_log_level_default(self):
        """Test getting default log level."""
        setup_logging()
        assert get_log_level() == "INFO"
    
    @pytest.mark.unit
    def test_set_log_level(self):
        """Test changing log level."""
        setup_logging(level="INFO")
        
        set_log_level("DEBUG")
        assert get_log_level() == "DEBUG"
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    @pytest.mark.unit
    def test_set_log_level_updates_handlers(self):
        """Test that changing level updates all handlers."""
        setup_logging(level="INFO")
        root_logger = logging.getLogger()
        
        # Get initial handler levels
        initial_levels = [h.level for h in root_logger.handlers]
        assert all(level == logging.INFO for level in initial_levels)
        
        # Change level
        set_log_level("WARNING")
        
        # Check handlers updated
        new_levels = [h.level for h in root_logger.handlers]
        assert all(level == logging.WARNING for level in new_levels)
    
    @pytest.mark.unit
    def test_log_level_case_insensitive(self):
        """Test that log level is case insensitive."""
        setup_logging(level="info")
        assert get_log_level() == "INFO"
        
        set_log_level("debug")
        assert get_log_level() == "DEBUG"


class TestModuleLogging:
    """Test module-specific logging control."""
    
    @pytest.mark.unit
    def test_disable_module_logging(self):
        """Test disabling logging for specific module."""
        setup_logging(level="DEBUG")
        
        # Create logger for test module
        logger = get_logger("noisy_module")
        
        # Disable it
        disable_module_logging("noisy_module")
        
        # Check it's disabled
        assert logger.level > logging.CRITICAL


class TestStreamlitConfiguration:
    """Test Streamlit-specific configuration."""
    
    @pytest.mark.unit
    def test_configure_for_streamlit_default(self):
        """Test default Streamlit configuration."""
        configure_for_streamlit(debug=False)
        
        assert get_log_level() == "INFO"
        
        # Check log file is configured
        root_logger = logging.getLogger()
        from logging.handlers import RotatingFileHandler
        file_handlers = [h for h in root_logger.handlers 
                        if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) > 0
    
    @pytest.mark.unit
    def test_configure_for_streamlit_debug(self):
        """Test Streamlit configuration in debug mode."""
        configure_for_streamlit(debug=True)
        
        assert get_log_level() == "DEBUG"
    
    @pytest.mark.unit
    def test_configure_for_streamlit_silences_libraries(self):
        """Test that Streamlit config silences noisy libraries."""
        configure_for_streamlit(debug=False)
        
        # Check that noisy loggers are silenced
        httpx_logger = logging.getLogger("httpx")
        urllib_logger = logging.getLogger("urllib3")
        
        assert httpx_logger.level > logging.CRITICAL
        assert urllib_logger.level > logging.CRITICAL


class TestTestingConfiguration:
    """Test testing-specific configuration."""
    
    @pytest.mark.unit
    def test_configure_for_testing(self):
        """Test testing configuration."""
        configure_for_testing()
        
        assert get_log_level() == "WARNING"
        
        # Check no console output
        root_logger = logging.getLogger()
        from logging.handlers import RotatingFileHandler
        console_handlers = [h for h in root_logger.handlers 
                           if isinstance(h, logging.StreamHandler)
                           and not isinstance(h, RotatingFileHandler)]
        assert len(console_handlers) == 0


class TestLogOutput:
    """Test actual log output."""
    
    @pytest.mark.unit
    def test_log_messages_appear(self, tmp_path):
        """Test that log messages actually appear in file."""
        log_file = tmp_path / "test_messages.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        logger = get_logger("test")
        
        logger.info("Test info message")
        logger.warning("Test warning message")
        
        # Verify messages appear in file
        content = log_file.read_text()
        assert "Test info message" in content
        assert "Test warning message" in content
    
    @pytest.mark.unit
    def test_debug_messages_filtered(self, tmp_path):
        """Test that debug messages are filtered at INFO level."""
        log_file = tmp_path / "test_filter.log"
        reset_logging()
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        logger = get_logger("test")
        
        logger.debug("Debug message")
        logger.info("Info message")
        
        # Info should appear, debug should not
        content = log_file.read_text()
        assert "Info message" in content
        assert "Debug message" not in content
    
    @pytest.mark.unit
    def test_log_file_content(self, tmp_path):
        """Test that log file contains expected content."""
        log_file = tmp_path / "test.log"
        
        setup_logging(level="INFO", log_file=str(log_file), console=False)
        logger = get_logger("test")
        
        logger.info("First message")
        logger.warning("Second message")
        logger.error("Third message")
        
        content = log_file.read_text()
        assert "First message" in content
        assert "Second message" in content
        assert "Third message" in content
        assert "INFO" in content
        assert "WARNING" in content
        assert "ERROR" in content


class TestLogRotation:
    """Test log file rotation."""
    
    @pytest.mark.unit
    def test_log_rotation_configuration(self, tmp_path):
        """Test that log rotation is properly configured."""
        log_file = tmp_path / "rotating.log"
        
        setup_logging(
            level="INFO",
            log_file=str(log_file),
            max_bytes=1024,  # Small size for testing
            backup_count=3
        )
        
        root_logger = logging.getLogger()
        from logging.handlers import RotatingFileHandler
        
        file_handlers = [h for h in root_logger.handlers 
                        if isinstance(h, RotatingFileHandler)]
        
        assert len(file_handlers) > 0
        
        handler = file_handlers[0]
        assert handler.maxBytes == 1024
        assert handler.backupCount == 3


class TestResetLogging:
    """Test logging reset functionality."""
    
    @pytest.mark.unit
    def test_reset_logging(self):
        """Test that reset clears configuration."""
        setup_logging(level="DEBUG", log_file="test.log")
        
        assert get_log_level() == "DEBUG"
        
        reset_logging()
        
        # After reset, should go back to default
        get_logger("test")  # This will auto-configure
        assert get_log_level() == "INFO"
    
    @pytest.mark.unit
    def test_reset_clears_handlers(self):
        """Test that reset clears all handlers."""
        setup_logging(level="INFO", log_file="test.log")
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
        
        reset_logging()
        
        assert len(root_logger.handlers) == 0

