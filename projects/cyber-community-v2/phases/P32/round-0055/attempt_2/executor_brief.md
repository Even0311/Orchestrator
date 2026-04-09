# Executor Brief — round-0055

## Task Contract
**Task Key:** P32-T3
**Title:** Complete T4 appraisal-to-residual pipeline: break bootstrapping deadlock
**Objective:** Make the T4 event-aware path produce a real, persisted relational residual when a qualifying social event (confrontation/withdrawal) is detected, closing the bootstrapping deadlock where no relational residuals ever exist because their creation requires pre-existing relational residuals.

**Exact Scope:**
- Modify the T4 pipeline in tick_bridge.py so that when a qualifying social event is detected AND no carried relational residual exists, a seed relational residual is created that can be carried to the next day — breaking the bootstrapping deadlock.
- The mechanism must work within the existing settlement contract: residuals are created by settle_appraisal_output when aftershock_days > 0 and absorption != none. The executor must find a way to satisfy these conditions for the initial qualifying event without violating the wake chain gate contract.
- The wake chain gate contract (Phase 23 strict conditions) must remain intact: the gate checks absorption >= partial, valence == negative, trust_shift in (mild_decrease, strong_decrease). When opened, it sets aftershock_days=1.
- The existing _adjust_t4() function behavior must be preserved: it upgrades surface→partial when a carried relational residual is present.
- Write a focused test that verifies the end-to-end pipeline: qualifying event on day N with no prior residuals → relational residual persisted in pending_residuals → available as carried residual on day N+1.
- All 900 existing tests must continue to pass.

**Constraints:**
- Settlement is engine-authoritative — residuals must be created via settle_appraisal_output (through _apply_bridge_signal), not by direct construction in the bridge layer.
- AppraisalSignal v1 is frozen — do not modify its field definitions.
- The T4 builder function (build_signal_from_t4_relationship_tick) emits the deterministic output shape. Changes to its output fields are allowed only for qualifying-event branches (confrontation/withdrawal/pattern A/pattern B) — the default positive path must not be touched.
- The existing test_t4_threshold_calibration.py tests define the calibrated contract. All 21 tests in that file must pass. Pay special attention to the 3 tests that failed in the previous attempt: test_collision_with_residual_t4_absorption_upgraded_to_partial, test_wake_gate_closed_no_t4_residual_without_carried_residual, test_wake_chain_decays_after_gate_opens.
- The composition audit record fields (t4_absorption, wake_chain_gate_open, t4_residual_created) must accurately reflect the actual state — do not fake audit values.
- Do not modify appraisal_settlement.py — the settlement engine is tick-agnostic and must stay that way.
- Residual creation requires aftershock_days > 0 in the signal passed to settle_appraisal_output. The Phase 23 gate is ONE mechanism that sets aftershock_days=1, but it is not the only possible mechanism — the executor may introduce additional aftershock_days assignment logic in the bridge layer for qualifying events.

**Forbidden Files (DO NOT modify):**
- `back/app/engines/appraisal_settlement.py`
- `back/app/domain/models.py`
- `back/app/domain/enums.py`
- `back/app/seed/**`
- `back/app/world/**`
- `back/app/services/**`
- `back/app/api/**`
- `front/**`
- `docs/**`

**Non-Goals (DO NOT do):**
- Do not expand bridge coverage to deferred ticks (T3/T5/T6/T7/T8).
- Do not add new event types or expand the qualifying event taxonomy.
- Do not modify the AppraisalSignal schema or settlement engine.
- Do not change T1 or T2 bridge logic.
- Do not implement target_id-based routing for social events.
- Do not redesign the wake chain gate — it must continue checking the same four conditions.
- Do not change the default positive T4 path (no qualifying event).

**Acceptance Criteria:**
- {'id': 'ac-1', 'description': 'All 900 existing tests pass (python3 -m pytest tests/ -v). Zero regressions.', 'verification': 'python3 -m pytest tests/ -v shows 900 passed, 0 failed.'}
- {'id': 'ac-2', 'description': 'All 21 tests in test_t4_threshold_calibration.py pass, including the 3 that failed in the previous attempt.', 'verification': 'python3 -m pytest tests/test_t4_threshold_calibration.py -v shows 21 passed.'}
- {'id': 'ac-3', 'description': "A qualifying social event (confrontation or withdrawal) on a day with NO carried relational residuals produces at least one relational residual in the day's pending_residuals output.", 'verification': 'New test: run simulate_day_bridged with a confrontation event and initial_residuals=[], verify pending_residuals contains a ResidualEntry with kind=relational.'}
- {'id': 'ac-4', 'description': 'The relational residual produced in ac-3 is available as a carried residual on the next day, enabling _adjust_t4 to fire and potentially open the wake chain gate if another qualifying event occurs.', 'verification': "New test: two-day sequence — day 1 confrontation with no residuals → produces relational residual; day 2 confrontation with day 1's pending_residuals as initial_residuals → _adjust_t4 invoked (adjustment_audit shows invoked=True)."}
- {'id': 'ac-5', 'description': 'Without a qualifying social event, the T4 path produces no relational residual regardless of carried residuals (default positive path unchanged).', 'verification': 'Existing test test_no_qualifying_event_no_t4_residual continues to pass.'}
- {'id': 'ac-6', 'description': "The bootstrapping deadlock comment in _adjust_t4 docstring ('currently dormant') and the 'STRUCTURALLY CLOSED GATE' comment in simulate_day_bridged are updated to reflect the new reality.", 'verification': "Grep for 'currently dormant' and 'STRUCTURALLY CLOSED GATE' in tick_bridge.py returns zero matches."}

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
