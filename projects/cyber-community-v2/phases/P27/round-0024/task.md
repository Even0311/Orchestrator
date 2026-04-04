# Task: Extend T4 Contract Documentation for Expanded Patterns

**ID:** round-0024  
**Objective:** Update the T4 behavior contract documentation to specify valid signal intensity ranges, activation thresholds, and output boundaries for Pattern A (Contested Endorsement) and Pattern B (High-Intensity Unilateral Disclosure), establishing deterministic bounds for the newly expanded relational appraisal coverage.

**Exact Scope:** IN: Extend docs/t4_negative_behavior_contract.md to include explicit valid signal intensity ranges (min/max bounds) for Pattern A and Pattern B, specify deterministic activation condition thresholds (e.g., minimum controversy levels, intensity floors), and define safety limits preventing downstream settlement instability. OUT: Implementation code changes, comprehensive test suite additions (deferred to P28-T4), signal calibration adjustments (deferred to P28-T6), modifications to pattern catalog documentation, T2/T4 composition audit work (deferred to P28-T5).

## Constraints
- Must preserve existing contract specifications for the original narrow T4 path without modification
- Must use deterministic language with explicit numerical bounds only—no ambiguous qualitative terms (e.g., 'significant', 'moderate') without quantified ranges
- Must not break existing 386 passing tests
- Contract specifications must be auditable with binary pass/fail criteria for behavior validation

## Acceptance Criteria
- docs/t4_negative_behavior_contract.md contains explicit valid signal intensity ranges with numerical minimum and maximum bounds for Contested Endorsement (Pattern A)
- docs/t4_negative_behavior_contract.md contains explicit valid signal intensity ranges with numerical minimum and maximum bounds for High-Intensity Unilateral Disclosure (Pattern B)
- Documentation specifies deterministic activation condition thresholds with explicit boundary values required to trigger each expanded pattern
- All documented intensity ranges specify hard magnitude caps that prevent downstream settlement instability
- Extended contract section maintains deterministic, unambiguous language without subjective qualitative assessments

## Required Tests
- test that Contested Endorsement signal generation respects the maximum negative intensity bound specified in the extended contract
- test that High-Intensity Unilateral Disclosure signal generation respects the maximum negative intensity bound specified in the extended contract
- test that activation logic adheres to the minimum threshold values documented for each expanded pattern

## Non-Goals
- do not modify T4 builder implementation code (completed in P28-T2)
- do not add comprehensive test coverage for edge cases (deferred to P28-T4)
- do not calibrate or adjust signal intensity values (deferred to P28-T6)
- do not audit T2/T4 composition safety (deferred to P28-T5)
- do not refactor pattern catalog documentation or other system components
