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

- T4 social event detection seam is verified operational (P26B-T1 complete)
- T4 will emit only minimal negative relational shapes (P26B-T2 focus)
- Downstream gates remain unchanged; they decide residual creation
- Existing T1/T2 continuity must remain stable during T4 output implementation
- World carryover distribution remains as calibrated

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder verified to read world.social_event via narrow seam (18 tests passing)
- Bridge coverage: T1/T2 active, T4 now narrow-active (detection phase complete)
- Settlement substrate unchanged
- Phase 26B progressing to output shape definition (P26B-T2)

## Known Risks

- Over-expanding T4 output shapes beyond minimal negative relational contract
- Accidentally destabilizing T1/T2 continuity during T4 output implementation
- Confusing Phase 26B narrow reopening with full T4 relational continuity
- Prematurely optimizing output intensity before seam is fully verified

## Resolved Strategic Decisions

- Phase 25 officially closed; Phase 26B entered per roadmap
- T4 reopening approved via Phase 26B social event path (not gate tuning)
- Scope strictly limited to minimal activation seam verification
- Stage 1 deferred ticks remain out of scope