# Evaluator Code Review — round-0065

**Task Key:** P33-T6
**Title:** Stage 2 appraisal safety contract document

## Acceptance Criteria
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

## Review Focus
- CRITICAL: Verify that every numeric threshold in the document matches the actual source code — especially the monotonic drift gate (warn >=10, fail >=20) and any degradation rate thresholds from degradation_tracker.py
- CRITICAL: Verify that no graduated response level references detection capabilities that do not exist in the current tooling (e.g., no monotonic span detection below 10 days)
- Check that per-tick preconditions for deferred ticks are concrete and specific, not vague aspirational statements
- Verify anti-patterns are consistent with decisions_summary.md and CLAUDE.md hard rules
- Confirm the document is purely a specification — no code changes, no implementation

## Code Changes (git diff)
```diff

diff --git a/docs/stage2_appraisal_safety_contract.md b/docs/stage2_appraisal_safety_contract.md
new file mode 100644
index 0000000..a049eeb
--- /dev/null
+++ b/docs/stage2_appraisal_safety_contract.md
@@ -0,0 +1,431 @@
+# Stage 2 Appraisal Safety Contract
+
+> Definitive reference for what constitutes safe appraisal deepening versus
+> dangerous narrative drift, the preconditions required before any new tick
+> gains live LLM authority, and the monitoring gates that Stage 2 must
+> continuously pass.
+>
+> This document specifies WHAT must hold — not HOW to build it.
+> It does not prescribe class names, function signatures, or file layouts
+> for Stage 2 implementation.
+
+---
+
+## 1. Definitions
+
+**Appraisal deepening** — extending or intensifying the LLM appraisal layer for
+existing or new tick types while the simulation remains stable, coherent, and
+reversible.
+
+**Narrative drift** — a state where LLM-generated appraisal signals push the
+agent's state or growth metrics into trajectories that are unbounded, monotonic,
+or structurally locked in ways that cannot be corrected by the existing
+settlement and residual mechanisms.
+
+**Live authority** — the condition in which `appraisal_router.route()` is called
+for a tick type on a given world day and its output (rather than the deterministic
+fallback) feeds the settlement engine. Auto-fallback suspension (see §6) revokes
+live authority temporarily without freezing the tick type entirely.
+
+---
+
+## 2. Safe Appraisal Deepening vs. Dangerous Narrative Drift
+
+### 2.1 Distinguishing Criteria
+
+A tick type's LLM output is considered **safe** when all three of the following
+hold. Any single violation classifies the output as drifting:
+
+**Criterion 1 — Signal is bounded and reversible.**
+The AppraisalOutput for each tick must produce an `absorption` level that, when
+settled across a 7-day rolling window, keeps all tracked dimensions within the
+saturation bounds defined in `audit_drift.py`:
+ceiling ≤ 93, floor ≥ 7 (0–100 scale).
+A signal is unsafe when it pushes a dimension to saturation and holds it there
+for 5 or more consecutive days (the `saturation_lock_window` default in
+`audit_drift.py`).
+
+*Safe example (T1):* On a neutral-valence day, the LLM returns
+`absorption=partial, valence=neutral, arousal=medium` for a public headline.
+Settlement writes +1 mood and no residual. The trajectory stays well within
+saturation bounds over 30 simulated days.
+
+*Unsafe example:* An LLM consistently returns `absorption=full, valence=positive,
+arousal=high` for T1 regardless of headline content, driving `moodScore` to 93
+and locking it there for 8 consecutive days — triggering a `saturation_lock`
+verdict in `audit_drift.py`.
+
+---
+
+**Criterion 2 — Signal is content-aware, not uniform.**
+An LLM path is safe when its outputs are distributed across the full
+`OutcomeClass` space: not all `acceptable` (which would suggest a rubber-stamping
+bias) and not predominantly `degraded`
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
