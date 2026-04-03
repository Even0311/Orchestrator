# Designer Context

## Phase Transition Rule
When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Active Constraints
- Phase 28 scope: Expand T4 deterministic coverage while preserving auditability; no LLM integration, no relationship graph redesign
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen per roadmap; no bridge work for these ticks
- All new T4 paths must remain explainable, contract-governed, and deterministic
- Settlement substrate remains engine-authoritative unchanged

## Working Assumptions
- Pattern catalog established: 2 new T4 relational impact patterns (Contested Endorsement, High-Intensity Unilateral Disclosure) documented and validated
- Phase 27 contract foundation stable with 338 tests passed
- Ready to implement expanded event condition branches in T4 builder
- Current T4 has single narrow activation path proven safe; expansion now has validated pattern library to draw from

## Architecture Snapshot
- Deterministic single-agent backbone operational with T1/T2/T4 bridge coverage
- T4 pattern catalog available at docs/p28_t4_pattern_catalog.md with 22 validation tests
- T4 builder has narrow event-aware seam with full instrumentation and formal contract
- Settlement substrate unchanged and engine-authoritative
- Contract verification suite: 21 dedicated tests (338 total) + 22 new pattern tests (360 total)

## Known Risks
- Over-expansion risk: Too many new paths may degrade auditability
- Composition complexity: More T4 paths increase T2/T4 same-day interaction patterns to validate
- Signal calibration risk: New output shapes require bounded intensity ranges to prevent settlement instability

## Resolved Strategic Decisions
- Phase 27 completed: T4 activation audited, composition safety verified, contract formalized in docs/t4_negative_behavior_contract.md
- Approved to proceed from single minimal seam to limited multi-condition coverage
- Expansion must remain deterministic, inspectable, and contract-governed; no natural-language appraisal permitted