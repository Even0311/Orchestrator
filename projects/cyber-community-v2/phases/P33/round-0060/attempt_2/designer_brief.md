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

## Prior Round Failed — Issues to Address
The previous round for this task failed. Your new contract must address these issues:
Previous attempt 1 failed.
Task: Multi-day LLM appraisal deviation audit
Review rationale: The script is well-structured, correctly uses comparison_harness.run_comparison() for deviation detection, does not modify any forbidden files, handles failures gracefully, and produces a markdown report that maps deviations to OUTPUT_FORMAT rules. All 928 existing tests pass with no regressions. However, criterion 3(a) is materially unmet: raw_llm_response is always null because ComparisonReport does not expose ShadowRunResult.raw_response. The comment at line 347 acknowledges this gap but leaves it unresolved. Since the explicit purpose of P33-T1 is to collect raw LLM output for P33-T2 prompt tightening, shipping with raw_llm_response=null throughout makes the audit JSON incomplete for its stated downstream use. The fix is small (one additional shadow_runner.run() call in _run_tick_comparison) and does not require touching any protected modules.
Unmet: 3a (BLOCKER): Per-tick records include a raw_llm_response field, but it is hardcoded to None on every path (line 347: '"raw_llm_response": None,  # not exposed via ComparisonReport — use shadow_runner directly'). The field is structurally present but semantically absent. Since raw LLM text is the primary input for P33-T2 prompt tightening, always-null defeats the stated purpose of the audit. ShadowRunResult.raw_response (shadow_runner.py line 60) already holds this value — it just isn't threaded through ComparisonReport.
Fix required: raw_llm_response always None — fix required before this audit is useful for P33-T2. The simplest correct fix: in _run_tick_comparison(), after calling run_comparison(), also call shadow_runner.run(appraisal_input) to retrieve the ShadowRunResult directly, and use ShadowRunResult.raw_response as the raw_llm_response value. This does not violate criterion 7 (comparison_harness.run_comparison() is still used for deviation detection); it only supplements it to capture raw text that ComparisonReport intentionally omits. Alternatively, extend ComparisonReport with an optional raw_llm_response field and thread it through run_comparison() — but that modifies an existing module, which is higher-risk.
All code changes from the previous attempt have been rolled back. The working tree is clean. You must re-implement from scratch.

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
