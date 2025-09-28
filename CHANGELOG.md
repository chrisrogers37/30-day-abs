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

## [Unreleased]

### Planned
- Streamlit Cloud deployment
- Additional question types and difficulty levels
- More statistical test options (chi-square, Fisher's exact)
- Export functionality for results and reports
- Custom scenario creation tools
- Advanced power analysis features

