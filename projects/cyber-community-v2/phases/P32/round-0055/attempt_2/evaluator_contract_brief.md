# Evaluator Contract Review — round-0055

**Task Key:** P32-T3
**Title:** Complete T4 appraisal-to-residual pipeline: break bootstrapping deadlock

## Proposed Acceptance Criteria
1. {'id': 'ac-1', 'description': 'All 900 existing tests pass (python3 -m pytest tests/ -v). Zero regressions.', 'verification': 'python3 -m pytest tests/ -v shows 900 passed, 0 failed.'}
2. {'id': 'ac-2', 'description': 'All 21 tests in test_t4_threshold_calibration.py pass, including the 3 that failed in the previous attempt.', 'verification': 'python3 -m pytest tests/test_t4_threshold_calibration.py -v shows 21 passed.'}
3. {'id': 'ac-3', 'description': "A qualifying social event (confrontation or withdrawal) on a day with NO carried relational residuals produces at least one relational residual in the day's pending_residuals output.", 'verification': 'New test: run simulate_day_bridged with a confrontation event and initial_residuals=[], verify pending_residuals contains a ResidualEntry with kind=relational.'}
4. {'id': 'ac-4', 'description': 'The relational residual produced in ac-3 is available as a carried residual on the next day, enabling _adjust_t4 to fire and potentially open the wake chain gate if another qualifying event occurs.', 'verification': "New test: two-day sequence — day 1 confrontation with no residuals → produces relational residual; day 2 confrontation with day 1's pending_residuals as initial_residuals → _adjust_t4 invoked (adjustment_audit shows invoked=True)."}
5. {'id': 'ac-5', 'description': 'Without a qualifying social event, the T4 path produces no relational residual regardless of carried residuals (default positive path unchanged).', 'verification': 'Existing test test_no_qualifying_event_no_t4_residual continues to pass.'}
6. {'id': 'ac-6', 'description': "The bootstrapping deadlock comment in _adjust_t4 docstring ('currently dormant') and the 'STRUCTURALLY CLOSED GATE' comment in simulate_day_bridged are updated to reflect the new reality.", 'verification': "Grep for 'currently dormant' and 'STRUCTURALLY CLOSED GATE' in tick_bridge.py returns zero matches."}

## Proposed Review Focus
- Verify that the mechanism for creating the initial/seed relational residual works through the settlement contract (aftershock_days > 0 → create_residual_from_appraisal) rather than bypassing it.
- Verify that the 3 previously-failing tests pass: test_collision_with_residual_t4_absorption_upgraded_to_partial, test_wake_gate_closed_no_t4_residual_without_carried_residual, test_wake_chain_decays_after_gate_opens. These define the calibrated contract.
- Verify that the composition audit fields (t4_absorption, wake_chain_gate_open) are truthful — especially that t4_absorption still reports 'surface' when no carried residual is present (test_collision_t4_absorption_stays_surface_without_residual).
- Confirm the seed residual mechanism does not create unbounded residual chains — the new residual should have aftershock_days=1 (or similar short decay) so it does not self-sustain indefinitely.
- Check that no changes were made to forbidden files.

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
