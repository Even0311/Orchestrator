# P30: Offline / Shadow LLM Appraisal Validation
<!-- status: approved -->

## Phase Goal
Validate LLM appraisal against the extracted appraisal seam without allowing it to drive the authoritative live path yet.

## In Scope
- run shadow or offline appraisal comparisons
- define approved prompt / schema format
- compare LLM output against deterministic expectations and acceptance rules
- evaluate whether LLM outputs are useful, bounded, and composable
- identify failure classes and required guardrails

## Out of Scope
- no full production live control handoff
- no open-ended autonomy
- no replacing settlement with model judgment
- no prompt-only “magic” as a substitute for contract discipline

## Task Queue
- [x] P30-T1: Define the prompt schema and template contract for converting AppraisalInput into an LLM prompt and parsing the LLM response back into AppraisalOutput — Round round-0036 — Prompt schema and template contract for LLM appraisal
- [ ] P30-T2: Build a shadow appraisal runner that accepts AppraisalInput, invokes the LLM offline, and returns a parsed AppraisalOutput without touching the live path
- [ ] P30-T3: Define acceptance rules that specify per-field comparison criteria between LLM-produced and deterministic AppraisalOutput, distinguishing structural validity from semantic quality
- [ ] P30-T4: Build a comparison harness that runs both deterministic and shadow LLM paths on the same AppraisalInput, produces a structured diff report, and flags acceptance-rule violations
- [ ] P30-T5: Execute shadow comparisons across representative T1/T2/T4 test scenarios, collect structured diff reports, and persist raw results for analysis
- [ ] P30-T6: Classify observed failure modes from shadow results into categories, define required guardrails for each category, and document which failures are blocking vs acceptable for live handoff
