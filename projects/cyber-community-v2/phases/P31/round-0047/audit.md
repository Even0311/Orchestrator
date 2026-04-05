# Audit — Round round-0047

**Status:** PASSED  
**Completed:** 2026-04-05 13:31 UTC  
**Total cost:** $1.4246  
**Attempts:** 1

## Task
**P31-T6** — Multi-day live simulation audit: LLM appraisal fallback rates, output stability, and deterministic-path regression
Write a test module that runs a multi-day simulation (3–5 days) with LLM appraisal active for T1/T2/T4, using mocked LLM responses to avoid real API calls, and asserts that fallback rates are within expected bounds, appraisal signals remain within valid ranges, deferred ticks always use the deterministic path, and the simulation completes without exceptions across all days.

