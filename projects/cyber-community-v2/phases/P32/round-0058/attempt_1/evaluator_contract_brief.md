# Evaluator Contract Review — round-0058

**Task Key:** P32-T6
**Title:** Audit T4 residual cross-day wake behavior and T1/T2 non-regression

## Proposed Acceptance Criteria
1. A new test file exists under back/tests/ that runs with `python -m pytest tests/<file> -v` from back/ and all tests pass
2. At least one test demonstrates a 3-day simulation where a T4 relational residual is created on day 1, carried to day 2 with days_remaining decremented by 1, and either carried again or expired on day 3
3. At least one test shows that the T4 relational residual produces a measurable state delta (compared to a no-residual baseline) on the day it is stepped
4. At least one test runs a multi-day simulation that produces both T1 public residuals and T4 relational residuals, and asserts that both kinds coexist in the residual pool without duplication (count by kind matches expected)
5. At least one test runs a multi-day simulation that produces both T2 influencer residuals and T4 relational residuals, and asserts coexistence without interference
6. At least one test verifies that T1 residual continuity (creation rate, carry, step, expire lifecycle) is not degraded when T4 relational residuals are also present — the T1 residual count and lifecycle must match a T4-absent baseline
7. No existing tests are broken (full test suite passes)
8. All assertions use concrete values or delta comparisons, not vague 'is not None' checks

## Proposed Review Focus
- Cross-day residual carry: are T4 relational residuals actually being carried via initial_residuals between days, not manually injected?
- Non-regression: does the test actually compare T1/T2 behavior with and without T4 residuals present, or does it only test T4 in isolation?
- Residual kind distinction: are assertions checking ResidualKind.relational vs ResidualKind.influencer vs default public, not just counting total residuals?
- State delta isolation: when asserting T4 residual effects, is the test comparing against a matched baseline to isolate the residual's contribution?
- Bound checking: are all trust, closeness, stress, mood, and growth values asserted to be within [0, 100]?

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
