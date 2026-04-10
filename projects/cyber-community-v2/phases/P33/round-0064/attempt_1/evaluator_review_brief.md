# Evaluator Code Review — round-0064

**Task Key:** P33-T5
**Title:** Multi-day drift audit: 30+ day state, growth, residual, and degradation trends

## Acceptance Criteria
1. A new file back/tools/audit_drift.py exists and is executable via `python back/tools/audit_drift.py --days 30`.
2. Running `python back/tools/audit_drift.py --days 30` completes without error and produces a JSON file in back/tools/audit_outputs/.
3. The output JSON contains a 'trajectories' object with keys for all 7 state fields and all 6 growth fields, each containing an array of per-day values with length equal to the number of simulated days plus the seed day.
4. The output JSON contains a 'residual_stacking' object with a per-day array of residual counts and a 'verdicts' sub-object.
5. The output JSON contains a 'drift_verdicts' object with one entry per tracked dimension, each having a 'status' field (pass/warn/fail) and a 'reasons' array.
6. The output JSON contains a top-level 'summary' object with an 'overall_status' field (pass/warn/fail).
7. A new test file back/tests/test_p33_t5_drift_audit.py exists.
8. All tests in back/tests/test_p33_t5_drift_audit.py pass via `python -m pytest back/tests/test_p33_t5_drift_audit.py -v`.
9. The test file includes at least one test that verifies monotonic-drift detection flags a synthetic trajectory that moves in one direction for 10+ consecutive days.
10. The test file includes at least one test that verifies saturation-lock detection flags a synthetic trajectory stuck at ceiling for 5+ consecutive days.
11. The test file includes at least one test that verifies residual-stacking detection flags monotonically non-decreasing residual counts over 7+ consecutive days.
12. The test file includes at least one end-to-end test that runs the audit for 30 days on the deterministic backbone and verifies the output JSON structure.
13. All existing tests pass: `python -m pytest back/tests/ -v` has no regressions.

## Review Focus
- Verify drift-detection pure functions are correct: monotonic detection should not false-positive on oscillating values, saturation detection should correctly handle values that briefly dip below threshold.
- Verify residual stacking reads from DaySnapshot.pending_residuals correctly and counts are accurate.
- Verify the audit tool does not import or instantiate any LLM client — it should work purely on the deterministic backbone unless an optional tracker is injected.
- Verify no forbidden files were modified.
- Verify test coverage includes edge cases: empty trajectories, single-day runs, exactly-at-threshold values.
- Verify JSON output is self-contained and machine-parseable — no embedded markdown, no prose-only sections.

## Code Changes (git diff)
```diff

diff --git a/back/tests/test_p33_t5_drift_audit.py b/back/tests/test_p33_t5_drift_audit.py
new file mode 100644
index 0000000..d04406b
--- /dev/null
+++ b/back/tests/test_p33_t5_drift_audit.py
@@ -0,0 +1,404 @@
+"""
+Tests for P33-T5: Multi-day drift audit tool.
+
+Verifies:
+  (a) The audit script runs to completion on the deterministic backbone for 30 days
+      without error, and the output JSON is well-formed with all required sections.
+  (b) Monotonic-drift detection correctly flags synthetic trajectories.
+  (c) Unbounded-growth detection correctly flags trajectories with large cumulative delta.
+  (d) Saturation-lock detection flags trajectories stuck at ceiling or floor.
+  (e) Residual-stacking detection flags synthetic residual count histories.
+  (f) The top-level summary and overall_status are present and correct.
+"""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+# ── Path setup ─────────────────────────────────────────────────────────────────
+TESTS_DIR = Path(__file__).resolve().parent
+BACK_DIR  = TESTS_DIR.parent
+TOOLS_DIR = BACK_DIR / "tools"
+sys.path.insert(0, str(BACK_DIR))
+sys.path.insert(0, str(TOOLS_DIR))
+
+import pytest
+
+from tools.audit_drift import (
+    detect_monotonic_drift,
+    detect_unbounded_growth,
+    detect_saturation_lock,
+    detect_residual_stacking,
+    build_dimension_verdict,
+    build_residual_verdict,
+    run_drift_audit,
+)
+
+
+# ── (b) Monotonic-drift detection ─────────────────────────────────────────────
+
+
+class TestDetectMonotonicDrift:
+    def test_rising_10_consecutive_days_flagged(self):
+        """A trajectory rising for exactly 10 consecutive days should be flagged."""
+        values = list(range(50, 61))   # [50, 51, ..., 60] — 11 points, 10 steps up
+        flags = detect_monotonic_drift(values, window=10)
+        assert len(flags) >= 1
+        assert flags[0]["direction"] == "rising"
+        assert flags[0]["length"] >= 10
+
+    def test_falling_10_consecutive_days_flagged(self):
+        """A trajectory falling for 10 consecutive days should be flagged."""
+        values = list(range(60, 49, -1))   # [60, 59, ..., 50]
+        flags = detect_monotonic_drift(values, window=10)
+        assert len(flags) >= 1
+        assert flags[0]["direction"] == "falling"
+        assert flags[0]["length"] >= 10
+
+    def test_short_streak_below_window_not_flagged(self):
+        """A streak shorter than the window should not be flagged."""
+        values = [50, 51, 52, 53, 54, 50, 50]   # 4-step rise then drop
+        flags = detect_monotonic_drift(values, window=10)
+        assert flags == []
+
+    def test_flat_trajectory_not_flagged(self):
+        """Flat (all-same) values should not be flagged."""
+        values = [55] * 15
+        flags = detect_monotonic_drift(values, window=10)
+        assert flags == []
+
+    def test_mixed_trajectory_with_long_run_flagged(self):
+        """A mixed trajectory with a 12-day run should flag
...(truncated)
```

## Your Task
1. Check each acceptance criterion against the actual code changes
2. Pay special attention to the review focus items
3. If existing test files were modified, examine whether the modifications are justified
4. Verify tests pass and no regressions were introduced

Write `review_verdict.json` with:
- `verdict` — PASS, FAIL, or REVISION_REQUIRED
- `confidence` — high, medium, or low
- `met_criteria` — list of criteria that passed
- `unmet_criteria` — list of criteria that failed
- `blocker_fixes` — must-fix issues (empty if PASS)
- `non_blocking_suggestions` — nice-to-have improvements
- `rationale` — explanation of verdict
