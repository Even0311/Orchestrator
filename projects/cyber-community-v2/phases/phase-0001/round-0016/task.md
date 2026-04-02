# Task: Audit T4 negative activation frequency

**ID:** round-0016  
**Objective:** Implement observability instrumentation to measure and record the frequency of T4 negative relational signal activations under current narrow event-aware conditions, enabling quantitative assessment of activation rates without modifying thresholds or settlement behavior.

**Exact Scope:** IN: Add instrumentation to track when build_signal_from_t4_relationship_tick() emits negative relational signals; capture activation counts, trigger conditions, and temporal distribution; expose metrics for frequency analysis; preserve existing behavior. OUT: Changes to activation thresholds, settlement logic, residual creation behavior, T2/T4 composition handling, or event taxonomy expansion.

## Constraints
- Must preserve existing deterministic behavior - observability only
- Must not break existing 247 tests
- Activation thresholds remain frozen - only measurement changes allowed
- Narrow event-aware activation seam from Phase 26B must remain unchanged

## Acceptance Criteria
- T4 negative activation events are logged with timestamp, trigger conditions, and target relationship
- Frequency metrics can be calculated from audit data (activations per day, activation rate percentage)
- Non-activation cases (misses) are distinguishable from activations in audit trail
- Existing test suite passes without modification

## Required Tests
- test that T4 negative signal activation is correctly detected and recorded when narrow event conditions are met
- test that absence of negative signal is correctly recorded when conditions are not met
- test that frequency statistics can be aggregated from multiple simulation days

## Non-Goals
- do not modify activation thresholds or guards
- do not change downstream residual creation logic
- do not refactor T4 builder architecture
- do not add new event types or broaden activation conditions
