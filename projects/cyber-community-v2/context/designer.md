# Designer Context

## Phase Transition Rule

When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder: narrow event-aware activation seam active
- Composition audit: CompositionAuditRecord dataclass and composition_audit_out parameter added to simulate_day_bridged for T2/T4 collision detection
- Bridge coverage: T1/T2 active, T4 narrow-active with composition observability
- Settlement substrate unchanged

## Active Constraints

- T4 activation seam verified stable; narrow path remains the only approved activation shape
- No broad event taxonomy expansion
- No changes to settlement/substrate or bridge architecture
- No live LLM integration yet
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen

## Working Assumptions

- Phase 27 active: P27-T1 composition audit complete (247 tests passed)
- T2/T4 collision detection now instrumented for observability
- Same-day composition safety verified in test environment
- Ready for activation frequency audit (P27-T2)

## Known Risks

- P27-T2 frequency audit may reveal excessive T4 activation requiring immediate recalibration
- Production load wake chain patterns may differ from test scenarios

## Resolved Strategic Decisions

- Phase 26B officially closed; Phase 27 now active
- T4 minimal activation seam established and composition-audit enabled
- Roadmap sequence preserved: Phase 27 (T4 Activation Audit and Composition Safety) underway