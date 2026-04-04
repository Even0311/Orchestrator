# Audit — Round round-0033

**Status:** PASSED  
**Completed:** 2026-04-04 14:02 UTC  
**Total cost:** $2.0441  
**Attempts:** 1

## Task
**P29-T4** — Wire T1/T2/T4 bridge builders to emit AppraisalInput and return AppraisalOutput
Refactor the three active bridge builders (build_signal_from_t1_world_tick, build_signal_from_t2_influencer_tick, build_signal_from_t4_relationship_tick) so that each one constructs an AppraisalInput, passes it through AppraisalOutput.from_deterministic_fallback (or a per-tick translation layer), and returns an AppraisalOutput instead of an AppraisalSignal. Add a thin adapter that converts an AppraisalOutput to the existing AppraisalSignal so that simulate_day_bridged can continue to call _apply_bridge_signal unchanged. All existing 441 tests must continue to pass.

