# Audit — Round round-0032

**Status:** PASSED  
**Completed:** 2026-04-04 13:52 UTC  
**Total cost:** $1.6657  
**Attempts:** 2

## Task
**P29-T3** — Tick-type-aware deterministic fallback mappings for T3/T5/T6/T7/T8
Extract the deferred-tick fallback logic from the generic else-branch in AppraisalOutput.from_deterministic_fallback into a dedicated module that maps each of T3, T5, T6, T7, and T8 to an explicit, individually documented AppraisalOutput. Each mapping must be independently testable and must produce a valid AppraisalOutput that passes all existing AppraisalOutput model validators.

