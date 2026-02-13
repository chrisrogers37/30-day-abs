# Development Documentation

Welcome to the development documentation for 30 Day A/Bs! This directory contains comprehensive guides for developers contributing to the project.

## Documentation Overview

### 📚 Available Guides

1. **[Development Guide](./DEVELOPMENT_GUIDE.md)** - Start here!
   - Project architecture and setup
   - Development workflow and best practices
   - Code standards and conventions
   - Git workflow and release process
   
2. **[Testing Guide](./TESTING_GUIDE.md)** - Essential for contributors
   - Testing philosophy and structure
   - How to write and run tests
   - Coverage requirements and strategies
   - Mock strategies and CI/CD integration

3. **[Enhancement Roadmap](./ENHANCEMENT_ROADMAP.md)** - Future feature planning
   - User experience and platform expansion ideas
   - Advanced statistical features roadmap
   - Implementation phases and priorities

4. **[Code Review: Experimental Rigor](./CODE_REVIEW_EXPERIMENTAL_RIGOR.md)** - Statistical audit
   - Detailed review of statistical implementations
   - Educational content gap analysis
   - Prioritized recommendations

5. **[Scenario Variety Improvement Plan](./SCENARIO_VARIETY_IMPROVEMENT_PLAN.md)** - COMPLETED
   - Expanded business context, parameter space, and question variety
   - All 5 phases complete

## Quick Start

### For New Developers

1. Read the [Development Guide](./DEVELOPMENT_GUIDE.md) to understand:
   - Project architecture
   - Setup and installation
   - Development workflow
   - Code standards

2. Review the [Testing Guide](./TESTING_GUIDE.md) to learn:
   - How to run tests
   - How to write tests
   - Coverage requirements
   - Testing best practices

3. Explore module-specific documentation:
   - [Core Module README](../core/README.md)
   - [LLM Module README](../llm/README.md)
   - [Schemas Module README](../schemas/README.md)

### For Contributors

**Before submitting a PR, ensure you've:**
- [ ] Read the Development Guide
- [ ] Followed code standards (Black, Ruff, type hints)
- [ ] Written tests with 80%+ coverage
- [ ] Updated CHANGELOG.md
- [ ] Reviewed the Testing Guide
- [ ] All tests passing locally

## Testing Achievement

**Current Status** (as of 2026-02-13):
- ✅ **634+ tests** across all modules
- ✅ **Comprehensive core module coverage**
- ✅ **10,000+ lines of test code**
- ✅ **Two tech debt remediations completed** (PRs #9-#24)

See the [Testing Guide](./TESTING_GUIDE.md) for full details on running and writing tests.

## Documentation Structure

```
development_docs/
├── README.md                                # This file - navigation guide
├── DEVELOPMENT_GUIDE.md                     # General development practices (719 lines)
├── TESTING_GUIDE.md                         # Testing standards and practices (889 lines)
├── ENHANCEMENT_ROADMAP.md                   # Future feature roadmap
├── CODE_REVIEW_EXPERIMENTAL_RIGOR.md        # Statistical rigor audit
└── SCENARIO_VARIETY_IMPROVEMENT_PLAN.md     # Scenario variety work (COMPLETED)

../
├── core/README.md               # Core module documentation
├── llm/README.md                # LLM module documentation
├── llm/prompts/README.md        # Prompt template documentation
├── schemas/README.md            # Schemas module documentation
├── ui/README.md                 # UI module documentation
├── tests/README.md              # Testing suite documentation
├── notebooks/README.md          # Jupyter notebook templates
├── .env.example                 # Environment variable template
├── CHANGELOG.md                 # Version history and changes
└── README.md                    # Project overview and quickstart
```

## CI/CD — GitHub Actions

Two workflows live in `.github/workflows/`:

### `claude.yml` — Claude Code Assistant
Triggers when `@claude` is mentioned in issue comments, PR review comments, or new issues. Runs Claude Code to respond to the request. Read-only permissions.

### `claude-code-review.yml` — Automated PR Review
Triggers automatically on PR events (opened, synchronize, ready_for_review, reopened). Runs the Claude Code Review plugin to leave review comments. No manual trigger needed.

Both workflows require the `CLAUDE_CODE_OAUTH_TOKEN` secret configured in the repo settings.

## Common Tasks

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/chrisrogers37/30-day-abs.git
cd 30-day-abs
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

See [Development Guide - Setup](./DEVELOPMENT_GUIDE.md#setup--installation) for details.

### Running Tests

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only
pytest tests/core/                # Specific module

# With coverage
pytest --cov=core --cov=schemas --cov-report=html
open htmlcov/index.html

# Demo: generate 3 scenarios to verify LLM variety (requires API key)
python test_scenario_variety.py
```

See [Testing Guide - Running Tests](./TESTING_GUIDE.md#running-tests) for details.

### Creating a Feature

```bash
# Create feature branch from main
git checkout main
git checkout -b feature/your-feature-name

# Make changes, test, commit
git add .
git commit -m "feat(module): description"
git push -u origin feature/your-feature-name
```

> **Note:** This project branches directly from `main`. There is no `develop` branch.

See [Development Guide - Git Workflow](./DEVELOPMENT_GUIDE.md#git-workflow) for details.

### Code Quality Checks

```bash
# Format code
black .

# Lint code
ruff check --fix .

# Type check
mypy core/ llm/ schemas/

# Run tests
pytest -m unit
```

See [Development Guide - Code Standards](./DEVELOPMENT_GUIDE.md#code-standards) for details.

## Module Documentation

### Core Modules

- **[core/](../core/README.md)** - Pure mathematical engine
  - Sample size calculations
  - Statistical analysis
  - Data simulation
  - Answer validation and scoring

- **[llm/](../llm/README.md)** - LLM integration
  - Scenario generation
  - JSON parsing
  - Guardrails and validation
  - Pipeline orchestration

- **[schemas/](../schemas/README.md)** - Data transfer objects
  - Pydantic models
  - API boundaries
  - Validation schemas

- **[ui/](../ui/README.md)** - Streamlit application
  - Web interface
  - Quiz flow
  - Data visualization

## Key Principles

### Architecture

**Separation of Concerns**: Clear boundaries between LLM, Core, and UI layers

**Pure Functions**: Core module has no side effects or external dependencies

**Type Safety**: Comprehensive type hints and Pydantic validation

**Testability**: Dependency injection and mock-friendly design

### Development

**Test-Driven**: Write tests first when possible

**Code Quality**: Use Black, Ruff, and mypy for consistency

**Documentation**: Update docs with code changes

**Git Flow**: Feature branches from main, PR to merge

### Testing

**Comprehensive Coverage**: High coverage on core modules

**Mock by Default**: Use mock LLM clients in tests

**Fast Feedback**: Full suite completes in ~25 minutes (634+ tests)

**Independent Tests**: Tests should not depend on each other

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for detailed version history.

**Current Version**: 1.5.1

Major milestones:
- **1.0.0**: Initial release with core functionality
- **1.1.0**: Jupyter notebook framework
- **1.2.0**: Analysis section with rollout decisions
- **1.3.0**: MIT license and Streamlit Cloud focus
- **1.4.0**: Bug fixes and UX improvements
- **1.5.0**: Comprehensive testing suite
- **1.5.1**: Centralized logging system with quiz session tracking

## Contributing

We welcome contributions! Please follow these steps:

1. **Read Documentation**: Start with this README and the guides
2. **Check Issues**: Look for open issues or create a new one
3. **Create Branch**: Feature branch from `main`
4. **Make Changes**: Follow code standards and write tests
5. **Submit PR**: Create pull request with description
6. **Code Review**: Address review feedback
7. **Merge**: Merge after approval

See [Development Guide - Git Workflow](./DEVELOPMENT_GUIDE.md#git-workflow) for detailed process.

## Getting Help

### Documentation

1. Check this README for navigation
2. Review relevant guide (Development, Testing, or Coverage Plan)
3. Check module-specific README files
4. Review CHANGELOG for recent changes

### Support

1. Search existing GitHub issues
2. Check closed issues for solutions
3. Create new issue with detailed description
4. Tag with appropriate labels

### Contact

For questions or suggestions:
- **GitHub Issues**: [Create an issue](https://github.com/chrisrogers37/30-day-abs/issues)
- **Email**: [christophertrogers37@gmail.com](mailto:christophertrogers37@gmail.com)
- **LinkedIn**: [chrisrogers37](https://linkedin.com/in/chrisrogers37)

## Additional Resources

### Project Resources
- [Main README](../README.md) - Project overview
- [CHANGELOG](../CHANGELOG.md) - Version history
- [LICENSE](../LICENSE) - MIT License

### External Resources
- [Python Documentation](https://docs.python.org/3/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Learning Resources
- [A/B Testing - Evan Miller](https://www.evanmiller.org/ab-testing/)
- [Statistical Power Analysis](https://statpower.net/)
- [Clean Code Principles](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)

---

**Last Updated**: 2026-02-10
**Version**: 2.1
**Maintained By**: Development Team
