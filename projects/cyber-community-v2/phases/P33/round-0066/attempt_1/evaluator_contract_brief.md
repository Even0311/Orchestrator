# Evaluator Contract Review — round-0066

**Task Key:** P33-T6
**Title:** Stage 2 appraisal safety contract specification

## Proposed Acceptance Criteria
1. AC1: docs/stage2_appraisal_safety_contract.md exists and is well-structured markdown with clear section hierarchy
2. AC2: A section defines 'safe appraisal deepening' with at least 3 concrete criteria, each with explicit safe and unsafe examples
3. AC3: A per-tick authority table covers all 8 ticks (T1-T8) with current status. Each deferred tick (T3, T5, T6, T7, T8) has individually specified activation preconditions, not a blanket rule. T4 is described as 'positive path active; negative path frozen (Phase 26B required)'
4. AC4: At least 4 monitoring gates are defined with concrete numeric thresholds — no TBD or placeholder values
5. AC5: The monotonic drift gate correctly states: warn at >=10 consecutive days, fail at >=20 consecutive days (= monotonic_window * 2 with default monotonic_window=10). This must be consistent everywhere the threshold appears in the document
6. AC6: No escalation level or response tier references detection of monotonic drift spans shorter than 10 days, since detect_monotonic_drift(window=10) cannot flag spans below its window size
7. AC7: The degradation rate threshold is stated as 0.5 (matching DegradationTracker.degradation_threshold default). If any lower advisory threshold is mentioned, it is explicitly labeled as a proposed Stage 2 addition not present in current code
8. AC8: Unbounded growth detection correctly uses |cumulative_delta| (absolute value) and is noted as producing 'warn' only (never 'fail' on its own) per build_dimension_verdict
9. AC9: A graduated response section defines at least 3 escalation levels with trigger conditions that reference the monitoring gates. Level trigger conditions must use the correct warn/fail thresholds from AC5/AC8
10. AC10: An anti-patterns section lists explicitly forbidden patterns consistent with decisions_summary.md hard rules and CLAUDE.md constraints
11. AC11: All existing tests pass with zero regressions (document-only change, so this should be trivially satisfied)

## Proposed Review Focus
- CRITICAL: Verify every numeric threshold and code-behavioral claim in the document against actual source files (back/tools/audit_drift.py lines 328-347 for drift verdicts, back/app/llm/degradation_tracker.py for threshold defaults). Prior rounds failed specifically because thresholds were wrong — this is the primary review axis
- Check internal consistency: thresholds stated in monitoring gates must match thresholds referenced in graduated response levels and per-tick preconditions. No contradictions within the document
- Verify that any threshold NOT currently in code is clearly labeled as a proposed Stage 2 policy, not presented as existing behavior
- Confirm T4 is described with split status (positive active / negative frozen) and not labeled simply 'Active'
- Confirm anti-patterns align with decisions_summary.md and CLAUDE.md hard rules

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
