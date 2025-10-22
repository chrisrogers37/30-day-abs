# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.1] - 2025-01-22

### Added
- **Centralized Logging System**: Unified logging configuration in `core/logging.py`
- **Quiz Session Logging**: Structured logging for complete user quiz journeys
- **Session Tracking**: Unique session IDs with detailed progress logging
- **Clean Terminal Output**: Organized, readable logs for end-to-end quiz sessions
- **Log File Management**: Automatic log rotation and organized file structure

### Enhanced
- **Streamlit Integration**: Quiz session logging integrated into UI workflow
- **Logging Tests**: 14 comprehensive tests for quiz logging functionality
- **Documentation**: Updated README with logging configuration and examples

### Technical Improvements
- **Consolidated Architecture**: Single logging module instead of duplicate systems
- **Structured Output**: Visual separators and organized log sections
- **Performance Tracking**: Session duration and timing metrics
- **Error Handling**: Graceful logging error management

## [1.5.0] - 2025-01-22

### Added
- **Comprehensive Testing Suite**: 288 tests with 89% core module coverage
- **Development Documentation**: 3,000+ lines of developer guides
- **Testing Infrastructure**: Complete pytest configuration with fixtures and helpers
- **Test Coverage**: 283 passing tests across all modules
- **Mock Strategy**: Mock LLM clients and deterministic RNG for reproducible testing
- **Custom Test Utilities**: 15 custom assertions, object factories, and mock helpers
- **Development Dependencies**: requirements-dev.txt with pytest, coverage, linting tools

### Testing Coverage Achievements
- **core/simulate.py**: 97% coverage (+36%) - CSV export, data generation, validation
- **core/validation.py**: 95% coverage (+63%) - All 13 quiz question validations
- **core/analyze.py**: 93% coverage (+50%) - Statistical tests, business impact, quality assessment
- **core/rng.py**: 93% coverage (+45%) - All probability distributions, determinism
- **core/utils.py**: 91% coverage (+63%) - All utility functions, formatters, validators
- **core/scoring.py**: 90% coverage (+57%) - Answer keys, quiz feedback, grading
- **core/types.py**: 81% coverage - Type validation and properties
- **core/design.py**: 63% coverage - Sample size calculations
- **schemas/***: 86-93% coverage - Pydantic validation

### Test Organization
- **Core Module Tests**: 18 test files with 249 tests
- **LLM Module Tests**: 5 test files with 10 tests (mock-based)
- **Schema Tests**: 6 test files with 11 tests
- **Integration Tests**: 4 E2E test files with 5 tests
- **Test Fixtures**: Mock responses, expected results, sample scenarios
- **Test Helpers**: Custom assertions, object factories, mock objects

### Documentation
- **Development Guide**: Complete setup, workflow, code standards (719 lines)
- **Testing Guide**: Comprehensive testing documentation (889 lines)
- **Testing Summary**: Achievement metrics and test structure (259 lines)
- **Development Docs README**: Navigation guide for all documentation (292 lines)
- **Tests README**: Testing suite documentation and usage

### Test Infrastructure
- **pytest.ini**: Complete configuration with markers (unit, integration, e2e, slow, requires_api)
- **conftest.py**: 20+ shared fixtures for all test modules
- **requirements-dev.txt**: All development dependencies (pytest, coverage, black, ruff, mypy)
- **Custom Assertions**: 15 specialized assertion functions for better test clarity
- **Object Factories**: Factory functions for creating test data
- **Mock Objects**: Complete mock implementations for LLM clients

### Test Features
- **Mock-First Approach**: Zero API costs during testing
- **Deterministic Testing**: Fixed RNG seeds for reproducibility
- **Fast Feedback**: Full suite runs in ~15 minutes
- **Parametrized Tests**: 30+ tests with multiple input combinations
- **Edge Case Coverage**: Comprehensive boundary condition testing
- **CI/CD Ready**: Proper test markers for automated pipelines

### Improved
- **Code Quality**: Enterprise-grade testing enables confident refactoring
- **Developer Experience**: Clear test examples demonstrate proper usage
- **Maintainability**: Well-documented tests serve as living documentation
- **Reliability**: 89% core coverage ensures mathematical correctness

### Technical Improvements
- **Test Isolation**: All tests are independent and can run in any order
- **Coverage Reporting**: HTML, terminal, and XML coverage reports
- **Async Support**: Full support for async/await testing patterns
- **Performance**: Optimized test execution with parallel capabilities

## [1.0.0] - 2025-01-12

### Added
- Initial release of 30 Day ABs - A/B Test Interview Practice System
- LLM-powered scenario generation using OpenAI GPT-4
- Interactive Streamlit web application for A/B test practice
- Comprehensive statistical analysis and validation system
- Progressive question flow with 5 design questions
- Real-time answer validation and scoring
- CSV data download for offline analysis
- Sample size calculation with Evan Miller calculator integration
- Confidence interval calculations with proper alpha handling
- Power analysis and achieved power calculations
- Business impact assessment and recommendations

### Features
- **Scenario Generation**: AI-generated realistic A/B test scenarios with single intervention focus
- **Design Questions**: 5 progressive questions covering relative lift, sample size, duration, business impact, and power analysis
- **Statistical Engine**: Robust mathematical calculations for sample size, power, and confidence intervals
- **Data Simulation**: Synthetic user-level data generation with configurable parameters
- **Interactive UI**: Clean, intuitive Streamlit interface with navigation and progress tracking
- **Answer Validation**: Real-time feedback with tolerance-based scoring
- **Educational Resources**: Links to Evan Miller's calculator and formula explanations

### Technical Implementation
- **Core Engine**: Mathematical functions for sample size calculation, power analysis, and statistical testing
- **LLM Integration**: OpenAI API integration with retry logic and validation
- **Data Validation**: Pydantic schemas for type safety and data validation
- **Session Management**: Streamlit session state for user progress tracking
- **Logging**: Comprehensive logging for debugging and monitoring
- **Error Handling**: Robust error handling and fallback mechanisms

### Statistical Accuracy
- Standard two-proportion z-test sample size formula implementation
- Proper z-score calculations for alpha (two-tailed) and beta (one-tailed)
- Dynamic confidence interval calculations based on specified alpha levels
- Consistent statistical methodology matching academic sources and ChatGPT calculations
- Tolerance-based validation accounting for calculator differences

### Documentation
- Comprehensive README with setup and usage instructions
- Inline code documentation and type hints
- Educational formula explanations in the UI
- Clear error messages and user guidance

## [1.1.0] - 2025-01-14

### Added
- **Jupyter Notebook Framework**: Downloadable template notebook for offline calculation work
- **Enhanced Question Flow**: Streamlined from 7 to 6 questions focusing on practical calculations
- **Business Impact Focus**: New Question 6 for calculating additional conversions per day
- **Improved Navigation**: Fixed question numbering inconsistencies and navigation logic
- **Offline Learning**: Complete framework for working through design questions outside the web app

### Changed
- **Question Flow Optimization**: Removed theoretical power analysis question (Question 7) for more practical focus
- **Enhanced UI**: Added notebook download section in design step with clear instructions
- **Question Numbering**: Fixed inconsistencies between navigation (5 vs 7 questions) to consistent 6 questions
- **Scoring Logic**: Updated to handle 6 questions instead of 7 with proper validation

### Improved
- **User Experience**: More focused learning path from statistical design to business impact
- **Educational Value**: Framework notebook provides structured approach to calculations
- **Interview Preparation**: Emphasizes most valuable skills for A/B testing interviews
- **Time Efficiency**: Streamlined flow gets users to data analysis faster

### Technical Improvements
- **Template System**: Created reusable Jupyter notebook template with placeholders
- **Download Integration**: Seamless notebook download with timestamped filenames
- **Error Handling**: Robust file handling for notebook template delivery
- **Code Organization**: Clean separation of concerns between web app and offline framework

## [1.2.0] - 2025-01-15

### Added
- **Question 7 - Rollout Decision**: New analysis question for interpreting confidence intervals vs business targets
- **`make_rollout_decision()` Function**: CI-based go/no-go decision logic with three outcomes
- **Enhanced Analysis Section**: Complete rebuild with 7 progressive questions
- **Core Validation Module**: Centralized answer validation and scoring system
- **Core Scoring Module**: Answer key generation and comprehensive quiz result management
- **Analysis Notebook Template**: Downloadable Jupyter notebook with all 7 analysis questions
- **Business Target Integration**: LLM scenario business targets used for rollout decisions
- **Progressive Question Display**: Analysis questions appear one by one like design section

### Changed
- **Architecture Refactoring**: Moved statistical calculations, validation, and scoring from UI to core modules
- **Analysis Question Flow**: Rebuilt from scratch with proper progressive display
- **Question Count**: Analysis section expanded from 6 to 7 questions
- **Validation System**: Centralized validation logic in `core/validation.py`
- **Scoring System**: Centralized scoring logic in `core/scoring.py`
- **UI Simplification**: UI layer now focuses on question flow and user interaction
- **Data Download Page**: Renovated with loading animation and improved messaging

### Improved
- **Separation of Concerns**: Clear `llm -> core -> ui` architecture
- **Code Maintainability**: Eliminated duplicated statistical calculations
- **Educational Value**: Complete analysis workflow from data to business decision
- **User Experience**: Consistent question flow between design and analysis sections
- **Statistical Accuracy**: Fixed p-value validation bug with duplicate dictionary keys
- **Business Decision Making**: Realistic rollout recommendations based on CI vs targets

### Technical Improvements
- **Core Module Enhancement**: Added `make_rollout_decision()` to `core/analyze.py`
- **Validation Updates**: Support for 7 analysis questions with business target integration
- **Scoring Updates**: Proper handling of rollout decision validation with exact match
- **Notebook Templates**: Updated analysis notebook with Question 7 decision logic
- **Error Handling**: Fixed validation issues and improved error messages
- **Type Safety**: Enhanced type hints and validation throughout core modules

### Fixed
- **P-value Validation Bug**: Fixed duplicate dictionary key issue in scoring
- **Question Numbering**: Consistent numbering across all sections
- **Navigation Logic**: Proper bounds checking for question navigation
- **Validation Tolerances**: Appropriate tolerances for different question types
- **Business Target Integration**: Proper use of LLM scenario business targets

### Documentation
- **Core README**: Comprehensive update documenting all new modules and functions
- **Function Status**: Clear documentation of which functions are used vs available
- **Usage Examples**: Updated examples showing new validation and scoring workflows
- **Architecture Documentation**: Clear explanation of separation of concerns

## [1.3.0] - 2025-01-16

### Added
- **MIT License**: Added proper MIT license file for open source distribution
- **Streamlit Cloud Focus**: Updated README to prioritize Streamlit Cloud deployment
- **Professional Contact Section**: Added clean contact information with clickable links
- **Origin Story**: Added engaging project story explaining the "30 Day A/Bs" name and purpose

### Changed
- **README Streamlined**: Reduced from 365 lines to 96 lines by removing duplicate content
- **Installation Focus**: Shifted from local installation to Streamlit Cloud deployment
- **Contact Information**: Professional formatting with LinkedIn, website, and email links
- **Project Description**: Updated to emphasize experimental design and statistics education

### Improved
- **User Experience**: Faster path to trying the application via Streamlit Cloud
- **Documentation Quality**: Removed redundant sections and improved clarity
- **Professional Presentation**: Better formatting and organization throughout README
- **Accessibility**: Streamlit Cloud deployment eliminates installation barriers

### Technical Improvements
- **Repository Structure**: Added proper LICENSE file for open source compliance
- **Documentation Maintenance**: Cleaned up outdated references and duplicate content
- **Deployment Ready**: Optimized for Streamlit Cloud deployment workflow

### Removed
- **Duplicate Content**: Eliminated redundant project structure sections
- **Complex Installation**: Simplified setup instructions for contributors only
- **Outdated References**: Removed references to non-existent files and directories

## [1.4.0] - 2025-01-16

### Fixed
- **Question 7 AttributeError**: Fixed data structure access for `target_lift_pct` and `mde_absolute` in rollout decision validation
- **Indentation Errors**: Resolved multiple Python indentation errors in streamlit_app.py
- **UnboundLocalError**: Fixed variable scope issues by moving design parameter definitions outside conditional blocks
- **Default Selection Issue**: Removed default selection from Question 7 dropdown to prevent immediate incorrect feedback
- **Validation Sync Issue**: Fixed discrepancy between inline validation and final scoring for Question 6 confidence interval
- **Error Message Improvements**: Enhanced error messages to be more encouraging without revealing correct answers
- **Redundant Answer Display**: Removed redundant answer display from correct responses

### Improved
- **User Experience**: Question 7 now requires active selection before validation, preventing immediate incorrect feedback
- **Error Handling**: More encouraging error messages that don't spoil the learning experience
- **Validation Consistency**: Inline validation and final scoring now produce consistent results
- **Code Quality**: Fixed multiple syntax and indentation issues for better maintainability

### Technical Improvements
- **Data Structure Access**: Corrected attribute access from `llm_expected` to `design_params` for business targets
- **Answer Transformation**: Added logic to convert separate confidence interval values to tuple format for scoring
- **Variable Scoping**: Proper variable definitions to prevent scope-related errors
- **Code Organization**: Improved code structure and error handling throughout the application

## [Unreleased]

### Planned
- Streamlit Cloud deployment
- Additional question types and difficulty levels
- More statistical test options (chi-square, Fisher's exact)
- Export functionality for results and reports
- Custom scenario creation tools
- Advanced power analysis features

