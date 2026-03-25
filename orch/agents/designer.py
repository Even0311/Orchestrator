"""Designer agent — plans tasks, repairs failed tasks, and maintains project documents."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from orch.agents.context import (
    build_designer_system_prompt,
    build_designer_repair_system_prompt,
    build_document_update_system_prompt,
    build_bootstrap_system_prompt,
    load_designer_context,
)
from orch.providers.base import LLMProvider


@dataclass
class TaskDefinition:
    """Structured task package sent to Executor."""
    task_id: str
    title: str
    objective: str
    exact_scope: str
    acceptance_criteria: list[str]
    verification_steps: list[str]
    non_goals: list[str]
    likely_files: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    cost_usd: float = 0.0

    # Backward compat properties used in orchestrator.py
    @property
    def description(self) -> str:
        return self.objective

    @property
    def context_notes(self) -> str:
        return ""

    def to_json(self) -> str:
        return json.dumps({
            "task_id": self.task_id,
            "title": self.title,
            "objective": self.objective,
            "exact_scope": self.exact_scope,
            "likely_files": self.likely_files,
            "constraints": self.constraints,
            "acceptance_criteria": self.acceptance_criteria,
            "verification_steps": self.verification_steps,
            "non_goals": self.non_goals,
        }, indent=2)


@dataclass
class DocumentUpdateResult:
    """Result of post-round document update."""
    decisions_entry: str       # append to decisions.md (empty string = no new decision)
    current_phase_md: str      # rewrite current_phase.md
    designer_context_md: str   # rewrite context/designer.md
    cost_usd: float = 0.0


@dataclass
class BootstrapResult:
    """Initial phase documents generated from vision.md."""
    current_phase_md: str
    designer_context_md: str
    cost_usd: float = 0.0


# ── Prompt constants ──────────────────────────────────────────────────────────

_TASK_JSON_SPEC = """\
Output EXACTLY this JSON (no prose, no markdown fences):
{
  "task_id": "<provided round_id>",
  "title": "<short descriptive title>",
  "objective": "<what must be implemented — concrete and specific>",
  "exact_scope": "<precise boundaries: what is in and out of this task>",
  "likely_files": ["path/to/file.py"],
  "constraints": ["must not break existing tests"],
  "acceptance_criteria": [
    "criterion 1 — observable and verifiable",
    "criterion 2"
  ],
  "verification_steps": [
    "pytest tests/",
    "python -c 'import module; assert something'"
  ],
  "non_goals": ["do not refactor unrelated code"]
}"""


# ── Agent ─────────────────────────────────────────────────────────────────────

class DesignerAgent:
    def __init__(self, provider: LLMProvider, state_dir: Path):
        self._provider = provider
        self._state_dir = state_dir

    def plan_next_task(self, instruction: str, round_id: str = "") -> TaskDefinition:
        """Given a high-level instruction, produce a concrete task package for the Executor."""
        context = load_designer_context(self._state_dir)
        system_prompt = build_designer_system_prompt(context)

        messages = [
            {
                "role": "user",
                "content": (
                    f"{instruction}\n\n"
                    f"Round ID: {round_id}\n\n"
                    + _TASK_JSON_SPEC
                ),
            }
        ]

        response = self._provider.complete(system_prompt, messages)
        task = _parse_task_json(response.content, round_id)
        task.cost_usd = response.cost_usd
        return task

    def repair_task(
        self,
        original_task: "TaskDefinition",
        review_result: "object",  # ReviewResult — avoid circular import
        evidence: "object",       # ExecutorEvidence
    ) -> TaskDefinition:
        """After a failed attempt, produce a repaired task targeting the specific failures."""
        context = load_designer_context(self._state_dir)
        system_prompt = build_designer_repair_system_prompt(context)

        unmet = getattr(review_result, "unmet_criteria", [])
        required_fixes = getattr(review_result, "required_fixes", [])
        rationale = getattr(review_result, "rationale", "")
        files_changed = getattr(evidence, "files_changed", [])
        commands_run = getattr(evidence, "commands_run", [])
        test_results = getattr(evidence, "test_results", "")
        unresolved = getattr(evidence, "unresolved_issues", [])

        messages = [
            {
                "role": "user",
                "content": (
                    "The first execution attempt failed review. Produce a REPAIRED task definition.\n\n"
                    f"## Original Task\n{original_task.to_json()}\n\n"
                    "## Review Verdict: FAIL\n"
                    f"Unmet criteria: {unmet}\n"
                    f"Required fixes: {required_fixes}\n"
                    f"Rationale: {rationale}\n\n"
                    "## Execution Evidence\n"
                    f"Files changed: {files_changed}\n"
                    f"Commands run: {commands_run}\n"
                    f"Test results: {test_results or 'none'}\n"
                    f"Unresolved issues: {unresolved}\n\n"
                    "Produce a repaired task that:\n"
                    "- Keeps the same core objective\n"
                    "- Explicitly addresses each required fix\n"
                    "- Has targeted verification_steps that would have caught the original failures\n\n"
                    + _TASK_JSON_SPEC
                ),
            }
        ]

        response = self._provider.complete(system_prompt, messages)
        task = _parse_task_json(response.content, original_task.task_id)
        task.cost_usd = response.cost_usd
        return task

    def update_documents(self, round_summary: str) -> DocumentUpdateResult:
        """After a successful round, update current_phase.md and context/designer.md."""
        context = load_designer_context(self._state_dir)
        system_prompt = build_document_update_system_prompt(context)

        messages = [
            {
                "role": "user",
                "content": (
                    f"Round completed successfully.\n\n{round_summary}\n\n"
                    "Update the project documents and return JSON."
                ),
            }
        ]

        response = self._provider.complete(system_prompt, messages)
        result = _parse_document_update(response.content, context)
        result.cost_usd = response.cost_usd
        return result

    def bootstrap_phase(self, vision_content: str) -> BootstrapResult:
        """Generate initial phase plan from vision.md (bootstrap mode)."""
        system_prompt = build_bootstrap_system_prompt(vision_content)

        messages = [
            {
                "role": "user",
                "content": (
                    "Bootstrap this project. Read the vision and produce the initial "
                    "current_phase_md and designer_context_md. Return JSON."
                ),
            }
        ]

        response = self._provider.complete(system_prompt, messages)
        result = _parse_bootstrap(response.content)
        result.cost_usd = response.cost_usd
        return result


# ── Parsers ───────────────────────────────────────────────────────────────────

def _extract_json(content: str) -> dict | None:
    """Extract the first JSON object from content, handling markdown code fences."""
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?\s*", "", content)
    cleaned = re.sub(r"```\s*", "", cleaned)

    # Try direct parse
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    # Try to find a JSON object
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def _parse_task_json(content: str, round_id: str) -> TaskDefinition:
    data = _extract_json(content)
    if data:
        return TaskDefinition(
            task_id=data.get("task_id", round_id),
            title=data.get("title", ""),
            objective=data.get("objective", data.get("description", content.strip()[:200])),
            exact_scope=data.get("exact_scope", ""),
            likely_files=data.get("likely_files", []),
            constraints=data.get("constraints", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
            verification_steps=data.get("verification_steps", []),
            non_goals=data.get("non_goals", []),
        )
    # Fallback: treat entire response as objective
    return TaskDefinition(
        task_id=round_id,
        title="",
        objective=content.strip(),
        exact_scope="",
        acceptance_criteria=[],
        verification_steps=[],
        non_goals=[],
    )


def _parse_document_update(content: str, fallback_context: dict[str, str]) -> DocumentUpdateResult:
    data = _extract_json(content)
    if data:
        return DocumentUpdateResult(
            decisions_entry=data.get("decisions_entry", ""),
            current_phase_md=data.get("current_phase_md", fallback_context.get("current_phase.md", "")),
            designer_context_md=data.get("designer_context_md", fallback_context.get("context/designer.md", "")),
        )
    return DocumentUpdateResult(
        decisions_entry="",
        current_phase_md=fallback_context.get("current_phase.md", ""),
        designer_context_md=fallback_context.get("context/designer.md", ""),
    )


def _parse_bootstrap(content: str) -> BootstrapResult:
    data = _extract_json(content)
    if data:
        return BootstrapResult(
            current_phase_md=data.get("current_phase_md", ""),
            designer_context_md=data.get("designer_context_md", ""),
        )
    return BootstrapResult(
        current_phase_md=content.strip(),
        designer_context_md="",
    )
