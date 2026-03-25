from typing import List, Optional
from pydantic import BaseModel

from .working_state import Risk


class Deliverables(BaseModel):
    description: str
    ingest_command: str


class RoundFiles(BaseModel):
    task_file: str = "task_for_claude.md"
    task_packet: str = "task_packet_claude.json"
    expected_return: str = "run_artifact_template.json"


class ClaudeSubmissionEnvelope(BaseModel):
    project_name: str
    round_id: str
    role: str = "claude"
    generated_at: str
    current_phase: str
    current_goal: str
    next_expected_step: Optional[str] = None
    implementation_boundaries: Optional[List[str]] = None
    current_risks: Optional[List[Risk]] = None
    deliverables: Deliverables
    round_files: RoundFiles
