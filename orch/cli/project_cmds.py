"""Project management CLI commands."""
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
from orch.config.settings import PROJECTS_DIR
from orch.utils.git_ops import is_git_repo, git_init


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

    _maybe_write(sot_dir / "vision.md", VISION_TEMPLATE.format(name=name, codebase_path=str(codebase_path)))
    _maybe_write(sot_dir / "road_map.md", ROADMAP_TEMPLATE)
    _maybe_write(sot_dir / "decisions.md", DECISIONS_TEMPLATE.format(name=name))
    _maybe_write(sot_dir / "current_phase.md", CURRENT_PHASE_TEMPLATE)

    return sot_dir


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

    create_project(project_id, name, str(codebase_path), str(sot_dir))

    all_projects = get_all_projects()
    active_note = ""
    if len(all_projects) == 1:
        set_active_project(project_id)
        active_note = " (set as active)"

    click.echo(f"Project '{name}' created{active_note}")
    click.echo(f"  Codebase  : {codebase_path}")
    click.echo(f"  SOT dir   : {sot_dir}")
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
