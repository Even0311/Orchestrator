import json
from pathlib import Path

import click

from orch.db.database import get_active_project, get_connection, init_db


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

        click.echo(f"\nTo resume: orch decide '<instruction>'")


@click.command("decide")
@click.argument("instruction")
def decide_cmd(instruction: str):
    """Provide a decision on the oldest escalated round and resume execution."""
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

    # Append human decision to current_phase.md
    state_dir = Path(project["state_dir"])
    phase_path = state_dir / "current_phase.md"
    existing = phase_path.read_text() if phase_path.exists() else ""
    phase_path.write_text(
        existing.rstrip() + f"\n\n## Human Decision ({round_id})\n{instruction}\n"
    )

    # Mark round as resolved
    with get_connection() as conn:
        conn.execute(
            "UPDATE rounds SET status = 'resolved_by_human', updated_at = datetime('now') WHERE id = ?",
            (round_id,),
        )

    click.echo(f"✓ Decision recorded for {round_id}")
    click.echo(f"  Run 'orch run' to continue from this point.")


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

    # Show task
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

    # Count attempts
    attempt_count = len(list(round_dir.glob("execution_report_attempt_*.json"))) or \
                    len(list(round_dir.glob("attempt_*.md")))

    for i in range(1, attempt_count + 1):
        click.echo(f"\n  --- Attempt {i} ---")

        # Show repaired task if this was attempt > 1
        repaired = round_dir / f"repaired_task_attempt_{i}.json"
        if repaired.exists():
            r = json.loads(repaired.read_text())
            click.echo(f"  [Repaired task] {r.get('title', '')} — {r.get('objective', '')}")

        # Show git evidence
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

        # Show review verdict
        review_json = round_dir / f"review_attempt_{i}.json"
        if review_json.exists():
            rv = json.loads(review_json.read_text())
            icon = "✓" if rv.get("result") == "PASS" else "✗"
            click.echo(f"  Review: {icon} {rv.get('result')} — {rv.get('rationale', '')[:120]}")
            if rv.get("required_fixes"):
                click.echo("  Required fixes:")
                for f in rv["required_fixes"]:
                    click.echo(f"    - {f}")

    # Show audit
    audit = round_dir / "audit.md"
    if audit.exists():
        click.echo(f"\n{audit.read_text()}")
