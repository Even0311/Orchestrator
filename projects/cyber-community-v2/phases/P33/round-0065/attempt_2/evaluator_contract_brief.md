# Evaluator Contract Review — round-0065

**Task Key:** P33-T6
**Title:** Stage 2 appraisal safety contract document

## Proposed Acceptance Criteria
1. docs/stage2_appraisal_safety_contract.md exists and is well-structured markdown
2. Section on safe vs unsafe defines at least 3 concrete criteria with examples distinguishing safe appraisal deepening from dangerous narrative drift
3. Per-tick authority table covers all 8 ticks (T1–T8) with current status and, for each deferred tick, specific preconditions for gaining live authority
4. At least 5 monitoring gates are defined with concrete numeric thresholds (no TBD or placeholder values)
5. Monotonic drift gate correctly states: warn at >=10 consecutive days, fail at >=20 consecutive days (matching audit_drift.py build_dimension_verdict with default monotonic_window=10)
6. No graduated response level references detection of monotonic spans shorter than 10 days, since detect_monotonic_drift(window=10) cannot flag spans below 10 days
7. Graduated response defines at least 3 escalation levels with trigger conditions tied to the defined monitoring gates
8. Anti-patterns section is consistent with decisions_summary.md (LLM cannot write ledger, AppraisalSignal v1 frozen, T4 frozen except via 26B, etc.)
9. All threshold values referenced in the document are verifiable against actual source code in back/tools/audit_drift.py and back/app/llm/degradation_tracker.py
10. All existing tests pass with no regressions (python -m pytest tests/ -v from back/)

## Proposed Review Focus
- CRITICAL: Verify that every numeric threshold in the document matches the actual source code — especially the monotonic drift gate (warn >=10, fail >=20) and any degradation rate thresholds from degradation_tracker.py
- CRITICAL: Verify that no graduated response level references detection capabilities that do not exist in the current tooling (e.g., no monotonic span detection below 10 days)
- Check that per-tick preconditions for deferred ticks are concrete and specific, not vague aspirational statements
- Verify anti-patterns are consistent with decisions_summary.md and CLAUDE.md hard rules
- Confirm the document is purely a specification — no code changes, no implementation

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
