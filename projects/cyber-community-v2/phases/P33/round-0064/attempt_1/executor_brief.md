# Executor Brief — round-0064

## Task Contract
**Task Key:** P33-T5
**Title:** Multi-day drift audit: 30+ day state, growth, residual, and degradation trends
**Objective:** Create a drift audit tool that runs a 30+ simulated-day session and systematically detects unbounded, monotonic, or structurally stuck drift patterns across all tracked dimensions — state values, growth-buffer accumulation, residual stacking, and degradation-rate trends — producing a machine-readable report with per-dimension verdicts.

**Exact Scope:**
- Create a new audit script (e.g. back/tools/audit_drift.py) that runs 30+ simulated days using the existing advance_day pathway and collects per-day snapshots of: (a) all AgentState numeric fields (moodScore, energy, stress, socialDrive, socialFulfillment, learningState, workState), (b) all AgentGrowth numeric fields (curiosity, caution, socialOpenness, expression, trustInOthers, emotionalStability), (c) pending_residuals count and composition per day from DaySnapshot, (d) DegradationTracker rolling rates and auto-fallback state per tick type if a tracker is provided.
- For each tracked dimension, compute and report: (1) monotonic-drift detection — flag any dimension that moves in the same direction for N consecutive days (N configurable, default 10), (2) unbounded-growth detection — flag any dimension whose cumulative delta exceeds a configurable threshold over the run, (3) saturation/floor lock — flag any dimension that stays at its ceiling (>=93) or floor (<=7) for more than M consecutive days (M configurable, default 5), (4) residual stacking — flag if pending_residuals count exceeds a configurable max on any day, or if residual count is monotonically non-decreasing over K consecutive days (K configurable, default 7).
- Output a JSON report file containing: per-dimension trajectory arrays, per-dimension drift verdicts (pass/warn/fail with reason), a residual-stacking section, a degradation-trend section (if tracker provided), and a top-level summary with overall pass/fail.
- Create a corresponding test file (e.g. back/tests/test_p33_t5_drift_audit.py) that verifies: (a) the audit script runs to completion on the deterministic backbone for 30 days without error, (b) each drift-detection rule produces correct verdicts on synthetic (hand-crafted) trajectory data, (c) residual-stacking detection works on synthetic residual histories, (d) the output JSON is well-formed and contains all required sections.

**Constraints:**
- The audit tool must use the existing advance_day / simulate_day pipeline — do not build a parallel simulation loop.
- The audit tool must be a pure observer — it must not modify any engine, domain model, or settlement logic.
- All drift-detection logic must be pure functions operating on collected trajectory arrays — no side effects, no LLM calls.
- The DegradationTracker is optional — the audit must work with or without one. When absent, the degradation-trend section is omitted from the report.
- Residual data must be read from DaySnapshot.pending_residuals — do not invent a new residual tracking mechanism.
- AppraisalSignal v1 is frozen — do not modify its field definitions.
- Do not modify any existing engine files, domain models, or test files.
- Output files go into back/tools/audit_outputs/ consistent with the existing audit_run.py convention.

**Forbidden Files (DO NOT modify):**
- `back/app/engines/*.py`
- `back/app/domain/*.py`
- `back/app/llm/*.py`
- `back/app/services/*.py`
- `back/app/world/*.py`
- `back/app/api/**`
- `back/app/seed/**`
- `front/**`
- `docs/**`
- `back/tests/test_residual_*.py`
- `back/tests/test_tick_bridge.py`
- `back/tests/test_appraisal_settlement.py`
- `back/tests/test_world_continuity.py`
- `back/tests/test_social_event_schema.py`
- `back/tests/test_p33_t2_*.py`
- `back/tests/test_p33_t3_*.py`
- `back/tests/test_p33_t4_*.py`

**Non-Goals (DO NOT do):**
- Do not fix or tune any drift patterns found — this task is observation and reporting only.
- Do not add new fields to any Pydantic domain model.
- Do not extend the bridge to deferred ticks (T3/T5/T6/T7/T8).
- Do not implement LLM-based appraisal or narrative analysis.
- Do not modify the DegradationTracker or any appraisal infrastructure.
- Do not add player-guidance scenarios — the audit runs with guidance=none.
- Do not produce a markdown report — JSON output is sufficient (the existing audit_run.py already covers markdown reporting).

**Acceptance Criteria:**
- A new file back/tools/audit_drift.py exists and is executable via `python back/tools/audit_drift.py --days 30`.
- Running `python back/tools/audit_drift.py --days 30` completes without error and produces a JSON file in back/tools/audit_outputs/.
- The output JSON contains a 'trajectories' object with keys for all 7 state fields and all 6 growth fields, each containing an array of per-day values with length equal to the number of simulated days plus the seed day.
- The output JSON contains a 'residual_stacking' object with a per-day array of residual counts and a 'verdicts' sub-object.
- The output JSON contains a 'drift_verdicts' object with one entry per tracked dimension, each having a 'status' field (pass/warn/fail) and a 'reasons' array.
- The output JSON contains a top-level 'summary' object with an 'overall_status' field (pass/warn/fail).
- A new test file back/tests/test_p33_t5_drift_audit.py exists.
- All tests in back/tests/test_p33_t5_drift_audit.py pass via `python -m pytest back/tests/test_p33_t5_drift_audit.py -v`.
- The test file includes at least one test that verifies monotonic-drift detection flags a synthetic trajectory that moves in one direction for 10+ consecutive days.
- The test file includes at least one test that verifies saturation-lock detection flags a synthetic trajectory stuck at ceiling for 5+ consecutive days.
- The test file includes at least one test that verifies residual-stacking detection flags monotonically non-decreasing residual counts over 7+ consecutive days.
- The test file includes at least one end-to-end test that runs the audit for 30 days on the deterministic backbone and verifies the output JSON structure.
- All existing tests pass: `python -m pytest back/tests/ -v` has no regressions.

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
