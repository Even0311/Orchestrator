# Task: Implement T4 builder condition branches for cataloged patterns

**ID:** round-0023  
**Objective:** Implement expanded event condition branches in the T4 builder function (build_signal_from_t4_relationship_tick) to handle the two cataloged patterns: Contested Endorsement and High-Intensity Unilateral Disclosure. Add deterministic logic to detect these event types and emit appropriate relational appraisal signals.

**Exact Scope:** IN: Add conditional branches to build_signal_from_t4_relationship_tick() for Contested Endorsement pattern detection and signal emission. Add conditional branches for High-Intensity Unilateral Disclosure pattern detection and signal emission. Integrate these branches with existing T4 logic ensuring deterministic evaluation. OUT: Does not include implementing patterns beyond these two cataloged ones; does not include LLM integration; does not include settlement substrate changes; does not include T2/T4 composition auditing (P28-T5); does not include signal intensity calibration (P28-T6); does not include contract documentation updates (P28-T3).

## Constraints
- Must preserve existing T4 narrow path behavior and pass all 360 existing tests
- Must follow pattern specifications from docs/p28_t4_pattern_catalog.md
- Must remain deterministic with no LLM integration
- New paths must be explainable and contract-governed per Phase 27 contract
- Do not modify settlement substrate or residual creation logic

## Acceptance Criteria
- Contested Endorsement events trigger the corresponding T4 relational appraisal signal path
- High-Intensity Unilateral Disclosure events trigger the corresponding T4 relational appraisal signal path
- Existing T4 narrow path activation remains functional without regression
- New event condition branches only activate for their specific event signatures

## Required Tests
- Test that Contested Endorsement events produce the expected relational appraisal signal
- Test that High-Intensity Unilateral Disclosure events produce the expected relational appraisal signal
- Test that non-matching events do not trigger the new T4 paths
- Test that existing T4 narrow path still activates correctly for its specific conditions

## Non-Goals
- Do not implement additional patterns beyond the two cataloged ones
- Do not add LLM or natural-language appraisal
- Do not refactor relationship graph or settlement substrate
- Do not perform composition safety auditing (deferred to P28-T5)
- Do not calibrate signal intensities (deferred to P28-T6)
- Do not update contract documentation (deferred to P28-T3)
