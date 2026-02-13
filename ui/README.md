# UI Module - Streamlit Dashboard

The UI module provides a comprehensive Streamlit-based web application for the 30 Day A/Bs project. This interactive dashboard allows users to practice A/B test analysis through a guided interview-style experience with realistic scenarios, data analysis, and automated scoring.

## Overview

The Streamlit dashboard serves as the main user interface for the AB test simulator, providing:

- **Interactive Scenario Generation**: AI-powered realistic business scenarios
- **Guided Learning Experience**: Step-by-step interview-style practice
- **Data Analysis Tools**: CSV downloads and analysis templates
- **Automated Scoring**: Real-time feedback and scoring system
- **Progress Tracking**: Session state management and progress indicators

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   Core Engine   │    │   LLM Module    │
│                 │    │                 │    │                 │
│ • Session State │───▶│ • Simulation    │◀───│ • Scenario Gen  │
│ • User Interface│    │ • Analysis      │    │ • Validation    │
│ • Progress Mgmt │    │ • Scoring       │    │ • Guardrails    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Export   │    │   Validation    │    │   File System   │
│                 │    │                 │    │                 │
│ • CSV Downloads │    │ • Answer Check  │    │ • Notebooks     │
│ • Jupyter       │    │ • Feedback      │    │ • Templates     │
│ • Templates     │    │ • Scoring       │    │ • Prompts       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Application Flow

The application follows a structured, interview-style workflow:

### 1. **Scenario Generation** 🔵
- Generate realistic business scenarios using LLM
- Display scenario narrative and business context
- Show design parameters and statistical requirements
- Provide scenario quality metrics and validation

### 2. **Design Phase** 🟡
- **Question 1**: Business's targeted MDE (Minimum Detectable Effect)
- **Question 2**: Target conversion rate calculation
- **Question 3**: Relative lift calculation from MDE
- **Question 4**: Sample size calculation with statistical formulas
- **Question 5**: Experiment duration based on daily traffic
- **Question 6**: Business impact calculation (additional conversions)

### 3. **Data Download** 🟢
- Interactive experiment simulation with progress animation
- CSV data download with user-level experimental data
- Jupyter notebook template download for analysis
- Analysis framework and tools

### 4. **Analysis Phase** 🟣
- **Question 1**: Control conversion rate calculation
- **Question 2**: Treatment conversion rate calculation
- **Question 3**: Absolute lift calculation
- **Question 4**: Relative lift calculation
- **Question 5**: Statistical significance (P-value)
- **Question 6**: 95% confidence interval for difference
- **Question 7**: Rollout decision based on business targets

## Key Features

### 🎯 **Interview-Style Practice**
- Realistic business scenarios with proper statistical parameters
- Progressive question unlocking (must answer correctly to proceed)
- Immediate feedback with correct answers and explanations
- Comprehensive scoring system with detailed feedback

### 🤖 **AI-Powered Scenario Generation**
- LLM-generated realistic business contexts
- Multiple company types (E-commerce, SaaS, Media, Fintech, etc.)
- Statistical parameter validation and guardrails
- Quality scoring and automatic regeneration

### 📊 **Data Analysis Tools**
- User-level CSV data export
- Jupyter notebook templates for analysis
- Statistical analysis frameworks
- Real-time simulation results

### 🎓 **Educational Resources**
- Built-in formulas and explanations
- External calculator links (Evan Miller's Sample Size Calculator)
- Step-by-step calculation guidance
- Comprehensive feedback and learning materials

### 📈 **Progress Tracking**
- Session state management
- Progress indicators and completion tracking
- Navigation between phases
- Sidebar with scenario specifications and correct answers

## File Structure

```
ui/
├── streamlit_app.py          # Main Streamlit application
├── README.md                 # This documentation file
└── __pycache__/              # Python bytecode cache
```

## Main Application (`streamlit_app.py`)

### **Configuration and Setup**

```python
# Page configuration
st.set_page_config(
    page_title="30 Day A/Bs",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### **Session State Management**

The application uses Streamlit's session state to maintain user progress:

```python
def initialize_session_state():
    """Initialize session state variables."""
    if 'scenario_data' not in st.session_state:
        st.session_state.scenario_data = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "scenario"
    # ... additional state variables
```

**Key State Variables:**
- `scenario_data`: Generated LLM scenario
- `simulation_results`: Experimental data results
- `analysis_results`: Statistical analysis results
- `design_answers`: User's design phase answers
- `analysis_answers`: User's analysis phase answers
- `current_step`: Current workflow phase
- `completed_questions`: Set of completed questions

### **Core Functions**

#### **Scenario Generation**
```python
def generate_scenario():
    """Generate a new A/B test scenario."""
    # Creates LLM client with OpenAI or mock provider
    # Generates scenario using LLM
    # Validates with guardrails
    # Returns validated scenario DTO
```

#### **Simulation Engine**
```python
def run_simulation(scenario_dto):
    """Run simulation based on scenario."""
    # Converts DTOs to core domain types
    # Calculates sample size
    # Runs data simulation
    # Performs statistical analysis
    # Returns simulation and analysis results
```

#### **Question System**
```python
def ask_single_design_question(question_num):
    """Ask a single design question based on question number."""
    # Progressive question unlocking
    # Real-time validation and feedback
    # Answer storage in session state
```

#### **Scoring System**
```python
def score_design_answers(user_answers, scenario_data, sample_size_result):
    """Score the design questions against correct values."""
    # Uses core validation engine
    # Calculates percentage scores
    # Provides detailed feedback
```

## User Interface Components

### **Header and Navigation**
- Main application title with custom styling
- Sidebar with progress tracking
- Navigation buttons between phases
- Scenario specifications display

### **Scenario Display**
- Business narrative and context
- Company type and user segment information
- Design parameters and statistical requirements
- LLM expectations and business interpretation

### **Question Interface**
- Progressive question unlocking system
- Real-time validation and feedback
- Input validation with helpful hints
- Correct answer explanations

### **Data Export Tools**
- CSV download with user-level data
- Jupyter notebook template downloads
- Analysis framework templates
- Experiment simulation animation

### **Scoring and Feedback**
- Real-time scoring system
- Detailed feedback for each question
- Overall performance metrics
- Grade calculation (A, B, C, D, F)

## Styling and Customization

### **Custom CSS**
```css
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: left;
    margin-bottom: 2rem;
}

.scenario-box {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    margin: 1rem 0;
}

.question-box {
    background-color: #fff3cd;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ffc107;
    margin: 1rem 0;
}
```

### **Color Coding System**
- 🔵 **Scenario Phase**: Blue theme
- 🟡 **Design Phase**: Yellow theme
- 🟢 **Data Download**: Green theme
- 🟣 **Analysis Phase**: Purple theme

## Integration Points

### **LLM Module Integration**
- Uses `llm.client.create_llm_client()` for scenario generation
- Integrates with `llm.parser.LLMOutputParser` for JSON parsing
- Utilizes `llm.guardrails.LLMGuardrails` for validation

### **Core Engine Integration**
- Uses `core.simulate.simulate_trial()` for data generation
- Integrates with `core.analyze.analyze_results()` for statistical analysis
- Utilizes `core.design.compute_sample_size()` for sample size calculations

### **Validation Integration**
- Uses `core.validation.validate_design_answer()` for design question validation
- Integrates with `core.validation.validate_analysis_answer()` for analysis validation
- Utilizes `core.validation.score_design_answers()` for comprehensive scoring

## Configuration

### **Environment Variables**
```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo

# Application Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### **Dependencies**
- `streamlit`: Web application framework
- `pandas`: Data manipulation and CSV handling
- `asyncio`: Async support for LLM calls
- `python-dotenv`: Environment variable management

## Usage

### **Starting the Application**
```bash
# From the project root
streamlit run ui/streamlit_app.py

# Or with custom configuration
streamlit run ui/streamlit_app.py --server.port 8501
```

### **Accessing the Application**
- Open browser to `http://localhost:8501`
- Use sidebar to generate new scenarios
- Follow the guided workflow through all phases
- Download data and analysis templates as needed

## Educational Features

### **Learning Resources**
- **Sample Size Calculator**: Links to Evan Miller's calculator
- **Statistical Formulas**: Built-in formula explanations
- **Business Context**: Realistic scenarios with proper context
- **Step-by-Step Guidance**: Progressive question unlocking

### **Assessment System**
- **Real-time Validation**: Immediate feedback on answers
- **Comprehensive Scoring**: Detailed scoring with explanations
- **Progress Tracking**: Visual progress indicators
- **Performance Metrics**: Grade calculation and statistics

## Error Handling

### **LLM Integration Errors**
- Graceful fallback to mock scenarios
- Error logging and user notification
- Retry logic with exponential backoff
- Validation error handling

### **User Input Validation**
- Input range validation
- Format validation for numerical inputs
- Real-time feedback on incorrect answers
- Helpful hints and guidance

### **Session State Management**
- Automatic state initialization
- State persistence across page reloads
- Error recovery and state reset
- Progress tracking and restoration

## Performance Considerations

### **Optimization Features**
- Async LLM calls for non-blocking operations
- Efficient session state management
- Lazy loading of heavy computations
- Progress bars for long-running operations

### **Scalability**
- Stateless design where possible
- Efficient data structures for session state
- Minimal external dependencies
- Optimized rendering and updates

## Future Enhancements

### **Planned Features**
- **User Authentication**: User accounts and progress saving
- **Advanced Analytics**: More sophisticated analysis questions
- **Custom Scenarios**: User-defined scenario parameters
- **Collaboration**: Multi-user sessions and sharing
- **Mobile Support**: Responsive design improvements

### **Technical Improvements**
- **Caching**: Response caching for LLM calls
- **Database Integration**: Persistent user data storage
- **API Endpoints**: REST API for external integrations
- **Real-time Updates**: WebSocket support for live updates

## Troubleshooting

### **Common Issues**

1. **LLM API Errors**
   - Check API key configuration
   - Verify network connectivity
   - Check API quota and rate limits

2. **Session State Issues**
   - Clear browser cache and cookies
   - Restart the Streamlit application
   - Check for conflicting session variables

3. **Import Errors**
   - Verify all dependencies are installed
   - Check Python path configuration
   - Ensure all modules are properly imported

### **Debug Mode**
Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Development Mode**
Run with auto-reload for development:

```bash
streamlit run ui/streamlit_app.py --server.runOnSave true
```

## Contributing

When contributing to the UI module:

1. **Follow Streamlit Best Practices**: Use proper session state management
2. **Maintain User Experience**: Ensure smooth navigation and feedback
3. **Test Thoroughly**: Test all user flows and edge cases
4. **Document Changes**: Update this README for significant changes
5. **Performance**: Optimize for responsiveness and user experience

## License

This module is part of the 30 Day A/Bs project and follows the same MIT license.
