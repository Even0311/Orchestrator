"""Project management CLI commands and subagent template definitions."""
import re
from pathlib import Path

import click

from orch.db.database import (
    create_project,
    get_all_projects,
    get_project_by_name,
    init_db,
    set_active_project,
    update_project_path,
    update_project_state_dir,
    update_project_test_cmd,
)
from orch.config.settings import CLAUDE_AGENTS_SUBDIR, PROJECTS_DIR
from orch.utils.git_ops import is_git_repo, git_init


# ── Subagent Templates ───────────────────────────────────────────────────────
# These are written to .claude/agents/ in the target repo.
# Claude Code reads them as project-level subagent definitions.

DESIGNER_SUBAGENT_TEMPLATE = """\
---
name: designer
description: Project-level planner. Read the round brief, propose the next task, and write task_contract.json.
---

You are the designer subagent for this repository.

## Input
Read the round brief file (round_brief.md) in the added directory for:
- Phase context (phase_id, phase goal, next task key)
- Prior failure context (if this is a retry attempt)
- Recent rounds summary (avoid redoing completed work)

Also read the project's CLAUDE.md for architecture and constraints.

## Rules
- Do not edit vision.md or road_map.md.
- Do not specify file paths or shell commands — you define WHAT, not HOW.
- Output must include `required_tests` in business language.
- The `task_key` must match the one from the round brief.

## Output
Write a file called `task_contract.json` to the round directory (the added directory) with this schema:
```json
{
  "phase_id": "P28",
  "task_key": "P28-T6",
  "title": "short title",
  "objective": "concrete objective",
  "exact_scope": "precise boundaries",
  "constraints": ["constraint 1"],
  "acceptance_criteria": ["criterion 1"],
  "required_tests": ["test expectation 1"],
  "non_goals": ["non-goal 1"],
  "allowed_files": ["back/**/*.py", "back/tests/**"],
  "forbidden_files": ["docs/vision.md"]
}
```
"""

EXECUTOR_SUBAGENT_TEMPLATE = """\
---
name: executor
description: Repo-aware implementer. Read task_contract.json, implement the task, write execution_evidence.json.
---

You are the executor subagent for this repository.

## Input
- Read `task_contract.json` from the round directory (the added directory).
- Read project CLAUDE.md for architecture and constraints.

## Rules
- Implement only what is in scope. Do not add features beyond acceptance criteria.
- Write tests that cover every item in `required_tests`.
- Run `pytest` before declaring done. If tests fail, fix them.
- Only modify files matching `allowed_files` patterns if specified.
- Never modify files matching `forbidden_files` patterns.

## Output
Write a file called `execution_evidence.json` to the round directory with EXACTLY these fields:
```json
{
  "summary": "one sentence summary of what was done",
  "files_changed": ["path/to/file.py"],
  "commands_run": ["pytest -q"],
  "test_results": "all passed / summary",
  "diff_summary": "brief diff summary",
  "unresolved_issues": []
}
```
Do NOT rename these fields. Use exactly these field names.
"""

REVIEWER_SUBAGENT_TEMPLATE = """\
---
name: reviewer
description: Repo-aware reviewer. Verify implementation against task_contract.json criteria, write review_verdict.json.
---

You are the reviewer subagent for this repository.

## Input
- Read `task_contract.json` from the round directory (the added directory).
- Read the actual code and tests that were changed.
- Read `execution_evidence.json` if it exists (supplementary — verify against actual code).

## Rules
- Judge correctness, not style preference.
- Check that acceptance_criteria are genuinely met, not just claimed.
- Check that required_tests exist and are non-trivial (not tautological).
- Check that no files outside `allowed_files` were modified (if specified).
- If tests pass and criteria are met, verdict is PASS.

## Output
Write a file called `review_verdict.json` to the round directory with this schema:
```json
{
  "verdict": "PASS or FAIL or REVISION_REQUIRED",
  "confidence": "high | medium | low",
  "met_criteria": ["criterion that was met"],
  "unmet_criteria": ["criterion that was NOT met"],
  "scope_violations": [],
  "blocker_fixes": [],
  "non_blocking_suggestions": [],
  "rationale": "brief justification"
}
```
"""

ROUND_DRIVER_SUBAGENT_TEMPLATE = """\
---
name: round-driver
description: Top-level round coordinator. Delegates all work to designer, executor, and reviewer subagents in strict sequence.
---

You are the round driver. You coordinate a single development round.
You have Agent, Read, and Write tools. You CANNOT run code or edit the codebase directly.

## Mandatory Process (no exceptions)

1. Read `round_brief.md` from the round directory (the added directory) for context.
2. Use the **designer** subagent to produce a task contract. Pass it the round context.
   - After designer finishes, verify `task_contract.json` exists in the round directory.
3. Use the **executor** subagent to implement the task.
   - After executor finishes, verify `execution_evidence.json` exists in the round directory.
4. Use the **reviewer** subagent to review the implementation.
   - After reviewer finishes, verify `review_verdict.json` exists in the round directory.
5. Report a brief summary of the round outcome.

## Rules
- You MUST delegate to all three subagents in order: designer → executor → reviewer.
- Do NOT skip any subagent.
- Do NOT implement code yourself — that is the executor's job.
- If a subagent fails to produce its artifact file, note this in your summary.
"""


# ── SOT Templates ────────────────────────────────────────────────────────────

VISION_TEMPLATE = """\
# {name} — Vision

## Project Goal
<!-- One or two sentences describing what this project solves -->

## Core Features
<!-- List core features -->
-

## Tech Stack
<!-- Languages, frameworks, key dependencies -->

## Out of Scope
<!-- Explicitly exclude to prevent scope creep -->
-

## Codebase Path
{codebase_path}
"""

ROADMAP_TEMPLATE = """\
# road_map.md

## Purpose
<!-- roadmap is stage ordering and strategic boundaries, not a task backlog -->

## Stage 1
<!-- First major milestone -->

## Coarse Outlook Beyond Stage 1
<!-- Direction only, no detailed tasks -->
"""

DECISIONS_TEMPLATE = """\
# {name} — Decisions

<!-- Format:
## YYYY-MM-DD — Decision Title
**Decision:** ...
**Reason:** ...
**Alternatives:** ...
-->
"""

CURRENT_PHASE_TEMPLATE = """\
# Phase — Initial Setup

## Phase Goal
Define the first phase goal after reviewing vision.md and road_map.md.

## In Scope
-

## Out of Scope
-

## Task Queue
- [ ] PHASE-T1: Define the first concrete task

## Completed Tasks
(none)

## Current Status
Awaiting first task definition.

## Risks / Blockers
-
"""


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug


def _maybe_write(path: Path, content: str) -> None:
    """Write file only if it doesn't already exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def _setup_sot(name: str, codebase_path: Path) -> Path:
    """Set up SOT directory in the orchestrator repo under projects/<name>/."""
    sot_dir = PROJECTS_DIR / name
    sot_dir.mkdir(parents=True, exist_ok=True)
    (sot_dir / "context").mkdir(exist_ok=True)
    (sot_dir / "rounds").mkdir(exist_ok=True)

    _maybe_write(sot_dir / "vision.md", VISION_TEMPLATE.format(name=name, codebase_path=str(codebase_path)))
    _maybe_write(sot_dir / "road_map.md", ROADMAP_TEMPLATE)
    _maybe_write(sot_dir / "decisions.md", DECISIONS_TEMPLATE.format(name=name))
    _maybe_write(sot_dir / "current_phase.md", CURRENT_PHASE_TEMPLATE)

    return sot_dir


def _setup_subagents(codebase_path: Path) -> None:
    """Write subagent definitions to .claude/agents/ in the target repo."""
    agents_dir = codebase_path / CLAUDE_AGENTS_SUBDIR
    _maybe_write(agents_dir / "designer.md", DESIGNER_SUBAGENT_TEMPLATE)
    _maybe_write(agents_dir / "executor.md", EXECUTOR_SUBAGENT_TEMPLATE)
    _maybe_write(agents_dir / "reviewer.md", REVIEWER_SUBAGENT_TEMPLATE)
    _maybe_write(agents_dir / "round-driver.md", ROUND_DRIVER_SUBAGENT_TEMPLATE)


@click.command("new")
@click.argument("name")
@click.option("--path", required=True, help="Path to the managed codebase directory")
def new_cmd(name: str, path: str):
    """Create a new managed project."""
    init_db()

    codebase_path = Path(path).resolve()
    if not codebase_path.exists():
        raise click.ClickException(f"Path does not exist: {codebase_path}")
    if not codebase_path.is_dir():
        raise click.ClickException(f"Path is not a directory: {codebase_path}")

    if get_project_by_name(name):
        raise click.ClickException(f"Project '{name}' already exists.")

    project_id = _slugify(name)
    existing = [row["id"] for row in get_all_projects()]
    base_id = project_id
    counter = 2
    while project_id in existing:
        project_id = f"{base_id}-{counter}"
        counter += 1

    if not is_git_repo(codebase_path):
        click.echo(f"  Initialising git repo in {codebase_path}...")
        git_init(codebase_path)
        click.echo("  done")

    # Set up SOT in orchestrator repo
    sot_dir = _setup_sot(name, codebase_path)

    # Set up subagent definitions in target repo
    _setup_subagents(codebase_path)

    create_project(project_id, name, str(codebase_path), str(sot_dir))

    all_projects = get_all_projects()
    active_note = ""
    if len(all_projects) == 1:
        set_active_project(project_id)
        active_note = " (set as active)"

    click.echo(f"Project '{name}' created{active_note}")
    click.echo(f"  Codebase  : {codebase_path}")
    click.echo(f"  SOT dir   : {sot_dir}")
    click.echo(f"  Subagents : {codebase_path / CLAUDE_AGENTS_SUBDIR}")
    click.echo("\nNext steps:")
    click.echo(f"  1. Edit {sot_dir / 'vision.md'}")
    click.echo(f"  2. Edit {sot_dir / 'road_map.md'}")
    click.echo(f"  3. Edit {sot_dir / 'current_phase.md'} with first phase tasks")
    click.echo(f"  4. Run 'orch run' to start")


@click.command("list")
def list_cmd():
    """List all managed projects."""
    init_db()
    projects = get_all_projects()
    if not projects:
        click.echo("No projects yet. Use: orch new <name> --path <path>")
        return

    for p in projects:
        active_marker = "* " if p["is_active"] else "  "
        click.echo(f"{active_marker}{p['name']}")
        click.echo(f"    codebase : {p['codebase_path']}")
        click.echo(f"    state    : {p['state_dir']}")
        if p["test_cmd"]:
            click.echo(f"    test_cmd : {p['test_cmd']}")


@click.command("switch")
@click.argument("name")
def switch_cmd(name: str):
    """Switch the active project."""
    init_db()
    project = get_project_by_name(name)
    if not project:
        raise click.ClickException(f"Project '{name}' not found.")
    set_active_project(project["id"])
    click.echo(f"Active project set to '{name}'")


@click.command("set-path")
@click.argument("name")
@click.argument("new_path")
def set_path_cmd(name: str, new_path: str):
    """Update the codebase path for a project."""
    init_db()
    project = get_project_by_name(name)
    if not project:
        raise click.ClickException(f"Project '{name}' not found.")

    resolved = Path(new_path).resolve()
    if not resolved.exists():
        raise click.ClickException(f"Path does not exist: {resolved}")

    update_project_path(project["id"], str(resolved))
    _setup_subagents(resolved)
    click.echo(f"Codebase path updated for '{name}': {resolved}")


@click.command("set-test-cmd")
@click.argument("name")
@click.argument("cmd")
def set_test_cmd_cmd(name: str, cmd: str):
    """Set a custom pytest command for the hard gate."""
    init_db()
    project = get_project_by_name(name)
    if not project:
        raise click.ClickException(f"Project '{name}' not found.")

    update_project_test_cmd(project["id"], cmd)
    click.echo(f"Test command updated for '{name}': {cmd}")
