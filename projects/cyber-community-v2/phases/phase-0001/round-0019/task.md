# Task: Audit _adjust_t4() path stability and interpretability

**ID:** round-0019  
**Objective:** Implement observability instrumentation for the `_adjust_t4()` path to capture input/output patterns and verify that threshold adjustments produce stable, bounded, and interpretable outcomes.

**Exact Scope:** IN: Instrument `_adjust_t4()` and related adjustment helpers to capture input parameters, intermediate calculations, and final output values; add audit records tracking adjustment magnitude, direction, and causal context; verify instrumentation captures complete adjustment chains without regression. OUT: Modification of threshold constants or calibration values (P27-T5); changes to settlement/substrate logic; new event taxonomy or relational system redesign; any calibration fixes based on findings.

## Constraints
- Must not break existing 259+ test suite from previous phases
- Instrumentation must be compatible with existing CompositionAuditRecord and downstream audit patterns from P27-T1/T2/T3
- If critical instability is detected, flag for human review in P27-T5 rather than unilateral threshold modification

## Acceptance Criteria
- _adjust_t4() inputs and outputs are captured in audit records for every invocation during simulation
- Threshold adjustment magnitudes are observable and remain within bounded, interpretable ranges without unbounded growth or chaotic oscillation
- Adjustment causality is traceable from relationship context and event input to final signal modification
- All existing tests continue to pass without regression
- Audit data integrates with existing observability streams from P27-T1/T2/T3

## Required Tests
- Test that _adjust_t4() produces deterministic, stable output for identical inputs across repeated invocations
- Test that extreme edge-case input values (e.g., maximum negative affinity, boundary thresholds) produce bounded adjustments without numeric instability
- Test that audit records capture complete input context including relationship state, event parameters, and resulting adjustment magnitude

## Non-Goals
- Do not modify threshold calculation formulas or calibration constants (deferred to P27-T5)
- Do not refactor relationship manager or bridge architecture
- Do not implement fixes for detected instabilities (document only)
- Do not add new relational event types or broaden event taxonomy
