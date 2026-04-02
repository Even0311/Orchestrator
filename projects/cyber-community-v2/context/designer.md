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

- T4 minimal negative output shape implemented (P26B-T2 complete): valence=negative, absorption=surface, trust_shift=mild_decrease, closeness_delta=-1
- Downstream gate behavior now the critical verification target (P26B-T3)
- T1/T2 continuity remains stable (verified by 205 tests)
- World carryover distribution remains as calibrated

## Architecture Snapshot

- Deterministic single-agent day runner persists
- T4 builder complete: narrow social event detection → minimal negative relational output emission pipeline operational
- Bridge coverage: T1/T2 active, T4 now narrow-active with full output contract
- Settlement substrate unchanged
- Phase 26B progressing to downstream gate audit (P26B-T3)

## Known Risks

- Downstream gate interactions between T4 and existing T1/T2 paths (same-day composition)
- Over-interpreting minimal output shape as full relational continuity
- Phase 26B scope creep beyond audit into tuning

## Resolved Strategic Decisions

- Phase 25 officially closed; Phase 26B entered per roadmap
- T4 reopening approved via Phase 26B social event path (not gate tuning)
- Scope strictly limited to minimal activation seam verification