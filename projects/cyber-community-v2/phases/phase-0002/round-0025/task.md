# Task: Add comprehensive test coverage for T4 interpretation paths

**ID:** round-0025  
**Objective:** Implement comprehensive test coverage for the expanded T4 deterministic relational appraisal paths (Pattern A: Contested Endorsement and Pattern B: High-Intensity Unilateral Disclosure), including boundary conditions, invalid inputs, and edge cases to ensure the expanded coverage behaves within documented contract bounds.

**Exact Scope:** IN: Implement new unit tests for Pattern A activation with valid social event parameters; implement new unit tests for Pattern B activation with valid social event parameters; implement boundary value tests for intensity thresholds and signal range limits documented in the contract; implement edge case tests for null/invalid social_event inputs, missing required fields, and malformed event data; verify all new tests integrate with existing test suite. OUT: No modifications to T4 builder implementation code in tick_bridge.py; no changes to contract documentation or numerical bounds specifications in docs/t4_negative_behavior_contract.md; no calibration of signal intensity values or thresholds; no audit or changes to T2/T4 same-day composition logic; no addition of new interpretation patterns beyond Pattern A and Pattern B.

## Constraints
- Must not break existing 401 tests
- Must follow existing test structure and patterns in the codebase
- Must not modify the T4 builder implementation logic
- Must not alter docs/t4_negative_behavior_contract.md or docs/p28_t4_pattern_catalog.md
- Tests must be deterministic and not rely on randomness or external state
- All new tests must pass before task completion

## Acceptance Criteria
- New tests exist for Pattern A (Contested Endorsement) activation that verify signal production within documented intensity bounds
- New tests exist for Pattern B (High-Intensity Unilateral Disclosure) activation that verify signal production within documented intensity bounds
- Boundary value tests exist for activation thresholds and signal intensity limits for both patterns
- Edge case tests exist for null social_event, missing fields, and invalid enum values, verifying graceful handling without unhandled exceptions
- Total test count increases by at least 15 new tests covering the above categories
- All new tests pass and existing 401 tests continue to pass

## Required Tests
- Test that Pattern A (Contested Endorsement) produces valid negative relational signal when social_event matches contested endorsement criteria
- Test that Pattern B (High-Intensity Unilateral Disclosure) produces valid negative relational signal when intensity exceeds documented threshold
- Test that boundary intensity values at exact threshold limits produce expected activation or deactivation behavior
- Test that null or malformed social_event inputs are handled deterministically without raising unhandled exceptions
- Test that invalid enum values or missing required fields in social_event result in deterministic fallback behavior (no signal or safe default)

## Non-Goals
- Do not modify T4 builder implementation logic
- Do not update contract documentation or pattern catalogs
- Do not calibrate signal intensity ranges or thresholds
- Do not implement T2/T4 composition safety audit
- Do not add new interpretation patterns beyond Pattern A and Pattern B
- Do not integrate LLM or change settlement substrate
