# AB Test Simulator

A lean, simple AB test simulator for interview preparation that generates realistic business scenarios and provides comprehensive statistical analysis.

## Overview

This project provides a comprehensive AB testing simulator designed specifically for interview preparation. It combines LLM-generated business scenarios with deterministic statistical calculations to create realistic interview experiences.

### Key Features

- **LLM-Generated Scenarios**: Realistic business contexts with proper statistical parameters
- **Deterministic Math Engine**: All calculations are computed deterministically for consistent results
- **Comprehensive Evaluation**: Multi-criteria scoring system for user responses
- **Interview-Style Feedback**: Detailed scoring and improvement suggestions
- **Multiple Statistical Tests**: Support for z-tests, chi-square, and Fisher's exact tests
- **Business Impact Analysis**: Revenue projections and risk assessments
- **Data Export**: CSV, JSON, and other format support

## Architecture

The system follows a clean, modular architecture with strict separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Layer     │    │   Core Engine   │    │   API Layer     │
│                 │    │                 │    │                 │
│ • Scenario Gen  │───▶│ • Math Engine   │◀───│ • FastAPI       │
│ • JSON Parsing  │    │ • Simulation    │    │ • Validation    │
│ • Guardrails    │    │ • Analysis      │    │ • Error Handling│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │    │   Data Layer    │    │   Config Layer  │
│                 │    │                 │    │                 │
│ • Streamlit     │    │ • SQLite/Postgres│   │ • YAML Config   │
│ • React (opt)   │    │ • Redis Cache   │    │ • Env Variables │
│ • Data Viz      │    │ • File Storage  │    │ • Feature Flags │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Current Implementation Status

### ✅ **Phase 1: Core Foundation (Complete)**
- **Core Types**: Pure mathematical domain objects with validation
- **Sample Size Calculation**: Two-proportion z-test with duration calculation
- **Data Simulation**: Deterministic simulation with seeded RNG and user-level data
- **Statistical Analysis**: Multiple test options (z-test, chi-square, Fisher's exact)
- **Utilities**: RNG factory, conversion helpers, business impact calculations
- **Testing**: Comprehensive test suite with 100% pass rate

### ✅ **Phase 2: Data Contracts and Validation (Complete)**
- **Schema Definitions**: Complete Pydantic DTOs for all API boundaries
- **Enhanced Validation**: Comprehensive bound checking and business context validation
- **Separation of Concerns**: Clean separation between core math and API schemas
- **Type Safety**: Full type annotations and validation

### 🔄 **Next: Phase 3 - LLM Integration**
- LLM client wrapper with retry logic
- Prompt engineering for scenario generation
- JSON parsing and validation
- Enhanced scenario generation with business context

## Project Structure

```
abtest-simulator/
├── core/                    # ✅ Pure mathematical domain logic
│   ├── types.py            # Mathematical domain types (Allocation, DesignParams, etc.)
│   ├── design.py           # Sample size calculation and statistical design
│   ├── simulate.py         # Deterministic data simulation with seeded RNG
│   ├── analyze.py          # Statistical analysis (z-test, chi-square, Fisher's exact)
│   ├── rng.py              # Centralized random number generation
│   ├── utils.py            # Mathematical utility functions
│   └── README.md           # Core module documentation
├── schemas/                 # ✅ Pydantic DTOs for API boundaries
│   ├── shared.py           # Common enums and types (CompanyType, TestType, etc.)
│   ├── scenario.py         # Business scenario DTOs (ScenarioDTO, LlmExpectedDTO)
│   ├── design.py           # Design parameter DTOs (DesignParamsDTO, SampleSizeDTO)
│   ├── simulate.py         # Simulation request/response DTOs
│   ├── analyze.py          # Analysis request/response DTOs
│   └── evaluation.py       # Evaluation criteria and scoring DTOs
├── api/                     # 🔄 FastAPI REST endpoints (Phase 4)
├── llm/                     # 🔄 LLM integration (Phase 3)
├── ui/                      # 🔄 User interface (Phase 5)
├── tests/                   # ✅ Test suite
├── configs/                 # ✅ Configuration files
└── docs/                    # ✅ Documentation
```

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (or Anthropic API key)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/abtest-simulator.git
   cd abtest-simulator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Option 1: Use the installation script (recommended)
   pip install -r requirements.txt
   
   # Option 2: Manual installation
   pip install -r requirements.txt
   
   # Option 3: Minimal installation (core functionality only)
   pip install -r requirements-minimal.txt
   
   # Option 4: Development installation (with dev tools)
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the application**
   ```bash
   # Start the API server
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or start the Streamlit UI
   streamlit run ui/streamlit_app.py
   ```

### Requirements Files

The project provides different requirements files for different use cases:

- **`requirements.txt`**: Full installation with all dependencies
- **`requirements-minimal.txt`**: Core functionality only (numpy, pandas, scipy, fastapi, pydantic)
- **`requirements-dev.txt`**: Development dependencies (includes testing, linting, documentation tools)

### Configuration

The application uses a hierarchical configuration system:

1. **Default values** in environment variables and code
2. **Environment variables** (see `.env.template`)
3. **Runtime overrides**

Key configuration areas:
- **LLM Settings**: API keys, models, retry logic
- **Statistical Parameters**: Default alpha, power, confidence levels
- **Business Logic**: Conversion rate bounds, lift limits
- **Feature Flags**: Enable/disable specific features

## Usage

### Basic Workflow

1. **Generate Scenario**: LLM creates a business scenario with statistical parameters
2. **Validate Parameters**: System ensures all parameters are within valid bounds
3. **Simulate Data**: Generate realistic user-level data based on expected rates
4. **Analyze Results**: Perform statistical tests and calculate business impact
5. **Evaluate Response**: Compare user analysis against answer key
6. **Provide Feedback**: Generate detailed scoring and improvement suggestions

### API Endpoints

- `POST /api/v1/scenarios/generate` - Generate new scenario
- `GET /api/v1/scenarios/{id}` - Get scenario details
- `POST /api/v1/design/compute-n` - Calculate sample size
- `POST /api/v1/simulate` - Run simulation
- `POST /api/v1/analyze` - Perform statistical analysis
- `POST /api/v1/evaluate` - Evaluate user response

### Example Usage

```python
from core.types import DesignParams, Allocation
from core.design import compute_sample_size
from core.simulate import simulate_trial
from core.analyze import analyze_results

# Create design parameters
allocation = Allocation(control=0.5, treatment=0.5)
params = DesignParams(
    baseline_conversion_rate=0.05,
    target_lift_pct=0.15,
    alpha=0.05,
    power=0.8,
    allocation=allocation,
    expected_daily_traffic=10000
)

# Calculate sample size
sample_size = compute_sample_size(params)
print(f"Required sample size: {sample_size.per_arm} per group")
print(f"Test duration: {sample_size.days_required} days")

# Simulate data
true_rates = {"control": 0.05, "treatment": 0.0575}
sim_result = simulate_trial(params, true_rates, seed=42)

# Analyze results
analysis = analyze_results(sim_result, alpha=0.05)
print(f"P-value: {analysis.p_value}")
print(f"Significant: {analysis.significant}")
print(f"Recommendation: {analysis.recommendation}")
```

## Development

### Project Structure

```
abtest-simulator/
├── core/                   # Core domain logic
│   ├── types.py           # Domain types and validation
│   ├── design.py          # Sample size calculations
│   ├── simulate.py        # Data simulation
│   ├── analyze.py         # Statistical analysis
│   ├── rng.py             # Random number generation
│   └── utils.py           # Utility functions
├── api/                   # FastAPI application
│   ├── main.py            # Application entry point
│   ├── routes/            # API endpoints
│   ├── deps.py            # Dependency injection
│   └── adapters.py        # Data adapters
├── llm/                   # LLM integration
│   ├── client.py          # LLM client wrapper
│   ├── prompts/           # Prompt templates
│   ├── parser.py          # JSON parsing
│   └── generator.py       # Scenario generation
├── schemas/               # Data schemas
│   ├── scenario.py        # Scenario DTOs
│   ├── design.py          # Design DTOs
│   └── analysis.py        # Analysis DTOs
├── ui/                    # User interface
│   ├── streamlit_app.py   # Streamlit UI
│   └── web/               # React UI (optional)
├── tests/                 # Test suite
├── configs/               # Configuration files
└── docs/                  # Documentation
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m e2e          # End-to-end tests
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing
- **Basic testing**: Run tests with pytest

```bash
# Run tests
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the existing code style and architecture
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting
- Use meaningful commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the example scenarios in `examples/`

## Roadmap

- [ ] Enhanced UI with React/Next.js
- [ ] Additional statistical test types
- [ ] Real-time collaboration features
- [ ] Advanced visualization options
- [ ] Integration with external data sources
- [ ] Mobile application
- [ ] API rate limiting and authentication
- [ ] Multi-language support

## Acknowledgments

- Built with FastAPI, Streamlit, and modern Python tools
- Inspired by real-world AB testing challenges
- Designed for interview preparation and learning
