# Designer Context

## Phase Transition Rule
When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Active Constraints
- Phase 28 scope: Expand T4 deterministic coverage while preserving auditability; no LLM integration, no relationship graph redesign
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen per roadmap; no bridge work for these ticks
- All new T4 paths must remain explainable, contract-governed, and deterministic
- Settlement substrate remains engine-authoritative unchanged

## Working Assumptions
- T4 builder now implements 2 expanded condition branches (Contested Endorsement, High-Intensity Unilateral Disclosure) beyond original narrow path
- Pattern detection logic operational with 26 new tests validating detection, signal shape, and fallthrough behavior
- Ready to update formal contract documentation to specify valid ranges for new coverage
- Expanded T4 deterministic coverage progressing without compromising auditability

## Architecture Snapshot
- Deterministic single-agent backbone operational with T1/T2/T4 bridge coverage
- T4 builder now has 3 activation paths: original narrow seam + Pattern A (Contested Endorsement) + Pattern B (High-Intensity Unilateral Disclosure)
- Settlement substrate unchanged and engine-authoritative
- Test coverage: 386 total tests including 48 dedicated T4 pattern and contract tests

## Known Risks
- Over-expansion risk: Too many new paths may degrade auditability
- Composition complexity: More T4 paths increase T2/T4 same-day interaction patterns to validate
- Signal calibration risk: New output shapes require bounded intensity ranges to prevent settlement instability

## Resolved Strategic Decisions
- Phase 27 completed: T4 activation audited, composition safety verified, contract formalized in docs/t4_negative_behavior_contract.md
- Phase 28-T1/T2 completed: Expanded from single minimal seam to 3-condition deterministic coverage with validated pattern library
- Expansion remains deterministic, inspectable, and contract-governed; no natural-language appraisal permitted