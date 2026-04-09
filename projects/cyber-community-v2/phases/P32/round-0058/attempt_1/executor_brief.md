# Executor Brief — round-0058

## Task Contract
**Task Key:** P32-T6
**Title:** Audit T4 residual cross-day wake behavior and T1/T2 non-regression
**Objective:** Write a validation test that runs a multi-day bridged simulation where T4 produces relational residuals on day N, then verifies those residuals carry over to day N+1 and N+2, appear in the subsequent tick bridge context, produce observable downstream effects, and do not regress the existing T1/T2 residual continuity that was already stable.

**Exact Scope:**
- Add a new test file that exercises a 3+ day bridged simulation where day 1 triggers a T4 relational residual (via a qualifying social event on the world snapshot)
- Verify that the T4 relational residual appears in the carried residuals list passed to day 2
- Verify that the carried T4 relational residual's days_remaining decrements correctly across days and expires when expected
- Verify that the carried T4 relational residual produces an observable state effect (trust/closeness/stress/mood delta) on the day it is stepped, compared to a baseline run without the residual
- Verify that T1 public residuals created on the same or subsequent days coexist with T4 relational residuals without duplication, corruption, or interference
- Verify that T2 influencer residuals created on the same or subsequent days coexist with T4 relational residuals without duplication, corruption, or interference
- Verify that pre-existing T1/T2 residual continuity behavior (creation, carry, step, expire) is not regressed by the presence of T4 relational residuals in the same residual pool

**Constraints:**
- All verification must use simulate_day_bridged() — do not call internal bridge functions directly
- Do not modify any engine, domain, or seed files — this is a pure audit/validation task
- Use only the existing public API of simulate_day_bridged() and its return values
- Test must use a qualifying SocialEventSpec (e.g., confrontation) to trigger T4 residual creation — do not fabricate residuals manually for the cross-day carry tests
- ResidualKind.relational for T4 residuals must be distinguished from ResidualKind.influencer for T2 residuals in assertions
- All state values must remain within valid bounds [0, 100] throughout the multi-day run

**Forbidden Files (DO NOT modify):**
- `back/app/engines/*.py`
- `back/app/domain/*.py`
- `back/app/seed/**`
- `back/app/world/*.py`
- `back/app/services/*.py`
- `back/app/api/**`
- `front/**`
- `docs/**`

**Non-Goals (DO NOT do):**
- Do not fix or modify any engine behavior — only observe and assert
- Do not extend bridge coverage to T3/T5/T6/T7/T8
- Do not add new residual kinds or modify the ResidualEntry schema
- Do not add audit tooling scripts — this is a test, not a reporting tool
- Do not test LLM appraisal paths
- Do not modify existing test files

**Acceptance Criteria:**
- A new test file exists under back/tests/ that runs with `python -m pytest tests/<file> -v` from back/ and all tests pass
- At least one test demonstrates a 3-day simulation where a T4 relational residual is created on day 1, carried to day 2 with days_remaining decremented by 1, and either carried again or expired on day 3
- At least one test shows that the T4 relational residual produces a measurable state delta (compared to a no-residual baseline) on the day it is stepped
- At least one test runs a multi-day simulation that produces both T1 public residuals and T4 relational residuals, and asserts that both kinds coexist in the residual pool without duplication (count by kind matches expected)
- At least one test runs a multi-day simulation that produces both T2 influencer residuals and T4 relational residuals, and asserts coexistence without interference
- At least one test verifies that T1 residual continuity (creation rate, carry, step, expire lifecycle) is not degraded when T4 relational residuals are also present — the T1 residual count and lifecycle must match a T4-absent baseline
- No existing tests are broken (full test suite passes)
- All assertions use concrete values or delta comparisons, not vague 'is not None' checks

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
