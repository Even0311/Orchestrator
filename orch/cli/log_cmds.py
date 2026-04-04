import json
from pathlib import Path

import click

from orch.db.database import get_active_project, get_connection, init_db
from orch.config.settings import PROJECTS_DIR


@click.command("log")
@click.argument("round_id", required=False)
def log_cmd(round_id: str):
    """Show round history, or a specific round's detail."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    if round_id:
        _show_round_detail(project, round_id)
    else:
        _show_round_list(project)


def _show_round_list(project) -> None:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, status, attempt_count, cost_usd, created_at FROM rounds "
            "WHERE project_id = ? ORDER BY created_at",
            (project["id"],),
        ).fetchall()

    if not rows:
        click.echo("No rounds yet.")
        return

    click.echo(f"Rounds for '{project['name']}':\n")
    icons = {"passed": "✓", "escalated": "!", "resolved_by_human": "H",
             "rolled_back": "↩", "pending": "…"}
    for r in rows:
        icon = icons.get(r["status"], "?")
        click.echo(
            f"  {icon} {r['id']}  {r['status']:20}  "
            f"attempts:{r['attempt_count']}  ${r['cost_usd']:.4f}  {r['created_at'][:16]}"
        )


def _show_round_detail(project, round_id: str) -> None:
    sot_dir = PROJECTS_DIR / project["name"]
    round_dir = _find_round_dir(sot_dir, round_id)

    if round_dir:
        _display_round_from_files(round_dir, round_id)
    else:
        _display_round_from_db(project, round_id)


def _find_round_dir(sot_dir: Path, round_id: str) -> Path | None:
    """Find round directory under sot_dir/<phase_id>/<round_id> or legacy sot_dir/rounds/<round_id>."""
    # New structure: sot_dir/P28/round-0029/
    for child in sorted(sot_dir.iterdir()):
        if child.is_dir() and (child / round_id).is_dir():
            return child / round_id
    # Legacy: sot_dir/rounds/round-0029/
    legacy = sot_dir / "rounds" / round_id
    if legacy.is_dir():
        return legacy
    return None


def _display_round_from_files(round_dir: Path, round_id: str) -> None:
    click.echo(f"\n{'='*60}")
    click.echo(f"  Round: {round_id}")
    click.echo(f"{'='*60}")

    # ── Task package ──────────────────────────────────────────────────────────
    task_json = round_dir / "task.json"
    if task_json.exists():
        t = json.loads(task_json.read_text())
        click.echo(f"\nTask: {t.get('title', '(no title)')}")
        click.echo(f"  Objective  : {t.get('objective', '')}")
        click.echo(f"  Scope      : {t.get('exact_scope', '')}")
        criteria = t.get("acceptance_criteria", [])
        if criteria:
            click.echo("  Criteria   :")
            for c in criteria:
                click.echo(f"    - {c}")
    elif (round_dir / "task.md").exists():
        click.echo("\n" + (round_dir / "task.md").read_text())

    # ── Attempts ─────────────────────────────────────────────────────────────
    attempt_count = max(
        len(list(round_dir.glob("execution_report_attempt_*.json"))),
        len(list(round_dir.glob("attempt_*.md"))),
    )

    for i in range(1, attempt_count + 1):
        click.echo(f"\n{'─'*50}")
        click.echo(f"Attempt {i}")

        # Repaired task (attempt > 1)
        repaired_json = round_dir / f"repaired_task_attempt_{i}.json"
        if repaired_json.exists():
            r = json.loads(repaired_json.read_text())
            click.echo(f"\n  [Repaired Task] {r.get('title', '')}")
            click.echo(f"  Objective: {r.get('objective', '')}")

        # Execution report (git-verified evidence)
        exec_json = round_dir / f"execution_report_attempt_{i}.json"
        if exec_json.exists():
            e = json.loads(exec_json.read_text())
            git_ev = e.get("git_evidence", {})
            ex_ev = e.get("executor_reported", {})

            click.echo("\n  Evidence (git-verified):")
            if git_ev.get("files_modified"):
                click.echo(f"    Modified : {git_ev['files_modified']}")
            if git_ev.get("files_added"):
                click.echo(f"    New files: {git_ev['files_added']}")
            if git_ev.get("files_deleted"):
                click.echo(f"    Deleted  : {git_ev['files_deleted']}")
            if git_ev.get("diff_stat"):
                for line in git_ev["diff_stat"].splitlines()[:5]:
                    click.echo(f"    {line}")
            if not git_ev.get("has_changes") and not git_ev.get("error"):
                click.echo("    (no git changes detected)")
            if git_ev.get("error"):
                click.echo(f"    (git unavailable: {git_ev['error']})")

            if ex_ev.get("commands_run"):
                click.echo(f"  Commands (self-reported): {ex_ev['commands_run']}")
            if ex_ev.get("test_results"):
                click.echo(f"  Tests    (self-reported): {ex_ev['test_results']}")
        else:
            # Fallback to old attempt_N.md
            old_attempt = round_dir / f"attempt_{i}.md"
            if old_attempt.exists():
                click.echo(old_attempt.read_text())
                continue

        # Review result
        review_json = round_dir / f"review_attempt_{i}.json"
        if review_json.exists():
            rv = json.loads(review_json.read_text())
            r_icon = "✓" if rv.get("result") == "PASS" else "✗"
            click.echo(
                f"\n  Review: {r_icon} {rv.get('result')} "
                f"(confidence: {rv.get('confidence', '?')})"
            )
            click.echo(f"  Rationale: {rv.get('rationale', '')}")
            if rv.get("unmet_criteria"):
                click.echo("  Unmet criteria:")
                for c in rv["unmet_criteria"]:
                    click.echo(f"    - {c}")
            if rv.get("required_fixes"):
                click.echo("  Required fixes:")
                for f in rv["required_fixes"]:
                    click.echo(f"    - {f}")

    # ── Audit summary ─────────────────────────────────────────────────────────
    audit = round_dir / "audit.md"
    if audit.exists():
        click.echo(f"\n{'─'*50}")
        click.echo(audit.read_text())


def _display_round_from_db(project, round_id: str) -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM rounds WHERE id = ? AND project_id = ?",
            (round_id, project["id"]),
        ).fetchone()

    if not row:
        raise click.ClickException(f"Round '{round_id}' not found.")

    click.echo(f"Round   : {row['id']}")
    click.echo(f"Status  : {row['status']}")
    click.echo(f"Attempts: {row['attempt_count']}")
    click.echo(f"Cost    : ${row['cost_usd']:.4f}")
    if row["task_description"]:
        click.echo(f"Task    : {row['task_description'][:100]}")
    if row["escalation_reason"]:
        click.echo(f"\nEscalation reason:\n{row['escalation_reason']}")
