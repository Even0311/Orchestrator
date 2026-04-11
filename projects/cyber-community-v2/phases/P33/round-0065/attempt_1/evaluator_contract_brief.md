# Evaluator Contract Review — round-0065

**Task Key:** P33-T6
**Title:** Stage 2 appraisal safety contract document

## Proposed Acceptance Criteria
1. docs/stage2_appraisal_safety_contract.md exists and is well-structured markdown
2. Document contains a section defining 'safe appraisal deepening' with at least 3 concrete criteria that distinguish it from 'dangerous narrative drift', with examples of each
3. Document contains a per-tick authority table covering all 8 ticks (T1-T8), stating current status (active/inactive/deferred) and specific preconditions for live authority
4. Document specifies at least 4 numeric monitoring gates (e.g., degradation rate thresholds, minimum observation days, maximum drift rates) that a tick must continuously pass to retain live authority
5. Document defines a graduated response protocol: what happens when a gate is breached (warning → throttle → fallback → freeze), referencing the existing DegradationTracker and auto-fallback mechanisms
6. Document contains a section on what Stage 2 must NOT do — explicit anti-patterns and forbidden expansions, consistent with the frozen contracts in decisions_summary.md
7. Document references at least the following existing infrastructure by name: DegradationTracker, OutcomeClass (acceptable/degraded/invalid), deterministic_fallback.py, audit_drift.py
8. All numeric thresholds in the document are stated as concrete values (not TBD or placeholders)

## Proposed Review Focus
- Consistency with docs/decisions_summary.md — no contradictions with frozen decisions or approved paths
- Concreteness of monitoring gates — are thresholds specific enough to be implemented and tested without ambiguity?
- Per-tick preconditions — does each deferred tick (T3/T5/T6/T7/T8) have individually specified activation criteria, not just a blanket rule?
- Grounding in existing infrastructure — does the document build on DegradationTracker, OutcomeClass, and audit tooling rather than inventing parallel systems?
- Anti-pattern section — does it clearly forbid the known failure modes (LLM writing ledger directly, narrative drift without settlement, skipping fallback gates)?

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
