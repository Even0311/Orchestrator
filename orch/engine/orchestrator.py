"""Main orchestration loop — runs rounds until completion or human intervention."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click

from orch.agents.designer import DesignerAgent
from orch.agents.executor import ExecutorAgent
from orch.agents.reviewer import ReviewerAgent
from orch.config.settings import OrchestratorConfig, load_config, REPO_ROOT
from orch.db.database import get_connection, now_iso, update_round_commits
from orch.engine.round_runner import RoundResult, run_round, inject_recent_rounds, cleanup_round_docs
from orch.providers.factory import get_provider
from orch.utils.claudemd_manager import generate_claudemd
from orch.utils.git_ops import commit_all, clean_working_tree, get_current_commit, GitError


@dataclass
class EscalationEvent:
    project_name: str
    round_id: str
    reason: str
    audit_path: Path
    timestamp: str


def run_project(project_row, run_once: bool = False) -> None:
    """Main loop: runs rounds for the active project until escalation or human intervention."""
    config = load_config()
    project_id = project_row["id"]
    project_name = project_row["name"]
    codebase_path = Path(project_row["codebase_path"])
    state_dir = Path(project_row["state_dir"])
    test_cmd = project_row["test_cmd"]  # may be None

    click.echo(f"\n{'='*60}")
    click.echo(f"  Orchestrator starting: {project_name}")
    click.echo(f"  Codebase : {codebase_path}")
    click.echo(f"{'='*60}\n")

    designer_provider = get_provider("designer", config)
    designer = DesignerAgent(designer_provider, state_dir)
    executor = ExecutorAgent(codebase_path=codebase_path, model=config.agents.executor_model)
    reviewer = ReviewerAgent(codebase_path=codebase_path, model=config.agents.reviewer_model)

    if _needs_bootstrap(state_dir):
        click.echo(f"[{_ts()}] Bootstrap mode: generating initial phase plan from vision.md...")
        _run_bootstrap(designer, state_dir, config)
        click.echo(f"[{_ts()}] Bootstrap complete. Proceeding to first round.\n")

    phase_id = _ensure_active_phase(project_id, state_dir)
    round_number = _next_round_number(project_id)

    while True:
        round_id = f"round-{round_number:04d}"
        round_dir = state_dir / "phases" / phase_id / round_id

        resolution = _get_pending_human_resolution(project_id)
        if resolution and resolution["status"] == "accepted_by_human":
            click.echo(f"\n{'─'*60}")
            click.echo(f"[{_ts()}] Applying human acceptance for {resolution['id']}")
            _apply_human_acceptance(designer, state_dir, resolution)
            orch_hash, target_hash = _commit_both(
                codebase_path,
                f"[orch] {resolution['id']}: accepted by human",
                resolution["id"],
            )
            update_round_commits(resolution["id"], orch_hash, target_hash)
            _set_round_status(resolution["id"], "accepted_applied")

            if _is_phase_complete(state_dir):
                click.echo(f"\n{'='*60}")
                click.echo(f"  Phase complete: {phase_id}")
                click.echo(f"{'='*60}")
                _close_phase(project_id, phase_id)
                _notify_phase_complete(project_name, phase_id, config)
                click.echo(f"  [{_ts()}] Planning next phase...")
                try:
                    _run_phase_plan(designer, state_dir)
                except Exception as e:
                    click.echo(f"  ⚠ Phase planning failed: {e}", err=True)
                    click.echo("  Next phase must be planned manually before re-running.", err=True)
                break

            if run_once:
                click.echo(f"[{_ts()}] --once: stopping after applying human acceptance for {resolution['id']}.")
                break

            round_number = _next_round_number(project_id)
            continue

        click.echo(f"\n{'─'*60}")
        click.echo(f"[{_ts()}] Starting {round_id}")

        try:
            generate_claudemd(state_dir, codebase_path)
        except Exception as e:
            click.echo(f"  ⚠ CLAUDE.md generation failed: {e}", err=True)

        try:
            recent = _build_recent_rounds_summary(project_id)
            inject_recent_rounds(codebase_path, recent)
        except Exception as e:
            click.echo(f"  ⚠ recent_rounds injection failed: {e}", err=True)

        instruction = (
            _build_resolution_instruction(state_dir, resolution, round_id)
            if resolution and resolution["status"] in ("resume_requested", "rejected_by_human")
            else _get_next_instruction(state_dir, round_id)
        )
        if resolution and resolution["status"] in ("resume_requested", "rejected_by_human"):
            consumed_status = "resume_consumed" if resolution["status"] == "resume_requested" else "redo_consumed"
            _set_round_status(resolution["id"], consumed_status)

        result = run_round(
            round_id=round_id,
            instruction=instruction,
            designer=designer,
            executor=executor,
            reviewer=reviewer,
            round_dir=round_dir,
            codebase_path=codebase_path,
            test_cmd=test_cmd,
        )

        _save_round(project_id, phase_id, round_id, result)

        try:
            cleanup_round_docs(codebase_path)
        except Exception as e:
            click.echo(f"  ⚠ .orch/runtime cleanup failed: {e}", err=True)

        if result.final_passed:
            click.echo(
                f"\n  [{_ts()}] {click.style(f'{round_id} PASSED', fg='green', bold=True)} "
                f"({len(result.attempts)} attempt(s), ${result.total_cost_usd:.4f})"
            )

            click.echo(f"  [{_ts()}] Updating project documents...")
            _update_documents(designer, state_dir, result)

            commit_msg = f"[orch] {round_id}: {result.task.description[:60]}"
            orch_hash, target_hash = _commit_both(codebase_path, commit_msg, round_id)
            update_round_commits(round_id, orch_hash, target_hash)

            if _is_phase_complete(state_dir):
                click.echo(f"\n{'='*60}")
                click.echo(f"  Phase complete: {phase_id}")
                click.echo(f"{'='*60}")
                _close_phase(project_id, phase_id)
                _notify_phase_complete(project_name, phase_id, config)

                click.echo(f"  [{_ts()}] Planning next phase...")
                try:
                    _run_phase_plan(designer, state_dir)
                except Exception as e:
                    click.echo(f"  ⚠ Phase planning failed: {e}", err=True)
                    click.echo("  Next phase must be planned manually before re-running.", err=True)
                break

            if run_once:
                click.echo(f"[{_ts()}] --once: stopping after round {round_id}.")
                break

            round_number += 1
        else:
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

            try:
                clean_working_tree(codebase_path)
                click.echo(f"  [{_ts()}] Target working tree cleaned")
            except Exception as e:
                click.echo(f"  ⚠ Working tree cleanup failed: {e}", err=True)

            break

    click.echo(f"\n[{_ts()}] Orchestrator stopped. Use 'orch review' to see pending escalations.")


def _needs_bootstrap(state_dir: Path) -> bool:
    phase_path = state_dir / "current_phase.md"
    if not phase_path.exists():
        return True
    content = phase_path.read_text()
    return "bootstrap_needed" in content or "待规划" in content


def _run_phase_plan(designer: DesignerAgent, state_dir: Path) -> None:
    result = designer.plan_phase()

    if result.current_phase_md:
        (state_dir / "current_phase.md").write_text(result.current_phase_md)
        click.echo("  ✓ current_phase.md — next phase planned")

    if result.designer_context_md:
        (state_dir / "context" / "designer.md").write_text(result.designer_context_md)
        click.echo("  ✓ context/designer.md updated")

    if result.cost_usd:
        click.echo(f"  Phase planning cost: ${result.cost_usd:.4f}")


def _run_bootstrap(designer: DesignerAgent, state_dir: Path, config: OrchestratorConfig) -> None:
    vision_path = state_dir / "vision.md"
    if not vision_path.exists():
        raise click.ClickException(
            "vision.md not found. Edit the vision file before running:\n"
            f"  {vision_path}"
        )

    vision_content = vision_path.read_text()
    if "<!-- " in vision_content and len(vision_content) < 500:
        raise click.ClickException(
            "vision.md appears to still be the template. Please fill in your project vision before running.\n"
            f"  {vision_path}"
        )

    result = designer.bootstrap_phase(vision_content)

    if result.current_phase_md:
        (state_dir / "current_phase.md").write_text(result.current_phase_md)
        click.echo("  ✓ current_phase.md generated")

    if result.designer_context_md:
        (state_dir / "context" / "designer.md").write_text(result.designer_context_md)
        click.echo("  ✓ context/designer.md generated")

    if result.cost_usd:
        click.echo(f"  Bootstrap cost: ${result.cost_usd:.4f}")


def _update_documents(designer: DesignerAgent, state_dir: Path, result: RoundResult) -> None:
    last_attempt = result.attempts[-1]
    ev = last_attempt.executor_evidence

    summary = (
        f"Round {result.round_id} completed successfully.\n"
        f"Task: {result.task.title} — {result.task.objective}\n\n"
        f"Execution summary: {ev.summary}\n"
        f"Files changed: {', '.join(ev.files_changed) or '(none)'}\n"
        f"Commands run: {', '.join(ev.commands_run) or '(none)'}\n"
        f"Test results: {ev.test_results or '(not run)'}\n"
        f"Unresolved issues: {', '.join(ev.unresolved_issues) or '(none)'}"
    )
    _apply_document_update(designer, state_dir, summary)


def _apply_human_acceptance(designer: DesignerAgent, state_dir: Path, resolution_row) -> None:
    round_id = resolution_row["id"]
    task_description = resolution_row["task_description"] or "(task description unavailable)"
    note = resolution_row["resolution_note"] or "(no note)"
    summary = (
        f"Round {round_id} was accepted by human override.\n"
        f"Task description: {task_description}\n"
        f"Human rationale: {note}\n\n"
        f"Treat this round as accepted and update current_phase.md / context/designer.md accordingly."
    )
    _apply_document_update(designer, state_dir, summary)


def _apply_document_update(designer: DesignerAgent, state_dir: Path, summary: str) -> None:
    update = designer.update_documents(summary)

    if update.decisions_entry and update.decisions_entry.strip():
        decisions_path = state_dir / "decisions.md"
        existing = decisions_path.read_text() if decisions_path.exists() else ""
        decisions_path.write_text(existing.rstrip() + "\n\n" + update.decisions_entry.strip() + "\n")
        click.echo("  ✓ decisions.md updated (appended)")

    if update.current_phase_md:
        (state_dir / "current_phase.md").write_text(update.current_phase_md)
        click.echo("  ✓ current_phase.md updated")

    if update.designer_context_md:
        (state_dir / "context" / "designer.md").write_text(update.designer_context_md)
        click.echo("  ✓ context/designer.md updated")


def _build_recent_rounds_summary(project_id: str, limit: int = 3) -> str:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, status, task_description, cost_usd FROM rounds "
            "WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit),
        ).fetchall()

    if not rows:
        return "# Recent Rounds\n\nNo previous rounds.\n"

    lines = ["# Recent Rounds", "", "Most recent first:", ""]
    for row in rows:
        status = row["status"].upper()
        desc = (row["task_description"] or "")[:80]
        lines.append(f"- **{row['id']}** [{status}] — {desc}")

    lines.append("")
    lines.append("Do not redo work that was already completed in a previous round.")
    lines.append("")
    return "\n".join(lines)


def _get_next_instruction(state_dir: Path, round_id: str) -> str:
    phase_path = state_dir / "current_phase.md"
    if phase_path.exists():
        content = phase_path.read_text()
        return (
            "Based on the current phase document, determine the next concrete task to implement.\n\n"
            f"Round ID: {round_id}\n\n"
            f"Current phase:\n{content}"
        )
    return f"Review the project vision and plan the next implementation task. Round ID: {round_id}"


def _build_resolution_instruction(state_dir: Path, resolution_row, next_round_id: str) -> str:
    phase_content = (state_dir / "current_phase.md").read_text() if (state_dir / "current_phase.md").exists() else ""
    round_id = resolution_row["id"]
    task_description = resolution_row["task_description"] or "(task description unavailable)"
    note = resolution_row["resolution_note"] or "(no note)"
    action = resolution_row["resolution_action"] or resolution_row["status"]

    if resolution_row["status"] == "resume_requested":
        resolution_header = (
            f"Human requested continuation after escalated round {round_id}.\n"
            f"Treat this as a follow-up continuation request, not a fresh unrelated task.\n"
        )
    else:
        resolution_header = (
            f"Human rejected the result of escalated round {round_id} and requested a redo.\n"
            f"Treat this as a fresh replacement attempt for the same intended outcome.\n"
        )

    return (
        f"{resolution_header}\n"
        f"Previous round: {round_id}\n"
        f"Recorded action: {action}\n"
        f"Human note: {note}\n"
        f"Original task description: {task_description}\n\n"
        f"Round ID: {next_round_id}\n\n"
        f"Current phase:\n{phase_content}"
    )


def _get_pending_human_resolution(project_id: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM rounds WHERE project_id = ? "
            "AND status IN ('accepted_by_human', 'resume_requested', 'rejected_by_human') "
            "ORDER BY updated_at ASC, created_at ASC LIMIT 1",
            (project_id,),
        ).fetchone()


def _set_round_status(round_id: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE rounds SET status = ?, updated_at = ? WHERE id = ?",
            (status, now_iso(), round_id),
        )


def _is_phase_complete(state_dir: Path) -> bool:
    import re
    phase_path = state_dir / "current_phase.md"
    if not phase_path.exists():
        return False
    content = phase_path.read_text()
    if any(m in content.lower() for m in ("phase complete", "all tasks done", "phase finished")):
        return True
    queue_match = re.search(r"## Task Queue\s*(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if queue_match:
        return "- [ ]" not in queue_match.group(1)
    return False


def _ensure_active_phase(project_id: str, state_dir: Path) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM phases WHERE project_id = ? AND status = 'in_progress' ORDER BY created_at DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        if row:
            return row["id"]

        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM phases WHERE project_id = ? AND id LIKE 'phase-%'",
            (project_id,),
        ).fetchone()
        next_num = (count_row["cnt"] or 0) + 1
        phase_id = f"phase-{next_num:04d}"
        conn.execute(
            "INSERT INTO phases (id, project_id, name, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (phase_id, project_id, f"Phase {next_num}", "in_progress", now_iso()),
        )
        (state_dir / "phases" / phase_id).mkdir(parents=True, exist_ok=True)
        return phase_id


def _close_phase(project_id: str, phase_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE phases SET status = 'completed' WHERE id = ? AND project_id = ?",
            (phase_id, project_id),
        )


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
                last_attempt.executor_output[:500] if last_attempt else "",
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
    click.echo("\nRun 'orch review' to see details.")
    click.echo("Then choose one of:")
    click.echo("  orch decide \"<note>\" --action reject_and_redo")
    click.echo("  orch decide \"<note>\" --action accept_and_close")
    click.echo("  orch decide \"<note>\" --action resume_round\n")


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
                f"Run 'orch review' and 'orch decide' to continue."
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


def _send_email(smtp_host: str, smtp_port: int, from_addr: str, to_addr: str, subject: str, body: str) -> None:
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
    """Record orchestrator revision and commit target project state/code."""
    try:
        orch_hash = get_current_commit(REPO_ROOT)
    except GitError as e:
        click.echo(f"  ⚠ Orchestrator revision lookup failed: {e}", err=True)
        orch_hash = ""

    try:
        target_hash = commit_all(codebase_path, message)
    except GitError as e:
        click.echo(f"  ⚠ Target project commit failed: {e}", err=True)
        target_hash = ""

    if orch_hash and target_hash:
        click.echo(f"  ✓ Committed — orch:{orch_hash[:7]}  target:{target_hash[:7]}")
    elif target_hash:
        click.echo(f"  ✓ Committed target project — {target_hash[:7]}")

    return orch_hash, target_hash


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")
