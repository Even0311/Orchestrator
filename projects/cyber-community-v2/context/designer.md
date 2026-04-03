# Designer Context

## Phase Transition Rule
When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Active Constraints
- Phase 28 scope: Expand T4 deterministic coverage while preserving auditability; no LLM integration, no relationship graph redesign
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen per roadmap; no bridge work for these ticks
- All new T4 paths must remain explainable, contract-governed, and deterministic
- Settlement substrate remains engine-authoritative unchanged

## Working Assumptions
- T4 builder implements 3 activation paths (original narrow seam + Pattern A Contested Endorsement + Pattern B High-Intensity Unilateral Disclosure)
- Contract documentation now specifies explicit numerical bounds for signal intensity ranges, activation thresholds, and output boundaries for all expanded patterns
- Pattern detection logic operational with 401 total tests including 63 dedicated T4 pattern and contract tests
- Ready to add comprehensive test coverage for edge cases and cross-pattern interactions

## Architecture Snapshot
- Deterministic single-agent backbone operational with T1/T2/T4 bridge coverage
- T4 builder has 3 activation paths with deterministic bounds formally documented
- Settlement substrate unchanged and engine-authoritative
- Test coverage: 401 total tests including 63 dedicated T4 pattern and contract tests
- Contract docs specify valid ranges for Pattern A and Pattern B intensity outputs

## Known Risks
- Over-expansion risk: Too many new paths may degrade auditability
- Composition complexity: More T4 paths increase T2/T4 same-day interaction patterns to validate
- Signal calibration risk: New output shapes require bounded intensity ranges to prevent settlement instability

## Resolved Strategic Decisions
- Phase 27 completed: T4 activation audited, composition safety verified, contract formalized
- Phase 28-T1/T2/T3 completed: Expanded from single minimal seam to 3-condition deterministic coverage with validated pattern library and explicit numerical bounds
- Expansion remains deterministic, inspectable, and contract-governed; no natural-language appraisal permitted