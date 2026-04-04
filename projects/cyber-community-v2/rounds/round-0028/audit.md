# Audit — Round round-0028

**Status:** ESCALATED  
**Completed:** 2026-04-04 06:31 UTC  
**Total cost:** $2.7536  
**Attempts:** 2

## Task
**P28-T6** — Calibrate signal intensity ranges for Pattern A and Pattern B relational appraisal outputs
Confirm and document the calibrated signal intensity ranges for Pattern A (Contested Endorsement) and Pattern B (High-Intensity Unilateral Disclosure) T4 relational appraisal outputs. The calibration decision is: uniform signal shape (arousal=low, absorption=surface, trust_shift=mild_decrease, closeness_delta=-1, risk_delta=0, aftershock_days=0) across all three negative T4 patterns (P0, Pattern A, Pattern B). The post-adjustment hard caps (closeness_delta floor=-2, trust_shift ceiling=mild_decrease) must also be formally verified. The test file back/tests/test_p28_t6_signal_calibration.py already exists with 30 passing tests that cover this calibration; uncommitted changes to tick_bridge.py (comment block for Pattern B rationale) and docs/t4_negative_behavior_contract.md (Section 8 calibration rationale expansion) need to be committed to lock in this task's deliverables.

## Escalation Reason
```
Round round-0028 failed after 2 attempt(s).

Attempt 1:
  Task: Calibrate signal intensity ranges for Pattern A and Pattern B relational appraisal outputs
  Verdict: FAIL (confidence: high)
  Rationale: Hard gate failure: target_protected_files: Protected control-plane files modified: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md; allowed_files: Files outside allowed patterns: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md; forbidden_files: Forbidden files modified: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md
  Fix required: target_protected_files: Protected control-plane files modified: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md
  Fix required: allowed_files: Files outside allowed patterns: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md
  Fix required: forbidden_files: Forbidden files modified: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md

Attempt 2:
  Task: Calibrate signal intensity ranges for Pattern A and Pattern B relational appraisal outputs
  Verdict: FAIL (confidence: high)
  Rationale: Hard gate failure: target_protected_files: Protected control-plane files modified: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md; allowed_files: Files outside allowed patterns: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md; forbidden_files: Forbidden files modified: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md
  Fix required: target_protected_files: Protected control-plane files modified: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md
  Fix required: allowed_files: Files outside allowed patterns: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md
  Fix required: forbidden_files: Forbidden files modified: .claude/agents/designer.md, .claude/agents/executor.md, .claude/agents/reviewer.md, .claude/agents/round-driver.md
```
