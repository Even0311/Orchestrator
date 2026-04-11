# Evaluator Code Review — round-0066

**Task Key:** P33-T6
**Title:** Stage 2 appraisal safety contract specification

## Acceptance Criteria
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

## Review Focus
- CRITICAL: Verify every numeric threshold and code-behavioral claim in the document against actual source files (back/tools/audit_drift.py lines 328-347 for drift verdicts, back/app/llm/degradation_tracker.py for threshold defaults). Prior rounds failed specifically because thresholds were wrong — this is the primary review axis
- Check internal consistency: thresholds stated in monitoring gates must match thresholds referenced in graduated response levels and per-tick preconditions. No contradictions within the document
- Verify that any threshold NOT currently in code is clearly labeled as a proposed Stage 2 policy, not presented as existing behavior
- Confirm T4 is described with split status (positive active / negative frozen) and not labeled simply 'Active'
- Confirm anti-patterns align with decisions_summary.md and CLAUDE.md hard rules

## Code Changes (git diff)
```diff

diff --git a/docs/stage2_appraisal_safety_contract.md b/docs/stage2_appraisal_safety_contract.md
new file mode 100644
index 0000000..7adc2a0
--- /dev/null
+++ b/docs/stage2_appraisal_safety_contract.md
@@ -0,0 +1,291 @@
+# Stage 2 Appraisal Safety Contract
+
+**Status:** Pre-implementation specification  
+**Scope:** Defines what constitutes safe appraisal deepening versus dangerous narrative drift, the preconditions for granting new ticks live LLM authority, and the monitoring gates Stage 2 must pass before expanding live authority beyond the current T1/T2 scope.
+
+---
+
+## 1. Context and Purpose
+
+The current Stage 1 backbone grants live LLM appraisal authority to T1 (information_exposure) and T2 (social_interaction). T4's positive relational path is active; its negative path is frozen pending Phase 26B. Ticks T3, T5, T6, T7, T8 remain deferred — they route through `deterministic_fallback.py` and produce `absorption=none` with no settlement effect.
+
+Stage 2 expands live LLM authority to deferred ticks, one at a time, under strict preconditions. This document defines the safety boundary: what signals indicate stable appraisal behavior, what patterns constitute unacceptable drift, and at what thresholds the system must halt expansion or roll back.
+
+---
+
+## 2. Safe Appraisal Deepening — Criteria and Examples
+
+Safe appraisal deepening means adding LLM authority to a tick type in a way that preserves deterministic invariants, stays within the settlement layer's bounded arithmetic, and avoids structural narrative lock-in.
+
+### Criterion 1 — Settlement remains the authority on all numeric values
+
+**Safe:** The LLM produces an `AppraisalSignal` (absorption, valence, arousal, growth token list, relational signal, aftershock_days, guidance_resonance). The engine settlement layer (`appraisal_settlement.py`) translates the signal into bounded state deltas using its own arithmetic. No LLM output is written directly to `agentState`, `agentGrowth`, the residual list, or any trust/closeness field.
+
+**Unsafe:** The LLM response includes a numeric delta (`mood += 12`, `curiosity = 74`) that is applied without passing through `appraisal_settlement.py`. This bypasses the bounded clamp and breaks the ledger contract (decision 4.2: LLM 不直接写 ledger 数值).
+
+### Criterion 2 — The new tick's appraisal output produces no monotonic drift over 10+ consecutive days
+
+**Safe:** After activating a new tick's live path, a 30-day `audit_drift.py` run produces `pass` or `warn` verdicts for all tracked dimensions, with no monotonic drift span ≥ 10 consecutive days on any dimension.
+
+**Unsafe:** A newly activated tick type systematically shifts a state dimension (e.g., `stress` steadily rising) for 10 or more consecutive days, triggering a monotonic drift `warn` in `build_dimension_verdict`. If the span reaches 20+ consecutive days, the verdict escalates to `fail`.
+
+### Criterion 3 — The DegradationTracker rolling rate stays at or below 0.5 after activation

...(truncated)
```

## Your Task
1. Check each acceptance criterion against the actual code changes
2. Pay special attention to the review focus items
3. If existing test files were modified, examine whether the modifications are justified
4. Verify tests pass and no regressions were introduced

Write `review_verdict.json` with:
- `verdict` — PASS, FAIL, or REVISION_REQUIRED
- `confidence` — high, medium, or low
- `met_criteria` — list of criteria that passed
- `unmet_criteria` — list of criteria that failed
- `blocker_fixes` — must-fix issues (empty if PASS)
- `non_blocking_suggestions` — nice-to-have improvements
- `rationale` — explanation of verdict
