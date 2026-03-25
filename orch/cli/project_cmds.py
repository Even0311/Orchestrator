import re
from pathlib import Path

import click

from orch.db.database import (
    create_project,
    get_active_project,
    get_all_projects,
    get_project_by_name,
    init_db,
    set_active_project,
    update_project_path,
)
from orch.config.settings import PROJECTS_DIR
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

## Active Constraints
-

## Working Assumptions
-

## Architecture Snapshot
-

## Known Risks
-

## Open Questions For Human
-
"""


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug


def _make_state_dir(project_id: str) -> Path:
    state_dir = PROJECTS_DIR / project_id
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "context").mkdir(exist_ok=True)
    (state_dir / "phases").mkdir(exist_ok=True)
    return state_dir


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
    # Handle slug collision
    existing = [row["id"] for row in get_all_projects()]
    base_id = project_id
    counter = 2
    while project_id in existing:
        project_id = f"{base_id}-{counter}"
        counter += 1

    state_dir = _make_state_dir(project_id)

    # Write template files
    vision_path = state_dir / "vision.md"
    vision_path.write_text(VISION_TEMPLATE.format(name=name, codebase_path=str(codebase_path)))

    (state_dir / "decisions.md").write_text(DECISIONS_TEMPLATE.format(name=name))
    (state_dir / "current_phase.md").write_text(CURRENT_PHASE_TEMPLATE)
    (state_dir / "context" / "designer.md").write_text(DESIGNER_CONTEXT_TEMPLATE)
    (state_dir / "context" / "executor.md").write_text("# Executor Context\n\n<!-- Auto-updated after each round -->\n")

    create_project(project_id, name, str(codebase_path), str(state_dir))

    # Ensure target project is a git repo
    if not is_git_repo(codebase_path):
        click.echo(f"  Initialising git repo in {codebase_path}...")
        git_init(codebase_path)
        click.echo(f"  ✓ git init done")

    # Auto-activate if first project
    all_projects = get_all_projects()
    if len(all_projects) == 1:
        set_active_project(project_id)
        active_note = " (set as active)"
    else:
        active_note = ""

    click.echo(f"✓ Project '{name}' created{active_note}")
    click.echo(f"  State dir : {state_dir}")
    click.echo(f"  Codebase  : {codebase_path}")
    click.echo(f"\nNext: edit the vision file before running:")
    click.echo(f"  {vision_path}")


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
    """Update the codebase path for a project."""
    init_db()
    project = get_project_by_name(name)
    if not project:
        raise click.ClickException(f"Project '{name}' not found.")

    resolved = Path(new_path).resolve()
    if not resolved.exists():
        raise click.ClickException(f"Path does not exist: {resolved}")

    update_project_path(project["id"], str(resolved))
    click.echo(f"✓ Codebase path updated for '{name}'")
    click.echo(f"  {resolved}")
