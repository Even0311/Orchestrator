"""Designer agent — plans tasks and maintains project documents."""
from dataclasses import dataclass
from pathlib import Path

from orch.agents.context import (
    build_designer_system_prompt,
    build_document_update_system_prompt,
    load_project_context,
)
from orch.providers.base import LLMProvider


@dataclass
class TaskDefinition:
    description: str
    acceptance_criteria: str
    context_notes: str = ""
    cost_usd: float = 0.0


@dataclass
class DocumentUpdateResult:
    decisions_md: str
    current_phase_md: str
    cost_usd: float = 0.0


class DesignerAgent:
    def __init__(self, provider: LLMProvider, state_dir: Path):
        self._provider = provider
        self._state_dir = state_dir

    def plan_next_task(self, instruction: str) -> TaskDefinition:
        """Given a high-level instruction, produce a concrete task definition for the Executor."""
        context = load_project_context(self._state_dir)
        system_prompt = build_designer_system_prompt(context)

        messages = [
            {
                "role": "user",
                "content": (
                    f"{instruction}\n\n"
                    "Produce a task definition for the Executor in this exact format:\n"
                    "TASK:\n<clear description of what to implement>\n\n"
                    "ACCEPTANCE CRITERIA:\n<bulleted list of what done looks like>\n\n"
                    "CONTEXT NOTES:\n<any relevant background the Executor needs>"
                ),
            }
        ]

        response = self._provider.complete(system_prompt, messages)
        task_def = _parse_task_definition(response.content)
        task_def.cost_usd = response.cost_usd
        return task_def

    def update_documents(self, round_summary: str) -> DocumentUpdateResult:
        """After a round completes, update decisions.md and current_phase.md."""
        context = load_project_context(self._state_dir)
        system_prompt = build_document_update_system_prompt(context)

        messages = [
            {
                "role": "user",
                "content": (
                    f"Round result summary:\n{round_summary}\n\n"
                    "Update the project documents as needed and return them in JSON format."
                ),
            }
        ]

        response = self._provider.complete(system_prompt, messages)
        result = _parse_document_update(response.content, context)
        result.cost_usd = response.cost_usd
        return result


def _parse_task_definition(content: str) -> TaskDefinition:
    """Parse the Designer's task definition output."""
    description = ""
    acceptance_criteria = ""
    context_notes = ""

    current_section = None
    lines_map: dict[str, list[str]] = {
        "task": [],
        "acceptance": [],
        "context": [],
    }

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("TASK:"):
            current_section = "task"
            remainder = stripped[5:].strip()
            if remainder:
                lines_map["task"].append(remainder)
        elif stripped.upper().startswith("ACCEPTANCE CRITERIA:"):
            current_section = "acceptance"
            remainder = stripped[20:].strip()
            if remainder:
                lines_map["acceptance"].append(remainder)
        elif stripped.upper().startswith("CONTEXT NOTES:"):
            current_section = "context"
            remainder = stripped[14:].strip()
            if remainder:
                lines_map["context"].append(remainder)
        elif current_section:
            lines_map[current_section].append(line)

    description = "\n".join(lines_map["task"]).strip() or content.strip()
    acceptance_criteria = "\n".join(lines_map["acceptance"]).strip()
    context_notes = "\n".join(lines_map["context"]).strip()

    return TaskDefinition(
        description=description,
        acceptance_criteria=acceptance_criteria,
        context_notes=context_notes,
    )


def _parse_document_update(content: str, fallback_context: dict[str, str]) -> DocumentUpdateResult:
    """Parse the Designer's JSON document update output."""
    import json
    import re

    # Extract JSON from the response (may be wrapped in markdown code block)
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return DocumentUpdateResult(
                decisions_md=data.get("decisions.md", fallback_context.get("decisions.md", "")),
                current_phase_md=data.get("current_phase.md", fallback_context.get("current_phase.md", "")),
            )
        except json.JSONDecodeError:
            pass

    # Fallback: return unchanged documents
    return DocumentUpdateResult(
        decisions_md=fallback_context.get("decisions.md", ""),
        current_phase_md=fallback_context.get("current_phase.md", ""),
    )
