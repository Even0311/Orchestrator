# Evaluator Contract Review — round-0063

**Task Key:** P33-T4
**Title:** Automatic recovery logic with exponential backoff after extended fallback

## Proposed Acceptance Criteria
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

## Proposed Review Focus
- Verify that existing DegradationTracker behavior is preserved — compute_rolling_rate and is_auto_fallback_active must not change semantics for callers that do not use recovery features.
- Check that probe outcomes are recorded in the tracker so they feed into the rolling rate correctly.
- Verify exponential backoff arithmetic: base * multiplier^cycles, with cap. Off-by-one errors in day counting are common.
- Ensure the probe integration in simulate_day_bridged does not break the existing auto-fallback skip logic — when should_probe is False, behavior must be identical to pre-T4 code.
- Check serialization round-trip: model_dump() -> model_validate() must preserve all recovery state fields.
- Verify that a single acceptable probe is sufficient to fully disengage fallback (no partial states).

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
