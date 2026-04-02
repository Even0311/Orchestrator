# Designer Context

## Phase Transition Rule

When the current phase is closing or a next phase is being proposed, Designer **must** read `roadmap.md` before proposing a phase transition. Next-phase proposals must follow the approved roadmap sequence. Designer may not invent new phases or skip ahead.

## Active Constraints

- T4 activation limited to narrow social event-aware path only
- No broad event taxonomy expansion
- No changes to settlement/substrate or bridge architecture
- No live LLM integration yet
- No routing based on social_event.target_id
- Stage 1 deferred ticks (T3/T5/T6/T7/T8) remain frozen

## Working Assumptions

- P26B-T3 complete: downstream gate behavior verified observable, auditable, and stable
- T4 negative signals compose safely with T1/T2 same-day paths
- 219 tests passing confirms pipeline integrity
- P26B-T4 (final stability check) is the remaining task before Phase 26B exit

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder operational: narrow event detection → minimal negative output emission
- Downstream gates audited: residual creation, wake triggers, and T1/T2 composition confirmed stable
- Bridge coverage: T1/T2 active, T4 narrow-active with full output contract and verified gate interactions
- Settlement substrate unchanged

## Known Risks

- Final exit condition verification (P26B-T4) could reveal edge cases in stability
- Over-interpreting minimal activation as full relational continuity
- Premature expansion into broader relational modeling before Phase 27 audit

## Resolved Strategic Decisions

- Phase 25 officially closed; Phase 26B entered per roadmap
- T4 reopening approved via Phase 26B social event path (not gate tuning)
- Scope strictly limited to minimal activation seam verification