# Designer Context

## Phase Transition Rule

When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder: narrow event-aware activation seam active
- Composition audit: CompositionAuditRecord dataclass and composition_audit_out parameter added to simulate_day_bridged for T2/T4 collision detection
- Frequency audit: Observability instrumentation for T4 negative activation rates now implemented
- Bridge coverage: T1/T2 active, T4 narrow-active with composition and frequency observability
- Settlement substrate unchanged

## Active Constraints

- T4 activation seam verified stable; narrow path remains the only approved activation shape
- No broad event taxonomy expansion
- No changes to settlement/substrate or bridge architecture
- No live LLM integration yet
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen

## Working Assumptions

- Phase 27 active: P27-T1 and P27-T2 complete (composition and frequency audit instrumentation verified, 506 total tests passed)
- T2/T4 collision detection and T4 activation frequency now both instrumented for observability
- Ready for downstream residual creation audit (P27-T3)

## Known Risks

- P27-T3 downstream audit may reveal unexpected residual cascades requiring immediate recalibration
- Production load wake chain patterns may differ from test scenarios

## Resolved Strategic Decisions

- Phase 26B officially closed; Phase 27 now active
- T4 minimal activation seam established with full observability (composition + frequency)
- Roadmap sequence preserved: Phase 27 (T4 Activation Audit and Composition Safety) progressing through audit tasks