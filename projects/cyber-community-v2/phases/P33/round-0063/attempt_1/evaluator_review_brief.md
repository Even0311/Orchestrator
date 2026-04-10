# Evaluator Code Review — round-0063

**Task Key:** P33-T4
**Title:** Automatic recovery logic with exponential backoff after extended fallback

## Acceptance Criteria
1. DegradationTracker has new fields for per-tick-type recovery state (fallback_activated_day, consecutive_failure_cycles, next_probe_day) that serialize/deserialize correctly via model_dump()/model_validate().
2. A new method (e.g. should_probe) returns True only when auto-fallback is active AND the current world_day >= next_probe_day for that tick type.
3. simulate_day_bridged correctly performs a probe LLM call (via route()) when should_probe is True, instead of unconditionally skipping.
4. A successful probe (acceptable outcome) resets consecutive_failure_cycles to 0 and disengages auto-fallback for that tick type.
5. A failed probe (degraded or invalid outcome) increments consecutive_failure_cycles and sets next_probe_day using exponential backoff: base_cooldown * (multiplier ^ consecutive_failure_cycles), capped at max_cooldown.
6. Default configuration: base_cooldown=1, multiplier=2, max_cooldown=14.
7. AppraisalAuditLog includes per-tick-type probe metadata (whether a probe was attempted, current backoff state).
8. All existing tests in test_p33_t3_degradation_tracker.py continue to pass without modification.
9. New test file exists with tests covering: probe fires after cooldown, successful probe resets state, failed probe escalates backoff, max cap is respected, full multi-day fallback-probe-recovery cycle, full multi-day persistent-failure escalation cycle.
10. python -m pytest tests/ -v passes with zero failures.

## Review Focus
- Verify that existing DegradationTracker behavior is preserved — compute_rolling_rate and is_auto_fallback_active must not change semantics for callers that do not use recovery features.
- Check that probe outcomes are recorded in the tracker so they feed into the rolling rate correctly.
- Verify exponential backoff arithmetic: base * multiplier^cycles, with cap. Off-by-one errors in day counting are common.
- Ensure the probe integration in simulate_day_bridged does not break the existing auto-fallback skip logic — when should_probe is False, behavior must be identical to pre-T4 code.
- Check serialization round-trip: model_dump() -> model_validate() must preserve all recovery state fields.
- Verify that a single acceptable probe is sufficient to fully disengage fallback (no partial states).

## Code Changes (git diff)
```diff

diff --git a/back/app/engines/tick_bridge.py b/back/app/engines/tick_bridge.py
index d4371e6..36fa5da 100644
--- a/back/app/engines/tick_bridge.py
+++ b/back/app/engines/tick_bridge.py
@@ -47,7 +47,11 @@ from app.domain.appraisal_input import (
 from app.domain.appraisal_output import AppraisalOutput
 from app.llm import appraisal_router as _appraisal_router
 from app.llm.appraisal_audit_log import AppraisalAuditEntry, AppraisalAuditLog
-from app.llm.degradation_tracker import DegradationTracker, classify_outcome as _classify_outcome
+from app.llm.degradation_tracker import (
+    DegradationTracker,
+    OutcomeClass as _OutcomeClass,
+    classify_outcome as _classify_outcome,
+)
 from app.domain.enums import EventCategory, RelationshipType, ResidualKind, SocialEventIntensity, SocialEventReciprocity, SocialEventType, Valence
 from app.domain.models import (
     AgentGrowth,
@@ -1558,10 +1562,44 @@ def simulate_day_bridged(
             EventCategory.information_exposure.value, world_day
         )
     )
-    if _t1_auto_fallback:
+    _t1_probe = False
+    if _t1_auto_fallback and degradation_tracker is not None:
+        degradation_tracker.notify_auto_fallback_active(
+            EventCategory.information_exposure.value, world_day
+        )
+        _t1_probe = degradation_tracker.should_probe(
+            EventCategory.information_exposure.value, world_day
+        )
+    if _t1_auto_fallback and not _t1_probe:
+        # Regular auto-fallback: skip route(), outcome NOT recorded
         _t1_router_result = None
         t1_output = build_signal_from_t1_world_tick(world, profile, state, growth)
+    elif _t1_auto_fallback and _t1_probe:
+        # Probe attempt: call route() to test recovery; outcome IS recorded
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
+            _t1_probe_outcome = _classify_outcome(_audit_entries[-1])
+            degradation_tracker.record_outcome(
+                EventCategory.information_exposure.value, world_day, _t1_probe_outcome
+            )
+        else:
+            _t1_probe_outcome = _OutcomeClass.invalid
+        degradation_tracker.record_probe_outcome(
+            EventCategory.information_exposure.value, world_day, _t1_probe_outcome
+        )
     else:
+        # Normal path: no auto-fallback, call route() unconditionally
         try:
             _t1_router_result = _appraisal_router.route(_t1_
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
