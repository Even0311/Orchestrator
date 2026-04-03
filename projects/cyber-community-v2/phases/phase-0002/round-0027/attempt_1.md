# Attempt 1

**Task:** Calibrate T4 signal intensity ranges for Pattern A and B

## Execution Evidence (self-reported)
- Summary: You're out of extra usage · resets 1am (Australia/Sydney)
- Commands run: (none)
- Test results: (not run)
- Unresolved issues: (none)

*(See execution_report_attempt_1.json for git-verified evidence)*

## Reviewer Verdict: FAIL (confidence: high)
Hard gate: pytest failed. settlement.py::test_validate_raises_unknown_target PASSED [  1%]
tests/test_appraisal_settlement.py::test_validate_growth_with_none_absorption_is_hard_failure PASSED [  1%]
tests/test_appraisal_settlement.py::test_validate_absorption_none_with_aftershock_is_hard_failure PASSED [  1%]
tests/test_appr

**Cost:** executor $0.8772 | reviewer $0.0000

## Unmet Criteria
- pytest failed — hard gate

## Required Fixes
- fix failing tests before proceeding
