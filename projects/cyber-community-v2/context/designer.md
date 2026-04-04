# Designer Context

## Phase Transition Rule
When the current phase is closing or a next phase is being proposed, Designer **must** read `road_map.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Active Constraints
- Phase 28 scope: Expand T4 deterministic coverage while preserving auditability; no LLM integration, no relationship graph redesign
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen per roadmap; no bridge work for these ticks
- All new T4 paths must remain explainable, contract-governed, and deterministic
- Settlement substrate remains engine-authoritative unchanged

## Working Assumptions
- T4 builder implements 3 activation paths with deterministic bounds formally documented
- Comprehensive test coverage (40 new tests) validates Pattern A, Pattern B, and original narrow seam for boundary conditions and edge cases
- Same-day T2/T4 composition safety audit completed — expanded coverage verified safe for same-day interaction with T2 influencer signals
- 441 total tests operational including 103 dedicated T4 tests
- Ready to calibrate signal intensity ranges for new output shapes

## Architecture Snapshot
- Deterministic single-agent backbone operational with T1/T2/T4 bridge coverage
- T4 builder has 3 activation paths with explicit numerical bounds, comprehensive test coverage, and verified composition safety with T2
- Settlement substrate unchanged and engine-authoritative
- Test coverage: 441 total tests including 103 dedicated T4 pattern, contract, and comprehensive coverage tests

## Known Risks
- Signal calibration risk: New output intensity ranges must be bounded to prevent downstream settlement instability (P28-T6 remaining)

## Resolved Strategic Decisions
- Phase 27 completed: T4 activation audited, composition safety verified, contract formalized
- Phase 28-T1/T2/T3/T4/T5 completed: Expanded from single minimal seam to 3-condition deterministic coverage with validated pattern library, explicit numerical bounds, comprehensive edge case test coverage, and verified T2/T4 same-day composition safety