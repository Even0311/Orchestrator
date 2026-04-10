# Designer Brief — round-0059

## Roadmap / Phase Context
## Phase 31 — First Live LLM Appraisal Integration
### Goal
Introduce the first controlled live LLM appraisal path into the agent loop.

### Why Now
At this point:
- deterministic backbone is established
- T4 event-aware seam exists
- relational appraisal has meaningful deterministic shape
- appraisal/settlement boundary is explicit
- LLM has passed offline/shadow validation

The system is ready for the first real LLM-assisted appraisal step.

### In Scope
- insert LLM into the appraisal seam only
- **first live authority is limited to T1 / T2 / T4 only** — deferred ticks (T3/T5/T6/T7/T8)
  remain on deterministic fallback even though the schema can represent them
- keep settlement / bookkeeping engine-authoritative
- preserve deterministic validation / fallback / guardrail path
- limit LLM responsibility to the approved appraisal contract
- audit resulting outputs and system stability

### Out of Scope
- no full agent autonomy explosion
- no replacement of simulation engine by the LLM
- no uncontrolled freeform memory/personality architecture expansion
- no multiplayer-scale live society rollout
- no granting live LLM authority to T3/T5/T6/T7/T8 (deferred to Stage 2)

### Exit Condition
- live LLM appraisal participates in the real loop for T1 / T2 / T4
- T3 / T5 / T6 / T7 / T8 remain on deterministic fallback
- engine remains authoritative for settlement
- outputs remain auditable
- fallback path remains functional
- the integration is stable enough to establish the first controlled live hybrid path
- Stage 1 closure is now pending only on the remaining T4 reality-closure gap

### Unlocks
- first controlled live hybrid path
- project has transitioned from pure deterministic baseline to controlled hybrid infrastructure:
  **LLM appraisal + engine settlement**
- safe entry into final Stage 1 closure work

---

## Phase 32 — T4 Reality Closure
### Goal
Close the remaining Stage 1 gap by turning the existing T4 event-aware seam
from a partially implemented path into a
...(truncated)

## Current Phase: P32: T4 Reality Closure
**Phase ID:** P32
**Phase Goal:** Close the remaining Stage 1 gap by turning the existing T4 event-aware seam
from a partially implemented path into a real, stage-closing relational contract.

**In Scope:**
- close the remaining T4 partial-unlock gap identified in the current repo status
- make the existing T4 event-aware path capable of completing the approved relational wake chain
- validate that T4 can progress beyond detection-only / negative-signal-only behavior
- verify that downstream relational residual creation becomes real and auditable
- verify that `_adjust_t4()` is no longer permanently dormant
- audit same-day T2/T4 composition and downstream wake behavior after closure
- produce explicit contract notes describing what Stage 1 now considers valid T4 relational continuity

**Out of Scope:**
- no deferred tick bridge or live-authority expansion for T3 / T5 / T6 / T7 / T8
- no broad social world redesign
- no rich new event taxonomy expansion
- no settlement / substrate redesign
- no bridge architecture rewrite
- no freeform memory / personality / identity-deepening work
- no uncontrolled broadening of LLM authority
- no rewriting Stage 1 into a richer Stage 2 system

## Recently Completed Tasks (same phase)
- P32-T2: Make the world generator produce qualifying social events at a controlled, low frequency so that the T4 event-aware detection path can actually trigger during real simulation runs — Round round-0054 — Wire qualifying social events into world generator for T4 ac
- P32-T3: Complete the T4 appraisal-to-residual pipeline so that a detected qualifying event produces a real, persisted relational residual — not just a detection log — closing the gap between event detection and downstream relational effect — Round round-0055 — Complete T4 appraisal-to-residual pipeline: break bootstrapp
- P32-T4: Unfreeze `_adjust_t4()` so it applies the relational residual to the appropriate relationship state, making the T4 wake chain functional rather than permanently dormant — Round round-0056 — Unfreeze _adjust_t4() wake chain: carried relational residua
- P32-T5: Validate same-day T2/T4 composition by running a multi-day simulation where both T2 social ticks and T4 relational ticks fire on the same day, confirming no double-counting, no state corruption, and correct ordering of effects — Round round-0057 — Validate same-day T2/T4 composition in multi-day simulation
- P32-T6: Audit downstream wake behavior after T4 closure — verify that T4-produced residuals carry over across days, appear in subsequent tick contexts, and do not regress T1/T2 continuity that was already stable — Round round-0058 — Audit T4 residual cross-day wake behavior and T1/T2 non-regr

## Selected Task
**Task Key:** P32-T7
**Description:** Write explicit Stage 1 T4 relational continuity contract notes — define what constitutes valid T4 output, what activation frequency is expected, and what remains deferred to Stage 2

## Recent Rounds
Most recent rounds (do not redo completed work):
- **round-0058** [PASSED] — Write a validation test that runs a multi-day bridged simulation where T4 produc
- **round-0057** [PASSED] — Write a validation test that runs a multi-day bridged simulation where both T2 (
- **round-0056** [PASSED] — Make _adjust_t4() functionally active so that when a relational residual is carr

## Your Task
Produce a `task_contract.json` file with the following fields:
- `phase_id`, `task_key`, `title`, `objective`, `exact_scope`
- `constraints` — architectural constraints the executor must respect
- `forbidden_files` — glob patterns for files the executor must NOT touch
- `non_goals` — what is explicitly out of scope
- `acceptance_criteria` — each criterion must be objectively verifiable
- `review_focus` — what the evaluator should pay special attention to

Write the contract to tell the executor WHAT to do and WHAT NOT to touch,
not HOW to implement it. The executor decides implementation details.
