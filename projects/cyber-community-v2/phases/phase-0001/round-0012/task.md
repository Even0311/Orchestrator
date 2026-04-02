# Task: Audit T4 Downstream Gate Observability

**ID:** round-0012  
**Objective:** Audit and verify how T4-generated AppraisalSignals interact with downstream settlement gates (residual creation, wake chain triggers, and same-day composition with T1/T2 signals) to ensure behavior remains observable, auditable, and stable.

**Exact Scope:** IN: Trace T4 signal flow through residual creation gates; audit same-day T1/T2/T4 composition behavior on shared relationship targets; verify wake chain trigger conditions when T4 signals present; document gate interaction patterns and observability hooks; add or verify logging/telemetry for T4 gate passages. OUT: Changes to gate thresholds or settlement logic; modifications to T1/T2 bridge implementations; expansion of T4 trigger conditions beyond current narrow social event path; live LLM integration; new residual creation logic.

## Constraints
- Must preserve existing 205 test pass rate
- Must not alter deterministic settlement contracts
- Human review needed if gate interactions reveal unexpected coupling between T1/T2 and T4 paths requiring architectural intervention

## Acceptance Criteria
- T4 signal passage through residual creation gates is logged and observable in settlement pipeline
- Same-day composition of T1/T2/T4 signals on identical targets produces deterministic, documented behavior
- Wake chain triggers fire or suppress appropriately when T4 signals with minimal negative valence enter the pipeline
- Audit artifacts exist showing at least one concrete example of T4 signal successfully traversing each downstream gate type
- No regression in existing T1/T2 continuity test results

## Required Tests
- Test that T4-generated minimal negative signal correctly traverses residual creation gate without error
- Test that same-day T1 public residual and T4 relational residual on same target compose deterministically without collision or double-counting
- Test that T4 signal with surface absorption triggers wake chain appropriately based on existing absorption rules
- Test that T4 signal audit telemetry captures valence, absorption type, and target relationship identifier

## Non-Goals
- Do not modify residual creation thresholds or gate logic
- Do not implement new settlement substrate features
- Do not expand T4 event detection beyond current narrow social event path
- Do not refactor T1/T2 bridge implementations
- Do not add new relationship graph structures
