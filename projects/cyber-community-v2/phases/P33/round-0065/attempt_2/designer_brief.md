# Designer Brief — round-0065

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
- **round-0064** [PASSED] — Create a drift audit tool that runs a 30+ simulated-day session and systematical
- **round-0063** [PASSED] — Extend DegradationTracker with explicit recovery logic so the system does not na
- **round-0062** [PASSED] — Add per-tick-type failure and degradation counters to the appraisal audit infras

## Prior Round Failed — Issues to Address
The previous round for this task failed. Your new contract must address these issues:
Previous attempt 1 failed.
Task: Stage 2 appraisal safety contract document
Review rationale: The document meets all 8 acceptance criteria — it exists, is well-structured, defines 3 concrete safe/unsafe criteria with examples, has an 8-tick authority table with individual deferred-tick preconditions, provides 7 numeric monitoring gates, specifies a 4-level graduated response referencing the correct infrastructure, forbids known anti-patterns consistent with decisions_summary.md, and uses concrete (non-TBD) threshold values throughout. All 1061 tests pass with no regressions.

However, two blocker-level factual inaccuracies exist in the monitoring gate specifications. First, Gate G3's fail threshold is stated as >=10 consecutive days of monotonic drift, but audit_drift.py only generates 'fail' at >=20 days (= monotonic_window * 2); 10 days produces a 'warn'. This error propagates into three per-tick precondition sections (T3, T5 implicitly, T6). Second, the Level 1 graduated response describes a warn condition for 7-9 day monotonic spans that audit_drift.py cannot detect with window=10. Both errors are verifiable against the actual code (back/tools/audit_drift.py, build_dimension_verdict, line 336). Since this document is a safety specification intended to guide Stage 2 implementation, having wrong fail thresholds for a critical monitoring gate is a meaningful defect — not a stylistic issue. These two items require correction before the document can serve as an authoritative contract.
Fix required: G3 fail threshold is factually wrong: Section 5 Gate G3 states 'No single dimension rising or falling for >=10 consecutive days' as the failure gate. But audit_drift.py::build_dimension_verdict (line 336) uses: `status = 'fail' if longest['length'] >= monotonic_window * 2 else 'warn'`. With the default monotonic_window=10, a span of >=10 days produces 'warn', not 'fail'. Failure only triggers at >=20 consecutive days. The same wrong threshold appears in §3.1 item 4, §3.2 item 4, §3.3 item 4. A Stage 2 implementer following this spec would wire G3 monitoring to fail at 10 days when the referenced tool only fails at 20 — creating a phantom gate breach signal. Fix: correct G3 to state 'warn at >=10 consecutive days; fail at >=20 consecutive days (= monotonic_window * 2)'.
Fix required: Level 1 monotonic drift warn condition is factually impossible: Section 6 Level 1 states 'a monotonic drift span of 7-9 days is detected by audit_drift.py (warn range: below the 10-day fail threshold)'. But detect_monotonic_drift(window=10) only flags spans where streak_len >= window (i.e., >=10). Spans of 7-9 days are not flagged at all by the tool with its default window. Fix: remove or correct this — Level 1 monotonic warn should reference >=10-day spans (which generate 'warn' from build_dimension_verdict), not 7-9-day spans which audit_drift.py cannot detect.
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
