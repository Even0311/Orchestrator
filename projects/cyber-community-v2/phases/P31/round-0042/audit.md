# Audit — Round round-0042

**Status:** PASSED  
**Completed:** 2026-04-05 12:14 UTC  
**Total cost:** $1.0252  
**Attempts:** 1

## Task
**P31-T1** — Build appraisal router: LLM path for T1/T2/T4, deterministic path for all others
Create a single public function that accepts an AppraisalInput and returns an AppraisalOutput by dispatching T1 (information_exposure), T2 (social_interaction), and T4 (relationship_shift) to the live LLM appraisal path, while routing all deferred ticks (T3, T5, T6, T7, T8) to the existing deterministic fallback path. The router must enforce all blocking guardrails identified in failure_taxonomy.py before returning any LLM-produced output.

