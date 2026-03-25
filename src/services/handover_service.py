import json
from datetime import datetime, timezone
from pathlib import Path

from src.models import HandoverPacket
from .file_reader import FileReader


RECENT_DECISIONS_LIMIT = 5


def generate_handover(state_dir: Path) -> HandoverPacket:
    reader = FileReader(state_dir)

    charter = reader.read_charter()
    state = reader.read_working_state()
    log = reader.read_decision_log()

    recent_decisions = log.decisions[-RECENT_DECISIONS_LIMIT:]

    packet = HandoverPacket(
        generated_at=datetime.now(timezone.utc).isoformat(),
        project_name=state.project_name,
        charter_excerpt=reader.build_charter_summary(charter),
        core_principles=reader.extract_core_principles(charter),
        current_phase=state.current_phase,
        current_goal=state.current_goal.strip(),
        recent_progress=state.recent_progress,
        current_risks=state.current_risks,
        next_expected_step=state.next_expected_step.strip(),
        recent_decisions=recent_decisions,
        context_notes=state.context_notes.strip() if state.context_notes else None,
    )
    return packet


def save_handover(packet: HandoverPacket, state_dir: Path) -> Path:
    output_path = state_dir / "handover_packet.json"
    output_path.write_text(
        json.dumps(packet.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
