from pydantic import BaseModel


class InputFiles(BaseModel):
    task_file: str
    submission_envelope: str
    artifact_template: str


class ClaudeInvocation(BaseModel):
    project_name: str
    round_id: str
    adapter_mode: str  # "manual_stub" for this phase
    generated_at: str
    input_files: InputFiles
    expected_output_file: str   # round-relative filename
    invocation_preview: str
