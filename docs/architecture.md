# Agent Orchestrator — Architecture & Data Flow

## System Overview

```
                        +------------------+
                        |     Human        |
                        |  (orch CLI)      |
                        +--------+---------+
                                 |
            orch run / orch phase next / orch decide
                                 |
                                 v
+================================================================+
|                      ORCHESTRATOR                              |
|                                                                |
|  +------------------+  +------------------+  +---------------+ |
|  | SOT Manager      |  | Round Engine     |  | Hard Gates    | |
|  | (sot.py)         |  | (orchestrator.py)|  | (hard_gates)  | |
|  |                  |  |                  |  |               | |
|  | parse phase      |  | run loop         |  | git_changes   | |
|  | mark complete    |  | attempt mgmt     |  | protected     | |
|  | track decisions  |  | escalation       |  | allowed/forb  | |
|  | phase status     |  | commit both      |  | round_dir     | |
|  +------------------+  +------------------+  | sot_mutation  | |
|                                              | pytest        | |
|  +------------------+  +------------------+  +---------------+ |
|  | Briefing Engine   |  | Phase Planner   |                    |
|  | (briefing.py)     |  | (phase_planner) |                    |
|  |                   |  |                 |                    |
|  | round_brief.md    |  | roadmap parse   |                    |
|  | vision summary    |  | Claude Opus     |                    |
|  | roadmap context   |  | task breakdown  |                    |
|  +------------------+  +-----------------+                     |
+================================================================+
         |                          ^
         | claude -p ... --agent    | JSON artifacts
         | round-driver             | + git evidence
         | --add-dir <attempt_dir>  |
         v                          |
+================================================================+
|              CLAUDE CODE (target repo cwd)                     |
|                                                                |
|  +------------------+                                          |
|  | Round Driver     |  tools: Agent, Read, Write               |
|  | (round-driver.md)|  model: sonnet                           |
|  +--------+---------+                                          |
|           |                                                    |
|           | 1. Spawn designer (opus)                           |
|           | 2. Spawn executor (sonnet)                         |
|           | 3. Spawn reviewer (sonnet)                         |
|           v                                                    |
|  +--------+---------+  +------------------+  +---------------+ |
|  | Designer          |  | Executor         |  | Reviewer      | |
|  | (designer.md)     |  | (executor.md)    |  | (reviewer.md) | |
|  |                   |  |                  |  |               | |
|  | reads:            |  | reads:           |  | reads:        | |
|  |  round_brief.md   |  |  task_contract   |  |  task_contract| |
|  |  CLAUDE.md        |  |  CLAUDE.md       |  |  exec_evidence| |
|  |                   |  |                  |  |  actual code  | |
|  | writes:           |  | writes:          |  |               | |
|  |  task_contract    |  |  code + tests    |  | writes:       | |
|  |  .json            |  |  exec_evidence   |  |  review_verdict|
|  |                   |  |  .json           |  |  .json        | |
|  +-------------------+  +------------------+  +---------------+ |
+================================================================+
```

## Data Flow Per Round

```
ORCHESTRATOR                           CLAUDE CODE
============                           ==========

1. Parse current_phase.md
   -> PhaseInfo (task_key, goal,
      scope, recent completed)
                    |
2. Generate round_brief.md -------->  round-driver reads brief
   (vision + roadmap + phase +            |
    decisions + recent rounds +           |
    prior failure)                        v
                                     designer reads brief + CLAUDE.md
                                     designer writes task_contract.json
                                          |
                                          v
                                     executor reads task_contract.json
                                     executor modifies code + tests
                                     executor runs pytest
                                     executor writes execution_evidence.json
                                          |
                                          v
                                     reviewer reads task_contract + evidence
                                     reviewer inspects actual code changes
                                     reviewer writes review_verdict.json
                                          |
3. Read 3 artifact files  <----------  round complete
4. Collect git evidence
   (diff, status, files changed)
5. Run hard gates:
   - git_changes
   - target_protected_files
   - allowed_files / forbidden_files
   - round_dir_boundary
   - sot_mutation
   - pytest
6. Adjudicate:
   hard gate overrides Claude verdict
                    |
        +-----------+-----------+
        |                       |
     PASS                    FAIL
        |                       |
  mark task [x]          attempt < max?
  commit both repos      yes -> retry
  append decision        no  -> escalate
  next task                     -> human
```

## SOT Directory Structure

```
projects/<project_name>/           # orchestrator repo
  |
  +-- vision.md                    # project goal, features, tech stack, constraints
  +-- road_map.md                  # phase-by-phase roadmap (H2 per phase)
  +-- current_phase.md             # active phase: goal, scope, task queue
  |     <!-- status: draft|approved -->
  +-- decisions.md                 # append-only: timestamped decision log
  +-- context/                     # optional persistent context files
  |
  +-- P28/                         # phase directory (auto-created)
  |     +-- round-0028/
  |     |     +-- attempt_1/
  |     |     |     +-- round_brief.md           [orchestrator -> Claude]
  |     |     |     +-- task_contract.json        [designer output]
  |     |     |     +-- execution_evidence.json   [executor output]
  |     |     |     +-- review_verdict.json       [reviewer output]
  |     |     |     +-- attempt_report.json       [orchestrator record]
  |     |     +-- audit.md                        [round summary]
  |     +-- round-0029/
  |           +-- ...
  |
  +-- P29/
        +-- round-0030/
              +-- ...
```

## Artifact Schemas

### task_contract.json (Designer -> Executor)

```json
{
  "phase_id": "P29",
  "task_key": "P29-T1",
  "title": "Extract appraisal input schema",
  "objective": "...",
  "exact_scope": "...",
  "constraints": ["..."],
  "acceptance_criteria": ["criterion 1", "criterion 2"],
  "required_tests": ["test expectation in business language"],
  "non_goals": ["..."],
  "allowed_files": ["back/**/*.py"],
  "forbidden_files": ["docs/vision.md"]
}
```

### execution_evidence.json (Executor -> Reviewer)

```json
{
  "summary": "Implemented ...",
  "files_changed": ["back/engines/foo.py", "back/tests/test_foo.py"],
  "commands_run": ["pytest tests/ -v"],
  "test_results": "42 passed",
  "diff_summary": "...",
  "unresolved_issues": []
}
```

### review_verdict.json (Reviewer -> Orchestrator)

```json
{
  "verdict": "PASS",
  "confidence": "high",
  "met_criteria": ["criterion 1 met because ..."],
  "unmet_criteria": [],
  "scope_violations": [],
  "blocker_fixes": [],
  "non_blocking_suggestions": ["consider ..."],
  "rationale": "All acceptance criteria met, tests pass."
}
```

## Hard Gates (Programmatic, Override Claude)

| Gate | What It Checks | Failure Means |
|------|---------------|---------------|
| `git_changes` | Claude must have made git changes | No work done |
| `target_protected_files` | CLAUDE.md, .claude/agents/** untouched | Control plane violated |
| `allowed_files` | All changes within allowed glob patterns | Scope violation |
| `forbidden_files` | No changes to forbidden patterns | Constraint violated |
| `round_dir_boundary` | Only 3 artifact files written to round dir | Path traversal / pollution |
| `sot_mutation` | SOT files (vision, roadmap, phase, decisions) unmodified | SOT integrity violated |
| `pytest` | Project test suite passes | Regression introduced |

## Phase Lifecycle

```
Phase complete (all tasks [x])
         |
         v
  orch phase next
  (Claude Opus generates task breakdown)
         |
         v
  current_phase.md [status: draft]
         |
    human edits file
         |
         v
  orch phase approve
  [status: approved]
         |
         v
  orch run  (proceeds with new phase)
```

## Model Assignment

| Role | Model | Rationale |
|------|-------|-----------|
| Designer | **Opus** | Strategic task decomposition needs strongest reasoning |
| Round Driver | Sonnet | Coordination only, no creative work |
| Executor | Sonnet | Code implementation, cost-efficient |
| Reviewer | Sonnet | Verification against criteria |
| Phase Planner | **Opus** | Phase-level task breakdown |

## Resolution Flow (Human-in-the-Loop)

```
Round FAIL (2 attempts exhausted)
         |
         v
    ESCALATED
    (audit.md written, email sent)
         |
    orch review  (human reads audit)
         |
         v
    orch decide "<note>" --action ...
         |
    +----+----+----+
    |         |         |
reject_and   accept_   resume_
  _redo      and_close   round
    |         |         |
  fresh     mark [x]   retry with
  round     commit     human note
```
