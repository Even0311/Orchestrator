# Evaluator Contract Review — round-0059

**Task Key:** P32-T7
**Title:** Write Stage 1 T4 relational continuity contract notes

## Proposed Acceptance Criteria
1. A new file `docs/stage1_t4_relational_continuity_contract.md` exists
2. The document contains a section defining valid T4 output: all three negative patterns (P0, Pattern A, Pattern B) are named with their exact activation conditions (event types, reciprocity, intensity values)
3. The document contains a section on activation frequency that states T4 is event-driven and references the world generator's controlled emission of qualifying events
4. The document contains a section on wake chain lifecycle that traces the full path from qualifying event to residual expiry, including the gate conditions (valence==negative, trust_shift in {mild_decrease, strong_decrease}, absorption not in {none, surface})
5. The document states the wake chain depth limit is 1 day with days_remaining=1 and explains the self-limiting property
6. The document contains a section on _adjust_t4() that lists at least the trust_shift hard stop (capped at mild_decrease), closeness_delta bounds ([-2, +2]), and absorption ceiling (deep)
7. The document contains a section on T2/T4 same-day composition safety referencing settlement order (T2 before T4)
8. The document contains a section on cross-day residual carry confirming T4 residuals coexist with T1/T2 residuals without interference
9. The document contains a section listing what is deferred to Stage 2, including at minimum: T3/T5/T6/T7/T8 bridge expansion, multi-target routing, and LLM-driven T4 appraisal
10. The document lists the test modules that protect the T4 contract (at minimum: test_t4_behavior_contract.py, test_residual_continuity_audit.py, test_residual_persistence.py)
11. No existing files are modified (git diff shows only the new file)
12. The full test suite passes: `cd back && python -m pytest tests/ -v` returns 0 exit code

## Proposed Review Focus
- Factual accuracy: do all stated thresholds, enum values, and gate conditions match the actual engine code?
- Completeness: are all three negative patterns documented, not just P0?
- Contract vs. calibration: does the document clearly distinguish between guaranteed behaviors and run-specific observations?
- Consistency: does the document contradict any existing docs/ files?
- Deferred scope: does the Stage 2 deferred section correctly identify what is NOT covered by Stage 1, without designing Stage 2?
- No code changes: confirm that only docs/stage1_t4_relational_continuity_contract.md was created and no other files were modified

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
