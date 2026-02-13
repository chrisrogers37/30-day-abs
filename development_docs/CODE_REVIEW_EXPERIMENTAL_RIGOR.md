# Code Review: Experimental Rigor Assessment

**Date:** January 2025
**Reviewer:** Advanced Data Science Perspective
**Branch:** `claude/review-project-codebase-I80YU`
**Status:** Review Complete — Partially addressed by tech debt remediation (PRs #9-#24, Feb 2026)

> **Staleness warning:** Line number references in this document are from January 2025. Code has been refactored significantly since then — line numbers are approximate. Fisher's exact and chi-square issues were fixed in PR #9 (scipy integration). See updated status markers below.

---

## Overall Assessment: Strong Foundation with Minor Refinements Needed

The codebase demonstrates solid understanding of A/B testing principles and statistical foundations. This review evaluates the implementation through the lens of teaching and evaluating experimental principles.

---

## 1. Statistical Test Selection (`core/analyze.py:15-100`)

### Strengths
- ✅ Correct implementation of the expected cell count < 5 rule for Fisher's exact test
- ✅ Proper consideration of normal approximation validity (np ≥ 5, n(1-p) ≥ 5)
- ✅ Good separation between test selection logic and test execution
- ✅ Excellent transparency via `StatisticalTestSelection` dataclass with reasoning

### Issues to Address

| Issue | Location | Severity | Recommendation |
|-------|----------|----------|----------------|
| **Chi-square threshold too conservative** | Line 63 | Medium | The threshold `min_sample < 30` for chi-square vs z-test is overly conservative. The z-test normal approximation is valid when np ≥ 10, not necessarily n ≥ 30. Consider checking the actual np and n(1-p) conditions instead of a blanket sample size threshold. |
| **~~Fisher's exact falls back to chi-square~~** | ~~Line 286~~ | ~~High~~ | ✅ **FIXED in PR #9** — Now uses `scipy.stats.fisher_exact` directly with no fallback. |
| **~~Chi-square p-value approximation~~** | ~~Lines 446-484~~ | ~~Medium~~ | ✅ **FIXED in PR #9** — Now uses `scipy.stats.chi2.sf` for accurate p-values. |

### Example of Excellent Design

The `StatisticalTestSelection` dataclass provides excellent transparency:

```python
StatisticalTestSelection(
    test_type="fisher_exact",
    reasoning="Fisher's exact test selected: One or more expected cell
              counts are below 5 (min expected: 3.2), which violates
              chi-square assumptions.",
    sample_size_adequate=True,
    assumptions_met=True,
    alternative_tests=["chi_square", "two_proportion_z"],
    min_expected_cell_count=3.2
)
```

This is **excellent for teaching** - students see *why* a test was chosen, not just which one.

---

## 2. Sample Size Calculations (`core/design.py:17-70`)

### Strengths
- ✅ Correct two-proportion z-test formula implementation
- ✅ Proper handling of z-scores for common alpha values (1.96, 2.576, 1.645)
- ✅ Achieved power calculation included
- ✅ Days required calculation based on traffic

### Issues to Address

| Issue | Location | Severity | Recommendation |
|-------|----------|----------|----------------|
| **Pooled variance assumption** | Line 49-51 | Low | The formula uses unpooled variance `[p1(1-p1) + p2(1-p2)]`. This is the **more conservative** approach, which is fine, but differs from some textbooks that use pooled variance under H0. Consider documenting this design choice. |
| **Unequal allocation not fully supported** | Line 54-56 | Medium | `total_n = 2 * n_per_arm` assumes 50/50 split. For unequal allocation (e.g., 80/20), the formula should account for allocation ratios using: `n_total = n_1 + n_2` where the variance term adjusts for unequal group sizes. |

### Formula Reference

The implemented formula:
```
n = (z_α + z_β)² × [p₁(1-p₁) + p₂(1-p₂)] / (p₂-p₁)²
```

This is correct for equal allocation with unpooled variance estimation.

---

## 3. Effect Size Metrics (`core/analyze.py:392-410`)

### Strengths
- ✅ Correct implementation of Cohen's h (arcsine transformation)
- ✅ Appropriate for proportion comparisons

### Educational Enhancement Needed

The current thresholds in `_generate_recommendation` use 0.1 and 0.2, but standard Cohen's h interpretations are:

| Cohen's h | Interpretation |
|-----------|----------------|
| |h| < 0.20 | Small effect |
| 0.20 ≤ |h| < 0.50 | Medium effect |
| 0.50 ≤ |h| < 0.80 | Large effect |
| |h| ≥ 0.80 | Very large effect |

Consider aligning thresholds or adding this interpretation guide to the UI.

---

## 4. Confidence Interval Calculation (`core/analyze.py:360-389`)

### Strengths
- ✅ Uses unpooled standard error (Wald interval)
- ✅ Correct margin of error calculation
- ✅ Proper z-score application

### Issues to Address

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| **Wald interval can exceed [0,1] bounds** | Medium | For proportions near 0 or 1, Wald CIs can produce impossible values (e.g., CI of [-0.02, 0.03] for a proportion). Consider adding bounds clipping: `max(0, lower), min(1, upper)` or noting this limitation. Wilson score intervals are more robust for edge cases. |
| **Continuity correction not applied** | Low | For educational completeness, could mention that continuity correction (Yates' correction) improves accuracy for small samples, though its use is debated. |

---

## 5. Question Bank Educational Content (`core/question_bank.py`)

### Strengths
- ✅ Excellent coverage of key concepts: MDE, sample size, hypothesis testing
- ✅ Good progression from EASY → MEDIUM → HARD difficulty
- ✅ Practical application questions (e.g., `small_sample_test` scenario)
- ✅ Planning questions address pre-registration, guardrail metrics
- ✅ Interpretation questions cover practical vs. statistical significance
- ✅ Skills-tested metadata enables targeted learning

### Educational Gaps to Fill

| Missing Concept | Priority | Suggested Question |
|-----------------|----------|---------------------|
| **Multiple testing correction** | High | "You're testing 5 variants against control. What alpha should each test use to maintain family-wise error rate (FWER) = 0.05?" |
| **Sequential testing / peeking** | High | "You check results daily and stop when p < 0.05. Why does this inflate false positive rates?" |
| **Regression to the mean** | Medium | "Last month's top-performing segment showed 50% lift. This month it's 10%. What statistical phenomenon might explain this?" |
| **Simpson's paradox** | Medium | "Overall treatment shows -5% lift, but every user segment shows positive lift. What's happening?" |
| **Network effects / SUTVA** | Medium | "In a social app experiment, treating user A might affect user B's behavior. What assumption is violated?" |
| **Minimum detectable effect tradeoffs** | Medium | "You can only run the test for 2 weeks. What MDE can you detect with 80% power?" |

---

## 6. Simulation Fidelity (`core/simulate.py`)

### Strengths
- ✅ Realistic effect variation (70/20/8/2 distribution for full/partial/no/negative effects)
- ✅ User-level data generation with realistic features (device, source, timestamp)
- ✅ Seed-based reproducibility for consistent testing
- ✅ Session duration and page views correlated with conversion

### Issues to Address

| Issue | Location | Severity | Recommendation |
|-------|----------|----------|----------------|
| **Fixed 30-day simulation** | Line 69 | Medium | `total_traffic = params.expected_daily_traffic * 30` ignores the calculated sample size. Should use `sample_size.days_required` for consistency with the design phase. |
| **Independent observations assumed** | Entire file | Low | For advanced users, could note this assumes no user revisits (SUTVA holds). Real experiments often have repeated measures requiring different analysis approaches. |

---

## 7. Educational Principles Assessment

| Principle | Implementation | Grade | Notes |
|-----------|---------------|-------|-------|
| **Pre-registration importance** | ✅ Covered in planning questions | A | `pre_registration` question explains HARKing prevention |
| **Power vs. significance distinction** | ✅ Power calculations, low-power warnings | A | Clear recommendations when power < 0.8 |
| **Practical vs. statistical significance** | ✅ MDE comparison, CI-based decisions | A | `statistical_vs_practical` question addresses this directly |
| **Multiple testing awareness** | ⚠️ Mentioned but no correction questions | B | Should add Bonferroni/FDR questions |
| **Effect size reporting** | ✅ Cohen's h calculated and reported | A | Included in all analysis results |
| **CI interpretation over p-values** | ✅ CI-based rollout decisions | A | `make_rollout_decision` uses CI bounds |
| **Test assumption checking** | ✅ Automatic test selection with reasoning | A | Excellent transparency in selection |
| **Guardrail metrics** | ✅ Planning question included | A | Addresses unintended consequences |

---

## 8. Code Quality Observations

### Well-Designed Patterns

1. **Separation of concerns**: Test selection logic separate from test execution
2. **Dataclass usage**: Clean data structures for results and parameters
3. **Comprehensive typing**: Good use of type hints throughout
4. **Detailed docstrings**: Functions well-documented with examples

### Areas for Improvement

1. **Scipy dependency**: Some statistical functions are approximated when scipy would be more accurate
2. **Error messages**: Could be more educational (explain *why* something failed)
3. **Edge case handling**: Some division-by-zero checks could be more robust

---

## Summary Recommendations

### High Priority
1. **~~Fix Fisher's exact test fallback~~** — ✅ `COMPLETED` (PR #9) — Now uses `scipy.stats.fisher_exact` directly
2. **Add multiple testing / Bonferroni questions** — `PENDING` — Critical gap in educational content
3. **Support unequal allocation properly** — `PENDING` — Formula needs adjustment for non-50/50 splits

### Medium Priority
4. **Add sequential testing education** — `PENDING` — Peeking bias is a common real-world problem
5. **~~Use scipy.stats when available~~** — ✅ `COMPLETED` (PR #9) — Both `fisher_exact` and `chi2` use scipy
6. **Add CI bounds checking** — `PENDING` — Prevent impossible confidence intervals
7. **Sync simulation duration with design** — `PENDING` — Use calculated days_required, not hardcoded 30

### Low Priority (Polish)
8. **Document pooled vs unpooled variance choice** — `PENDING` — Educational transparency
9. **Add Cohen's h interpretation guidelines** — `PENDING` — Help users understand effect sizes
10. **Note SUTVA assumptions** — `PENDING` — Important caveat for advanced users

---

## Verdict

This is a **well-designed educational tool** that correctly implements core A/B testing concepts. The automatic test selection with reasoning is particularly valuable for teaching - students learn not just which test to use, but *why*.

The main gaps are in advanced topics (multiple testing, sequential analysis) which would elevate this from a solid foundation to a comprehensive learning platform. The statistical implementations are sound for educational purposes, though production use would benefit from scipy integration for edge cases.

**Recommendation:** Merge with confidence. Address high-priority items in follow-up PRs.

---

## Appendix: Key File References

| File | Purpose | Lines of Interest |
|------|---------|-------------------|
| `core/analyze.py` | Statistical analysis | 15-100 (test selection), 144-201 (z-test), 360-389 (CI) |
| `core/design.py` | Sample size calculation | 17-70 (main formula), 119-148 (power) |
| `core/simulate.py` | Data simulation | 15-92 (trial simulation), 69 (duration issue) |
| `core/question_bank.py` | Educational content | 88-200 (design), 400-597 (planning), 604-700 (interpretation) |
| `core/types.py` | Data structures | `StatisticalTestSelection`, `AnalysisResult` |
