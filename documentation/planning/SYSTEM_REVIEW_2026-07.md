# System Review & Issue Tracker — July 2026

**Session:** `system-review_2026-07-07`
**Scope:** Full-system review of `core/`, `llm/`, `schemas/`, `ui/`, `tests/`, docs, and infrastructure.
**Verification:** All P0 findings were verified directly against the code. Full test suite run on a clean install: **636 passed, 6 skipped** (after installing `pytest-timeout`, which is required by tests but missing from `requirements-dev.txt` — see INFRA-2). App boots headless via `streamlit run ui/streamlit_app.py`.

All findings are filed on GitHub: P0/P1 as individual issues (#27–#50), P2/P3/enhancements as clustered issues (#51–#56). Issue links appear on each heading below. Status values: `OPEN`, `IN PROGRESS`, `DONE`, `WONTFIX`.

---

## How to read this

- **P0 — Product-breaking correctness bugs.** The app's core promise is *accurate grading of experimental-design answers*. These bugs make the app grade users incorrectly or lose their progress. Fix before any feature work.
- **P1 — Statistical & pipeline correctness.** Wrong math in secondary paths, LLM pipeline waste/fragility. Fix soon; several are cheap.
- **P2 — Architecture & tech debt.** Structural problems that make every future change slower and riskier.
- **P3 — Testing, infra, docs.** Gaps in the safety net and stale documentation.

A separate document, [`STEADY_STATE_PLAN.md`](./STEADY_STATE_PLAN.md), sequences this work into phases toward the target end state.

---

## P0 — Product-breaking correctness bugs

### P0-1: Design batch scoring uses mismatched answer keys — Q4–Q6 always marked wrong — `OPEN` — [#27](https://github.com/chrisrogers37/30-day-abs/issues/27)
**Area:** `ui/streamlit_app.py` (~lines 629, 662, 687) vs `core/validation.py` (lines 184–191)

The UI stores design answers under `sample_size_per_group`, `experiment_duration_days`, and `additional_conversions_per_day`, but `_DESIGN_SCORING_SPECS` in core scoring expects `sample_size`, `duration`, and `additional_conversions`. Per-question inline validation works (it goes through a different path), but "Submit All Answers" always scores those three questions as unanswered/wrong.

**Fix:** Standardize on one set of keys (prefer the core spec keys), and add a test that submits the UI's session-state dict through `score_design_answers()`.

### P0-2: Design scoring results are computed but never displayed — `OPEN` — [#28](https://github.com/chrisrogers37/30-day-abs/issues/28)
**Area:** `ui/streamlit_app.py` (~lines 1595–1606)

After design submit, results are stored in `st.session_state.design_scoring_results` and `st.rerun()` advances to the `data_download` step — which never renders them. Users complete the design phase and get no feedback (the analysis phase, by contrast, has a proper per-question results display).

**Fix:** Render design scoring results on the data-download step (mirroring `display_analysis_scoring_results`), or add a dedicated results step.

### P0-3: ID-based `rollout_decision` correct answer is always "No" — `OPEN` — [#29](https://github.com/chrisrogers37/30-day-abs/issues/29)
**Area:** `core/validation.py` (lines 715–719)

`make_rollout_decision()` returns `"proceed_with_confidence" | "proceed_with_caution" | "do_not_proceed"`, but the ID-based answer calculation maps it with `"Yes" if decision.lower() == "yes" else "No"`. No return value equals `"yes"`, so the graded correct answer is unconditionally "No" regardless of the data. (The legacy numbered Q7 path handles the 3-way string correctly.)

**Fix:** Map `proceed_with_confidence`/`proceed_with_caution` → "Yes", `do_not_proceed` → "No" (or grade the 3-way decision directly). Add a regression test with a clearly-winning treatment.

### P0-4: "Generate New Scenario" does not fully reset session state — `OPEN` — [#30](https://github.com/chrisrogers37/30-day-abs/issues/30)
**Area:** `ui/streamlit_app.py` (~lines 1116–1122)

The new-scenario handler resets design/analysis answers and scoring results, but not `current_analysis_question`, `completed_analysis_questions`, `experiment_started`, `experiment_completed`, or `answers_visible`. A second quiz inherits the previous session's analysis progress and skips the experiment-run step.

**Fix:** Introduce a single `reset_quiz_session()` function that owns the complete list of session keys, and call it from every restart path. This is also a prerequisite for splitting the UI (P2-1).

### P0-5: Analysis grading hardcodes `alpha=0.05`, ignoring the scenario's alpha — `OPEN` — [#31](https://github.com/chrisrogers37/30-day-abs/issues/31)
**Area:** `core/validation.py` (lines 330, 339, 360, 433)

Scenario generation can produce designs with alpha ≠ 0.05 (the schema allows 0.01–0.1), and the simulation/analysis honors it, but answer validation and scoring call `analyze_results(sim_result, alpha=0.05)` unconditionally. Significance and CI answers are graded against the wrong alpha for those scenarios.

**Fix:** Thread `design_params.alpha` through `validate_analysis_answer` / `score_analysis_answers` / `calculate_correct_analysis_answers` (a `ScoringContext` already exists — use it consistently).

### P0-6: UI validation hardcodes 50/50 allocation regardless of scenario — `OPEN` — [#32](https://github.com/chrisrogers37/30-day-abs/issues/32)
**Area:** `ui/streamlit_app.py` (lines 416, ~1310); related core bug in `core/validation.py` (lines 608–613)

`validate_question_answer()` and the sidebar answer panel construct `Allocation(control=0.5, treatment=0.5)` instead of using `scenario.design_params.allocation`. Separately, `sample_size_with_allocation` in core reads allocation with `allocation.get('control', 0.5)` on an `Allocation` dataclass (not a dict), so it always falls back to 0.5. Non-50/50 scenarios are graded incorrectly.

**Fix:** Pass the scenario's real allocation through `to_design_params()` everywhere; fix the dict/dataclass confusion in `sample_size_with_allocation`.

### P0-7: Duration answers use two different formulas that disagree for unequal allocation — `OPEN` — [#33](https://github.com/chrisrogers37/30-day-abs/issues/33)
**Area:** `core/design.py` (lines 62–63) vs `core/validation.py` (lines 261–262, 403–404, 615–617)

`compute_sample_size()` computes days as `ceil(n_per_arm / (daily_traffic × control_allocation))`, while validation computes `round(2 × n_per_arm / daily_traffic)`. These match for 50/50 but diverge otherwise, so a user who answers using the design-engine value can be marked wrong.

**Fix:** Validation should read `sample_size_result.days_required` from the design engine rather than recomputing. One formula, one source of truth.

### P0-8: `validate_test_duration` / `suggest_parameter_adjustments` crash on call — `OPEN` — [#34](https://github.com/chrisrogers37/30-day-abs/issues/34)
**Area:** `core/design.py` (lines 76–138)

Both functions reference `params.min_test_duration_days` / `params.max_test_duration_days`, which do not exist on `DesignParams`. Tests explicitly skip them (`tests/core/test_design_helpers.py`). Any real call raises `AttributeError`.

**Fix:** Either add optional duration-constraint fields to `DesignParams` (they exist on the DTO's `duration_constraints`) and un-skip the tests, or delete both functions and their README mentions.

### P0-9: `score_analysis_answers()` raises `KeyError` when `business_target_absolute` is None — `OPEN` — [#35](https://github.com/chrisrogers37/30-day-abs/issues/35)
**Area:** `core/validation.py` (lines 194–201, ~519, ~534)

`_ANALYSIS_SCORING_SPECS` always includes `rollout_decision`, but `calculate_correct_analysis_answers()` omits that key when `business_target_absolute` is `None`, so scoring crashes.

**Fix:** Skip specs whose correct answer is absent, or make the calculation always produce the key (possibly `None`-scored). Add a test with `business_target_absolute=None`.

---

## P1 — Statistical & pipeline correctness

### P1-1: `get_z_score()` lookup table returns wrong critical value for two-tailed α=0.10 — `OPEN` — [#36](https://github.com/chrisrogers37/30-day-abs/issues/36)
**Area:** `core/utils.py` (lines 331–355)

For two-tailed tests α is halved and then matched against the *original* α thresholds, so α=0.10 two-tailed returns 1.96 instead of 1.645. Standard cases (0.05, 0.01) work by coincidence. **Fix:** drop the lookup table and always use `scipy.stats.norm.ppf` — the scipy fallback already exists.

### P1-2: Inconsistent `z_beta` tail direction across sample-size helpers — `OPEN` — [#37](https://github.com/chrisrogers37/30-day-abs/issues/37)
**Area:** `core/design.py` (line 49), `core/utils.py` (lines 133, 443)

`compute_sample_size()` correctly uses one-tailed `z_beta`; `calculate_required_sample_size_for_power()` and `calculate_sample_size_for_revenue_detection()` use two-tailed. Duplicate formulas can disagree on required n for identical inputs. **Fix:** all helpers delegate to one canonical sample-size function.

### P1-3: `relative_lift_to_absolute()` percent/decimal convention conflicts with the rest of the codebase — `OPEN` — [#38](https://github.com/chrisrogers37/30-day-abs/issues/38)
**Area:** `core/utils.py` (lines 24–35)

This helper divides by 100 (expects `20.0` = 20%), while `DesignParams.target_lift_pct` and everything else use decimals (`0.20` = 20%). A silent 100× error is waiting for the first caller who mixes them. **Fix:** standardize on decimal everywhere; rename fields/args to make the unit unambiguous (`target_lift_rel`).

### P1-4: Revenue "confidence interval" is not a confidence interval — `OPEN` — [#39](https://github.com/chrisrogers37/30-day-abs/issues/39)
**Area:** `core/utils.py` (lines 89–103); related dead heuristic in `core/analyze.py` (line 450)

`margin = revenue_impact × (1 − confidence_level)` — i.e., ±5% of the point estimate at 95% "confidence" — has no statistical basis. In `analyze.py`, `confidence_in_revenue` checks `sim_result.p_value` which never exists, so it's always 0.7. For a statistics education tool this is actively harmful. **Fix:** propagate the conversion-rate CI through the revenue arithmetic, or remove the revenue CI until done properly.

### P1-5: Simulation volume is hardcoded to 30 days, decoupled from the designed sample size — `OPEN` — [#40](https://github.com/chrisrogers37/30-day-abs/issues/40)
**Area:** `core/simulate.py` (lines 95–99, `DEFAULT_SIMULATION_DAYS`)

Users calculate a required sample size and duration in the design phase, then receive a dataset sized `daily_traffic × 30` regardless. The data they analyze doesn't reflect the experiment they designed — a pedagogical inconsistency at the heart of the product. **Fix:** simulate `days_required` worth of traffic (or the user's submitted duration), and surface that linkage in the UI.

### P1-6: Generator path sends the full scenario prompt twice per API call — `OPEN` — [#41](https://github.com/chrisrogers37/30-day-abs/issues/41)
**Area:** `llm/generator.py` (lines 299, 418–421) + `llm/client.py` (lines 391–396)

`_create_prompt(None)` returns the entire `scenario_prompt.txt` as the **user** message; `client.generate_scenario()` then independently loads the same file as the **system** prompt. Every generator-path call pays ~2× input tokens and gives the model conflicting message structure. (The UI path avoids this only because it bypasses the generator entirely — see P2-3.) **Fix:** generator should pass only the short trigger + request-specific hints as the user message.

### P1-7: Generator accepts below-threshold quality scenarios on the final attempt — `OPEN` — [#42](https://github.com/chrisrogers37/30-day-abs/issues/42)
**Area:** `llm/generator.py` (lines 336–340)

When `quality_score < min_quality_score` on the last attempt, control falls through to the success path instead of using the fallback. The `min_quality_score` contract is silently violated. **Fix:** decide explicitly — either document "best effort on final attempt" and set `used_fallback`-style metadata, or route to fallback.

### P1-8: `LLMOutputParser.parsing_errors` accumulates across calls — `OPEN` — [#43](https://github.com/chrisrogers37/30-day-abs/issues/43)
**Area:** `llm/parser.py` (lines 214–215, 302, 374)

The parser instance is reused (generator, integration, UI) and `parsing_errors` is never cleared per call, so stale errors from earlier parses leak into later results. **Fix:** make errors local to each `parse_llm_response()` call.

### P1-9: Bounds disagree three ways: prompt vs Pydantic schema vs guardrails — `OPEN` — [#44](https://github.com/chrisrogers37/30-day-abs/issues/44)
**Area:** `llm/prompts/scenario_prompt.txt`, `schemas/design.py` (lines 16–39), `llm/guardrails.py`; also `schemas/scenario.py` `SimulationHintsDTO` (caps rates at 0.5 while prompt/guardrails allow 0.8)

The prompt encourages early-stage traffic of 100–1K/day and alpha down to 0.001; the DTO requires `expected_daily_traffic ≥ 1000` and `alpha ≥ 0.01`; guardrails allow wider ranges than both; core `DesignParams` has a fourth set of bounds. LLM outputs that follow the prompt can fail schema validation, burning retries and falling back silently. **Fix:** define one bounds table (single module), and generate the prompt's parameter-guidance section, the Pydantic validators, and the guardrail checks from it.

### P1-10: Guardrails hard-fail on MDE/lift rounding — `OPEN` — [#45](https://github.com/chrisrogers37/30-day-abs/issues/45)
**Area:** `llm/guardrails.py` (lines 493–500)

`abs(target_lift − mde/baseline) > 0.001` is a hard error, so ordinary LLM rounding (0.167 vs 0.1667) fails validation and triggers retries/fallback. **Fix:** widen tolerance to relative terms (e.g., 2%) or auto-correct via the existing-but-never-called `clamp_parameters()`.

### P1-11: Fallback scenarios masquerade as success — `OPEN` — [#46](https://github.com/chrisrogers37/30-day-abs/issues/46)
**Area:** `llm/generator.py` (lines 392–397), `llm/integration.py`

On total failure the generator returns `success=True, used_fallback=True`, and `used_fallback` is not propagated through the integration pipeline or shown in any UI. Users can practice on the same canned scenario believing it was freshly generated. **Fix:** propagate and display fallback status; consider `success=False` with the fallback attached.

### P1-12: Client retry loop treats `AuthenticationError` like a transient failure; typed exceptions unused — `OPEN` — [#47](https://github.com/chrisrogers37/30-day-abs/issues/47)
**Area:** `llm/client.py` (lines 299–327)

Invalid API keys are retried with backoff (4 wasted attempts before a generic `LLMError`). `LLMRateLimitError`/`LLMTimeoutError` are defined and documented but never raised. Also: `response.choices[0].message.content` can be `None` (unhandled), and `response.usage.dict()` is legacy SDK syntax that may break on newer `openai` versions. **Fix:** fail fast on auth errors, raise the typed exceptions, guard null content, use `model_dump()`.

### P1-13: No JSON mode; expensive defaults — `OPEN` — [#48](https://github.com/chrisrogers37/30-day-abs/issues/48)
**Area:** `llm/client.py` (lines 127–133), `llm/parser.py` (lines 285–295)

The client doesn't use `response_format={"type": "json_object"}` (or structured outputs), relying instead on a greedy `\{.*\}` regex that can swallow prose or merge objects. Defaults are `model="gpt-4"` (legacy, expensive), `max_tokens=4000` (~3–4× need), `temperature=0.7` (high for structured output). Combined with client-level retries (×4) nested inside generator retries (×3), worst case is ~12 expensive API calls per scenario. **Fix:** enable JSON mode, default to a current cost-efficient model via config, cap tokens, lower temperature, and cap combined retries.

### P1-14: CSV export writes the wrong "correct answer" column — `OPEN` — [#49](https://github.com/chrisrogers37/30-day-abs/issues/49)
**Area:** `core/scoring.py` (lines 303–304)

Both `correct_answer` and `is_correct` columns are populated from the boolean `score_info["correct"]`; the actual correct answer is dropped. **Fix:** use `score_info["correct_answer"]`; add an export assertion test (the existing "data export" integration test doesn't test export at all — see INFRA-6).

### P1-15: Legacy analysis answer key has 6 questions; the live quiz has 7 — `OPEN` — [#50](https://github.com/chrisrogers37/30-day-abs/issues/50)
**Area:** `core/scoring.py` (lines 106–162)

`generate_analysis_answer_key()` omits the rollout-decision question and sets `max_score=6`, while the UI and legacy validation grade 7 questions. **Fix:** align (will likely be subsumed by the quiz-engine consolidation, P2-2).

---

## P2 — Architecture & tech debt

### P2-1: `ui/streamlit_app.py` is a 1,813-line monolith — `OPEN` — filed in cluster [#51](https://github.com/chrisrogers37/30-day-abs/issues/51)
**Area:** `ui/streamlit_app.py` (entire file)

One file contains: LLM client construction and async orchestration, simulation invocation, validation wrappers, 13 hardcoded question blocks, scoring display, sidebar, landing page, CSS, and session-state initialization. `main()` is a nested-conditional step dispatcher. It has 0% test coverage and several defects above live in the seams. **Fix:** split into `ui/state.py` (session state + reset), `ui/services.py` (scenario generation + simulation orchestration — no Streamlit imports), and one module per quiz phase; `main()` becomes a step registry. See the steady-state plan, Phase 2.

### P2-2: Two parallel quiz/scoring systems that disagree — `OPEN` — filed in cluster [#51](https://github.com/chrisrogers37/30-day-abs/issues/51)
**Area:** `core/validation.py`, `core/scoring.py`, `core/question_bank.py`, `ui/streamlit_app.py`

A legacy numbered system (Q1–7, hardcoded question text duplicated in the UI) and a question-bank ID system (~50 questions with difficulty metadata) coexist. They differ on rollout-decision format, answer-key length, duration formulas, and tolerances. The UI *selects* question-bank IDs on every new scenario (`selected_design_questions` etc.) and then ignores them, rendering the hardcoded questions instead. Roughly 30 planning/interpretation questions in the bank have no grading logic at all. **Fix:** commit to the question-bank system, port the 13 legacy questions into it, delete the legacy path. This is the single highest-leverage refactor in the codebase.

### P2-3: UI bypasses the LLM orchestrator, losing retries/fallback/novelty — `OPEN` — filed in cluster [#51](https://github.com/chrisrogers37/30-day-abs/issues/51)
**Area:** `ui/streamlit_app.py` (lines 154–248) vs `llm/generator.py`, `llm/integration.py`

The UI hand-rolls client → parse → guardrails with no retry, no fallback, and no novelty scoring, so users see hard failures the generator layer was built to absorb. Meanwhile the generator/integration path has its own bugs (P1-6) because nothing exercises it in production. **Fix:** one orchestration function (in `llm/integration.py` or a new service layer) used by both the UI and any future API.

### P2-4: Dead and unused code across all layers — `OPEN` — filed in cluster [#52](https://github.com/chrisrogers37/30-day-abs/issues/52)
**Inventory:**
- `ui/streamlit_app.py`: `get_question_display_info`, `display_question_from_bank`, `ask_data_analysis_questions`, `display_simulation_results`, `display_scoring_results` (which also has its own display bug) — all unreachable; duplicate `design_answers` init; a local `score_design_answers()` that shadows the core import of the same name.
- `core/rng.py`: ~400 lines of NumPy generator infrastructure (mixtures, multivariate normal, time series) with zero production callers — `simulate.py` uses stdlib `random`.
- `llm/`: Anthropic provider enum/factory branch raising `NotImplementedError`; exception classes never raised (`ScenarioGenerationError`, `JSONParsingError`, `SchemaValidationError`, `GuardrailError`); `clamp_parameters()` and `generate_regeneration_hints()` never called; `traffic_tiers`/`metric_baseline_ranges`/`effect_size_profiles`/`alpha_guidance`/`power_guidance` config never read; `integration.py` creates a parser it never uses.
- `schemas/`: `evaluation.py` DTOs with no implementation behind them; `complications.py` not integrated into any pipeline; `SimulationConfigDTO` traffic-pattern/novelty fields unimplemented; `complications` missing from `schemas/__init__.py`.
- `core/analyze.py`: `assess_test_quality()` returns hardcoded placeholders (`traffic_consistency=0.95`, `power_achieved=0.8`).

**Fix:** delete what has no near-term plan (rng extras, Anthropic stub, unused guardrail config, dead UI functions); file P3 items for what should be finished instead (fallback wiring, clamping). Deleting is a feature: it shrinks the surface the docs must describe and tests must cover.

### P2-5: `core/logging.py` gives the "pure" core filesystem side effects — `OPEN` — filed in cluster [#52](https://github.com/chrisrogers37/30-day-abs/issues/52)
**Area:** `core/logging.py` (imported by `core/design.py`, `core/utils.py`)

Creates `logs/` on import and does file I/O from modules documented as pure math. **Fix:** move quiz-session logging up to the app layer; core modules use plain `logging.getLogger(__name__)` with no handler configuration.

### P2-6: Duplicated statistical helpers — `OPEN` — filed in cluster [#52](https://github.com/chrisrogers37/30-day-abs/issues/52)
**Area:** `core/utils.py`

`calculate_confidence_interval_for_proportion()` (lines 228–258) and `calculate_conversion_rate_confidence_interval()` (lines 526–552) are the same function under two names. `AnalysisResult.test_statistic` stores a z-score, chi-square stat, or odds ratio depending on `test_type_used`, forcing consumers to branch. **Fix:** consolidate; consider a typed union or separate fields for the statistic.

### P2-7: Schema ↔ core bounds and enums don't round-trip — `OPEN` — filed in cluster [#51](https://github.com/chrisrogers37/30-day-abs/issues/51)
**Area:** `schemas/design.py` vs `core/types.py`; `schemas/shared.py` vs `core/analyze.py`

Four fields have different valid ranges in the DTO vs the core dataclass (`baseline_conversion_rate`, `target_lift_pct`, `alpha`, `expected_daily_traffic`), so `to_design_params()` can fail on schema-valid data. `RolloutRecommendation` enum values (`full_rollout`…) don't match core's strings (`proceed_with_confidence`…). `to_design_params()` also drops `mde_absolute`, `duration_constraints`, `test_type`, `test_direction`. **Fix:** single bounds table (same fix as P1-9); add an enum mapping or unify the vocabulary.

### P2-8: Module docstrings and READMEs describe an aspirational system — `OPEN` — filed in cluster [#52](https://github.com/chrisrogers37/30-day-abs/issues/52)
**Area:** `llm/*` module docstrings (~50–70 lines each), `ui/README.md`, `core/README.md`, `llm/README.md`

Documented-but-nonexistent: caching, streaming, connection pooling, Anthropic support, WebSocket, DB persistence, auth, retry/backoff in the UI, component-based RNG in simulation, "precise" test-quality assessment. This actively misleads contributors (and AI tools reading the repo). **Fix:** cut docstrings to what the code does; move aspirations to the roadmap.

---

## P3 — Testing, infrastructure, docs

### INFRA-1: No CI test workflow — `OPEN` — filed in cluster [#53](https://github.com/chrisrogers37/30-day-abs/issues/53)
`.github/workflows/` contains only Claude-assistant workflows. `tests/README.md` and `TESTING_GUIDE.md` describe a `test.yml` that does not exist. Nothing runs pytest or lint on PRs — which is how P0-1/P0-2-class regressions ship. **Fix:** add `test.yml` (pytest on 3.11/3.12, ruff, optionally mypy) as the very first change; make it required for merge.

### INFRA-2: Dependency gaps and unpinned requirements — `OPEN` — filed in cluster [#53](https://github.com/chrisrogers37/30-day-abs/issues/53)
- `pytest-timeout` is used by `tests/integration/test_real_api.py` but absent from `requirements-dev.txt` → **test collection fails on a clean install** (reproduced in this review).
- `statsmodels` is used by `notebooks/ab_experimental_analysis_template.ipynb` (and referenced in UI hint text) but not declared anywhere.
- `requirements.txt` is fully unpinned; `requirements-dev.txt` has lower bounds only; `pytest-benchmark` is declared but unused.
**Fix:** add the missing deps, pin production requirements (or adopt a lockfile), drop unused dev deps.

### INFRA-3: UI has zero real tests; some "tests" can't fail — `OPEN` — filed in cluster [#54](https://github.com/chrisrogers37/30-day-abs/issues/54)
- `tests/ui/test_streamlit_app_enhanced.py` never imports `ui/streamlit_app.py` (import-smoke of other modules only).
- `tests/test_streamlit_app.py` contains zero `assert` statements; `tests/test_basic.py::test_core_imports` returns a bool instead of asserting.
- Placeholders that always pass: `tests/integration/test_llm_pipeline.py` (`assert True`), `tests/schemas/test_analyze.py`, `test_simulate.py`, `test_evaluation.py`.
**Fix:** adopt Streamlit's `AppTest` for the quiz flow (session reset, scoring keys, step transitions — the exact spots where P0 bugs live); replace or delete the placeholders so the suite's green is trustworthy.

### INFRA-4: Real `llm.client` retry/error paths untested — `OPEN` — filed in cluster [#54](https://github.com/chrisrogers37/30-day-abs/issues/54)
`tests/llm/test_client.py` exercises a mock helper in `tests/helpers/mocks.py`, not `llm.client.LLMClient`. Retry logic, auth failure, null content, and usage parsing (P1-12) have no coverage. **Fix:** unit tests with a mocked OpenAI SDK client.

### INFRA-5: Root-level `test_scenario_variety.py` is a manual API script, not a test — `OPEN` — filed in cluster [#54](https://github.com/chrisrogers37/30-day-abs/issues/54)
It calls the real OpenAI API and isn't collected by pytest (testpaths=tests) but is named like a test. The scenario-variety plan's actual acceptance test ("generate 100 scenarios, measure distribution") was never implemented. **Fix:** move to `scripts/`; add an offline distributional test over the question bank/guardrail features where feasible.

### INFRA-6: Integration tests don't test what their names claim — `OPEN` — filed in cluster [#54](https://github.com/chrisrogers37/30-day-abs/issues/54)
`tests/integration/test_data_export.py` asserts `control_n > 0` and never exports anything (would have caught P1-14). `tests/fixtures/scenarios/*.json` referenced by `tests/README.md` doesn't exist. `tests/performance/` is an empty placeholder. `@pytest.mark.e2e` is defined and unused; most `tests/llm/` tests lack the `unit` marker so `pytest -m unit` under-reports. **Fix:** make names honest — implement or delete.

### INFRA-7: Stale/inflated documentation claims — `OPEN` — filed in cluster [#54](https://github.com/chrisrogers37/30-day-abs/issues/54)
Docs claim "634+ tests" (actual: 636 collected today, but CHANGELOG says 456 at v1.5.0 — the number drifts); `test.yml` CI (doesn't exist); JSON scenario fixtures (don't exist); "2 skipped statistical tests" in the variety plan (none found); full-suite runtime "~25 minutes" (actual: ~8.5 minutes). `.gitignore` is ~950 lines with mass duplication. **Fix:** one pass to reconcile docs with `pytest --collect-only` reality; dedupe `.gitignore`; prefer linking to a single source of truth over repeating counts.

---

## Enhancement backlog (from `CODE_REVIEW_EXPERIMENTAL_RIGOR.md`, still open)

These carry over from the prior statistical audit and remain valid. Filed together as cluster [#55](https://github.com/chrisrogers37/30-day-abs/issues/55); the Phase 3 strong-UI milestone is filed as [#56](https://github.com/chrisrogers37/30-day-abs/issues/56):

- **E-1:** Proper unequal-allocation support in the sample-size formula (currently equal n per arm regardless of split; `SampleSize` type forbids `total ≠ 2 × per_arm`).
- **E-2:** Question-bank content for multiple-testing correction, sequential testing/peeking, regression to the mean, Simpson's paradox, network effects/SUTVA.
- **E-3:** Wilson (or clipped Wald) intervals for proportions near 0/1.
- **E-4:** Document pooled-vs-unpooled variance choice; align Cohen's h thresholds with standard cutoffs; document the chi-square/Fisher selection heuristic (`min n < 30`) or switch to expected-count rules.
- **E-5:** Statistical test auto-selection (`test_type="auto"`) exists in `analyze.py` but grading always uses the default z-test path — wire it through or teach it explicitly.

---

## Summary counts

| Priority | Count | Theme |
|----------|-------|-------|
| P0 | 9 | Grading correctness, crashes, state leaks |
| P1 | 15 | Statistical edge cases, LLM pipeline waste/fragility |
| P2 | 8 | Monolith UI, dual quiz systems, dead code, doc drift |
| P3 (infra) | 7 | No CI, dependency gaps, untrustworthy tests |
| Enhancements | 5 | Carried over from rigor audit |

**Bottom line:** the statistical core is genuinely strong for the standard case (50/50, α=0.05, z-test) and well-tested there — 636 tests pass. The product breaks at the seams: UI↔core key contracts, scenario-parameter passthrough (alpha, allocation), and the LLM orchestration that production doesn't actually use. The steady-state plan sequences fixes accordingly.
