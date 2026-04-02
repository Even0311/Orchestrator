# Designer Context

## Phase Transition Rule

When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Active Constraints

- T4 activation seam verified stable; narrow path remains the only approved activation shape
- No broad event taxonomy expansion
- No changes to settlement/substrate or bridge architecture
- No live LLM integration yet
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen

## Working Assumptions

- Phase 26B complete: all exit conditions met, P26B-T4 verification passed (233 tests)
- T4 narrow activation produces stable, auditable downstream behavior
- Same-day T1/T2/T4 composition verified safe
- Ready for Phase 27 entry per roadmap

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder: narrow event-aware activation seam fully verified with 14 exit-condition tests
- Downstream gates: residual creation and wake chains confirmed stable under T4 load
- Bridge coverage: T1/T2 active, T4 narrow-active with verified contracts and gate interactions
- Settlement substrate unchanged

## Known Risks

- Phase 27 audit may reveal subtle composition issues at higher activation frequencies
- Risk of interpreting verification success as justification for immediate coverage expansion (deferred to Phase 28)

## Resolved Strategic Decisions

- Phase 26B officially closed; T4 minimal activation seam established and exit-verified
- Next phase approved: Phase 27 (T4 Activation Audit and Composition Safety) per roadmap.md
- Deterministic T4 relational negative path now confirmed as stable baseline for future appraisal work