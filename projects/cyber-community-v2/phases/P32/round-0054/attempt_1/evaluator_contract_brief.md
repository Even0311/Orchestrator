# Evaluator Contract Review — round-0054

**Task Key:** P32-T2
**Title:** World generator produces qualifying social events at controlled low frequency

## Proposed Acceptance Criteria
1. 1. In the day range 3–60, at least 6 and at most 14 days have a non-None social_event on their WorldSnapshot (i.e., 10%–25% of the 58 days).
2. 2. At least 2 days in the range 3–60 produce a social_event with event_type in {confrontation, withdrawal} (T4-qualifying).
3. 3. At least 1 day in the arc-covered range (days 3–16) has a non-None social_event.
4. 4. At least 1 day in the fallback range (days 17–60) has a non-None social_event.
5. 5. For days 61–120 (extended fallback range), get_world_snapshot(day) returns a non-None social_event for at least 1 day but no more than 30% of those days (i.e., at most 18 out of 60 days).
6. 6. _snapshot_from_phase propagates ArcPhase.social_event to WorldSnapshot.social_event.
7. 7. World generation remains deterministic — calling get_world_snapshot(d) twice for any d in 3–60 returns identical WorldSnapshot objects.
8. 8. All existing tests pass without modification (python -m pytest back/tests/ -v).
9. 9. A new test file exists under back/tests/ that verifies criteria 1–7 by calling get_world_snapshot for the relevant day ranges.

## Proposed Review Focus
- Count non-None social_event instances across days 3–60 and verify the count is between 6 and 14 inclusive.
- Count T4-qualifying events (confrontation or withdrawal) and verify at least 2 exist.
- Verify at least 1 event in arc days (3–16) and at least 1 in fallback days (17–60).
- Verify fallback range coverage: for days 61–120, count non-None social_event and confirm at least 1 and at most 18.
- Verify _snapshot_from_phase passes social_event through from ArcPhase to WorldSnapshot.
- Verify determinism by calling get_world_snapshot twice per day.
- Verify no forbidden files were modified.
- Verify all existing tests still pass.

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
