# Evaluator Code Review — round-0054

**Task Key:** P32-T2
**Title:** Wire qualifying social events into world generator for T4 activation

## Acceptance Criteria
1. 1. In back/app/world/generator.py, _snapshot_from_phase() passes social_event=phase.social_event to the WorldSnapshot constructor.
2. 2. In back/app/world/arcs.py, at least 1 and no more than 3 ArcPhase definitions (days 3–16) have a SocialEventSpec with event_type in {SocialEventType.confrontation, SocialEventType.withdrawal}.
3. 3. For each qualifying arc day, get_world_snapshot(day).social_event is not None and its event_type is SocialEventType.confrontation or SocialEventType.withdrawal.
4. 4. For non-qualifying arc days (days 3–16 that were not given a SocialEventSpec), get_world_snapshot(day).social_event is None.
5. 5. Passing a qualifying day's WorldSnapshot to _detect_qualifying_t4_social_event() returns a non-None result.
6. 6. A multi-day simulation test over days 3–16 using the real get_world_snapshot (not injected) confirms T4 activation rate > 0.0 (at least one day activates the T4 event-aware path).
7. 7. Full determinism: the implementation uses no random module, no entropy, no time-dependent values — only hardcoded SocialEventSpec assignments on specific ArcPhase objects. The reviewer verifies this by code inspection (grep for 'random', 'os.urandom', 'time.time', 'uuid') AND by running pytest twice in independent processes and confirming identical pass/fail results for all count-dependent assertions.
8. 8. All pytest tests pass (python -m pytest tests/ -v from back/): zero failures, zero errors. This includes any updated assertions in test_p32_t1_t4_live_audit.py and all new tests.
9. 9. A new test file exists under back/tests/ that programmatically verifies criteria 2–6.

## Review Focus
- Verify _snapshot_from_phase() now passes social_event through — this is the core wire-through fix.
- Verify qualifying ArcPhase definitions use only confrontation or withdrawal event types.
- Verify qualifying event count is 1–3 out of 14 arc days (low frequency).
- Verify full determinism by code inspection: grep the changed files for 'import random', 'os.urandom', 'time.time', 'uuid', 'seed' — none should appear. Then run pytest twice in separate invocations and confirm identical results.
- Run pytest twice independently (two separate 'python -m pytest tests/ -v' invocations) and confirm identical pass/fail outcomes to validate cross-run stability of count-dependent criteria.
- Verify no forbidden files were modified.
- Verify existing test logic was not deleted, only narrowed where assertions were invalidated by the new behavior.

## Code Changes (git diff)
```diff

diff --git a/back/app/world/arcs.py b/back/app/world/arcs.py
index cf3c704..e01b683 100644
--- a/back/app/world/arcs.py
+++ b/back/app/world/arcs.py
@@ -20,7 +20,7 @@ Current arcs:
 from __future__ import annotations
 from dataclasses import dataclass, field
 from typing import Optional
-from app.domain.enums import District, FeedTone
+from app.domain.enums import District, FeedTone, SocialEventType
 from app.domain.models import SocialEventSpec
 
 
@@ -276,6 +276,10 @@ _ARC2 = WorldArc(
                 FeedSpec("Signal District Monitor",  District.signal_district,  "Loud voices split: some back platforms, others back the builders",             FeedTone.analytical),
                 FeedSpec("Workshop Quarter Digest",  District.workshop_quarter, "Builders dismiss financial arguments: infrastructure serves the long game",    FeedTone.hopeful),
             ],
+            social_event=SocialEventSpec(
+                event_type=SocialEventType.confrontation,
+                note="Ideological confrontation between platform defenders and decentralization builders",
+            ),
         ),
 
         # ── Day 14 ── Commons settles
@@ -308,6 +312,10 @@ _ARC2 = WorldArc(
                 FeedSpec("Signal District Monitor",  District.signal_district,  "Fringe theories crossing into mainstream discourse — unusual signal",          FeedTone.analytical),
                 FeedSpec("Commons Observer",         District.commons,          "Some residents report feeling manipulated by recent attention cycles",          FeedTone.anxious),
             ],
+            social_event=SocialEventSpec(
+                event_type=SocialEventType.withdrawal,
+                note="Residents deliberately disengaging from mainstream attention cycles",
+            ),
         ),
 
         # ── Day 16 ── New consensus
diff --git a/back/app/world/generator.py b/back/app/world/generator.py
index 8c503ce..a9cfe88 100644
--- a/back/app/world/generator.py
+++ b/back/app/world/generator.py
@@ -63,6 +63,7 @@ def _snapshot_from_phase(world_day: int, phase: ArcPhase) -> WorldSnapshot:
             "quote": phase.influencer_quote,
         },
         publicFeedPool=feed_items,
+        social_event=phase.social_event,
     )
 
 

diff --git a/back/tests/test_p32_t2_social_event_wiring.py b/back/tests/test_p32_t2_social_event_wiring.py
new file mode 100644
index 0000000..6ce4b63
--- /dev/null
+++ b/back/tests/test_p32_t2_social_event_wiring.py
@@ -0,0 +1,454 @@
+"""
+P32-T2 — Social Event Wiring Tests.
+
+Verifies that:
+  1. get_world_snapshot() correctly passes social_event from ArcPhase to WorldSnapshot
+     (_snapshot_from_phase wiring — acceptance criterion 1).
+  2. At least 1 and no more than 3 arc phases in days 3–16 have a qualifying
+     SocialEventSpec (confrontation or withdrawal) (criterion 2).
+  3. get_world_snapshot(qualifying_day).social_event is not None and has the
+     correct qualifying event_type (criterion 3).
+  4. get_world_snapshot(non-qualifyin
...(truncated)
```

## Your Task
1. Check each acceptance criterion against the actual code changes
2. Pay special attention to the review focus items
3. If existing test files were modified, examine whether the modifications are justified
4. Verify tests pass and no regressions were introduced

Write `review_verdict.json` with:
- `verdict` — PASS, FAIL, or REVISION_REQUIRED
- `confidence` — high, medium, or low
- `met_criteria` — list of criteria that passed
- `unmet_criteria` — list of criteria that failed
- `blocker_fixes` — must-fix issues (empty if PASS)
- `non_blocking_suggestions` — nice-to-have improvements
- `rationale` — explanation of verdict
