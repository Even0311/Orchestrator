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
from orch.config.settings import CLAUDE_AGENTS_SUBDIR, get_repo_state_dir
from orch.utils.git_ops import is_git_repo, git_init

VISION_TEMPLATE = """\
# {name} — Vision

## 项目目标
<!-- 一两句话描述这个项目要解决什么问题 -->

## 核心功能
<!-- 列出核心功能点 -->
-

## 技术栈
<!-- 语言、框架、主要依赖 -->

## 不做什么（边界）
<!-- 明确排除在外的内容，防止范围蔓延 -->
-

## 代码库路径
{codebase_path}

## 当前状态（已有项目填写，全新项目可删除此节）

### 已完成的部分
-

### 未完成的部分
-

### 已知问题或技术债
-

### 重要决策记录（为什么这么设计）
-
"""

ROADMAP_TEMPLATE = """\
# roadmap.md

## Purpose
<!-- roadmap 是阶段顺序和战略边界，不是 task backlog -->

## Stage 1
<!-- 填写到第一个主要里程碑为止 -->

## Coarse Outlook Beyond Stage 1
<!-- 仅做方向参考，不写细 task -->
"""

DECISIONS_TEMPLATE = """\
# {name} — Decisions

<!-- 每条决策格式：
## YYYY-MM-DD — 决策标题
**决定：** ...
**原因：** ...
**备选方案：** ...
-->
"""

CURRENT_PHASE_TEMPLATE = """\
# Phase — bootstrap_needed

## Phase Goal
<!-- bootstrap_needed — run `orch run` to auto-generate from vision.md -->

## In Scope
-

## Out of Scope
-

## Task Queue
- [ ] bootstrap_needed

## Completed Tasks
(none)

## Current Status
bootstrap_needed

## Risks / Blockers
-

## Next Recommended Task
bootstrap_needed
"""

DESIGNER_CONTEXT_TEMPLATE = """\
# Designer Context

## Phase Transition Rule
If current phase is closing or the next phase is being proposed, roadmap.md must be read before phase transition.

## Active Constraints
-

## Working Assumptions
-

## Architecture Snapshot
-

## Known Risks
-

## Resolved Strategic Decisions
-
"""

EXECUTOR_CONTEXT_TEMPLATE = "# Executor Context\n\n<!-- Auto-updated after each round -->\n"

DESIGNER_SUBAGENT_TEMPLATE = """\
---
name: designer
description: Project-level planner. Read .orch source-of-truth files, propose the next task, and propose controlled document updates.
---

You are the designer subagent for this repository.
Read repo-local orchestration state from .orch/ before proposing work.
Do not edit vision.md or roadmap.md unless the task explicitly authorizes it.
"""

EXECUTOR_SUBAGENT_TEMPLATE = """\
---
name: executor
description: Repo-aware implementer. Execute the current task from .orch/runtime/current_task.md and make the smallest correct change set.
---

You are the executor subagent for this repository.
Start by reading .orch/runtime/current_task.md and .orch/runtime/recent_rounds.md when present.
Implement only what is in scope.
"""

REVIEWER_SUBAGENT_TEMPLATE = """\
---
name: reviewer
description: Repo-aware reviewer. Verify implementation against acceptance criteria and required tests.
---

You are the reviewer subagent for this repository.
Read the actual code and tests. Judge correctness, not style preference.
"""


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug


def _ensure_state_dirs(state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "context").mkdir(exist_ok=True)
    (state_dir / "phases").mkdir(exist_ok=True)
    (state_dir / "runtime").mkdir(exist_ok=True)


def _maybe_write(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def _bootstrap_repo_local_state(name: str, codebase_path: Path) -> Path:
    state_dir = get_repo_state_dir(codebase_path)
    _ensure_state_dirs(state_dir)

    _maybe_write(state_dir / "vision.md", VISION_TEMPLATE.format(name=name, codebase_path=str(codebase_path)))
    _maybe_write(state_dir / "roadmap.md", ROADMAP_TEMPLATE)
    _maybe_write(state_dir / "decisions.md", DECISIONS_TEMPLATE.format(name=name))
    _maybe_write(state_dir / "current_phase.md", CURRENT_PHASE_TEMPLATE)
    _maybe_write(state_dir / "context" / "designer.md", DESIGNER_CONTEXT_TEMPLATE)
    _maybe_write(state_dir / "context" / "executor.md", EXECUTOR_CONTEXT_TEMPLATE)

    agents_dir = codebase_path / CLAUDE_AGENTS_SUBDIR
    _maybe_write(agents_dir / "designer.md", DESIGNER_SUBAGENT_TEMPLATE)
    _maybe_write(agents_dir / "executor.md", EXECUTOR_SUBAGENT_TEMPLATE)
    _maybe_write(agents_dir / "reviewer.md", REVIEWER_SUBAGENT_TEMPLATE)

    return state_dir


@click.command("new")
@click.argument("name")
@click.option("--path", required=True, help="Path to the managed codebase directory")
def new_cmd(name: str, path: str):
    """Create a new managed project with repo-local .orch state."""
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
        click.echo("  ✓ git init done")

    state_dir = _bootstrap_repo_local_state(name, codebase_path)
    create_project(project_id, name, str(codebase_path), str(state_dir))

    all_projects = get_all_projects()
    active_note = ""
    if len(all_projects) == 1:
        set_active_project(project_id)
        active_note = " (set as active)"

    click.echo(f"✓ Project '{name}' created{active_note}")
    click.echo(f"  Codebase  : {codebase_path}")
    click.echo(f"  State dir : {state_dir}")
    click.echo("\nNext: edit the repo-local vision file before running:")
    click.echo(f"  {state_dir / 'vision.md'}")


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
    click.echo(f"✓ Active project set to '{name}'")


@click.command("set-path")
@click.argument("name")
@click.argument("new_path")
def set_path_cmd(name: str, new_path: str):
    """Update the codebase path for a project and move state_dir to the new repo-local .orch path."""
    init_db()
    project = get_project_by_name(name)
    if not project:
        raise click.ClickException(f"Project '{name}' not found.")

    resolved = Path(new_path).resolve()
    if not resolved.exists():
        raise click.ClickException(f"Path does not exist: {resolved}")

    update_project_path(project["id"], str(resolved))
    new_state_dir = _bootstrap_repo_local_state(name, resolved)
    update_project_state_dir(project["id"], str(new_state_dir))
    click.echo(f"✓ Codebase path updated for '{name}'")
    click.echo(f"  Codebase  : {resolved}")
    click.echo(f"  State dir : {new_state_dir}")


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
    click.echo(f"✓ Test command updated for '{name}'")
    click.echo(f"  {cmd}")
