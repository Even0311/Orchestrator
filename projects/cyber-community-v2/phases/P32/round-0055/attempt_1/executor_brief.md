# Executor Brief — round-0055

## Task Contract
**Task Key:** P32-T3
**Title:** Complete T4 appraisal-to-residual pipeline for qualifying social events
**Objective:** Make the T4 relationship_shift tick produce a real, persisted relational residual when a qualifying social event (confrontation or withdrawal) is detected, closing the gap between event detection and downstream relational effect.

**Exact Scope:**
- Modify the T4 signal builder so that when a qualifying social event is detected, the resulting AppraisalSignal carries negative valence, a trust-decrease shift, and aftershock_days >= 1 — the three conditions required by the existing residual-creation gate.
- Ensure the qualifying social event context (from world.social_event) is available to the T4 signal builder so it can branch on event type.
- Verify that the existing residual-creation gate in the settlement path opens for these signals and that a relational residual is actually persisted to ctx.new_residuals / DaySnapshot.pending_residuals.
- Verify that _adjust_t4() activates on the next day when a carried relational residual exists from the previous day's T4 output.
- Add or extend tests that confirm: (a) a qualifying event produces a T4 signal with aftershock_days >= 1; (b) settlement creates a non-None relational residual from that signal; (c) the residual persists cross-day and is picked up by _adjust_t4() on the following day.

**Constraints:**
- AppraisalSignal v1 schema is frozen — do not add, remove, or rename any fields.
- Settlement logic in appraisal_settlement.py must remain engine-authoritative — the T4 builder produces signals, settlement decides state changes.
- The existing residual-creation gate conditions (negative valence, trust decrease, absorption >= partial) must not be weakened or bypassed — the signal must genuinely satisfy them.
- The deterministic fallback path must remain functional — when no qualifying event is present, T4 must continue producing the existing default positive/neutral signal.
- Do not modify the T4_QUALIFYING_EVENT_TYPES set or the _detect_qualifying_t4_social_event() detection logic (this was established in round-0054).
- Do not alter the LLM appraisal router or its fallback behavior — changes are limited to the deterministic signal builder path.
- Cross-day residual persistence mechanism (DaySnapshot.pending_residuals, world_continuity.py carryover) must not be restructured.

**Forbidden Files (DO NOT modify):**
- `back/app/domain/enums.py`
- `back/app/domain/models.py`
- `back/app/world/*.py`
- `back/app/engines/growth_*.py`
- `back/app/engines/influence_*.py`
- `back/app/seed/**`
- `front/**`
- `docs/**`

**Non-Goals (DO NOT do):**
- Expanding bridge coverage to deferred ticks (T3, T5, T6, T7, T8).
- Adding new social event types or modifying the world generator's event production.
- Modifying the AppraisalSignal schema.
- Redesigning settlement arithmetic or residual data structures.
- Introducing LLM authority changes or modifying the LLM appraisal path.
- Adding UI, dashboard, or chatbot features.
- Activating T4 negative residuals through any path other than genuine qualifying social events.

**Acceptance Criteria:**
- A multi-day simulation that includes a qualifying social event (confrontation or withdrawal) produces at least one non-None relational residual from the T4 tick.
- The relational residual created by T4 persists into the next day's DaySnapshot.pending_residuals.
- _adjust_t4() returns a non-None adjustment on the day following a T4 residual creation (i.e., it is no longer permanently dormant when qualifying events have occurred).
- When no qualifying social event is present, the T4 signal remains unchanged from its current default behavior (positive valence, mild_increase trust, aftershock_days=0).
- All existing tests pass (pytest back/tests/ -v) with zero failures.
- At least one new test verifies the full chain: qualifying event → T4 signal with aftershock_days >= 1 → settlement creates relational residual → residual carried to next day → _adjust_t4() activates.

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
