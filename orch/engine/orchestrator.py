"""Main orchestration loop — runs rounds until completion or human intervention."""
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import click

from orch.agents.context import load_project_context
from orch.agents.designer import DesignerAgent
from orch.agents.executor import ExecutorAgent
from orch.agents.reviewer import ReviewerAgent
from orch.config.settings import OrchestratorConfig, load_config, REPO_ROOT
from orch.db.database import get_connection, now_iso, update_round_commits
from orch.engine.round_runner import RoundResult, run_round
from orch.providers.factory import get_provider
from orch.utils.git_ops import commit_projects_dir, commit_all, GitError


@dataclass
class EscalationEvent:
    project_name: str
    round_id: str
    reason: str
    audit_path: Path
    timestamp: str


def run_project(project_row) -> None:
    """Main loop: runs rounds for the active project until escalation or completion."""
    config = load_config()
    project_id = project_row["id"]
    project_name = project_row["name"]
    codebase_path = Path(project_row["codebase_path"])
    state_dir = Path(project_row["state_dir"])

    click.echo(f"\n{'='*60}")
    click.echo(f"  Orchestrator starting: {project_name}")
    click.echo(f"  Codebase : {codebase_path}")
    click.echo(f"{'='*60}\n")

    # Build agents
    designer_provider = get_provider("designer", config)
    reviewer_provider = get_provider("reviewer", config)

    designer = DesignerAgent(designer_provider, state_dir)
    executor = ExecutorAgent(
        codebase_path=codebase_path,
        model=config.agents.executor_model,
    )
    reviewer = ReviewerAgent(reviewer_provider, state_dir)

    # Get or create active phase
    phase_id = _ensure_active_phase(project_id, state_dir)

    # Main loop
    round_number = _next_round_number(project_id)

    while True:
        round_id = f"round-{round_number:04d}"
        round_dir = state_dir / "phases" / phase_id / round_id

        click.echo(f"[{_ts()}] Starting {round_id}...")

        # Get next instruction from Designer via current_phase.md
        instruction = _get_next_instruction(state_dir, round_id)

        # Run the round
        result = run_round(
            round_id=round_id,
            instruction=instruction,
            designer=designer,
            executor=executor,
            reviewer=reviewer,
            round_dir=round_dir,
        )

        # Persist round to DB
        _save_round(project_id, phase_id, round_id, result)

        if result.final_passed:
            click.echo(f"[{_ts()}] {round_id} PASSED (cost: ${result.total_cost_usd:.4f})")

            # Update project documents after successful round
            click.echo(f"[{_ts()}] Updating project documents...")
            _update_documents(designer, state_dir, result)

            # Commit both repos
            commit_msg = f"[orch] {round_id}: {result.task.description[:60]}"
            orch_hash, target_hash = _commit_both(codebase_path, commit_msg, round_id)
            update_round_commits(round_id, orch_hash, target_hash)

            # Check if phase is complete
            if _is_phase_complete(state_dir):
                click.echo(f"\n{'='*60}")
                click.echo(f"  Phase complete: {phase_id}")
                click.echo(f"{'='*60}")
                _notify_phase_complete(project_name, phase_id, config)
                break

            round_number += 1

        else:
            # Escalate — stop and notify user
            event = EscalationEvent(
                project_name=project_name,
                round_id=round_id,
                reason=result.escalation_reason,
                audit_path=round_dir / "audit.md",
                timestamp=_ts(),
            )
            _print_escalation_report(event)
            _notify_escalation(event, config)
            _save_escalation(project_id, round_id, result.escalation_reason)
            break

    click.echo(f"\n[{_ts()}] Orchestrator stopped. Use 'orch review' to see pending escalations.")


def _get_next_instruction(state_dir: Path, round_id: str) -> str:
    """Read the next instruction from current_phase.md."""
    phase_path = state_dir / "current_phase.md"
    if phase_path.exists():
        content = phase_path.read_text()
        return (
            f"Based on the current phase document, determine the next concrete task to implement.\n\n"
            f"Round ID: {round_id}\n\n"
            f"Current phase:\n{content}"
        )
    return f"Review the project vision and plan the next implementation task. Round ID: {round_id}"


def _update_documents(designer: DesignerAgent, state_dir: Path, result: RoundResult) -> None:
    """Trigger Designer to update decisions.md and current_phase.md after a round."""
    last_attempt = result.attempts[-1]
    summary = (
        f"Round {result.round_id} completed successfully.\n"
        f"Task: {result.task.description}\n"
        f"Output: {last_attempt.executor_output[:500]}"
    )
    update = designer.update_documents(summary)

    (state_dir / "decisions.md").write_text(update.decisions_md)
    (state_dir / "current_phase.md").write_text(update.current_phase_md)


def _is_phase_complete(state_dir: Path) -> bool:
    """Check if current_phase.md indicates all tasks are done."""
    phase_path = state_dir / "current_phase.md"
    if not phase_path.exists():
        return False
    content = phase_path.read_text().lower()
    # Phase is complete if Designer wrote completion indicators
    return any(marker in content for marker in ("phase complete", "all tasks done", "phase finished"))


def _ensure_active_phase(project_id: str, state_dir: Path) -> str:
    """Get or create the active phase for a project."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM phases WHERE project_id = ? AND status = 'in_progress' ORDER BY created_at DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        if row:
            return row["id"]

        # Create initial phase
        phase_id = "phase-0001"
        conn.execute(
            "INSERT INTO phases (id, project_id, name, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (phase_id, project_id, "Phase 1", "in_progress", now_iso()),
        )
        (state_dir / "phases" / phase_id).mkdir(parents=True, exist_ok=True)
        return phase_id


def _next_round_number(project_id: str) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM rounds WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        return (row["cnt"] or 0) + 1


def _save_round(project_id: str, phase_id: str, round_id: str, result: RoundResult) -> None:
    last_attempt = result.attempts[-1] if result.attempts else None
    status = "passed" if result.final_passed else "escalated"
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO rounds
               (id, project_id, phase_id, status, attempt_count,
                task_description, executor_result, reviewer_verdict,
                escalation_reason, cost_usd, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                round_id, project_id, phase_id, status,
                len(result.attempts),
                result.task.description,
                last_attempt.executor_output if last_attempt else "",
                "PASS" if result.final_passed else "FAIL",
                result.escalation_reason or None,
                result.total_cost_usd,
                now_iso(), now_iso(),
            ),
        )


def _save_escalation(project_id: str, round_id: str, reason: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO phases (id, project_id, name, description, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
            (f"escalation-{round_id}", project_id, "Escalation", reason, "pending", now_iso()),
        )


def _print_escalation_report(event: EscalationEvent) -> None:
    click.echo(f"\n{'!'*60}")
    click.echo(f"  ACTION REQUIRED — {event.project_name}")
    click.echo(f"  Round {event.round_id} failed after 2 attempts")
    click.echo(f"{'!'*60}")
    click.echo(f"\n{event.reason}")
    click.echo(f"\nAudit report: {event.audit_path}")
    click.echo(f"\nRun 'orch review' to see details.")
    click.echo(f"Run 'orch decide <instruction>' to resume.\n")


def _notify_escalation(event: EscalationEvent, config: OrchestratorConfig) -> None:
    if not config.notification.email:
        return
    email_cfg = config.notification.email
    if not email_cfg.to_addr or not email_cfg.from_addr:
        return
    try:
        _send_email(
            smtp_host=email_cfg.smtp_host,
            smtp_port=email_cfg.smtp_port,
            from_addr=email_cfg.from_addr,
            to_addr=email_cfg.to_addr,
            subject=f"[Orchestrator] Action required — {event.project_name} / {event.round_id}",
            body=(
                f"Round {event.round_id} failed after 2 attempts and requires your attention.\n\n"
                f"Project: {event.project_name}\n"
                f"Time: {event.timestamp}\n\n"
                f"Reason:\n{event.reason}\n\n"
                f"Audit report: {event.audit_path}\n\n"
                f"Run 'orch review' and 'orch decide' to resume."
            ),
        )
        click.echo(f"[{event.timestamp}] Email notification sent to {email_cfg.to_addr}")
    except Exception as e:
        click.echo(f"[{event.timestamp}] Email notification failed: {e}", err=True)


def _notify_phase_complete(project_name: str, phase_id: str, config: OrchestratorConfig) -> None:
    if not config.notification.email:
        return
    email_cfg = config.notification.email
    if not email_cfg.to_addr or not email_cfg.from_addr:
        return
    try:
        _send_email(
            smtp_host=email_cfg.smtp_host,
            smtp_port=email_cfg.smtp_port,
            from_addr=email_cfg.from_addr,
            to_addr=email_cfg.to_addr,
            subject=f"[Orchestrator] Phase complete — {project_name} / {phase_id}",
            body=f"Phase {phase_id} of project '{project_name}' has been completed successfully.",
        )
    except Exception:
        pass


def _send_email(smtp_host: str, smtp_port: int, from_addr: str, to_addr: str,
                subject: str, body: str) -> None:
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.sendmail(from_addr, [to_addr], msg.as_string())


def _commit_both(codebase_path: Path, message: str, round_id: str) -> tuple[str, str]:
    """Commit orchestrator projects/ dir and target project. Returns (orch_hash, target_hash)."""
    try:
        orch_hash = commit_projects_dir(REPO_ROOT, message)
    except GitError as e:
        click.echo(f"  ⚠ Orchestrator commit failed: {e}", err=True)
        orch_hash = ""

    try:
        target_hash = commit_all(codebase_path, message)
    except GitError as e:
        click.echo(f"  ⚠ Target project commit failed: {e}", err=True)
        target_hash = ""

    if orch_hash and target_hash:
        click.echo(f"  ✓ Committed — orch:{orch_hash[:7]}  target:{target_hash[:7]}")

    return orch_hash, target_hash


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")
