# 30 Day A/Bs - Quick Context for Claude

**Copy this entire file and paste at the start of a Claude web/phone session.**

---

## What Is This Project?

**30 Day A/Bs** is an A/B testing interview practice simulator. It generates AI-powered business scenarios and quizzes users on experimental design and statistical analysis.

**Tech**: Python 3.11+, Streamlit (UI), OpenAI GPT-4 (scenarios), Pydantic (schemas), pytest

**Repo**: https://github.com/chrisrogers37/30-day-abs

---

## Architecture (3 Layers)

```
LLM (OpenAI) → Core (pure math) → UI (Streamlit)
```

- **core/** - Pure mathematical functions, NO side effects, NO I/O
- **llm/** - OpenAI integration for scenario generation
- **schemas/** - Pydantic DTOs for type-safe data transfer
- **ui/** - Streamlit web application

---

## Key Files

| File | Purpose |
|------|---------|
| `core/types.py` | Domain types: DesignParams, SampleSize, SimResult, AnalysisResult |
| `core/design.py` | Sample size calculations (two-proportion z-test) |
| `core/simulate.py` | Data simulation with realistic treatment effects |
| `core/analyze.py` | Statistical analysis: z-test, CI, p-value |
| `core/validation.py` | Answer validation for quiz questions |
| `ui/streamlit_app.py` | Main web app (quiz interface) |
| `llm/generator.py` | AI scenario generation |
| `schemas/*.py` | Pydantic models for all data |

---

## Current State (v1.5.1)

**Working**: App runs, tests pass (283 tests, 89% core coverage)

**Recent fixes**:
- Simulation performance (27s → 0.01s)
- AttributeError in logging

**Known issues**:
- Streamlit Cloud badge is placeholder
- E2E tests need OpenAI API key

---

## Code Patterns

### Creating Design Parameters
```python
from core.types import DesignParams, Allocation

params = DesignParams(
    baseline_conversion_rate=0.05,  # 5%
    target_lift_pct=0.20,           # 20% lift
    alpha=0.05,
    power=0.80,
    allocation=Allocation(0.5, 0.5),
    expected_daily_traffic=10000
)
```

### Sample Size Calculation
```python
from core.design import compute_sample_size
result = compute_sample_size(params)
# result.per_arm, result.total, result.days_required
```

### Simulation (Use Fast Mode)
```python
from core.simulate import simulate_trial
sim = simulate_trial(params, seed=42, sample_size_per_arm=result.per_arm, generate_user_data=False)
```

### Analysis
```python
from core.analyze import analyze_results
analysis = analyze_results(sim, alpha=0.05)
# analysis.p_value, analysis.significant, analysis.confidence_interval
```

---

## Commands

```bash
streamlit run ui/streamlit_app.py  # Run app
pytest                              # Run tests
pytest -m unit                      # Unit tests only
mypy core/ llm/ schemas/            # Type check
ruff check . && black .             # Lint & format
```

---

## Rules for Claude

1. **Don't modify .env** - Contains API keys
2. **Always write tests** - For new functionality
3. **Use Pydantic schemas** - For all data between layers
4. **Keep core/ pure** - No I/O, no side effects
5. **Check for None** - Before accessing simulation results
6. **Update CHANGELOG.md** - For any changes

---

## A/B Testing Glossary

- **Alpha (α)**: Significance level (typically 0.05)
- **Power**: 1-β, typically 0.80
- **MDE**: Minimum Detectable Effect
- **Relative Lift**: (treatment - control) / control
- **CI**: Confidence Interval

---

## How to Use This

1. Paste this context at the start of your Claude conversation
2. Upload or paste the specific file you're working on
3. Describe what you want to accomplish
4. Include any error messages

For full documentation, see CLAUDE.md in the repo root.
