# Audit — Round round-0062

**Status:** PASSED  
**Completed:** 2026-04-10 05:14 UTC  
**Total cost:** $2.7262  
**Attempts:** 1

## Task
**P33-T3** — Rolling degradation-rate tracking with auto-fallback threshold
Add per-tick-type failure and degradation counters to the appraisal audit infrastructure, compute a rolling-window degradation rate, and define the threshold above which the live LLM path must auto-fallback to deterministic output for that tick type.

