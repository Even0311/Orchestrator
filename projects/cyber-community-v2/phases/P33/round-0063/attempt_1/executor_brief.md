# Executor Brief — round-0063

## Task Contract
**Task Key:** P33-T4
**Title:** Automatic recovery logic with exponential backoff after extended fallback
**Objective:** Extend DegradationTracker with explicit recovery logic so the system does not naively re-enable LLM for all ticks simultaneously after the rolling window slides, but instead probes with controlled retry attempts using exponential backoff when repeated failures persist.

**Exact Scope:**
- Add recovery state tracking to DegradationTracker — track when auto-fallback was activated, how many consecutive fallback-to-failure cycles have occurred per tick type, and when the next probe retry is allowed.
- Implement a probe-retry mechanism: when auto-fallback is active and a configurable cooldown period has elapsed, allow a single LLM probe call for that tick type on the next day. If the probe succeeds (acceptable outcome), disengage auto-fallback. If it fails, increment the consecutive-failure counter and apply exponential backoff to the next cooldown.
- Integrate the probe-retry decision into simulate_day_bridged's auto-fallback check points (T1, T2, T4) — the existing is_auto_fallback_active checks must be replaced or augmented with a should_attempt_probe query that accounts for backoff timing.
- Ensure that probe outcomes ARE recorded in the tracker (unlike regular auto-fallback days where outcomes are not recorded), so the probe result feeds back into the degradation rate correctly.
- Add exponential backoff with a configurable base cooldown (default: 1 day), multiplier (default: 2), and maximum cooldown cap (default: 14 days).
- Add a reset mechanism: a single acceptable probe outcome resets the consecutive-failure counter to zero and disengages auto-fallback for that tick type.
- Write tests covering: (a) probe fires after cooldown expires, (b) successful probe disengages fallback and resets counter, (c) failed probe doubles the cooldown, (d) cooldown respects the max cap, (e) multi-day simulation showing the full fallback->backoff->probe->recovery cycle, (f) multi-day simulation showing persistent failure with escalating backoff.
- Update AppraisalAuditLog to include probe-retry metadata: whether a probe was attempted on each tick type, and the current backoff state.

**Constraints:**
- DegradationTracker must remain a serializable Pydantic model — all new state must be JSON-serializable via model_dump() and reconstructible via model_validate().
- The tracker remains a pure data structure — it observes and tracks state but does not call route() or any LLM code.
- Do not change the existing OutcomeClass, DayTickRecord, classify_outcome, or compute_rolling_rate signatures or behavior — these are used by T3 tests.
- Do not modify AppraisalSignal v1 fields.
- Do not expand bridge coverage to deferred ticks (T3/T5/T6/T7/T8).
- All new code must be importable with no side effects — no LLM call, no file I/O at import time.
- Tests must mock appraisal_router.route (no real LLM calls in tests).

**Forbidden Files (DO NOT modify):**
- `back/app/domain/enums.py`
- `back/app/engines/appraisal_settlement.py`
- `back/app/engines/growth_synthesizer.py`
- `back/app/engines/relationship_synthesizer.py`
- `back/app/engines/relationship_drift.py`
- `back/app/engines/growth_stage_evolver.py`
- `back/app/engines/world_continuity.py`
- `back/app/engines/deterministic_fallback.py`
- `back/app/engines/influence_action_generator.py`
- `back/app/llm/acceptance_rules.py`
- `back/app/llm/shadow_runner.py`
- `back/app/llm/comparison_harness.py`
- `back/app/llm/failure_taxonomy.py`
- `back/app/llm/validation_gate.py`
- `back/app/llm/response_parser.py`
- `back/app/seed/**`
- `back/app/domain/appraisal_input.py`
- `back/app/domain/appraisal_output.py`
- `front/**`
- `docs/**`

**Non-Goals (DO NOT do):**
- No changes to the deterministic fallback logic itself — only when/whether the LLM path is attempted.
- No new tick types or bridge expansion.
- No LLM prompt changes.
- No UI or API changes.
- No changes to how outcomes are classified (OutcomeClass taxonomy is frozen from T3).
- No persistence layer — the tracker is still in-memory, serializable but not auto-saved to disk.
- No alerting or notification system — observability is limited to audit log fields.

**Acceptance Criteria:**
- DegradationTracker has new fields for per-tick-type recovery state (fallback_activated_day, consecutive_failure_cycles, next_probe_day) that serialize/deserialize correctly via model_dump()/model_validate().
- A new method (e.g. should_probe) returns True only when auto-fallback is active AND the current world_day >= next_probe_day for that tick type.
- simulate_day_bridged correctly performs a probe LLM call (via route()) when should_probe is True, instead of unconditionally skipping.
- A successful probe (acceptable outcome) resets consecutive_failure_cycles to 0 and disengages auto-fallback for that tick type.
- A failed probe (degraded or invalid outcome) increments consecutive_failure_cycles and sets next_probe_day using exponential backoff: base_cooldown * (multiplier ^ consecutive_failure_cycles), capped at max_cooldown.
- Default configuration: base_cooldown=1, multiplier=2, max_cooldown=14.
- AppraisalAuditLog includes per-tick-type probe metadata (whether a probe was attempted, current backoff state).
- All existing tests in test_p33_t3_degradation_tracker.py continue to pass without modification.
- New test file exists with tests covering: probe fires after cooldown, successful probe resets state, failed probe escalates backoff, max cap is respected, full multi-day fallback-probe-recovery cycle, full multi-day persistent-failure escalation cycle.
- python -m pytest tests/ -v passes with zero failures.

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
