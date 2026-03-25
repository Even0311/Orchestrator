"""Phase 7 — Approved Update Application Service."""
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.models import StateUpdateProposal
from src.services.file_reader import FileReader


class ApplyError(Exception):
    pass


@dataclass
class ApplyResult:
    project_name: str
    proposal_path: Path
    sections_applied: list[str] = field(default_factory=list)
    working_state_modified: bool = False
    decision_log_modified: bool = False
    backup_paths: list[Path] = field(default_factory=list)

    @property
    def no_op(self) -> bool:
        return not self.working_state_modified and not self.decision_log_modified


# ---------------------------------------------------------------------------
# Loaders and validators
# ---------------------------------------------------------------------------

def _load_proposal(proposal_path: Path, expected_project_name: str) -> StateUpdateProposal:
    if not proposal_path.exists():
        raise ApplyError(f"Proposal file not found: {proposal_path}")
    try:
        data = json.loads(proposal_path.read_text(encoding="utf-8"))
        proposal = StateUpdateProposal(**data)
    except ApplyError:
        raise
    except Exception as e:
        raise ApplyError(f"Invalid proposal file: {e}")
    if proposal.project_name != expected_project_name:
        raise ApplyError(
            f"Project mismatch: proposal is for '{proposal.project_name}', "
            f"but target project is '{expected_project_name}'."
        )
    return proposal


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def _backup_file(src: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    dest = backup_dir / f"{src.stem}_{ts}{src.suffix}"
    shutil.copy2(src, dest)
    return dest


# ---------------------------------------------------------------------------
# Risk / decision helpers
# ---------------------------------------------------------------------------

def _extract_risk_description(candidate: str) -> str:
    prefix = "[NEW RISK CANDIDATE] "
    return candidate[len(prefix):] if candidate.startswith(prefix) else candidate


def _derive_decision_title(candidate: str) -> str:
    prefix = "Consider documenting: "
    if candidate.startswith(prefix):
        rest = candidate[len(prefix):]
        parts = rest.split(" — ")
        title = parts[0].strip()
    else:
        title = candidate
    if len(title) > 70:
        title = title[:70].rsplit(" ", 1)[0] or title[:70]
    return title


# ---------------------------------------------------------------------------
# Application logic
# ---------------------------------------------------------------------------

def _apply_working_state(
    state_dir: Path,
    proposal: StateUpdateProposal,
    backup_dir: Path,
) -> tuple[bool, list[str], list[Path]]:
    """Apply working_state-relevant proposal sections.

    Returns (modified, sections_applied, backup_paths).
    """
    has_changes = bool(
        proposal.proposed_recent_progress_additions
        or proposal.proposed_current_goal_update
        or proposal.proposed_next_expected_step_update
        or proposal.proposed_risk_updates
    )
    if not has_changes:
        return False, [], []

    state_file = state_dir / "working_state.yaml"
    data = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    backup = _backup_file(state_file, backup_dir)
    sections: list[str] = []

    if proposal.proposed_recent_progress_additions:
        additions = [
            {"item": item, "completed": True}
            for item in proposal.proposed_recent_progress_additions
        ]
        data.setdefault("recent_progress", [])
        data["recent_progress"].extend(additions)
        sections.append(
            f"recent_progress: appended {len(additions)} item(s)"
        )

    if proposal.proposed_current_goal_update:
        data["current_goal"] = proposal.proposed_current_goal_update
        sections.append("current_goal: updated")

    if proposal.proposed_next_expected_step_update:
        data["next_expected_step"] = proposal.proposed_next_expected_step_update
        sections.append("next_expected_step: updated")

    if proposal.proposed_risk_updates:
        new_risks = [
            {"description": _extract_risk_description(r), "severity": "medium"}
            for r in proposal.proposed_risk_updates
        ]
        data.setdefault("current_risks", [])
        data["current_risks"].extend(new_risks)
        sections.append(
            f"current_risks: appended {len(new_risks)} candidate(s)"
        )

    state_file.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return True, sections, [backup]


def _apply_decision_log(
    state_dir: Path,
    proposal: StateUpdateProposal,
    backup_dir: Path,
) -> tuple[bool, list[str], list[Path]]:
    """Apply decision_log-relevant proposal sections.

    Returns (modified, sections_applied, backup_paths).
    """
    if not proposal.proposed_decision_log_candidates:
        return False, [], []

    log_file = state_dir / "decision_log.yaml"
    if log_file.exists():
        raw = yaml.safe_load(log_file.read_text(encoding="utf-8")) or {}
        backup_list: list[Path] = [_backup_file(log_file, backup_dir)]
    else:
        raw = {}
        backup_list = []

    existing = raw.get("decisions", []) or []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    new_entries = [
        {
            "date": today,
            "title": _derive_decision_title(candidate),
            "decision": candidate,
            "rationale": "Applied from approved state update proposal.",
        }
        for candidate in proposal.proposed_decision_log_candidates
    ]
    existing.extend(new_entries)
    raw["decisions"] = existing

    log_file.write_text(
        yaml.dump(raw, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    sections = [f"decision_log: appended {len(new_entries)} entry(s)"]
    return True, sections, backup_list


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_approved_update(state_dir: Path, proposal_path: Path) -> ApplyResult:
    """Apply an already-approved state update proposal to source-of-truth files.

    Supported targets: working_state.yaml, decision_log.yaml.
    project_charter.md is explicitly unsupported and never modified.

    Does NOT infer approval. Must only be called via explicit CLI invocation
    after the human user has reviewed and approved the proposal.
    """
    reader = FileReader(state_dir)
    state = reader.read_working_state()

    proposal = _load_proposal(proposal_path, state.project_name)

    backup_dir = state_dir / "backups"
    result = ApplyResult(project_name=state.project_name, proposal_path=proposal_path)

    ws_modified, ws_sections, ws_backups = _apply_working_state(
        state_dir, proposal, backup_dir
    )
    dl_modified, dl_sections, dl_backups = _apply_decision_log(
        state_dir, proposal, backup_dir
    )

    result.working_state_modified = ws_modified
    result.decision_log_modified = dl_modified
    result.sections_applied = ws_sections + dl_sections
    result.backup_paths = ws_backups + dl_backups

    return result
