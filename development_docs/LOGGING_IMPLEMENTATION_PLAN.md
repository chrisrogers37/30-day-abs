# Centralized Logging Implementation Plan

## Overview

This document outlines the detailed implementation plan for adding a centralized logging system to the 30 Day A/Bs project. This enhancement addresses critical technical debt and establishes foundation for production monitoring.

**Version**: 1.5.1  
**Branch**: `feature/centralized-logging`  
**Estimated Effort**: 6-8 hours  
**Priority**: 🔴 Critical

---

## Current State Analysis

### Problems Identified

1. **Multiple `basicConfig()` Calls**: 8 modules independently configure logging
   - `llm/client.py:79`
   - `llm/generator.py:88`
   - `llm/parser.py:89`
   - `llm/integration.py:88`
   - `llm/guardrails.py` (line ~79)
   - `ui/streamlit_app.py:29`
   - Plus ad-hoc imports in `core/design.py:111`

2. **Configuration Conflicts**: Only the first `basicConfig()` takes effect

3. **Inconsistent Logging**: Different formats and levels across modules

4. **Root Directory Clutter**: `streamlit.log` file in project root

5. **No Central Control**: Can't globally change log levels or formats

6. **110+ Logger Calls**: Uncoordinated across 7 files

### Impact on Project

- ❌ Difficult debugging in production
- ❌ Can't enable DEBUG mode easily
- ❌ No log aggregation capability
- ❌ Technical debt accumulation
- ❌ Inconsistent developer experience

---

## Implementation Plan

### Phase 1: Foundation (Steps 1-3)

#### Step 1: Create Core Logging Module
**File**: `core/logging.py`  
**Estimated Time**: 2 hours

**Implementation**:

```python
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
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Default log format
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
    """
    global _logging_configured
    
    # Ensure logging is configured
    if not _logging_configured:
        setup_logging()
    
    return logging.getLogger(name)


def get_log_level() -> str:
    """Get the current log level."""
    return _log_level


def set_log_level(level: str):
    """
    Change the log level for all loggers.
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Examples:
        Enable debug logging:
            set_log_level("DEBUG")
        
        Reduce noise:
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
    """
    logging.getLogger(module_name).setLevel(logging.CRITICAL + 1)


# Convenience function for common use case
def configure_for_streamlit(debug: bool = False):
    """
    Configure logging optimized for Streamlit application.
    
    Args:
        debug: Whether to enable debug logging
    
    Examples:
        In streamlit_app.py:
            from core.logging import configure_for_streamlit
            configure_for_streamlit(debug=False)
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


def configure_for_testing():
    """
    Configure logging optimized for testing.
    
    Reduces noise during test runs.
    
    Examples:
        In conftest.py:
            from core.logging import configure_for_testing
            configure_for_testing()
    """
    setup_logging(
        level="WARNING",
        console=False  # Don't clutter test output
    )
```

**Tests to Add**:
```python
# tests/core/test_logging.py
"""Tests for centralized logging configuration."""

import pytest
import logging
from pathlib import Path
from core.logging import (
    setup_logging,
    get_logger,
    get_log_level,
    set_log_level,
    configure_for_testing
)

class TestLoggingSetup:
    """Test logging setup and configuration."""
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert get_log_level() == "INFO"
    
    def test_get_logger(self):
        """Test getting a module logger."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_set_log_level(self):
        """Test changing log level."""
        setup_logging(level="INFO")
        set_log_level("DEBUG")
        assert get_log_level() == "DEBUG"
    
    def test_log_file_creation(self, tmp_path):
        """Test that log files are created."""
        log_file = tmp_path / "test.log"
        setup_logging(level="INFO", log_file=str(log_file))
        
        logger = get_logger("test")
        logger.info("Test message")
        
        assert log_file.exists()
```

**Deliverables**:
- ✅ `core/logging.py` with full implementation
- ✅ `tests/core/test_logging.py` with comprehensive tests
- ✅ Documentation in docstrings

---

#### Step 2: Create Logs Infrastructure
**Estimated Time**: 30 minutes

**Tasks**:

1. Create `logs/` directory:
```bash
mkdir -p logs
```

2. Create `logs/.gitignore`:
```gitignore
# Ignore all log files
*.log
*.log.*

# But keep the directory
!.gitignore
```

3. Update root `.gitignore`:
```gitignore
# Add to existing .gitignore
streamlit.log
logs/*.log
logs/*.log.*
*.log
```

4. Remove existing log file:
```bash
git rm streamlit.log  # If tracked
# or
rm streamlit.log  # If not tracked
```

**Deliverables**:
- ✅ `logs/` directory with `.gitignore`
- ✅ Updated root `.gitignore`
- ✅ Removed `streamlit.log` from root

---

#### Step 3: Add Configuration Integration
**File**: Update `core/config.py` or create if doesn't exist  
**Estimated Time**: 1 hour

**Implementation**:

If `core/config.py` doesn't exist, create it with logging config.
If it exists, add logging configuration fields.

```python
# In core/config.py (add to existing or create new)

from pydantic import BaseModel, Field
from typing import Optional

class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    console: bool = Field(default=True)
    file: Optional[str] = Field(default=None)
    format: Optional[str] = Field(default=None)

class AppConfig(BaseModel):
    """Application configuration."""
    
    # ... existing config fields ...
    
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment."""
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        logging_config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            console=os.getenv("LOG_CONSOLE", "true").lower() == "true",
            file=os.getenv("LOG_FILE"),
        )
        
        return cls(
            # ... existing config ...
            logging=logging_config
        )
```

**Deliverables**:
- ✅ Logging config in `core/config.py`
- ✅ Environment variable support
- ✅ `.env.example` updated

---

### Phase 2: Module Migration (Steps 4-6)

#### Step 4: Refactor LLM Modules
**Estimated Time**: 1.5 hours

**Files to Update**:
1. `llm/client.py`
2. `llm/generator.py`
3. `llm/parser.py`
4. `llm/integration.py`
5. `llm/guardrails.py`

**Pattern to Apply**:

**BEFORE**:
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**AFTER**:
```python
from core.logging import get_logger

logger = get_logger(__name__)
```

**Process**:
1. Remove `import logging` if only used for logger
2. Remove `logging.basicConfig()` call
3. Replace `logging.getLogger(__name__)` with `get_logger(__name__)`
4. Import from `core.logging`

**Deliverables**:
- ✅ 5 LLM modules refactored
- ✅ All basicConfig() calls removed
- ✅ Consistent logger usage

---

#### Step 5: Refactor UI Module
**Estimated Time**: 30 minutes

**File**: `ui/streamlit_app.py`

**Changes**:
```python
# BEFORE (lines 18-37)
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for Streamlit app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# AFTER
from datetime import datetime
from dotenv import load_dotenv
from core.logging import configure_for_streamlit, get_logger

# Load environment variables
load_dotenv()

# Configure logging for Streamlit
configure_for_streamlit(debug=False)

logger = get_logger(__name__)
```

**Deliverables**:
- ✅ Streamlit app uses centralized logging
- ✅ Cleaner configuration
- ✅ Easy debug mode toggle

---

#### Step 6: Refactor Core Module
**Estimated Time**: 15 minutes

**File**: `core/design.py`

**Changes**:
```python
# BEFORE (lines 110-113)
def _get_z_score(...):
    # Log z-score calculation for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Z-score calculation: ...")
    
# AFTER (at top of file)
from core.logging import get_logger

logger = get_logger(__name__)

# In function:
def _get_z_score(...):
    # Log z-score calculation for debugging
    logger.debug(f"Z-score calculation: ...")
```

**Deliverables**:
- ✅ Remove ad-hoc logging import
- ✅ Use module-level logger
- ✅ Cleaner code

---

### Phase 3: Testing & Documentation (Steps 7-9)

#### Step 7: Add Comprehensive Tests
**Estimated Time**: 1 hour

**File**: `tests/core/test_logging.py`

**Test Coverage**:
- ✅ Default configuration
- ✅ Custom log levels
- ✅ File logging with rotation
- ✅ Console logging
- ✅ Logger retrieval
- ✅ Log level changes
- ✅ Module-specific configuration
- ✅ Streamlit configuration
- ✅ Testing configuration

**Run Tests**:
```bash
pytest tests/core/test_logging.py -v
```

**Deliverables**:
- ✅ 10+ tests for logging module
- ✅ All tests passing
- ✅ 90%+ coverage on logging module

---

#### Step 8: Update Documentation
**Estimated Time**: 1 hour

**Files to Update**:

1. **Development Guide** (`development_docs/DEVELOPMENT_GUIDE.md`):
   - Add "Logging" section
   - Explain how to use logging
   - Show examples

2. **README.md**:
   - Add note about logging configuration
   - Mention environment variables

3. **Create Logging Guide** (optional):
   - Detailed logging documentation
   - Best practices
   - Troubleshooting

**Deliverables**:
- ✅ Updated development documentation
- ✅ README mentions logging
- ✅ Examples provided

---

#### Step 9: Update CHANGELOG
**Estimated Time**: 15 minutes

**File**: `CHANGELOG.md`

**Add**:
```markdown
## [1.5.1] - 2025-01-22

### Added
- **Centralized Logging System**: Complete logging infrastructure
  - `core/logging.py` with unified configuration
  - Log file rotation and management
  - Environment-aware log levels
  - Structured log formatting
  - Per-module logger creation

### Fixed
- **Logging Configuration Conflicts**: Removed multiple `basicConfig()` calls
  - Refactored 8 modules to use centralized logging
  - Consistent log format across all modules
  - Single source of truth for logging config

### Changed
- **Log File Location**: Moved from root to `logs/` directory
- **LLM Modules**: Refactored to use `core.logging`
- **UI Module**: Updated Streamlit logging configuration
- **Core Module**: Removed ad-hoc logging imports

### Improved
- **Debuggability**: Easy to enable DEBUG mode globally
- **Production Readiness**: Proper log rotation and management
- **Code Quality**: Eliminated logging technical debt
```

**Deliverables**:
- ✅ CHANGELOG updated with v1.5.1
- ✅ All changes documented

---

## Implementation Checklist

### Phase 1: Foundation ✅
- [ ] Step 1: Create `core/logging.py` with full implementation
- [ ] Step 1: Create `tests/core/test_logging.py`
- [ ] Step 2: Create `logs/` directory with `.gitignore`
- [ ] Step 2: Update root `.gitignore`
- [ ] Step 2: Remove `streamlit.log` from root
- [ ] Step 3: Add logging config to `core/config.py` (if needed)

### Phase 2: Module Migration ✅
- [ ] Step 4: Refactor `llm/client.py`
- [ ] Step 4: Refactor `llm/generator.py`
- [ ] Step 4: Refactor `llm/parser.py`
- [ ] Step 4: Refactor `llm/integration.py`
- [ ] Step 4: Refactor `llm/guardrails.py`
- [ ] Step 5: Refactor `ui/streamlit_app.py`
- [ ] Step 6: Refactor `core/design.py`

### Phase 3: Testing & Documentation ✅
- [ ] Step 7: Run all tests and verify passing
- [ ] Step 7: Check logging test coverage (90%+ target)
- [ ] Step 8: Update Development Guide
- [ ] Step 8: Update README
- [ ] Step 9: Update CHANGELOG for v1.5.1

### Final Validation ✅
- [ ] All tests passing
- [ ] No more `basicConfig()` calls in codebase
- [ ] Log files go to `logs/` directory
- [ ] Can toggle DEBUG mode via environment
- [ ] Documentation complete

---

## Testing Strategy

### Unit Tests
```bash
# Test logging module
pytest tests/core/test_logging.py -v

# Test with different log levels
LOG_LEVEL=DEBUG pytest tests/core/test_logging.py -v
```

### Integration Tests
```bash
# Test that all modules use centralized logging
pytest tests/ -v --log-cli-level=DEBUG

# Verify no logging conflicts
pytest tests/ -v 2>&1 | grep -i "logging"
```

### Manual Testing
```bash
# Test Streamlit app logging
LOG_LEVEL=DEBUG streamlit run ui/streamlit_app.py

# Check log file creation
ls -la logs/
tail -f logs/streamlit.log
```

---

## Success Criteria

### Technical
- ✅ All 8 modules using centralized logging
- ✅ Zero `basicConfig()` calls in codebase
- ✅ All tests passing (283+ tests)
- ✅ 90%+ coverage on logging module
- ✅ Log files properly managed in `logs/`

### Functional
- ✅ Can change log level globally via environment
- ✅ Logs appear in both console and file
- ✅ Log rotation works properly
- ✅ Debug mode can be enabled easily
- ✅ No logging conflicts or warnings

### Documentation
- ✅ Development guide updated
- ✅ README mentions logging
- ✅ CHANGELOG updated for v1.5.1
- ✅ All functions have docstrings

---

## Rollback Plan

If issues arise:

1. **Revert Branch**:
   ```bash
   git checkout main
   git branch -D feature/centralized-logging
   ```

2. **Partial Rollback**:
   - Keep `core/logging.py` but don't refactor modules yet
   - Test in isolation before full migration

3. **Emergency Fix**:
   - Create hotfix branch from main
   - Apply minimal fixes
   - Defer full logging to later

---

## Timeline Estimate

| Phase | Tasks | Time | Cumulative |
|-------|-------|------|------------|
| Planning | This document | 1h | 1h |
| Phase 1 | Foundation (Steps 1-3) | 3.5h | 4.5h |
| Phase 2 | Migration (Steps 4-6) | 2h | 6.5h |
| Phase 3 | Testing & Docs (Steps 7-9) | 2h | 8.5h |
| **Total** | | **8.5h** | |

**Target Completion**: Today (single session)

---

## Next Steps After Completion

After centralized logging is complete, tackle:

1. **Configuration Management** (ENHANCEMENT_RECOMMENDATIONS.md #2)
2. **Error Handling Framework** (ENHANCEMENT_RECOMMENDATIONS.md #3)
3. **Performance Monitoring** (ENHANCEMENT_RECOMMENDATIONS.md #5)

---

**Status**: Ready to Execute  
**Branch**: `feature/centralized-logging`  
**Version**: 1.5.1  
**Go/No-Go**: ✅ GO!


