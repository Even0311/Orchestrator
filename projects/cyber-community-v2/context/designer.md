# Designer Context

## Phase Transition Rule

When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder: narrow event-aware activation seam active with composition and frequency observability
- Downstream audit: wake chain depth tracking and cascade pattern detection instrumentation now active
- Bridge coverage: T1/T2 active, T4 narrow-active with full audit instrumentation (composition, frequency, downstream)
- Settlement substrate unchanged

## Active Constraints

- T4 activation seam verified stable; narrow path remains the only approved activation shape
- No broad event taxonomy expansion
- No changes to settlement/substrate or bridge architecture
- No live LLM integration yet
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen

## Working Assumptions

- Phase 27 active: P27-T1, P27-T2, and P27-T3 complete (composition, frequency, and downstream audit instrumentation all verified)
- T2/T4 collision detection, T4 activation frequency, and downstream residual propagation now all instrumented for observability
- Ready for _adjust_t4() path stability audit (P27-T4)

## Known Risks

- P27-T4 audit may reveal threshold adjustment instabilities or non-interpretable output shapes requiring immediate recalibration
- Production load wake chain patterns may differ from test scenarios despite instrumentation

## Resolved Strategic Decisions

- Phase 26B officially closed; Phase 27 now active
- T4 minimal activation seam established with full observability (composition + frequency + downstream)
- Roadmap sequence preserved: Phase 27 (T4 Activation Audit and Composition Safety) progressing through audit tasks