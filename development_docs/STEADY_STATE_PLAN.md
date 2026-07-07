# Steady-State Plan — 30 Day A/Bs

**Companion to:** [`SYSTEM_REVIEW_2026-07.md`](./SYSTEM_REVIEW_2026-07.md) (issue IDs referenced below)
**Supersedes for sequencing purposes:** the scope-heavy portions of `ENHANCEMENT_ROADMAP.md` (auth, REST API, mobile apps, multi-tenant enterprise). Those remain long-horizon options but are explicitly *not* on the path to steady state.

---

## 1. Project direction (as understood from the code and docs)

30 Day A/Bs is a **single-player statistical fitness app**: an LLM generates a realistic business scenario, a deterministic engine computes the ground-truth design math and simulates the experiment, and the user is graded on designing and analyzing the test — like an interview loop they can run every day.

The value proposition rests on exactly three pillars:

1. **The grading is right.** Every number the app marks correct/incorrect must come from one trustworthy engine.
2. **The loop is coherent.** Scenario → design → *data that reflects that design* → analysis → decision → feedback. The user should feel one continuous experiment, not disconnected screens.
3. **The experience teaches.** Feedback explains *why*, difficulty varies, and the UI makes statistical concepts visible (distributions, CIs, power curves) instead of just numeric quiz fields.

The current codebase has pillar 1 mostly built but broken at the seams (P0 issues), pillar 2 partially violated (simulation ignores the designed sample size; design feedback never shown), and pillar 3 scaffolded but unwired (question bank, planning/interpretation phases, no charts).

**Definition of steady state:** a deployed Streamlit app where a user can, without ever hitting a bug or an unexplained grade: generate a fresh scenario, design the experiment with correct grading and rich feedback, receive simulated data sized by their design, analyze it with visual support, make a rollout decision, and see a session summary — with CI guarding every merge and no dead subsystem in the repo.

---

## 2. What we are deliberately NOT building

Scoping this out is as important as the plan itself. The prior `ENHANCEMENT_ROADMAP.md` sketches user accounts, PostgreSQL/Redis, FastAPI, mobile apps, real-time collaboration, and enterprise SSO. For a single-maintainer educational tool none of that is on the critical path, and each item multiplies operational surface. Steady state is achievable with: **Streamlit + session state + the existing core engine + one LLM provider.**

Revisit persistence (progress history) only after the core loop is polished — and even then, start with browser-local or file-based storage, not a database cluster.

---

## 3. Phases

Ordering principle: **safety net → correctness → consolidation → experience → depth.** Each phase leaves `main` shippable.

### Phase 0 — Safety net (small, do first)

The single biggest process gap is that nothing runs the 636-test suite on PRs.

- Add `.github/workflows/test.yml`: pytest (Python 3.11 + 3.12) + ruff on every PR; required check. *(INFRA-1)*
- Fix dependencies so a clean install works: add `pytest-timeout` to dev requirements, add `statsmodels` (notebook dependency), pin `requirements.txt`. *(INFRA-2)*
- Neutralize the tests that cannot fail (`assert True` placeholders, assert-free test files) — delete or mark as TODO-skips so green means something. *(INFRA-3, INFRA-6)*

**Exit criteria:** a PR that reintroduces any P0 bug class at least runs the suite; clean `pip install -r requirements*.txt && pytest` passes from scratch.

### Phase 1 — Grading correctness (the P0 batch)

Fix the nine P0 issues. Natural grouping:

1. **UI↔core contract** — align design answer keys; render design scoring results; full session reset via a single `reset_quiz_session()`. *(P0-1, P0-2, P0-4)* Add Streamlit `AppTest` coverage for exactly these paths so they can't regress silently. *(INFRA-3)*
2. **Parameter passthrough** — thread scenario `alpha` and real `allocation` through all validation/scoring; fix the `Allocation`-as-dict bug. *(P0-5, P0-6)*
3. **Single source of truth for answers** — validation reads `days_required` from the design engine instead of recomputing; fix rollout-decision mapping; fix the `business_target_absolute=None` crash; delete or finish the broken duration helpers. *(P0-3, P0-7, P0-8, P0-9)*

Also fold in the cheap P1 math fixes while touching these files: `get_z_score` two-tailed bug, `z_beta` consistency, CSV export column, 6-vs-7 answer key. *(P1-1, P1-2, P1-14, P1-15)*

**Exit criteria:** a full quiz pass on a non-default scenario (α≠0.05, unequal allocation) grades every question correctly, shows design feedback, and a second scenario starts clean.

### Phase 2 — One quiz engine, one generation pipeline (the consolidation)

This is the structural phase that makes everything after it cheap.

1. **Kill the dual quiz system** *(P2-2)*: port the 13 hardcoded legacy questions into `core/question_bank.py`, make the UI render from the already-selected question IDs, grade everything through `validate_answer_by_id`/`score_answers_by_id` with `ScoringContext`, then delete the legacy numbered path. Difficulty selection starts actually working as a side effect.
2. **One LLM orchestration path** *(P2-3, P1-6, P1-7, P1-8, P1-11)*: a single `generate_scenario_for_session()` service (async, retries, guardrails, fallback flagged and surfaced) used by the UI. Fix the doubled prompt, the final-attempt quality bypass, the parser error accumulation, and propagate `used_fallback` to the UI banner.
3. **Cheaper, more reliable generation** *(P1-13, P1-9, P1-10)*: JSON mode, current model via config, lower temperature and token cap, capped combined retries; one shared bounds table generating prompt guidance + Pydantic validators + guardrail checks; tolerance-based MDE/lift check.
4. **Delete dead weight** *(P2-4, P2-5, P2-6, P2-8)*: unused UI functions, rng extras, Anthropic stub, never-raised exceptions, unused guardrail config; move quiz-session logging out of core; consolidate duplicate CI helpers; rewrite module docstrings to match reality.
5. **Split the UI monolith** *(P2-1)*: `ui/state.py`, `ui/services.py`, one module per phase (`scenario`, `design`, `experiment`, `analysis`, `results`), `main()` as a step registry. Do this *after* steps 1–2 so you're moving less code.

**Exit criteria:** one grading path, one generation path, `ui/streamlit_app.py` under ~300 lines of dispatch, no module documented as doing something it doesn't.

### Phase 3 — The strong UI

With correct grading and a clean structure, invest in experience. Priorities, in order of learning impact:

1. **Close the design→data loop** *(P1-5)*: simulate the duration/sample size the user designed (or the engine's `days_required`), and say so — "You planned 21 days at 10,000 visitors/day; here are your 210,000 rows." Replace the fake blocking `time.sleep` progress bar with an honest "simulating your experiment" step.
2. **Visualizations where they teach** — this is an experimentation education tool with zero charts today:
   - Daily conversion-rate time series for control vs treatment (with cumulative view showing noise settling into signal).
   - Confidence-interval plot for the lift vs the business target — makes the rollout decision visual.
   - Power curve / MDE-vs-sample-size interactive on the design step.
   - Score summary radar/bars by skill area on the results step.
   Plotly is already mentioned in the README; add it for real.
3. **Coherent progress and feedback** — phase stepper with "question 3/6" progress; consistent per-question feedback in both phases; a real end-of-session summary (score by category, review of misses with explanations, CSV/notebook downloads in one place).
4. **Fix the incentive design** — the sidebar "Show Answers" panel currently leaks the entire answer key mid-quiz *(and the analysis step directs users to it)*. Replace with graduated hints: hint → formula → answer-with-explanation, each costing score or simply logged.
5. **Consistent visual language** — the landing page's polish (cards, gradient hero) extended into the quiz; the defined-but-unused CSS classes applied or removed; number inputs without misleading defaults *(the `value=None → min_value` bug)*; graceful error states with a retry action.
6. **Deploy** — Streamlit Cloud deployment with secrets configured, badge in README (the README already promises this).

**Exit criteria:** a first-time visitor can complete a full session on Streamlit Cloud and correctly explain, from the charts alone, why the rollout decision was right.

### Phase 4 — Educational depth

Now the roadmap items that expand what the tool teaches, prioritized by the rigor audit:

1. **Planning & interpretation phases become real** — they're currently ungraded text boxes. Grade them with an LLM rubric call (the `schemas/evaluation.py` DTOs already model this — implement or delete them) or with structured multiple-choice from the bank's 30 ungraded questions.
2. **Unequal allocation done properly** *(E-1)* — correct sample-size math for non-50/50 splits, `SampleSize` type support, scenarios that exercise it.
3. **Statistical breadth** *(E-2, E-4, E-5)* — teach test selection (the auto-selection logic exists; surface it as a question: "which test and why?"); add multiple-testing, peeking/sequential-testing, and Simpson's paradox content; document variance and threshold choices inline where users see results.
4. **Scenario variety regression** *(INFRA-5)* — the promised distributional test over generated scenarios, plus fallback-rate monitoring.
5. **Optional, only if demand exists:** local progress history (file/browser-based), difficulty adaptation from past sessions.

---

## 4. Sequencing rationale & risk notes

- **Phase 0 before everything:** every later phase is multi-file surgery on grading logic; doing it without CI is how the current P0s shipped.
- **Phase 1 before Phase 2:** the P0 fixes are small and shippable individually; the consolidation is invasive. Fixing correctness first means the consolidation can be verified against known-good behavior (and the new AppTest suite).
- **Phase 2 before Phase 3:** building a strong UI on top of the dual quiz system would double the migration cost later. The monolith split is deliberately *last within* Phase 2 so it moves already-cleaned code.
- **Biggest technical risk:** the quiz-engine consolidation (P2-2) touches validation, scoring, question bank, and every UI phase simultaneously. Mitigate by porting question-by-question behind the existing UI, with the AppTest suite from Phase 1 as the harness.
- **Biggest product risk:** Phase 3 scope creep. The chart list is intentionally short (four charts); resist dashboard-building beyond what teaches.

---

## 5. Steady-state definition of done

- [ ] CI (tests + lint) required on every PR; clean-install test run passes
- [ ] All P0 issues closed; P1 statistical items closed or explicitly documented as teaching choices
- [ ] One quiz engine (question bank), one LLM pipeline (with fallback surfaced), one source of truth for every graded number
- [ ] `ui/` is modular; session state has a single owner and reset
- [ ] Simulated data reflects the user's design; every phase gives feedback; four core visualizations live
- [ ] Hints replace the answer-key leak
- [ ] Deployed on Streamlit Cloud, linked from README
- [ ] No module README/docstring describes functionality that doesn't exist
- [ ] Planning/interpretation phases graded or removed; evaluation schemas implemented or deleted

---

**Document version:** 1.0
**Created:** 2026-07-07
**Source review:** `SYSTEM_REVIEW_2026-07.md`
