# Executor Brief — round-0056

## Task Contract
**Task Key:** P32-T4
**Title:** Unfreeze _adjust_t4() wake chain: carried relational residuals must modify relationship state
**Objective:** Make _adjust_t4() functionally active so that when a relational residual is carried from a prior day into a day with a T4 signal, the residual biases the T4 appraisal signal (absorption upgrade, valence/arousal/trust/closeness shifts), the wake chain gate opens, settlement applies the adjusted signal to relationship state, and a new relational residual is created for downstream carry. The T4 wake chain must be demonstrably non-dormant in a multi-day simulation that includes qualifying social events.

**Exact Scope:**
- Identify and fix whatever prevents _adjust_t4() from actually firing and producing observable relationship state changes across a multi-day simulation with qualifying social events and carried relational residuals
- Update or replace the test `test_t4_produces_zero_relational_residuals_across_multiple_days` which currently asserts zero relational residuals — this assertion contradicts the now-functional residual creation from round-0055
- Add a test that runs a multi-day simulation with qualifying social events, verifies _adjust_t4() is invoked on at least one day (via T4AdjustmentAuditRecord.invoked=True), and verifies that relationship state (trust/closeness) is measurably changed by the T4 adjusted signal
- Ensure the wake chain gate (_t4_wake_chain_gate_open) opens on at least one day in the multi-day test — i.e., the adjusted absorption is not in (none, surface)
- Verify that relational residuals are created AND carried across days (not just created on the first qualifying event day)

**Constraints:**
- AppraisalSignal v1 is frozen — do not modify its field definitions
- Settlement belongs to the engine — _adjust_t4() modifies the appraisal signal only, settlement arithmetic stays in appraisal_settlement.py
- _adjust_t4() internal logic (absorption step maps, valence/arousal/trust/closeness shift rules, growth dimension choices) must not be rewritten — the function is correctly implemented, the issue is activation not logic
- The T4 wake chain gate conditions (negative valence, trust_shift in mild/strong_decrease, absorption >= partial) must remain as-is — do not weaken the gate
- Do not fabricate test scenarios that bypass the normal simulation pipeline — tests must use simulate_day_bridged with realistic inputs
- All existing passing tests must continue to pass (900 tests currently green)
- Do not modify T1/T2 bridge logic or residual handling
- Do not modify deferred tick paths (T3/T5/T6/T7/T8)

**Forbidden Files (DO NOT modify):**
- `back/app/engines/appraisal_settlement.py`
- `back/app/engines/growth_synthesizer.py`
- `back/app/engines/relationship_synthesizer.py`
- `back/app/engines/relationship_drift.py`
- `back/app/engines/growth_stage_evolver.py`
- `back/app/engines/world_continuity.py`
- `back/app/engines/influence_action_generator.py`
- `back/app/domain/models.py`
- `back/app/domain/enums.py`
- `back/app/seed/**`
- `back/app/world/**`
- `back/app/services/**`
- `back/app/api/**`
- `front/**`
- `docs/**`

**Non-Goals (DO NOT do):**
- Rewriting _adjust_t4() internal logic — the function works correctly when called, the task is about making it actually fire
- Expanding T4 to positive relational events — current scope is negative wake chain only (confrontation/withdrawal)
- Adding new social event types or modifying the qualifying event detection
- Changing the wake chain gate conditions or absorption thresholds
- Modifying T1/T2 bridge or residual paths
- Enabling bridge for deferred ticks (T3/T5/T6/T7/T8)
- Modifying settlement arithmetic or relationship inertia tables
- Adding LLM integration or modifying the LLM appraisal path
- World generator changes — qualifying events are already produced (round-0054)

**Acceptance Criteria:**
- A multi-day test (3+ days) with qualifying social events demonstrates that _adjust_t4() is invoked=True on at least one day (verified via T4AdjustmentAuditRecord)
- The T4AdjustmentAuditRecord shows at least one field changed by _adjust_t4() (changed_fields is non-empty)
- The wake chain gate (_t4_wake_chain_gate_open) opens on at least one day — verified by a relational residual being created with kind=relational in the simulation output
- Relationship state (trust or closeness) differs from initial values after the multi-day simulation — the T4 signal actually settles into relationship state
- Relational residuals are carried across at least one day boundary — i.e., a residual created on day N appears in carried_residuals on day N+1
- The old test asserting zero relational residuals is updated to reflect the new reality (T4 now produces relational residuals when qualifying events are present)
- All 900 existing tests pass (allowing for the intentional update to the zero-residual assertion test)
- python3 -m pytest tests/ -v passes from the back/ directory with zero failures

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
