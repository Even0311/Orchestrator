# Designer Brief — round-0066

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

## Recently Completed Tasks (same phase)
- P33-T1: Audit prompt and output-format contract tightness — run a controlled multi-day simulation, collect raw LLM responses, classify every deviation between LLM output and deterministic baseline, and report which prompt instructions the LLM most frequently violates or stretches — accepted by human
- P33-T2: Tighten prompt schema and output-format instructions to close the specific deviation patterns found in T1 — reduce ambiguity in field-level guidance, add explicit negative examples for the most common failure modes, and verify tightened prompts reduce deviation rate in a repeat audit — Round round-0061 — Tighten prompt schema and output-format instructions to redu
- P33-T3: Implement rolling degradation-rate tracking — add per-tick-type failure and degradation counters to the audit log, compute a rolling window degradation rate, and define the threshold above which the live path must auto-fallback to deterministic output — Round round-0062 — Rolling degradation-rate tracking with auto-fallback thresho
- P33-T4: Implement automatic recovery logic — define when the system retries LLM after an extended fallback period, add exponential backoff for repeated failures, and verify the fallback-to-retry cycle works correctly across multi-day simulation — Round round-0063 — Automatic recovery logic with exponential backoff after exte
- P33-T5: Run a full multi-day drift audit (30+ simulated days) — measure state-value drift, growth-buffer accumulation patterns, residual stacking behavior, and degradation-rate trends over time, and flag any unbounded or monotonic drift patterns — Round round-0064 — Multi-day drift audit: 30+ day state, growth, residual, and

## Selected Task
**Task Key:** P33-T6
**Description:** Write the Stage 2 appraisal safety contract — document explicitly what constitutes safe appraisal deepening versus dangerous narrative drift, define the preconditions that must hold before any new tick gains live LLM authority, and specify the monitoring gates Stage 2 must pass

## Recent Rounds
Most recent rounds (do not redo completed work):
- **round-0065** [REDO_CONSUMED] — Write a specification document (docs/stage2_appraisal_safety_contract.md) that e
- **round-0064** [PASSED] — Create a drift audit tool that runs a 30+ simulated-day session and systematical
- **round-0063** [PASSED] — Extend DegradationTracker with explicit recovery logic so the system does not na

## Prior Round Failed — Issues to Address
The previous round for this task failed. Your new contract must address these issues:
Human rejected round round-0065 and requested a redo.
Action: reject_and_redo
Human note: generated documents is not good enough. There are some errors that mentioned by the evaluator did not get fixed
All code changes from prior attempts have been rolled back. The working tree is clean. You must re-implement from scratch.

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
