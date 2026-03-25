import json
from datetime import datetime, timezone
from pathlib import Path

from src.models import TaskPacket, SUPPORTED_ROLES
from .file_reader import FileReader


RECENT_DECISIONS_LIMIT = 5
DECISION_MAKER_DECISIONS_LIMIT = 3
TOP_RISKS_LIMIT = 3

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def generate_task_packet(state_dir: Path, role: str) -> TaskPacket:
    if role not in SUPPORTED_ROLES:
        raise ValueError(
            f"Unsupported role: {role!r}. Must be one of: {sorted(SUPPORTED_ROLES)}"
        )

    reader = FileReader(state_dir)
    charter = reader.read_charter()
    state = reader.read_working_state()
    log = reader.read_decision_log()

    now = datetime.now(timezone.utc).isoformat()

    if role == "claude":
        return _build_claude_packet(now, charter, state, log, reader)
    elif role == "reviewer":
        return _build_reviewer_packet(now, charter, state, log, reader)
    else:  # decision_maker
        return _build_decision_maker_packet(now, charter, state, log, reader)


def _build_claude_packet(now, charter, state, log, reader) -> TaskPacket:
    """Implementation-focused: phase, goal, next step, constraints, risks, decisions."""
    boundaries = reader.extract_out_of_scope(charter)
    return TaskPacket(
        generated_at=now,
        role="claude",
        project_name=state.project_name,
        current_phase=state.current_phase,
        current_goal=state.current_goal.strip(),
        next_expected_step=state.next_expected_step.strip(),
        context_notes=state.context_notes.strip() if state.context_notes else None,
        recent_progress=state.recent_progress or None,
        current_risks=state.current_risks or None,
        recent_decisions=log.decisions[-RECENT_DECISIONS_LIMIT:] or None,
        implementation_boundaries=boundaries or None,
    )


def _build_reviewer_packet(now, charter, state, log, reader) -> TaskPacket:
    """Audit/review-facing: summary, progress, risks, decisions, what to inspect."""
    return TaskPacket(
        generated_at=now,
        role="reviewer",
        project_name=state.project_name,
        current_phase=state.current_phase,
        current_goal=state.current_goal.strip(),
        project_summary=reader.build_charter_summary(charter),
        recent_progress=state.recent_progress or None,
        current_risks=state.current_risks or None,
        recent_decisions=log.decisions[-RECENT_DECISIONS_LIMIT:] or None,
        inspect_next=state.next_expected_step.strip() if state.next_expected_step else None,
    )


def _build_decision_maker_packet(now, charter, state, log, reader) -> TaskPacket:
    """Concise escalation packet: decision needed, why now, top risks, decision backdrop."""
    top_risks = sorted(
        state.current_risks,
        key=lambda r: _SEVERITY_ORDER.get(r.severity, 99),
    )[:TOP_RISKS_LIMIT]

    return TaskPacket(
        generated_at=now,
        role="decision_maker",
        project_name=state.project_name,
        current_phase=state.current_phase,
        current_goal=state.current_goal.strip(),
        decision_needed=state.next_expected_step.strip() if state.next_expected_step else None,
        why_now=state.context_notes.strip() if state.context_notes else None,
        current_risks=top_risks or None,
        recent_decisions=log.decisions[-DECISION_MAKER_DECISIONS_LIMIT:] or None,
    )


def save_task_packet(packet: TaskPacket, state_dir: Path) -> Path:
    output_path = state_dir / f"task_packet_{packet.role}.json"
    output_path.write_text(
        json.dumps(packet.model_dump(exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
