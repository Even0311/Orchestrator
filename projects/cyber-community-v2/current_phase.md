# P31: First Live LLM Appraisal Integration
<!-- status: approved -->

## Phase Goal
Introduce the first controlled live LLM appraisal path into the agent loop.

## In Scope
- insert LLM into the appraisal seam only
- **first live authority is limited to T1 / T2 / T4 only** — deferred ticks (T3/T5/T6/T7/T8)
  remain on deterministic fallback even though the schema can represent them
- keep settlement / bookkeeping engine-authoritative
- preserve deterministic validation / fallback / guardrail path
- limit LLM responsibility to the approved appraisal contract
- audit resulting outputs and system stability

## Out of Scope
- no full agent autonomy explosion
- no replacement of simulation engine by the LLM
- no uncontrolled freeform memory/personality architecture expansion
- no multiplayer-scale live society rollout
- no granting live LLM authority to T3/T5/T6/T7/T8 (deferred to Stage 2)

## Task Queue
- [x] P31-T1: Build an appraisal router that inspects tick type and dispatches T1/T2/T4 to the LLM appraisal path while sending all other ticks to the existing deterministic path — Round round-0042 — Build appraisal router: LLM path for T1/T2/T4, deterministic
- [ ] P31-T2: Add a runtime validation gate that applies P30 acceptance rules and guardrails to each live LLM appraisal result, falling back to deterministic output on any rejection
- [ ] P31-T3: Integrate the appraisal router and validation gate into the live agent tick loop so LLM appraisal runs in-line for eligible ticks during actual simulation
- [ ] P31-T4: Build structured audit logging that records per-tick path selection, LLM raw output, validation verdict, and fallback events for every appraisal invocation
- [ ] P31-T5: Verify that settlement and bookkeeping engines produce correct results when consuming LLM-sourced appraisal output, confirming contract compatibility end-to-end
- [ ] P31-T6: Run multi-day live simulation with LLM appraisal active for T1/T2/T4, audit fallback rates and output stability, and confirm no regression in deterministic-path ticks
