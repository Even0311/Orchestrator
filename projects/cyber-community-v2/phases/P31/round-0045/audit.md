# Audit — Round round-0045

**Status:** PASSED  
**Completed:** 2026-04-05 13:12 UTC  
**Total cost:** $4.3261  
**Attempts:** 2

## Task
**P31-T4** — Structured audit logging for per-tick LLM appraisal path selection
Build a structured audit logging layer that captures, for every appraisal invocation inside simulate_day_bridged, exactly which path was taken (LLM vs deterministic), the raw LLM text output, the ComparisonVerdict produced by acceptance_rules, and any fallback event with its classified failure category. The log must be machine-readable and returned alongside the SimulationResult so that calling code can inspect or persist it. This requires extending RouterResult with a raw_llm_response field so that raw LLM text flows from ShadowRunResult through the router into the audit entry.

