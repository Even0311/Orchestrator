# P29: Appraisal / Settlement Boundary Extraction
<!-- status: approved -->

## Phase Goal
Make the appraisal layer an explicit seam in the architecture, without yet introducing live LLM runtime.

## In Scope
- extract or formalize appraisal-facing input schema
- **input schema must accommodate all 8 tick types** (T1–T8), not just the 3 with active bridges,
  so that future tick coverage does not require schema redesign
- formalize appraisal output contract
- define what fields are advisory vs contract-bearing
- define how deterministic fallback works when no external appraisal is available
- make boundary testable and reviewable

## Out of Scope
- no production LLM integration yet
- no prompt experimentation as the main work
- no dynamic open-ended agent cognition system
- no removal of deterministic fallback behavior
- no granting live authority to T3/T5/T6/T7/T8 (schema accommodation only)

## Task Queue
- [x] P29-T1: Define a unified AppraisalInput schema that represents all 8 tick types with their context slices — Round round-0030 — Define unified AppraisalInput schema for all 8 tick types
- [x] P29-T2: Formalize the AppraisalOutput contract, marking each field as advisory or contract-bearing — Round round-0031 — Formalize AppraisalOutput contract with advisory vs contract
- [x] P29-T3: Define deterministic fallback mappings for T3/T5/T6/T7/T8 that produce valid AppraisalOutput without external appraisal — Round round-0032 — Tick-type-aware deterministic fallback mappings for T3/T5/T6
- [x] P29-T4: Refactor existing T1/T2/T4 bridges to emit through the new AppraisalInput → AppraisalOutput boundary — Round round-0033 — Wire T1/T2/T4 bridge builders to emit AppraisalInput and ret
- [x] P29-T5: Extract settlement as a pure consumer of AppraisalOutput, decoupled from tick-specific knowledge — Round round-0034 — Settlement as pure AppraisalOutput consumer, tick-specific k
- [ ] P29-T6: Add boundary contract tests that verify schema completeness, fallback correctness, and settlement isolation
