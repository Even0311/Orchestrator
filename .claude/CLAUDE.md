# Agent Orchestrator — CLAUDE.md

## Project Purpose

CLI 工具 (`orch`)，驱动 Claude Code 以 phase/round/artifact 流程完成长期软件项目。Orchestrator 管控状态机和治理，Claude Code 负责设计/实现/评审。

## Tech Stack

- Python 3.12, Click (CLI), SQLite (DB at ~/.orch/orchestrator.db)
- Pydantic (config), dataclasses (models)
- pytest for testing
- Claude Code CLI as subprocess (`claude -p ... --agent ...`)

## Package Structure

```
orch/
  cli/                  # Click commands
    main.py             # CLI entry point, command registration
    project_cmds.py     # new, list, switch, set-path, set-test-cmd + subagent templates
    run_cmds.py         # run, status
    review_cmds.py      # review, decide
    log_cmds.py         # log
    phase_cmds.py       # phase next/approve/status
    config_cmds.py      # config set/show
    rollback_cmd.py     # rollback
  engine/
    orchestrator.py     # Main run loop: run_project() -> _run_round()
    claude_round_driver.py  # Invoke Claude CLI, parse response + artifacts
    hard_gates.py       # 7 programmatic gates (pytest, scope, SOT mutation, etc.)
    phase_planner.py    # Claude Opus call for task breakdown
  config/
    settings.py         # OrchestratorConfig, paths, constants
  db/
    database.py         # SQLite init, tables (projects, phases, rounds)
  models.py             # TaskContract, ExecutionEvidence, ReviewVerdict, etc.
  sot.py                # SOT parsing: PhaseInfo, phase status, roadmap extraction
  briefing.py           # Generate round_brief.md from SOT context
  utils/
    git_ops.py          # Git operations (commit, clean, evidence collection)
tests/
  test_sot.py
  test_briefing.py
  test_hard_gates.py
  test_phase_planning.py
  ...
```

## Architecture Decisions

### Three-Subagent Model (2026-04-02)
Claude Code is invoked once per round with `--agent round-driver`. The round-driver spawns 3 isolated subagents via Agent tool: Designer (Opus) -> Executor (Sonnet) -> Reviewer (Sonnet). Subagent definitions live in target repo `.claude/agents/`.

### Dual-Gate Verification (2026-04-02)
- **Hard gates** (orchestrator-side, programmatic): pytest, file scope, SOT immutability, protected files. Hard gates override Claude's review verdict.
- **Soft gate** (Claude-side): Reviewer subagent writes review_verdict.json. This is advisory — hard gates have final authority.

### Designer Uses Opus, Others Use Sonnet (2026-04-04)
Designer subagent and phase planner use Opus for stronger reasoning on task decomposition. Executor, reviewer, and round-driver use Sonnet for cost efficiency. Configured via `agents.designer_model` and `agents.executor_model`.

### SOT in Orchestrator Repo (2026-04-02)
Project SOT files (vision.md, road_map.md, current_phase.md, decisions.md) live in `projects/<name>/` within the orchestrator repo, not in the target repo. This prevents Claude from modifying SOT. SOT mutation is enforced by SHA-256 snapshot comparison (hard gate).

### Phase-Organized Round Directories (2026-04-05)
Round artifacts are stored under `projects/<name>/<phase_id>/<round_id>/attempt_N/`. This keeps each phase's rounds together and avoids a flat directory with hundreds of rounds.

### Phase Lifecycle: Draft -> Approved (2026-04-05)
`orch phase next` generates current_phase.md with `<!-- status: draft -->`. Human edits the file directly, then `orch phase approve` sets status to approved. Orchestrator refuses to run rounds on a draft phase.

### current_phase.md Canonical Sections (2026-04-05)
Only 5 sections are parsed by the orchestrator:
- `# <title>` (H1) — phase_id extracted via regex `P\d+`
- `## Phase Goal`
- `## In Scope`
- `## Out of Scope`
- `## Task Queue` — `- [ ]` for pending, `- [x]` for completed

Other sections (Completed Tasks, Current Status, Risks/Blockers) were removed as they were not in the data flow.

### Orchestrator Does NOT Write to Target Repo
Orchestrator only reads target repo state (git evidence). All target repo writes are done by Claude Code. Orchestrator commits after Claude finishes (if hard gates pass).

### Evidence Hierarchy
Orchestrator collects git evidence independently of Claude's self-report. Git diff/status is authoritative; execution_evidence.json is supplementary.

## Running Tests

```bash
python3 -m pytest tests/ -v
```

## Key Invariants

- SOT files are immutable during Claude execution (enforced by sot_mutation gate)
- Hard gate verdict overrides Claude reviewer verdict
- Claude cannot modify CLAUDE.md or .claude/agents/** in target repo
- Task queue format: `- [ ] P{n}-T{m}: description`
- All phase transitions require human approval (draft -> approved)
- Decisions are append-only (decisions.md never edited, only appended)
- Round artifacts are write-once per attempt

## Current State (2026-04-05)

- P28 (Deterministic Relational Appraisal Expansion) complete
- P29 (Appraisal / Settlement Boundary Extraction) starting
- 121 orchestrator tests passing
- Target project: cyber-community-v2 (609 tests)
