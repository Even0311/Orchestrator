# Evaluator Contract Review — round-0064

**Task Key:** P33-T5
**Title:** Multi-day drift audit: 30+ day state, growth, residual, and degradation trends

## Proposed Acceptance Criteria
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

## Proposed Review Focus
- Verify drift-detection pure functions are correct: monotonic detection should not false-positive on oscillating values, saturation detection should correctly handle values that briefly dip below threshold.
- Verify residual stacking reads from DaySnapshot.pending_residuals correctly and counts are accurate.
- Verify the audit tool does not import or instantiate any LLM client — it should work purely on the deterministic backbone unless an optional tracker is injected.
- Verify no forbidden files were modified.
- Verify test coverage includes edge cases: empty trajectories, single-day runs, exactly-at-threshold values.
- Verify JSON output is self-contained and machine-parseable — no embedded markdown, no prose-only sections.

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
