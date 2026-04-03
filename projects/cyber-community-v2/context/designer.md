# Designer Context

## Phase Transition Rule

When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder: narrow event-aware activation seam active with full audit instrumentation
- T4 behavior contract formalized: docs/t4_negative_behavior_contract.md defines valid activation conditions, composition rules, and propagation boundaries
- Contract verification suite: 21 dedicated tests validating T4 semantics (338 total tests passed)
- Bridge coverage: T1/T2 active, T4 narrow-active with complete instrumentation and formal contract
- Settlement substrate unchanged

## Active Constraints

- T4 behavior contract now formally documented and tested
- No broad event taxonomy expansion
- No changes to settlement/substrate or bridge architecture
- No live LLM integration yet
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen
- Phase 27 complete; awaiting human review for transition to Phase 28 per roadmap

## Working Assumptions

- Phase 27 complete: all audit, calibration, and contract documentation tasks finished
- T4 behavior now governed by explicit contract specification
- Test suite stable at 338 passed (including 21 new contract tests)
- System ready for Phase 28 (Deterministic Relational Appraisal Expansion) upon human approval

## Resolved Strategic Decisions

- Phase 27 closed: T4 activation audit, calibration, and behavior contract formalization complete
- T4 negative relational continuity seam verified stable, auditable, and contractually bounded
- Explicit contract documentation establishes valid T4 behavior specifications for future expansion