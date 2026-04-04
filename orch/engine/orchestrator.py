"""Main orchestration loop — control plane only.

The orchestrator manages SOT, selects work items, invokes Claude Code once
per round, runs post-round hard gates, and updates state on PASS.
All internal round coordination (designer/executor/reviewer) is handled
by Claude Code via subagent definitions.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click

from orch.briefing import generate_round_brief, read_artifacts
from orch.config.settings import OrchestratorConfig, load_config, REPO_ROOT, PROJECTS_DIR
from orch.db.database import get_connection, now_iso, update_round_commits
from orch.engine.claude_round_driver import run_attempt, subagents_available
from orch.engine.hard_gates import run_hard_gates, validate_proposed_scope, HardGateResults, snapshot_sot_dir, detect_sot_mutation
from orch.models import (
    AttemptRecord,
    ExecutionEvidence,
    ReviewVerdict,
    RoundResult,
    TaskContract,
    Verdict,
)
from orch.sot import parse_current_phase, mark_task_complete, is_phase_complete, append_decision_entry, PhaseInfo
from orch.utils.evidence_collector import collect_git_evidence
from orch.utils.git_ops import commit_all, clean_working_tree, get_current_commit, GitError


@dataclass
class EscalationEvent:
    project_name: str
    round_id: str
    reason: str
    audit_path: Path
    timestamp: str


def run_project(project_row, run_once: bool = False) -> None:
    """Main loop: run rounds for the active project until escalation or completion."""
    config = load_config()
    project_id = project_row["id"]
    project_name = project_row["name"]
    codebase_path = Path(project_row["codebase_path"])
    test_cmd = project_row["test_cmd"]

    # SOT lives in orchestrator repo under projects/<name>/
    sot_dir = PROJECTS_DIR / project_name
    if not sot_dir.exists():
        # Fallback to state_dir from DB for backward compat
        sot_dir = Path(project_row["state_dir"])

    click.echo(f"\n{'='*60}")
    click.echo(f"  Orchestrator starting: {project_name}")
    click.echo(f"  Codebase : {codebase_path}")
    click.echo(f"{'='*60}\n")

    if not subagents_available(codebase_path):
        raise click.ClickException(
            "Subagent definitions not found in target repo.\n"
            "Ensure .claude/agents/ contains: designer.md, executor.md, reviewer.md, round-driver.md\n"
            "Run 'orch new' or manually create them."
        )

    phase_id = _ensure_active_phase(project_id, sot_dir)
    round_number = _next_round_number(project_id)

    while True:
        round_id = f"round-{round_number:04d}"

        # Handle pending human resolutions
        resolution = _get_pending_human_resolution(project_id)
        if resolution and resolution["status"] == "accepted_by_human":
            click.echo(f"\n{'─'*60}")
            click.echo(f"[{_ts()}] Applying human acceptance for {resolution['id']}")

            # Mark task complete in SOT if we know the task key
            task_desc = resolution["task_description"] or ""
            _try_mark_task_complete(sot_dir, task_desc, "accepted by human")

            orch_hash, target_hash = _commit_both(
                codebase_path,
                f"[orch] {resolution['id']}: accepted by human",
                resolution["id"],
            )
            update_round_commits(resolution["id"], orch_hash, target_hash)
            _set_round_status(resolution["id"], "accepted_applied")

            if is_phase_complete(sot_dir):
                _handle_phase_complete(project_id, phase_id, project_name, config)
                break

            if run_once:
                click.echo(f"[{_ts()}] --once: stopping after human acceptance.")
                break

            round_number = _next_round_number(project_id)
            continue

        # Parse SOT to find next task
        phase_info = parse_current_phase(sot_dir)
        if phase_info.all_done:
            _handle_phase_complete(project_id, phase_id, project_name, config)
            break

        if not phase_info.next_task_key:
            raise click.ClickException(
                "No tasks found in current_phase.md Task Queue. "
                "Add tasks or mark the phase complete."
            )

        click.echo(f"\n{'─'*60}")
        click.echo(f"[{_ts()}] Starting {round_id}")
        click.echo(f"  Task: {phase_info.next_task_key} — {phase_info.next_task_desc[:80]}")

        # Determine round directory
        rounds_base = sot_dir / "rounds"
        round_dir = rounds_base / round_id

        # Build resolution instruction if applicable
        prior_failure = ""
        if resolution and resolution["status"] in ("resume_requested", "rejected_by_human"):
            prior_failure = _build_resolution_context(resolution)
            consumed_status = "resume_consumed" if resolution["status"] == "resume_requested" else "redo_consumed"
            _set_round_status(resolution["id"], consumed_status)

        # Build recent rounds summary
        recent = _build_recent_rounds_summary(project_id)

        # Run round (up to 2 attempts)
        result = _run_round(
            round_id=round_id,
            round_dir=round_dir,
            codebase_path=codebase_path,
            sot_dir=sot_dir,
            phase_info=phase_info,
            test_cmd=test_cmd,
            model=config.agents.executor_model,
            prior_failure=prior_failure,
            recent_rounds=recent,
        )

        _save_round(project_id, phase_id, round_id, result)

        if result.final_passed:
            click.echo(
                f"\n  [{_ts()}] {click.style(f'{round_id} PASSED', fg='green', bold=True)} "
                f"({len(result.attempts)} attempt(s), ${result.total_cost_usd:.4f})"
            )

            # Mark task complete in SOT
            task_key = result.task.task_key
            if task_key:
                marked = mark_task_complete(
                    sot_dir, task_key,
                    f"Round {round_id} — {result.task.title[:60]}",
                )
                if marked:
                    click.echo(f"  [{_ts()}] Marked {task_key} complete in current_phase.md")

            # Append decision entry (C: restore decisions.md update on PASS)
            last_attempt = result.attempts[-1] if result.attempts else None
            gate_summary = ""
            if last_attempt:
                gate_summary = "all passed"
            append_decision_entry(
                sot_dir,
                round_id=round_id,
                phase_id=result.task.phase_id,
                task_key=result.task.task_key,
                task_title=result.task.title,
                outcome_summary=result.task.objective[:200],
                hard_gate_summary=gate_summary,
                notes=last_attempt.execution_evidence.summary[:200] if last_attempt else "",
            )
            click.echo(f"  [{_ts()}] Appended decision entry to decisions.md")

            # Commit both orchestrator SOT and target repo
            commit_msg = f"[orch] {round_id}: {result.task.title[:60]}"
            orch_hash, target_hash = _commit_both(codebase_path, commit_msg, round_id)
            update_round_commits(round_id, orch_hash, target_hash)

            if is_phase_complete(sot_dir):
                _handle_phase_complete(project_id, phase_id, project_name, config)
                break

            if run_once:
                click.echo(f"[{_ts()}] --once: stopping after round {round_id}.")
                break

            round_number += 1
        else:
            # Escalate
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


def _run_round(
    *,
    round_id: str,
    round_dir: Path,
    codebase_path: Path,
    sot_dir: Path,
    phase_info: PhaseInfo,
    test_cmd: str | None,
    model: str,
    prior_failure: str = "",
    recent_rounds: str = "",
    max_attempts: int = 2,
) -> RoundResult:
    """Execute a complete round with up to max_attempts."""
    placeholder_task = TaskContract(
        phase_id=phase_info.phase_id,
        task_key=phase_info.next_task_key,
        title=phase_info.next_task_desc[:80],
        objective=phase_info.next_task_desc,
    )
    result = RoundResult(round_id=round_id, task=placeholder_task)

    for attempt_num in range(1, max_attempts + 1):
        attempt_dir = round_dir / f"attempt_{attempt_num}"
        attempt_dir.mkdir(parents=True, exist_ok=True)

        click.echo(f"\n  [{_ts()}] --- Attempt {attempt_num}/{max_attempts} ---")

        # Generate briefing
        generate_round_brief(
            round_dir=attempt_dir,
            sot_dir=sot_dir,
            phase_info=phase_info,
            round_id=round_id,
            attempt_num=attempt_num,
            prior_failure=prior_failure,
            recent_rounds_summary=recent_rounds,
        )

        # Snapshot canonical SOT state BEFORE Claude runs.
        # The only allowed write area is the current attempt_dir.
        sot_snapshot = snapshot_sot_dir(sot_dir, allowed_write_prefix=attempt_dir)

        # Invoke Claude
        click.echo(f"  [{_ts()}] Claude round driver running...", nl=False)
        t0 = time.time()
        attempt = run_attempt(
            codebase_path=codebase_path,
            round_dir=attempt_dir,
            round_id=round_id,
            attempt_num=attempt_num,
            model=model,
        )
        elapsed = time.time() - t0
        elapsed_str = f"{elapsed:.0f}s" if elapsed < 60 else f"{elapsed / 60:.1f}m"
        click.echo(f" done ({elapsed_str}, ${attempt.claude_cost_usd:.4f})")

        if attempt.execution_evidence.summary:
            click.echo(f"           Summary: {attempt.execution_evidence.summary[:120]}")

        # Update task from what Claude produced
        if attempt.task.title and attempt.task.title != "(task contract not produced)":
            result.task = attempt.task

        # Validate Claude-proposed file scope (D: not self-authoritative)
        scope = validate_proposed_scope(
            proposed_allowed=attempt.task.allowed_files or [],
            proposed_forbidden=attempt.task.forbidden_files or [],
            git_evidence=attempt.git_evidence,
        )
        if not scope.valid:
            click.echo(f"  [{_ts()}] Scope policy rejected Claude's proposed file scope:")
            for v in scope.violations:
                click.echo(f"           {v}")

        # Run hard gates with sanitized scope
        click.echo(f"  [{_ts()}] Hard gates...", nl=False)
        t0 = time.time()
        gate_results = run_hard_gates(
            codebase_path=codebase_path,
            git_evidence=attempt.git_evidence,
            round_dir=attempt_dir,
            allowed_files=scope.sanitized_allowed or None,
            forbidden_files=scope.sanitized_forbidden or None,
            test_cmd=test_cmd,
        )
        # Canonical SOT mutation detection (before/after comparison)
        sot_gate = detect_sot_mutation(sot_snapshot, sot_dir, allowed_write_prefix=attempt_dir)
        gate_results.gates.append(sot_gate)

        # Merge scope violations into gate results
        if not scope.valid:
            from orch.engine.hard_gates import GateResult
            gate_results.gates.append(GateResult(
                name="scope_policy",
                passed=False,
                detail="; ".join(scope.violations),
            ))
        elapsed = time.time() - t0
        elapsed_str = f"{elapsed:.0f}s" if elapsed < 60 else f"{elapsed / 60:.1f}m"

        if gate_results.all_passed:
            click.echo(f" {click.style('ALL PASS', fg='green')} ({elapsed_str})")
        else:
            click.echo(f" {click.style('FAIL', fg='red')} ({elapsed_str})")
            for g in gate_results.failures:
                click.echo(f"           {g.name}: {g.detail[:120]}")

        # Adjudicate: hard gates override Claude's internal review
        hard_gate_verdict = gate_results.to_verdict()
        if hard_gate_verdict:
            attempt = AttemptRecord(
                attempt_number=attempt.attempt_number,
                task=attempt.task,
                execution_evidence=attempt.execution_evidence,
                git_evidence=attempt.git_evidence,
                review_verdict=hard_gate_verdict,
                claude_cost_usd=attempt.claude_cost_usd,
                is_token_exhausted=attempt.is_token_exhausted,
                claude_output=attempt.claude_output,
            )
            click.echo(f"  [{_ts()}] Hard gate overrides internal review → FAIL")
        else:
            # Hard gates pass — use Claude's internal review
            verdict_color = "green" if attempt.review_verdict.passed else "red"
            verdict_text = click.style(attempt.review_verdict.verdict.value, fg=verdict_color, bold=True)
            click.echo(f"  [{_ts()}] Internal reviewer verdict: {verdict_text}")

        # Write attempt artifacts
        _write_attempt_report(attempt_dir, attempt, gate_results)

        result.attempts.append(attempt)

        if attempt.passed:
            result.final_passed = True
            break

        # Build prior_failure for next attempt
        prior_failure = _build_failure_context(attempt, gate_results)
        if attempt_num == max_attempts:
            click.echo(f"\n  [{_ts()}] Max attempts reached — escalating")
            result.escalation_reason = _build_escalation_reason(result)

    _write_audit_file(round_dir / "audit.md", result)
    return result


# ── Helper functions ─────────────────────────────────────────────────────────

def _build_failure_context(attempt: AttemptRecord, gate_results: HardGateResults) -> str:
    lines = [f"Previous attempt {attempt.attempt_number} failed."]
    if attempt.task.title:
        lines.append(f"Task: {attempt.task.title}")
    lines.append(f"Review rationale: {attempt.review_verdict.rationale}")
    for c in attempt.review_verdict.unmet_criteria:
        lines.append(f"Unmet: {c}")
    for f in attempt.review_verdict.blocker_fixes:
        lines.append(f"Fix required: {f}")
    for g in gate_results.failures:
        lines.append(f"Hard gate {g.name}: {g.detail}")
    return "\n".join(lines)


def _build_resolution_context(resolution_row) -> str:
    round_id = resolution_row["id"]
    note = resolution_row["resolution_note"] or "(no note)"
    task_desc = resolution_row["task_description"] or "(unknown)"
    action = resolution_row["resolution_action"] or resolution_row["status"]

    if resolution_row["status"] == "resume_requested":
        header = f"Human requested continuation after escalated round {round_id}."
    else:
        header = f"Human rejected round {round_id} and requested a redo."

    return f"{header}\nAction: {action}\nHuman note: {note}\nOriginal task: {task_desc}"


def _try_mark_task_complete(sot_dir: Path, task_desc: str, note: str) -> None:
    """Try to extract task_key from description and mark complete."""
    import re
    m = re.search(r"(P\d+-T\d+)", task_desc)
    if m:
        mark_task_complete(sot_dir, m.group(1), note)


def _write_attempt_report(attempt_dir: Path, attempt: AttemptRecord, gate_results: HardGateResults) -> None:
    report = {
        "attempt": attempt.attempt_number,
        "passed": attempt.passed,
        "cost_usd": attempt.claude_cost_usd,
        "is_token_exhausted": attempt.is_token_exhausted,
        "task": attempt.task.to_dict() if hasattr(attempt.task, "to_dict") else {},
        "execution_evidence": attempt.execution_evidence.to_dict(),
        "review_verdict": attempt.review_verdict.to_dict(),
        "hard_gates": [
            {"name": g.name, "passed": g.passed, "detail": g.detail}
            for g in gate_results.gates
        ],
        "git_evidence": {
            "files_modified": getattr(attempt.git_evidence, "files_modified", []),
            "files_added": getattr(attempt.git_evidence, "files_added", []),
            "files_deleted": getattr(attempt.git_evidence, "files_deleted", []),
            "diff_stat": getattr(attempt.git_evidence, "diff_stat", ""),
            "has_changes": getattr(attempt.git_evidence, "has_changes", False),
        },
        "claude_output_truncated": attempt.claude_output[:2000],
    }
    (attempt_dir / "attempt_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)
    )


def _write_audit_file(path: Path, result: RoundResult) -> None:
    from datetime import timezone
    status = "PASSED" if result.final_passed else "ESCALATED"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = (
        f"# Audit — Round {result.round_id}\n\n"
        f"**Status:** {status}  \n"
        f"**Completed:** {ts}  \n"
        f"**Total cost:** ${result.total_cost_usd:.4f}  \n"
        f"**Attempts:** {len(result.attempts)}\n\n"
        f"## Task\n**{result.task.task_key}** — {result.task.title}\n"
        f"{result.task.objective}\n\n"
    )
    if result.escalated:
        content += f"## Escalation Reason\n```\n{result.escalation_reason}\n```\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_escalation_reason(result: RoundResult) -> str:
    lines = [f"Round {result.round_id} failed after {len(result.attempts)} attempt(s)."]
    for a in result.attempts:
        exhausted = " [TOKEN EXHAUSTED]" if a.is_token_exhausted else ""
        lines.append(f"\nAttempt {a.attempt_number}{exhausted}:")
        lines.append(f"  Task: {a.task.title}")
        lines.append(f"  Verdict: {a.review_verdict.verdict.value} (confidence: {a.review_verdict.confidence})")
        lines.append(f"  Rationale: {a.review_verdict.rationale}")
        for fix in a.review_verdict.blocker_fixes:
            lines.append(f"  Fix required: {fix}")
    return "\n".join(lines)


def _build_recent_rounds_summary(project_id: str, limit: int = 3) -> str:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, status, task_description, cost_usd FROM rounds "
            "WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit),
        ).fetchall()

    if not rows:
        return ""

    lines = ["Most recent rounds (do not redo completed work):"]
    for row in rows:
        status = row["status"].upper()
        desc = (row["task_description"] or "")[:80]
        lines.append(f"- **{row['id']}** [{status}] — {desc}")
    return "\n".join(lines)


def _handle_phase_complete(project_id: str, phase_id: str, project_name: str, config: OrchestratorConfig) -> None:
    click.echo(f"\n{'='*60}")
    click.echo(f"  Phase complete: {phase_id}")
    click.echo(f"{'='*60}")
    _close_phase(project_id, phase_id)
    _notify_phase_complete(project_name, phase_id, config)
    click.echo("  Next phase must be planned manually before re-running.")
    click.echo("  Edit current_phase.md in the SOT directory to define the next phase.")


# ── DB helpers ───────────────────────────────────────────────────────────────

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


def _ensure_active_phase(project_id: str, sot_dir: Path) -> str:
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
                last_attempt.claude_output[:500] if last_attempt else "",
                last_attempt.review_verdict.verdict.value if last_attempt else "FAIL",
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


def _commit_both(codebase_path: Path, message: str, round_id: str) -> tuple[str, str]:
    """Commit orchestrator SOT (projects/ dir) and target project."""
    from orch.utils.git_ops import commit_projects_dir

    try:
        orch_hash = commit_projects_dir(REPO_ROOT, f"{message} (SOT)")
    except (GitError, Exception) as e:
        click.echo(f"  ⚠ Orchestrator SOT commit failed: {e}", err=True)
        orch_hash = ""

    try:
        target_hash = commit_all(codebase_path, message)
    except (GitError, Exception) as e:
        click.echo(f"  ⚠ Target project commit failed: {e}", err=True)
        target_hash = ""

    if orch_hash and target_hash:
        click.echo(f"  ✓ Committed — orch:{orch_hash[:7]}  target:{target_hash[:7]}")
    elif target_hash:
        click.echo(f"  ✓ Committed target — {target_hash[:7]}")

    return orch_hash, target_hash


# ── Notifications ────────────────────────────────────────────────────────────

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
                f"Round {event.round_id} failed after 2 attempts.\n\n"
                f"Project: {event.project_name}\n"
                f"Time: {event.timestamp}\n\n"
                f"Reason:\n{event.reason}\n\n"
                f"Audit report: {event.audit_path}\n\n"
                f"Run 'orch review' and 'orch decide' to continue."
            ),
        )
    except Exception as e:
        click.echo(f"  ⚠ Email notification failed: {e}", err=True)


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
            body=f"Phase {phase_id} of project '{project_name}' has been completed.",
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


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")
