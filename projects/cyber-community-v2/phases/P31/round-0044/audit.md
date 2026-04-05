# Audit — Round round-0044

**Status:** PASSED  
**Completed:** 2026-04-05 12:42 UTC  
**Total cost:** $2.3929  
**Attempts:** 1

## Task
**P31-T3** — Wire appraisal router into simulate_day_bridged for live LLM appraisal on T1/T2/T4
Modify simulate_day_bridged in tick_bridge.py so that the three T1/T2/T4 signal-building steps call appraisal_router.route() instead of the bare builder functions (build_signal_from_t1_world_tick, build_signal_from_t2_influencer_tick, build_signal_from_t4_relationship_tick). The router already dispatches eligible ticks to the LLM path via shadow_runner and enforces guardrails with automatic deterministic fallback. After wiring, a live simulation day running under ENABLE_APPRAISAL_BRIDGE=true will produce AppraisalOutput values that may come from the LLM for T1, T2, and T4, while all settlement arithmetic, residual bookkeeping, and audit paths downstream of the signal remain unchanged.

