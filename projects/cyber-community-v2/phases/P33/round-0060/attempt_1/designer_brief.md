# Designer Brief — round-0060

## Roadmap / Phase Context
## Ultimate Vision Reference
Long-term, CyberLife / Cyber Community should become:

a shared cyber society in which each player places one developing agent into a living world,
then influences that agent through care, timing, and limited guidance,
while the agent is continuously shaped by world events, relationships, memory, inner appraisal, and the player's presence.

The product should feel like:
- witnessing a life
- nurturing a becoming self
- observing social fate unfold
- participating through care, not control

It should not collapse into:
- chatbot
- dashboard
- task executor
- freeform roleplay shell
- pure simulation sandbox with no emotional product loop

---

## Usage Rules For Designer
When selecting the next phase:
- first read `vision.md`
- then read `roadmap.md`
- then read `current_phase.md`

Designer may:
- refine task sequencing within the approved current phase
- define rounds inside the active phase
- update current status and risks

Designer may not:
- skip forward to a later roadmap phase without explicit authorization
- merge multiple roadmap phases into one large phase
- invent a new strategic direction outside the roadmap
- broaden a phase beyond its approved scope in the name of completeness

If reality changes, revise `roadmap.md` explicitly.
Do not silently drift around it.

## Current Phase: P33: Appraisal Discipline Hardening
**Phase ID:** P33
**Phase Goal:** Harden the live appraisal path so Stage 2 begins from explicit evaluation discipline rather than vague prompt optimism.

**In Scope:**
- tighten prompt / schema / evaluation discipline for current live-authority ticks
- define explicit classes for:
  - acceptable output
  - degraded-but-usable output
  - invalid / forced-fallback output
- improve live-path observability and reviewability
- audit multi-day drift and failure accumulation, not only single-tick correctness
- document what Stage 2 considers safe appraisal deepening versus dangerous narrative drift

**Out of Scope:**
- no deferred-tick live-authority expansion yet
- no freeform memory system
- no identity-growth implementation yet
- no player influence redesign
- no world-generator redesign

## Selected Task
**Task Key:** P33-T1
**Description:** Audit prompt and output-format contract tightness — run a controlled multi-day simulation, collect raw LLM responses, classify every deviation between LLM output and deterministic baseline, and report which prompt instructions the LLM most frequently violates or stretches

## Recent Rounds
Most recent rounds (do not redo completed work):
- **round-0059** [PASSED] — Create a docs/ file that formally defines the Stage 1 T4 relational continuity c
- **round-0058** [PASSED] — Write a validation test that runs a multi-day bridged simulation where T4 produc
- **round-0057** [PASSED] — Write a validation test that runs a multi-day bridged simulation where both T2 (

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
