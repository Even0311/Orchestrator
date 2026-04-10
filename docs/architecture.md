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
|                      ORCHESTRATOR (Python, deterministic)       |
|                                                                |
|  +------------------+  +------------------+  +---------------+ |
|  | SOT Manager      |  | Round Engine     |  | Hard Gates    | |
|  | (sot.py)         |  | (orchestrator.py)|  | (hard_gates)  | |
|  |                  |  |                  |  |               | |
|  | parse phase      |  | 10-step flow     |  | git_changes   | |
|  | mark complete    |  | per-role briefs  |  | protected     | |
|  | track decisions  |  | cold CLI calls   |  | forbidden     | |
|  | phase status     |  | escalation       |  | round_dir     | |
|  +------------------+  +------------------+  | sot_mutation  | |
|                                              | pytest        | |
|  +------------------+  +------------------+  +---------------+ |
|  | Briefing Engine   |  | Phase Planner   |                    |
|  | (briefing.py)     |  | (phase_planner) |                    |
|  |                   |  |                 |                    |
|  | designer_brief    |  | roadmap parse   |                    |
|  | executor_brief    |  | Claude Opus     |                    |
|  | evaluator briefs  |  | task breakdown  |                    |
|  +------------------+  +-----------------+                     |
+================================================================+
         |                          ^
         | Independent cold-start   | JSON artifacts
         | Claude CLI sessions      | + git evidence
         | (no shared context)      |
         v                          |
+================================================================+
|         INDEPENDENT CLAUDE CLI SESSIONS                        |
|                                                                |
|  Session #1: Designer (Opus)                                   |
|    reads: designer_brief.md (vision, roadmap, phase, decisions)|
|    writes: task_contract.json                                  |
|                                                                |
|  Session #2: Evaluator — Contract Review (Sonnet)              |
|    reads: evaluator_contract_brief.md (criteria only)          |
|    writes: contract_feedback.json                              |
|                                                                |
|  Session #1b: Designer Revision (Opus, if needed)              |
|    reads: designer_brief.md + contract_feedback.json           |
|    writes: revised task_contract.json                          |
|                                                                |
|  Session #3: Executor (Sonnet)                                 |
|    reads: executor_brief.md + source code                      |
|    writes: code changes + execution_evidence.json              |
|                                                                |
|  Session #4: Evaluator — Code Review (Sonnet)                  |
|    reads: evaluator_review_brief.md (git diff + criteria)      |
|    writes: review_verdict.json                                 |
+================================================================+
```

## Data Flow Per Round

```
ORCHESTRATOR                           CLAUDE CLI SESSIONS
============                           ===================

1. Parse current_phase.md
   -> PhaseInfo (task_key, goal,
      scope, recent completed)

2. Generate designer_brief.md ------> CLI #1: Designer (Opus)
   (vision + roadmap + phase +              |
    decisions + prior failure)              v
                                      writes task_contract.json
                                      (acceptance_criteria + review_focus)

3. Generate evaluator_contract     --> CLI #2: Evaluator (Sonnet)
   _brief.md (criteria only)              |
                                          v
                                      writes contract_feedback.json
                                      (can_evaluate / cannot_evaluate)

4. [If revision needed]
   Generate designer_brief.md  -----> CLI #1b: Designer (Opus)
   + contract_feedback.json               |
                                          v
                                      writes revised task_contract.json

5. Hard gate: forbidden_files check
6. Snapshot SOT + baseline commit
7. Generate executor_brief.md  -----> CLI #3: Executor (Sonnet)
   (task_contract only)                    |
                                          v
                                      modifies code + tests
                                      writes execution_evidence.json

8. Hard gates:
   - git_changes
   - target_protected_files
   - forbidden_files
   - round_dir_boundary
   - sot_mutation
   - pytest
   FAIL -> skip evaluator, roll back

9. Generate evaluator_review       --> CLI #4: Evaluator (Sonnet)
   _brief.md (git diff + criteria)        |
                                          v
                                      writes review_verdict.json

10. Adjudicate:
    hard gate overrides evaluator
                    |
        +-----------+-----------+
        |                       |
     PASS                    FAIL
        |                       |
  mark task [x]          problems -> designer
  commit both repos      attempt < max?
  append decision        yes -> new attempt
  next task              no  -> escalate
```

## Context Isolation

Each agent gets a different brief with only the context it needs:

| Agent | Sees | Does NOT See |
|-------|------|-------------|
| Designer | vision.md, road_map.md, current_phase.md, decisions.md, code structure, prior failure | executor code, evaluator reasoning |
| Evaluator (contract) | acceptance_criteria, review_focus | vision, roadmap, designer reasoning |
| Executor | task_contract.json (final), source code | designer reasoning, vision, evaluator |
| Evaluator (review) | git diff, acceptance_criteria, review_focus | executor reasoning, designer reasoning |

## Contract Schema

```json
{
  "phase_id": "P29",
  "task_key": "P29-T1",
  "title": "Extract appraisal input schema",
  "objective": "...",
  "exact_scope": "...",
  "constraints": ["architectural constraints"],
  "forbidden_files": ["docs/vision.md", "back/app/domain/**"],
  "non_goals": ["explicitly out of scope"],
  "acceptance_criteria": ["each must be objectively verifiable"],
  "review_focus": ["evaluator pays special attention to these"]
}
```

**Design principles:**
- No `allowed_files` — executor is free outside forbidden_files
- No `required_tests` — executor decides how to test
- Deterministic boundaries use hard gates, judgment boundaries use evaluator

## Hard Gates (Deterministic, Override Evaluator)

| Gate | What It Checks | Failure Means |
|------|---------------|---------------|
| `git_changes` | Claude must have made git changes | No work done |
| `target_protected_files` | CLAUDE.md, .claude/agents/** untouched | Control plane violated |
| `forbidden_files` | No changes to forbidden patterns | Constraint violated |
| `round_dir_boundary` | Only allowed artifact files in round dir | Path traversal / pollution |
| `sot_mutation` | SOT files (vision, roadmap, phase, decisions) unmodified | SOT integrity violated |
| `pytest` | Project test suite passes | Regression introduced |

Hard gates run BEFORE evaluator. If they fail, evaluator is skipped (saves tokens).

## Model Assignment

| Role | Model | Rationale |
|------|-------|-----------|
| Designer | **Opus** | Strategic task decomposition needs strongest reasoning |
| Executor | Sonnet | Code implementation, cost-efficient |
| Evaluator (contract) | Sonnet | Criteria review, lightweight |
| Evaluator (review) | Sonnet | Code verification against criteria |
| Phase Planner | **Opus** | Phase-level task breakdown |

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
  +-- phases/
        +-- P28/
        |     +-- round-0028/
        |     |     +-- attempt_1/
        |     |     |     +-- designer_brief.md            [orch -> designer]
        |     |     |     +-- executor_brief.md            [orch -> executor]
        |     |     |     +-- evaluator_contract_brief.md  [orch -> evaluator]
        |     |     |     +-- evaluator_review_brief.md    [orch -> evaluator]
        |     |     |     +-- task_contract.json           [designer output]
        |     |     |     +-- contract_feedback.json       [evaluator output]
        |     |     |     +-- execution_evidence.json      [executor output]
        |     |     |     +-- review_verdict.json          [evaluator output]
        |     |     |     +-- attempt_report.json          [orch record]
        |     |     +-- audit.md                           [round summary]
        |     +-- round-0029/
        |           +-- ...
        +-- P29/
              +-- ...
```

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
