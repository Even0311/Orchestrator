# P32: T4 Reality Closure
<!-- status: approved -->

## Phase Goal
Close the remaining Stage 1 gap by turning the existing T4 event-aware seam
from a partially implemented path into a real, stage-closing relational contract.

## In Scope
- close the remaining T4 partial-unlock gap identified in the current repo status
- make the existing T4 event-aware path capable of completing the approved relational wake chain
- validate that T4 can progress beyond detection-only / negative-signal-only behavior
- verify that downstream relational residual creation becomes real and auditable
- verify that `_adjust_t4()` is no longer permanently dormant
- audit same-day T2/T4 composition and downstream wake behavior after closure
- produce explicit contract notes describing what Stage 1 now considers valid T4 relational continuity

## Out of Scope
- no deferred tick bridge or live-authority expansion for T3 / T5 / T6 / T7 / T8
- no broad social world redesign
- no rich new event taxonomy expansion
- no settlement / substrate redesign
- no bridge architecture rewrite
- no freeform memory / personality / identity-deepening work
- no uncontrolled broadening of LLM authority
- no rewriting Stage 1 into a richer Stage 2 system

## Task Queue
- [x] P32-T1: Audit the current T4 path end-to-end in a live multi-day simulation — confirm actual activation rate is zero, identify every point where the path goes dormant, and document the exact chain of blockers preventing real T4 relational output — Round round-0048 — T4 End-to-End Audit: Confirm Zero Activation Rate and Docume
- [x] P32-T2: Make the world generator produce qualifying social events at a controlled, low frequency so that the T4 event-aware detection path can actually trigger during real simulation runs — Round round-0054 — Wire qualifying social events into world generator for T4 ac
- [ ] P32-T3: Complete the T4 appraisal-to-residual pipeline so that a detected qualifying event produces a real, persisted relational residual — not just a detection log — closing the gap between event detection and downstream relational effect
- [ ] P32-T4: Unfreeze `_adjust_t4()` so it applies the relational residual to the appropriate relationship state, making the T4 wake chain functional rather than permanently dormant
- [ ] P32-T5: Validate same-day T2/T4 composition by running a multi-day simulation where both T2 social ticks and T4 relational ticks fire on the same day, confirming no double-counting, no state corruption, and correct ordering of effects
- [ ] P32-T6: Audit downstream wake behavior after T4 closure — verify that T4-produced residuals carry over across days, appear in subsequent tick contexts, and do not regress T1/T2 continuity that was already stable
- [ ] P32-T7: Write explicit Stage 1 T4 relational continuity contract notes — define what constitutes valid T4 output, what activation frequency is expected, and what remains deferred to Stage 2
