# P33: Appraisal Discipline Hardening
<!-- status: approved -->

## Phase Goal
Harden the live appraisal path so Stage 2 begins from explicit evaluation discipline rather than vague prompt optimism.

## In Scope
- tighten prompt / schema / evaluation discipline for current live-authority ticks
- define explicit classes for:
  - acceptable output
  - degraded-but-usable output
  - invalid / forced-fallback output
- improve live-path observability and reviewability
- audit multi-day drift and failure accumulation, not only single-tick correctness
- document what Stage 2 considers safe appraisal deepening versus dangerous narrative drift

## Out of Scope
- no deferred-tick live-authority expansion yet
- no freeform memory system
- no identity-growth implementation yet
- no player influence redesign
- no world-generator redesign

## Task Queue
- [x] P33-T1: Audit prompt and output-format contract tightness — run a controlled multi-day simulation, collect raw LLM responses, classify every deviation between LLM output and deterministic baseline, and report which prompt instructions the LLM most frequently violates or stretches — accepted by human
- [x] P33-T2: Tighten prompt schema and output-format instructions to close the specific deviation patterns found in T1 — reduce ambiguity in field-level guidance, add explicit negative examples for the most common failure modes, and verify tightened prompts reduce deviation rate in a repeat audit — Round round-0061 — Tighten prompt schema and output-format instructions to redu
- [x] P33-T3: Implement rolling degradation-rate tracking — add per-tick-type failure and degradation counters to the audit log, compute a rolling window degradation rate, and define the threshold above which the live path must auto-fallback to deterministic output — Round round-0062 — Rolling degradation-rate tracking with auto-fallback thresho
- [x] P33-T4: Implement automatic recovery logic — define when the system retries LLM after an extended fallback period, add exponential backoff for repeated failures, and verify the fallback-to-retry cycle works correctly across multi-day simulation — Round round-0063 — Automatic recovery logic with exponential backoff after exte
- [ ] P33-T5: Run a full multi-day drift audit (30+ simulated days) — measure state-value drift, growth-buffer accumulation patterns, residual stacking behavior, and degradation-rate trends over time, and flag any unbounded or monotonic drift patterns
- [ ] P33-T6: Write the Stage 2 appraisal safety contract — document explicitly what constitutes safe appraisal deepening versus dangerous narrative drift, define the preconditions that must hold before any new tick gains live LLM authority, and specify the monitoring gates Stage 2 must pass
