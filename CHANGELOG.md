# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### Planned
- Additional question types and difficulty levels
- More statistical test options (chi-square, Fisher's exact)
- Export functionality for results and reports
- User progress tracking and analytics
- Custom scenario creation tools
- Advanced power analysis features

