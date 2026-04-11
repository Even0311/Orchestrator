# Executor Brief — round-0066

## Task Contract
**Task Key:** P33-T6
**Title:** Stage 2 appraisal safety contract specification
**Objective:** Write a specification document (docs/stage2_appraisal_safety_contract.md) that defines what constitutes safe appraisal deepening versus dangerous narrative drift, the preconditions for granting new ticks live LLM authority, and the monitoring gates Stage 2 must pass. This is a documentation-only task — no code changes.

**Exact Scope:**
- Create docs/stage2_appraisal_safety_contract.md containing all sections listed in the acceptance criteria
- The document must reference existing infrastructure by exact names (DegradationTracker, OutcomeClass, deterministic_fallback.py, audit_drift.py) and quote their actual parameter defaults and threshold values accurately
- All numeric thresholds stated in the document must be verifiable against the current source code — no invented constants, no derived values presented as existing code behavior

**Constraints:**
- Document-only change — no source code, test, or config modifications
- Every numeric threshold or behavioral claim about existing code must match the actual implementation. The executor MUST read the relevant source files (back/tools/audit_drift.py, back/app/llm/degradation_tracker.py) before writing threshold values
- Key code facts the document must accurately reflect: (a) degradation_threshold defaults to 0.5 — there is NO 0.35 warn threshold in code; (b) monotonic drift detection uses window=10 — spans shorter than 10 days CANNOT be detected; (c) build_dimension_verdict produces 'warn' at >=10 consecutive days and 'fail' at >=20 consecutive days (monotonic_window * 2); (d) unbounded growth check uses abs(cumulative_delta) and can only produce 'warn', never 'fail' on its own; (e) max_cooldown=14 is a probe backoff cap, not a stability observation period
- If the document proposes NEW thresholds or policies not yet in code, they MUST be explicitly labeled as 'Stage 2 requirement — not yet implemented' to distinguish them from existing infrastructure behavior
- T4 continuity status: positive path is active, negative path is frozen pending Phase 26B. Do not label T4 as simply 'Active'
- Anti-patterns section must align with decisions_summary.md and CLAUDE.md hard rules
- AppraisalSignal v1 is frozen — do not propose modifications to its fields

**Forbidden Files (DO NOT modify):**
- `back/app/**`
- `back/tools/**`
- `back/tests/**`
- `front/**`
- `*.py`
- `*.ts`
- `*.tsx`
- `*.json`
- `docs/decisions_summary.md`
- `docs/phase25_continuity_status.md`
- `CLAUDE.md`
- `.claude/**`

**Non-Goals (DO NOT do):**
- Implementing any code changes, monitoring infrastructure, or new thresholds
- Modifying existing engines, bridges, or settlement logic
- Expanding bridge coverage to deferred ticks (T3/T5/T6/T7/T8)
- Designing a freeform memory system or identity-growth mechanics
- Player influence redesign or world-generator changes
- Proposing changes to AppraisalSignal v1 schema

**Acceptance Criteria:**
- AC1: docs/stage2_appraisal_safety_contract.md exists and is well-structured markdown with clear section hierarchy
- AC2: A section defines 'safe appraisal deepening' with at least 3 concrete criteria, each with explicit safe and unsafe examples
- AC3: A per-tick authority table covers all 8 ticks (T1-T8) with current status. Each deferred tick (T3, T5, T6, T7, T8) has individually specified activation preconditions, not a blanket rule. T4 is described as 'positive path active; negative path frozen (Phase 26B required)'
- AC4: At least 4 monitoring gates are defined with concrete numeric thresholds — no TBD or placeholder values
- AC5: The monotonic drift gate correctly states: warn at >=10 consecutive days, fail at >=20 consecutive days (= monotonic_window * 2 with default monotonic_window=10). This must be consistent everywhere the threshold appears in the document
- AC6: No escalation level or response tier references detection of monotonic drift spans shorter than 10 days, since detect_monotonic_drift(window=10) cannot flag spans below its window size
- AC7: The degradation rate threshold is stated as 0.5 (matching DegradationTracker.degradation_threshold default). If any lower advisory threshold is mentioned, it is explicitly labeled as a proposed Stage 2 addition not present in current code
- AC8: Unbounded growth detection correctly uses |cumulative_delta| (absolute value) and is noted as producing 'warn' only (never 'fail' on its own) per build_dimension_verdict
- AC9: A graduated response section defines at least 3 escalation levels with trigger conditions that reference the monitoring gates. Level trigger conditions must use the correct warn/fail thresholds from AC5/AC8
- AC10: An anti-patterns section lists explicitly forbidden patterns consistent with decisions_summary.md hard rules and CLAUDE.md constraints
- AC11: All existing tests pass with zero regressions (document-only change, so this should be trivially satisfied)

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
