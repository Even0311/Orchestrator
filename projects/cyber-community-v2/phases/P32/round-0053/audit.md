# Audit — Round round-0053

**Status:** ESCALATED  
**Completed:** 2026-04-06 11:23 UTC  
**Total cost:** $2.5416  
**Attempts:** 2

## Task
**P32-T2** — Wire qualifying social events into world generator so T4 can trigger
Modify the world generator so that WorldSnapshot objects carry a non-None social_event field with a qualifying SocialEventType (confrontation or withdrawal) on roughly 1-in-7 days. This gives the T4 event-aware detection path an actual qualifying event to detect during live simulation runs, closing the gap where T4 activation rate is permanently zero because no qualifying event ever reaches the world snapshot.

## Escalation Reason
```
Round round-0053 failed after 2 attempt(s).

Attempt 1:
  Task: Wire qualifying social events into world generator so T4 can trigger
  Verdict: FAIL (confidence: high)
  Rationale: Hard gate failure: allowed_files: Files outside allowed patterns: back/tests/test_social_event_schema.py
  Fix required: allowed_files: Files outside allowed patterns: back/tests/test_social_event_schema.py

Attempt 2:
  Task: Wire qualifying social events into world generator so T4 can trigger
  Verdict: FAIL (confidence: high)
  Rationale: Hard gate failure: allowed_files: Files outside allowed patterns: back/tests/test_p32_t2_social_event_wire.py; forbidden_files: Forbidden files modified: back/tests/test_p32_t2_social_event_wire.py; pytest: AILED tests/test_p32_t1_t4_live_audit.py::TestWorldSocialEventAlwaysNone::test_social_event_none_for_every_day
FAILED tests/test_p32_t1_t4_live_audit.py::TestWorldSocialEventAlwaysNone::test_no_day_has_social_event
FAILED tests/test_p32_t1_t4_live_audit.py::TestWorldSocialEventAlwaysNone::test_social_event_none_inline_generator_call
FAILED tests/test_social_event_schema.py::test_generator_produces_social_event_none
======================== 4 failed, 894 passed in 8.27s =========================

  Fix required: allowed_files: Files outside allowed patterns: back/tests/test_p32_t2_social_event_wire.py
  Fix required: forbidden_files: Forbidden files modified: back/tests/test_p32_t2_social_event_wire.py
  Fix required: pytest: AILED tests/test_p32_t1_t4_live_audit.py::TestWorldSocialEventAlwaysNone::test_social_event_none_for_every_day
FAILED tests/test_p32_t1_t4_live_audit.py::TestWorldSocialEventAlwaysNone::test_no_day_has_social_event
FAILED tests/test_p32_t1_t4_live_audit.py::TestWorldSocialEventAlwaysNone::test_social_event_none_inline_generator_call
FAILED tests/test_social_event_schema.py::test_generator_produces_social_event_none
======================== 4 failed, 894 passed in 8.27s =========================

```
