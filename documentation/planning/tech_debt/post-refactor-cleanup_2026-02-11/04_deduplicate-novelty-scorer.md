# Phase 04: Deduplicate NoveltyScorer Similarity Calculation

**PR Title:** `refactor(guardrails): extract similarity helper in NoveltyScorer`
**Risk Level:** Low
**Estimated Effort:** Small (1-2 hours)
**Files Modified:** `llm/guardrails.py`
**Dependencies:** None
**Blocks:** None

---

## Problem

In `llm/guardrails.py`, `NoveltyScorer.score_novelty()` (lines 813-892) computes feature-by-feature similarity **twice**:

1. **Full similarity** (lines 831-866): Compares all 8 features with weighted penalties, iterating over all recent scenarios
2. **Recency-weighted similarity** (lines 873-884): Compares only 3 features (company_type, user_segment, primary_kpi) with recency weights, iterating over all recent scenarios again

The feature comparison logic is duplicated. It should be computed once per scenario and reused.

Additionally, `_extract_features()` (lines 762-811) contains three nearly identical if-elif tier classification blocks for traffic, baseline, and effect size.

---

## Implementation

### Step 1: Add `_classify_tier()` static helper

Add this method to the `NoveltyScorer` class **before** `_extract_features()` (before line 762):

```python
    @staticmethod
    def _classify_tier(value: float, thresholds: list) -> str:
        """
        Classify a numeric value into a tier based on thresholds.

        Args:
            value: The numeric value to classify
            thresholds: List of (threshold, tier_name) tuples in ascending order,
                       followed by a final (None, tier_name) for the highest tier.

        Returns:
            The tier name string
        """
        for threshold, tier_name in thresholds:
            if threshold is None or value < threshold:
                return tier_name
        return thresholds[-1][1]  # Fallback to last tier
```

### Step 2: Simplify `_extract_features()` to use `_classify_tier()`

**Before** (lines 762-811):
```python
    def _extract_features(self, scenario_dto: ScenarioResponseDTO) -> Dict:
        """Extract features from a scenario for comparison."""
        scenario = scenario_dto.scenario
        design_params = scenario_dto.design_params

        # Determine traffic tier
        traffic = design_params.expected_daily_traffic
        if traffic < 1000:
            traffic_tier = "early_stage"
        elif traffic < 10000:
            traffic_tier = "growth"
        elif traffic < 100000:
            traffic_tier = "scale"
        else:
            traffic_tier = "enterprise"

        # Determine baseline tier
        baseline = design_params.baseline_conversion_rate
        if baseline < 0.01:
            baseline_tier = "very_low"
        elif baseline < 0.05:
            baseline_tier = "low"
        elif baseline < 0.15:
            baseline_tier = "medium"
        elif baseline < 0.30:
            baseline_tier = "high"
        else:
            baseline_tier = "very_high"

        # Determine effect size tier
        lift = design_params.target_lift_pct
        if lift < 0.05:
            effect_tier = "incremental"
        elif lift < 0.20:
            effect_tier = "moderate"
        elif lift < 0.50:
            effect_tier = "significant"
        else:
            effect_tier = "transformational"

        return { ... }
```

**After:**
```python
    # Tier classification thresholds (threshold, tier_name)
    _TRAFFIC_TIERS = [
        (1000, "early_stage"),
        (10000, "growth"),
        (100000, "scale"),
        (None, "enterprise"),
    ]

    _BASELINE_TIERS = [
        (0.01, "very_low"),
        (0.05, "low"),
        (0.15, "medium"),
        (0.30, "high"),
        (None, "very_high"),
    ]

    _EFFECT_TIERS = [
        (0.05, "incremental"),
        (0.20, "moderate"),
        (0.50, "significant"),
        (None, "transformational"),
    ]

    def _extract_features(self, scenario_dto: ScenarioResponseDTO) -> Dict:
        """Extract features from a scenario for comparison."""
        scenario = scenario_dto.scenario
        design_params = scenario_dto.design_params

        traffic_tier = self._classify_tier(design_params.expected_daily_traffic, self._TRAFFIC_TIERS)
        baseline_tier = self._classify_tier(design_params.baseline_conversion_rate, self._BASELINE_TIERS)
        effect_tier = self._classify_tier(design_params.target_lift_pct, self._EFFECT_TIERS)

        return {
            "company_type": scenario.company_type.value if hasattr(scenario.company_type, 'value') else str(scenario.company_type),
            "user_segment": scenario.user_segment.value if hasattr(scenario.user_segment, 'value') else str(scenario.user_segment),
            "primary_kpi": scenario.primary_kpi,
            "traffic_tier": traffic_tier,
            "baseline_tier": baseline_tier,
            "effect_tier": effect_tier,
            "alpha": design_params.alpha,
            "power": design_params.power,
        }
```

Place the class-level constants (`_TRAFFIC_TIERS`, `_BASELINE_TIERS`, `_EFFECT_TIERS`) right before `_extract_features()` inside the `NoveltyScorer` class.

### Step 3: Add `_calculate_similarity()` private method

Add this method **after** `_extract_features()` and **before** `score_novelty()`:

```python
    # Feature weights for similarity scoring
    _SIMILARITY_WEIGHTS = {
        "company_type": 0.25,
        "user_segment": 0.15,
        "primary_kpi": 0.10,
        "traffic_tier": 0.10,
        "baseline_tier": 0.10,
        "effect_tier": 0.10,
        "alpha": 0.10,
        "power": 0.10,
    }

    def _calculate_similarity(self, features_a: Dict, features_b: Dict) -> float:
        """
        Calculate similarity between two feature sets.

        Args:
            features_a: Features from the new scenario
            features_b: Features from a recent scenario

        Returns:
            Similarity score from 0.0 (completely different) to 1.0 (identical)
        """
        similarity = 0.0
        for feature, weight in self._SIMILARITY_WEIGHTS.items():
            if features_a.get(feature) == features_b.get(feature):
                similarity += weight
        return similarity
```

### Step 4: Rewrite `score_novelty()` to use `_calculate_similarity()`

**Before** (lines 813-892):
The method has two separate loops over `self.recent_scenarios`, each computing similarity independently.

**After:**
```python
    def score_novelty(self, scenario_dto: ScenarioResponseDTO) -> float:
        """
        Calculate a novelty score for a scenario compared to recent history.

        Args:
            scenario_dto: The scenario to score

        Returns:
            Novelty score from 0 (highly repetitive) to 1 (highly novel)
        """
        if not self.recent_scenarios:
            return 1.0  # First scenario is always novel

        new_features = self._extract_features(scenario_dto)

        # Calculate similarity to each recent scenario in a single pass
        total_similarity = 0.0
        recency_weighted_similarity = 0.0

        for i, recent in enumerate(self.recent_scenarios):
            similarity = self._calculate_similarity(new_features, recent)
            total_similarity += similarity

            # Recency weight: more recent scenarios have higher weight
            recency_weight = (i + 1) / len(self.recent_scenarios)
            # Use only the top-3 features for recency weighting (matching original behavior)
            recency_sim = 0.0
            if new_features["company_type"] == recent["company_type"]:
                recency_sim += 0.25
            if new_features["user_segment"] == recent["user_segment"]:
                recency_sim += 0.15
            if new_features["primary_kpi"] == recent["primary_kpi"]:
                recency_sim += 0.10
            recency_weighted_similarity += recency_sim * recency_weight

        avg_similarity = total_similarity / len(self.recent_scenarios)

        # Combine average and recency-weighted similarity
        combined_similarity = (avg_similarity + recency_weighted_similarity) / 2

        # Convert to novelty score
        novelty = max(0.0, 1.0 - combined_similarity)

        return novelty
```

**Note:** The recency-weighted calculation only uses 3 features (company_type, user_segment, primary_kpi) while the full similarity uses all 8. This matches the original behavior exactly. We keep the recency calculation inline because it uses a different subset of features than `_calculate_similarity()`.

---

## Verification Checklist

1. Run guardrails tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/llm/test_guardrails.py -v
   ```

2. Run novelty-specific tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/llm/test_novelty_scoring.py -v
   ```

3. Verify the tier classification produces identical results by checking:
   - Traffic tier: 999 -> "early_stage", 1000 -> "growth", 9999 -> "growth", 10000 -> "scale", 99999 -> "scale", 100000 -> "enterprise"
   - Baseline tier: 0.009 -> "very_low", 0.01 -> "low", 0.049 -> "low", 0.05 -> "medium", 0.149 -> "medium", 0.15 -> "high", 0.299 -> "high", 0.30 -> "very_high"
   - Effect tier: 0.049 -> "incremental", 0.05 -> "moderate", 0.199 -> "moderate", 0.20 -> "significant", 0.499 -> "significant", 0.50 -> "transformational"

4. Run broader tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q
   ```

---

## What NOT To Do

1. **Do NOT change the similarity weights.** The values (0.25, 0.15, 0.10, etc.) are tuned and must remain identical.

2. **Do NOT change the recency weighting formula.** `(i + 1) / len(self.recent_scenarios)` produces the correct weight where the most recent scenario has weight 1.0.

3. **Do NOT change `record_scenario()` or `get_diversity_suggestions()`.** These methods are not part of this refactoring.

4. **Do NOT make the tier thresholds module-level constants.** They are implementation details of `NoveltyScorer` and should stay as class-level attributes.

5. **Do NOT combine the full similarity and recency-weighted similarity into a single calculation.** They use different feature subsets and must remain separate computations (but in a single loop pass).
