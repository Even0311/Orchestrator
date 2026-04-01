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

- Phase 26B activates T4 via social event reading, not gate tuning
- T4 will emit only minimal negative relational shapes
- Downstream gates remain unchanged; they decide residual creation
- Existing T1/T2 continuity must remain stable during T4 activation
- World carryover distribution remains as calibrated

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder now reads world.social_event (narrow seam)
- Bridge coverage: T1/T2 active, T4 transitioning from inactive to narrow-active
- Settlement substrate unchanged
- Phase 26B focuses on event-aware activation without architecture redesign

## Known Risks

- Over-expanding T4 trigger conditions beyond narrow approved path
- Accidentally destabilizing T1/T2 continuity during T4 work
- Confusing Phase 26B narrow reopening with full T4 relational continuity
- Prematurely optimizing output shapes before seam is verified

## Resolved Strategic Decisions

- Phase 25 officially closed; Phase 26B entered per roadmap
- T4 reopening approved via Phase 26B social event path (not gate tuning)
- Scope strictly limited to minimal activation seam verification
- Stage 1 deferred ticks remain out of scope