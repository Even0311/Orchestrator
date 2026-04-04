# Task: Audit downstream residual creation from T4 activation — fix reviewability

**ID:** round-0017  
**Objective:** Implement observability instrumentation to audit and measure downstream residual creation behavior and wake chain effects triggered by T4 negative relational signals, establishing quantitative visibility into residual cascades before calibration.

**Exact Scope:** IN: Add instrumentation to track residual creation events downstream of T4 signal emission; observe wake chain depth, residual count per activation, and carryover distribution patterns; ensure audit records capture T4-specific residual provenance; produce structured JSON audit output and human-readable summary logs for manual verification. OUT: No changes to residual creation thresholds or settlement logic; no modifications to T2/T4 composition handling; no calibration adjustments.

## Constraints
- must not modify existing settlement or residual creation logic (observation-only)
- must not break existing 506+ test suite
- must preserve deterministic behavior while adding instrumentation
- must produce structured JSON output with schema-validated fields for automated parsing
- must include human-readable summary output for manual review verification
- human review needed if audit reveals cascades exceeding depth bounds that require immediate guard intervention

## Acceptance Criteria
- Instrumentation captures residual creation events triggered by T4 signals with traceable provenance
- Wake chain depth and cumulative residual count per T4 activation are observable and bounded within expected limits
- Audit data distinguishes T4-induced residuals from T1/T2 induced residuals in settlement substrate
- Existing test suite continues to pass without modification to test assertions
- NEW: Audit output is produced in valid JSON format with documented schema for reliable parsing
- NEW: Human-readable summary report is generated showing key metrics (activation count, max wake depth, total residuals created) for manual verification

## Required Tests
- test that T4 negative signal activation produces observable downstream residual creation records
- test that wake chain depth from T4 activation remains within documented bounds under load
- test that residual creation audit correctly attributes provenance to T4 source vs other tick types
- NEW: test that audit JSON output conforms to expected schema and is parseable
- NEW: test that human-readable summary contains required metrics and is generated without errors

## Non-Goals
- do not modify residual creation thresholds or guards
- do not refactor settlement substrate architecture
- do not implement calibration adjustments (deferred to P27-T5)
- do not add new event types or expand T4 activation conditions
