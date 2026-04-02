# Task: Implement narrow social event reading path in T4 builder

**ID:** round-0008  
**Objective:** Modify `build_signal_from_t4_relationship_tick()` to read `world.social_event` and evaluate it against narrow trigger conditions approved for Phase 26B, establishing the input seam for event-aware T4 activation.

**Exact Scope:** IN: Adding logic to `build_signal_from_t4_relationship_tick()` to access `world.social_event` and check for qualifying events using narrow trigger conditions (specific event types/categories approved for Phase 26B), returning appropriate indicators when qualifying events are detected. OUT: Defining detailed output signal shapes (covered in P26B-T2), modifying downstream residual creation gates, expanding event taxonomy beyond the approved narrow set, implementing routing based on `social_event.target_id`, changes to other tick bridges (T1/T2/T3/T5-T8), settlement/substrate modifications, LLM integration.

## Constraints
- Must use only narrow social event trigger conditions explicitly approved for Phase 26B
- Must not implement routing or filtering based on `social_event.target_id`
- Must preserve existing T1/T2 continuity behavior without regression
- Must not modify settlement substrate or bridge architecture beyond T4 reading logic
- Must remain deterministic; no LLM integration permitted

## Acceptance Criteria
- `build_signal_from_t4_relationship_tick()` accesses `world.social_event` during T4 tick processing
- Function correctly identifies qualifying narrow social events based on approved trigger conditions
- Function correctly ignores non-qualifying social events and returns no signal or existing default behavior
- Existing T1/T2 bridge behavior remains stable and unaffected by T4 modifications

## Required Tests
- test that T4 builder correctly detects qualifying narrow social events present in world.social_event
- test that T4 builder ignores non-qualifying social events without triggering false activation
- test that T4 builder does not perform routing based on social_event.target_id
- test that existing T1/T2 bridge behavior remains unchanged (regression protection)

## Non-Goals
- do not define or implement detailed negative relational output shapes (deferred to P26B-T2)
- do not modify downstream residual creation gates or settlement logic
- do not expand social event taxonomy beyond narrow approved set
- do not refactor T1/T2 bridge code or other tick bridges
- do not introduce live LLM appraisal or non-deterministic evaluation
