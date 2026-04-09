# Evaluator Contract Review — round-0055

**Task Key:** P32-T3
**Title:** Complete T4 appraisal-to-residual pipeline for qualifying social events

## Proposed Acceptance Criteria
1. A multi-day simulation that includes a qualifying social event (confrontation or withdrawal) produces at least one non-None relational residual from the T4 tick.
2. The relational residual created by T4 persists into the next day's DaySnapshot.pending_residuals.
3. _adjust_t4() returns a non-None adjustment on the day following a T4 residual creation (i.e., it is no longer permanently dormant when qualifying events have occurred).
4. When no qualifying social event is present, the T4 signal remains unchanged from its current default behavior (positive valence, mild_increase trust, aftershock_days=0).
5. All existing tests pass (pytest back/tests/ -v) with zero failures.
6. At least one new test verifies the full chain: qualifying event → T4 signal with aftershock_days >= 1 → settlement creates relational residual → residual carried to next day → _adjust_t4() activates.

## Proposed Review Focus
- Confirm the residual-creation gate is satisfied by genuine signal values, not by loosening gate conditions.
- Confirm the default (no qualifying event) T4 path is untouched and still produces the prior default signal.
- Confirm _adjust_t4() actually fires and produces a meaningful adjustment — not just a no-op wrapper.
- Confirm no forbidden files were modified.
- Confirm AppraisalSignal schema was not altered.
- Confirm existing test suite passes without modification to existing test assertions.

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
