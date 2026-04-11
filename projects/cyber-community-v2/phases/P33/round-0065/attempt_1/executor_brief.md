# Executor Brief — round-0065

## Task Contract
**Task Key:** P33-T6
**Title:** Stage 2 appraisal safety contract document
**Objective:** Write a definitive reference document (docs/stage2_appraisal_safety_contract.md) that specifies what constitutes safe appraisal deepening versus dangerous narrative drift, the preconditions required before any new tick gains live LLM authority, and the monitoring gates that Stage 2 must continuously pass.

**Exact Scope:**
- Create docs/stage2_appraisal_safety_contract.md containing all sections described in the acceptance criteria below
- The document must reference the actual existing infrastructure by name (DegradationTracker, OutcomeClass, AppraisalAuditEntry, deterministic_fallback.py, audit_drift.py) — not hypothetical systems
- The document must cover all 8 tick types (T1-T8) individually, stating the current authority status and the specific preconditions for each deferred tick to gain live LLM authority
- The document must define concrete, numeric monitoring gates (thresholds, window sizes, observation periods) that Stage 2 must pass — not vague aspirational language

**Constraints:**
- This is a documentation-only task — no source code changes, no engine modifications, no new Python modules
- The document must be consistent with all existing decisions in docs/decisions_summary.md (especially frozen contracts: AppraisalSignal v1, T4 freeze, Stage 1 deferred tick boundaries)
- The document must not prescribe implementation details (class names, function signatures, file layout) for Stage 2 — it specifies WHAT must hold, not HOW to build it
- All monitoring thresholds referenced must be grounded in the existing DegradationTracker infrastructure (window_days, degradation_threshold, OutcomeClass taxonomy)
- The document must acknowledge the T4 deadlock (inactive due to no negative base signal in deterministic builder) and state that Phase 26B social-event-aware activation is the only approved unfreeze path

**Forbidden Files (DO NOT modify):**
- `back/app/**/*.py`
- `back/tests/**/*.py`
- `back/tools/**/*.py`
- `front/**/*`
- `docs/decisions_summary.md`
- `docs/vision.md`
- `.claude/**/*`

**Non-Goals (DO NOT do):**
- No implementation of any Stage 2 feature — this is a specification document only
- No modification to existing engine, bridge, or settlement code
- No expansion of Stage 1 bridge scope (T3/T5/T6/T7/T8 remain deferred)
- No new test files or audit scripts
- No changes to AppraisalSignal v1 schema definition
- No roadmap or phase planning beyond specifying Stage 2 safety gates
- No LLM prompt engineering or prompt template changes

**Acceptance Criteria:**
- docs/stage2_appraisal_safety_contract.md exists and is well-structured markdown
- Document contains a section defining 'safe appraisal deepening' with at least 3 concrete criteria that distinguish it from 'dangerous narrative drift', with examples of each
- Document contains a per-tick authority table covering all 8 ticks (T1-T8), stating current status (active/inactive/deferred) and specific preconditions for live authority
- Document specifies at least 4 numeric monitoring gates (e.g., degradation rate thresholds, minimum observation days, maximum drift rates) that a tick must continuously pass to retain live authority
- Document defines a graduated response protocol: what happens when a gate is breached (warning → throttle → fallback → freeze), referencing the existing DegradationTracker and auto-fallback mechanisms
- Document contains a section on what Stage 2 must NOT do — explicit anti-patterns and forbidden expansions, consistent with the frozen contracts in decisions_summary.md
- Document references at least the following existing infrastructure by name: DegradationTracker, OutcomeClass (acceptable/degraded/invalid), deterministic_fallback.py, audit_drift.py
- All numeric thresholds in the document are stated as concrete values (not TBD or placeholders)

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
