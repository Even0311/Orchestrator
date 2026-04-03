import json
from pathlib import Path

import click

from orch.db.database import get_active_project, get_connection, init_db, resolve_round


RESOLUTION_ACTIONS = ("reject_and_redo", "accept_and_close", "resume_round")
STATUS_BY_ACTION = {
    "reject_and_redo": "rejected_by_human",
    "accept_and_close": "accepted_by_human",
    "resume_round": "resume_requested",
}


@click.command("review")
def review_cmd():
    """Show escalated rounds waiting for your decision."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, escalation_reason, cost_usd, created_at FROM rounds "
            "WHERE project_id = ? AND status = 'escalated' ORDER BY created_at",
            (project["id"],),
        ).fetchall()

    if not rows:
        click.echo("No escalated rounds. Everything is running or complete.")
        return

    state_dir = Path(project["state_dir"])

    for row in rows:
        round_id = row["id"]
        click.echo(f"\n{'!'*60}")
        click.echo(f"  Escalated round: {round_id}")
        click.echo(f"  Cost so far    : ${row['cost_usd']:.4f}")
        click.echo(f"{'!'*60}")

        round_dir = _find_round_dir(state_dir, round_id)
        if round_dir:
            _show_escalated_round(round_dir)
        else:
            click.echo(f"\nReason:\n{row['escalation_reason']}")

        click.echo("\nResolution options:")
        click.echo("  orch decide '<note>' --action reject_and_redo")
        click.echo("  orch decide '<note>' --action accept_and_close")
        click.echo("  orch decide '<note>' --action resume_round")


@click.command("decide")
@click.argument("instruction")
@click.option("--action", type=click.Choice(RESOLUTION_ACTIONS), default="resume_round", show_default=True)
def decide_cmd(instruction: str, action: str):
    """Resolve the oldest escalated round and record the chosen action."""
    init_db()
    project = get_active_project()
    if not project:
        raise click.ClickException("No active project. Use: orch switch <name>")

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM rounds WHERE project_id = ? AND status = 'escalated' ORDER BY created_at LIMIT 1",
            (project["id"],),
        ).fetchone()

    if not row:
        raise click.ClickException("No escalated rounds to decide on.")

    round_id = row["id"]
    state_dir = Path(project["state_dir"])
    phase_path = state_dir / "current_phase.md"
    existing = phase_path.read_text() if phase_path.exists() else ""
    resolution_block = (
        f"\n\n## Human Resolution ({round_id})\n"
        f"Action: {action}\n"
        f"Note: {instruction}\n"
    )
    phase_path.write_text(existing.rstrip() + resolution_block)

    resolve_round(
        round_id=round_id,
        status=STATUS_BY_ACTION[action],
        action=action,
        note=instruction,
        resolved_by="human",
    )

    click.echo(f"✓ Resolution recorded for {round_id}")
    if action == "accept_and_close":
        click.echo("  Current round is marked accepted_by_human.")
    elif action == "reject_and_redo":
        click.echo("  Current round is marked rejected_by_human. Run 'orch run' to start a fresh replacement round.")
    else:
        click.echo("  Current round is marked resume_requested. Run 'orch run' to continue with the recorded human note.")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_round_dir(state_dir: Path, round_id: str) -> Path | None:
    phases_dir = state_dir / "phases"
    if not phases_dir.exists():
        return None
    for phase_dir in sorted(phases_dir.iterdir()):
        candidate = phase_dir / round_id
        if candidate.exists():
            return candidate
    return None


def _show_escalated_round(round_dir: Path) -> None:
    """Show detailed view of an escalated round for human decision."""
    task_json = round_dir / "task.json"
    if task_json.exists():
        t = json.loads(task_json.read_text())
        click.echo(f"\nTask: {t.get('title', '')}")
        click.echo(f"  Objective: {t.get('objective', '')}")
        criteria = t.get("acceptance_criteria", [])
        if criteria:
            click.echo("  Acceptance criteria:")
            for c in criteria:
                click.echo(f"    - {c}")

    attempt_count = len(list(round_dir.glob("execution_report_attempt_*.json"))) or len(list(round_dir.glob("attempt_*.md")))

    for i in range(1, attempt_count + 1):
        click.echo(f"\n  --- Attempt {i} ---")
        repaired = round_dir / f"repaired_task_attempt_{i}.json"
        if repaired.exists():
            r = json.loads(repaired.read_text())
            click.echo(f"  [Repaired task] {r.get('title', '')} — {r.get('objective', '')}")

        exec_json = round_dir / f"execution_report_attempt_{i}.json"
        if exec_json.exists():
            e = json.loads(exec_json.read_text())
            git_ev = e.get("git_evidence", {})
            if git_ev.get("has_changes"):
                files = git_ev.get("files_modified", []) + git_ev.get("files_added", [])
                click.echo(f"  Files changed (git): {files}")
                if git_ev.get("diff_stat"):
                    click.echo(f"  {git_ev['diff_stat'].splitlines()[0] if git_ev['diff_stat'] else ''}")
            else:
                click.echo("  (no git changes detected)")
            ex_ev = e.get("executor_reported", {})
            if ex_ev.get("test_results"):
                click.echo(f"  Tests: {ex_ev['test_results']}")

        review_json = round_dir / f"review_attempt_{i}.json"
        if review_json.exists():
            rv = json.loads(review_json.read_text())
            icon = "✓" if rv.get("result") == "PASS" else "✗"
            click.echo(f"  Review: {icon} {rv.get('result')} — {rv.get('rationale', '')[:120]}")
            if rv.get("required_fixes"):
                click.echo("  Required fixes:")
                for f in rv["required_fixes"]:
                    click.echo(f"    - {f}")

    audit = round_dir / "audit.md"
    if audit.exists():
        click.echo(f"\n{audit.read_text()}")
