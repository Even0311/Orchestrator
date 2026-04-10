# Evaluator Code Review — round-0062

**Task Key:** P33-T3
**Title:** Rolling degradation-rate tracking with auto-fallback threshold

## Acceptance Criteria
1. A degradation tracker model exists that stores per-tick-type counters: total_attempts, failure_count, degraded_count, and a timestamped history sufficient to compute a rolling window rate
2. Each route() outcome in simulate_day_bridged is classified into exactly one of: acceptable, degraded, or invalid — classification logic is testable in isolation
3. A rolling-window degradation rate is computable per tick type over a configurable number of past days (default 7)
4. When the rolling degradation rate for a tick type exceeds the configured threshold, simulate_day_bridged skips the LLM call for that tick type and uses the deterministic path instead
5. The auto-fallback-triggered state is recorded in the AppraisalAuditLog (or an attached structure) so that callers can observe when and why auto-fallback was engaged
6. When the rolling window slides past the degraded entries (i.e., enough good days pass or enough days elapse), auto-fallback disengages and the LLM path is retried
7. The tracker is passable as an optional parameter to simulate_day_bridged — callers that do not pass it get the current behavior (no auto-fallback)
8. All existing tests in back/tests/ pass without modification
9. New tests cover: outcome classification, rolling rate computation, threshold-triggered fallback, and window-based recovery

## Review Focus
- Verify the three-class outcome classification is unambiguous — every possible AppraisalAuditEntry state maps to exactly one class
- Verify the rolling window computation is correct at boundary conditions (empty history, exactly at threshold, window shorter than configured)
- Verify auto-fallback does not permanently lock out the LLM path — recovery must be demonstrated in tests
- Verify the tracker does not leak into the settlement layer — it should only observe and gate, never write state
- Verify backward compatibility: simulate_day_bridged without the tracker parameter behaves identically to current behavior
- Verify the tracker is JSON-serializable for cross-day persistence

## Code Changes (git diff)
```diff

diff --git a/back/app/engines/tick_bridge.py b/back/app/engines/tick_bridge.py
index 51f58f8..d4371e6 100644
--- a/back/app/engines/tick_bridge.py
+++ b/back/app/engines/tick_bridge.py
@@ -47,6 +47,7 @@ from app.domain.appraisal_input import (
 from app.domain.appraisal_output import AppraisalOutput
 from app.llm import appraisal_router as _appraisal_router
 from app.llm.appraisal_audit_log import AppraisalAuditEntry, AppraisalAuditLog
+from app.llm.degradation_tracker import DegradationTracker, classify_outcome as _classify_outcome
 from app.domain.enums import EventCategory, RelationshipType, ResidualKind, SocialEventIntensity, SocialEventReciprocity, SocialEventType, Valence
 from app.domain.models import (
     AgentGrowth,
@@ -1481,6 +1482,7 @@ def simulate_day_bridged(
     t4_activation_audit_out: list[T4ActivationAuditRecord] | None = None,
     t4_residual_audit_out: list[T4ResidualCreationAuditRecord] | None = None,
     t4_adjustment_audit_out: list[T4AdjustmentAuditRecord] | None = None,
+    degradation_tracker: Optional[DegradationTracker] = None,
 ) -> "DaySimulationResult":
     """
     Run a full day simulation with the appraisal settlement bridge active.
@@ -1550,19 +1552,35 @@ def simulate_day_bridged(
         social_event_context=None,
         player_context=None,
     )
-    try:
-        _t1_router_result = _appraisal_router.route(_t1_appraisal_input)
-        if _t1_router_result.llm_used:
-            t1_output = _t1_router_result.output
-        else:
-            t1_output = build_signal_from_t1_world_tick(world, profile, state, growth)
-    except Exception:
+    _t1_auto_fallback = (
+        degradation_tracker is not None
+        and degradation_tracker.is_auto_fallback_active(
+            EventCategory.information_exposure.value, world_day
+        )
+    )
+    if _t1_auto_fallback:
         _t1_router_result = None
         t1_output = build_signal_from_t1_world_tick(world, profile, state, growth)
-    if _t1_router_result is not None:
-        _audit_entries.append(_build_audit_entry(
-            world_day, EventCategory.information_exposure, _t1_router_result
-        ))
+    else:
+        try:
+            _t1_router_result = _appraisal_router.route(_t1_appraisal_input)
+            if _t1_router_result.llm_used:
+                t1_output = _t1_router_result.output
+            else:
+                t1_output = build_signal_from_t1_world_tick(world, profile, state, growth)
+        except Exception:
+            _t1_router_result = None
+            t1_output = build_signal_from_t1_world_tick(world, profile, state, growth)
+        if _t1_router_result is not None:
+            _audit_entries.append(_build_audit_entry(
+                world_day, EventCategory.information_exposure, _t1_router_result
+            ))
+            if degradation_tracker is not None:
+                degradation_tracker.record_outcome(
+                    EventCategory.information_exposure.value,
+                    wor
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
