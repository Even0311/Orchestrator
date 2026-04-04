# Task: Audit downstream residual creation behavior

**ID:** round-0018  
**Objective:** Implement observability instrumentation to audit how T4 negative signals propagate through downstream residual creation paths, including wake chain depth tracking and cascade pattern detection.

**Exact Scope:** IN: Add audit instrumentation to capture residual creation events triggered by T4 negative activation; implement wake chain depth metrics; track cascade patterns through residual creation gates; ensure audit records are accessible for quantitative analysis. OUT: Modifications to residual creation thresholds or guards; changes to _adjust_t4() implementation; production of contract notes or documentation.

## Constraints
- Must not break existing 506+ tests
- Observability-only changes: do not alter residual creation logic or thresholds yet
- Preserve existing T4 narrow activation seam behavior

## Acceptance Criteria
- Residual creation events triggered by T4 negative signals generate auditable records with traceable causality
- Wake chain depth metrics are observable and measurable for all T4-initiated residual paths
- Existing test suite passes without regression (506+ tests)

## Required Tests
- Test that T4 negative activation generates downstream residual creation audit records with correct provenance
- Test that wake chain depth tracking correctly captures propagation bounds when residuals trigger secondary residuals
- Test that cascade patterns are measurable when multiple related residuals create within the same activation window

## Non-Goals
- Do not modify residual creation thresholds or calibration (deferred to P27-T5)
- Do not refactor _adjust_t4() logic (deferred to P27-T4)
- Do not produce contract notes or documentation (deferred to P27-T6)
