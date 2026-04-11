# Evaluator Code Review — round-0065

**Task Key:** P33-T6
**Title:** Stage 2 appraisal safety contract document

## Acceptance Criteria
1. docs/stage2_appraisal_safety_contract.md exists and is well-structured markdown
2. Document contains a section defining 'safe appraisal deepening' with at least 3 concrete criteria that distinguish it from 'dangerous narrative drift', with examples of each
3. Document contains a per-tick authority table covering all 8 ticks (T1-T8), stating current status (active/inactive/deferred) and specific preconditions for live authority
4. Document specifies at least 4 numeric monitoring gates (e.g., degradation rate thresholds, minimum observation days, maximum drift rates) that a tick must continuously pass to retain live authority
5. Document defines a graduated response protocol: what happens when a gate is breached (warning → throttle → fallback → freeze), referencing the existing DegradationTracker and auto-fallback mechanisms
6. Document contains a section on what Stage 2 must NOT do — explicit anti-patterns and forbidden expansions, consistent with the frozen contracts in decisions_summary.md
7. Document references at least the following existing infrastructure by name: DegradationTracker, OutcomeClass (acceptable/degraded/invalid), deterministic_fallback.py, audit_drift.py
8. All numeric thresholds in the document are stated as concrete values (not TBD or placeholders)

## Review Focus
- Consistency with docs/decisions_summary.md — no contradictions with frozen decisions or approved paths
- Concreteness of monitoring gates — are thresholds specific enough to be implemented and tested without ambiguity?
- Per-tick preconditions — does each deferred tick (T3/T5/T6/T7/T8) have individually specified activation criteria, not just a blanket rule?
- Grounding in existing infrastructure — does the document build on DegradationTracker, OutcomeClass, and audit tooling rather than inventing parallel systems?
- Anti-pattern section — does it clearly forbid the known failure modes (LLM writing ledger directly, narrative drift without settlement, skipping fallback gates)?

## Code Changes (git diff)
```diff

diff --git a/docs/stage2_appraisal_safety_contract.md b/docs/stage2_appraisal_safety_contract.md
new file mode 100644
index 0000000..328462e
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
