# Task: Implement T4 narrow social event reading path

**ID:** round-0009  
**Objective:** Modify build_signal_from_t4_relationship_tick() to read world.social_event and emit a minimal activation signal when narrow trigger conditions are met, establishing the first event-aware T4 seam.

**Exact Scope:** IN: Modifying build_signal_from_t4_relationship_tick() to check world.social_event for qualifying narrow trigger conditions (e.g., specific negative event categories), returning a minimal AppraisalSignal when triggered, returning None when no qualifying event exists. OUT: Defining detailed output schema variations, modifying downstream settlement gates, expanding event taxonomy, implementing target_id routing, changing existing T1/T2 bridge logic.

## Constraints
- Must use only narrow trigger conditions approved for Phase 26B (no broad event taxonomy expansion)
- Must not route based on social_event.target_id
- Must not modify settlement substrate or bridge architecture
- Must preserve existing T1/T2 continuity behavior (no regression)
- Must not activate deferred ticks T3/T5/T6/T7/T8

## Acceptance Criteria
- build_signal_from_t4_relationship_tick() checks world.social_event for qualifying narrow triggers
- Function returns non-None minimal signal when qualifying social event is present
- Function returns None when no qualifying social event exists
- Existing T1 and T2 bridge functionality continues to work as before
- T4 activation only occurs for approved narrow trigger shapes (no broad activation)

## Required Tests
- Test that T4 builder detects qualifying narrow social event and returns activation signal
- Test that T4 builder returns None when social event is absent or does not meet narrow trigger conditions
- Test that existing T1/T2 residual creation remains stable when T4 builder checks for social events

## Non-Goals
- Do not implement full negative relational output shape refinement (deferred to P26B-T2)
- Do not modify downstream residual creation gates
- Do not expand social event taxonomy beyond narrow approved set
- Do not refactor bridge or settlement architecture
