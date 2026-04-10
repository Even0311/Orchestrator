# Executor Brief — round-0059

## Task Contract
**Task Key:** P32-T7
**Title:** Write Stage 1 T4 relational continuity contract notes
**Objective:** Create a docs/ file that formally defines the Stage 1 T4 relational continuity contract — what constitutes valid T4 output after P32 closure, what activation frequency is expected, what the wake chain guarantees are, and what remains deferred to Stage 2.

**Exact Scope:**
- Create a new file `docs/stage1_t4_relational_continuity_contract.md` that serves as the Stage 1 closure contract for T4 relational continuity
- Document what constitutes valid T4 output: the three negative activation patterns (P0 confrontation/withdrawal, Pattern A contested endorsement, Pattern B high-intensity unilateral disclosure) and the default positive path
- Document the activation frequency expectation: event-driven only, controlled by world generator's qualifying event emission rate (not probabilistic or drift-based)
- Document the full T4 wake chain lifecycle as now validated: qualifying event → negative base signal → _adjust_t4() with carried residual → gate open → residual creation → cross-day carry → step → expire
- Document the wake chain depth limit (1 day maximum) and the self-limiting property
- Document the _adjust_t4() hard stops and bounded adjustment semantics that are now active (not dormant)
- Document T2/T4 same-day composition safety as validated by P32-T5
- Document T4 residual cross-day carry and T1/T2 non-regression as validated by P32-T6
- Document what remains deferred to Stage 2: T3/T5/T6/T7/T8 bridge expansion, multi-target routing, richer event taxonomy, LLM-driven appraisal for T4
- Document the test modules that protect the T4 relational continuity contract

**Constraints:**
- The document must be factual and grounded in the current codebase state — no aspirational or speculative content
- All claims about behavior must be verifiable by reading the engine code or running the existing test suite
- The document must not contradict the existing `docs/t4_negative_behavior_contract.md` — it extends and contextualizes it for Stage 1 closure, not replaces it
- The document must not contradict `docs/decisions_summary.md` or `docs/phase25_continuity_status.md`
- Use concrete values (enum names, threshold numbers, field names) rather than vague descriptions
- The document must clearly separate established contracts (tested, load-bearing) from calibration artifacts (run-specific observations)

**Forbidden Files (DO NOT modify):**
- `back/app/engines/*.py`
- `back/app/domain/*.py`
- `back/app/seed/**`
- `back/app/world/*.py`
- `back/app/services/*.py`
- `back/app/api/**`
- `back/tests/**`
- `back/tools/**`
- `front/**`
- `docs/t4_negative_behavior_contract.md`
- `docs/decisions_summary.md`
- `docs/phase25_continuity_status.md`
- `docs/phase25_roadmap_alignment.md`
- `docs/phase25_t4_freeze_boundary.md`
- `docs/p28_t4_pattern_catalog.md`
- `docs/p32_t4_blocker_audit.md`

**Non-Goals (DO NOT do):**
- Do not modify any engine, domain, seed, world, or test code
- Do not modify any existing docs/ files
- Do not propose new features, new patterns, or new activation paths
- Do not design Stage 2 — only name what is deferred
- Do not add or modify tests
- Do not create audit tooling or scripts
- Do not redesign the T4 pipeline — document what exists

**Acceptance Criteria:**
- A new file `docs/stage1_t4_relational_continuity_contract.md` exists
- The document contains a section defining valid T4 output: all three negative patterns (P0, Pattern A, Pattern B) are named with their exact activation conditions (event types, reciprocity, intensity values)
- The document contains a section on activation frequency that states T4 is event-driven and references the world generator's controlled emission of qualifying events
- The document contains a section on wake chain lifecycle that traces the full path from qualifying event to residual expiry, including the gate conditions (valence==negative, trust_shift in {mild_decrease, strong_decrease}, absorption not in {none, surface})
- The document states the wake chain depth limit is 1 day with days_remaining=1 and explains the self-limiting property
- The document contains a section on _adjust_t4() that lists at least the trust_shift hard stop (capped at mild_decrease), closeness_delta bounds ([-2, +2]), and absorption ceiling (deep)
- The document contains a section on T2/T4 same-day composition safety referencing settlement order (T2 before T4)
- The document contains a section on cross-day residual carry confirming T4 residuals coexist with T1/T2 residuals without interference
- The document contains a section listing what is deferred to Stage 2, including at minimum: T3/T5/T6/T7/T8 bridge expansion, multi-target routing, and LLM-driven T4 appraisal
- The document lists the test modules that protect the T4 contract (at minimum: test_t4_behavior_contract.py, test_residual_continuity_audit.py, test_residual_persistence.py)
- No existing files are modified (git diff shows only the new file)
- The full test suite passes: `cd back && python -m pytest tests/ -v` returns 0 exit code

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
