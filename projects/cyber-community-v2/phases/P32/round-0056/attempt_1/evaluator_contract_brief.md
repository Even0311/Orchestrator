# Evaluator Contract Review — round-0056

**Task Key:** P32-T4
**Title:** Unfreeze _adjust_t4() wake chain: carried relational residuals must modify relationship state

## Proposed Acceptance Criteria
1. A multi-day test (3+ days) with qualifying social events demonstrates that _adjust_t4() is invoked=True on at least one day (verified via T4AdjustmentAuditRecord)
2. The T4AdjustmentAuditRecord shows at least one field changed by _adjust_t4() (changed_fields is non-empty)
3. The wake chain gate (_t4_wake_chain_gate_open) opens on at least one day — verified by a relational residual being created with kind=relational in the simulation output
4. Relationship state (trust or closeness) differs from initial values after the multi-day simulation — the T4 signal actually settles into relationship state
5. Relational residuals are carried across at least one day boundary — i.e., a residual created on day N appears in carried_residuals on day N+1
6. The old test asserting zero relational residuals is updated to reflect the new reality (T4 now produces relational residuals when qualifying events are present)
7. All 900 existing tests pass (allowing for the intentional update to the zero-residual assertion test)
8. python3 -m pytest tests/ -v passes from the back/ directory with zero failures

## Proposed Review Focus
- Verify _adjust_t4() is reached through the normal pipeline path (simulate_day_bridged → _select_residual → _adjust_t4), not via test-only shortcuts
- Confirm the wake chain gate conditions are unchanged — absorption >= partial, negative valence, trust_shift in mild/strong_decrease
- Check that the multi-day test carries residuals properly between days (initial_residuals parameter fed from previous day's output)
- Verify that the updated zero-residual test still validates a meaningful contract (not just deleted or made trivially true)
- Confirm no forbidden files were modified
- Check that _adjust_t4() internal logic was not rewritten — only activation/wiring changes are acceptable in tick_bridge.py
- Verify the test uses qualifying social events (confrontation/withdrawal) through the standard world snapshot, not injected signals

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
