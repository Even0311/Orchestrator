# Evaluator Contract Review — round-0062

**Task Key:** P33-T3
**Title:** Rolling degradation-rate tracking with auto-fallback threshold

## Proposed Acceptance Criteria
1. A degradation tracker model exists that stores per-tick-type counters: total_attempts, failure_count, degraded_count, and a timestamped history sufficient to compute a rolling window rate
2. Each route() outcome in simulate_day_bridged is classified into exactly one of: acceptable, degraded, or invalid — classification logic is testable in isolation
3. A rolling-window degradation rate is computable per tick type over a configurable number of past days (default 7)
4. When the rolling degradation rate for a tick type exceeds the configured threshold, simulate_day_bridged skips the LLM call for that tick type and uses the deterministic path instead
5. The auto-fallback-triggered state is recorded in the AppraisalAuditLog (or an attached structure) so that callers can observe when and why auto-fallback was engaged
6. When the rolling window slides past the degraded entries (i.e., enough good days pass or enough days elapse), auto-fallback disengages and the LLM path is retried
7. The tracker is passable as an optional parameter to simulate_day_bridged — callers that do not pass it get the current behavior (no auto-fallback)
8. All existing tests in back/tests/ pass without modification
9. New tests cover: outcome classification, rolling rate computation, threshold-triggered fallback, and window-based recovery

## Proposed Review Focus
- Verify the three-class outcome classification is unambiguous — every possible AppraisalAuditEntry state maps to exactly one class
- Verify the rolling window computation is correct at boundary conditions (empty history, exactly at threshold, window shorter than configured)
- Verify auto-fallback does not permanently lock out the LLM path — recovery must be demonstrated in tests
- Verify the tracker does not leak into the settlement layer — it should only observe and gate, never write state
- Verify backward compatibility: simulate_day_bridged without the tracker parameter behaves identically to current behavior
- Verify the tracker is JSON-serializable for cross-day persistence

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
