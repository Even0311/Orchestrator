"""Builds structured context documents for agents from project state files."""
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    """Load a prompt file from orch/prompts/. Raises FileNotFoundError if missing."""
    path = _PROMPTS_DIR / name
    return path.read_text()


def load_designer_context(state_dir: Path) -> dict[str, str]:
    """Load context for Designer: vision + current_phase + designer working memory.

    decisions.md is intentionally EXCLUDED — it is human-only audit history and
    must never be fed to any AI agent.
    """
    docs = {}
    files = [
        ("vision.md", state_dir / "vision.md"),
        ("current_phase.md", state_dir / "current_phase.md"),
        ("context/designer.md", state_dir / "context" / "designer.md"),
    ]
    for name, path in files:
        if path.exists():
            docs[name] = path.read_text()
    return docs


def load_reviewer_context(state_dir: Path) -> dict[str, str]:
    """Load context for Reviewer: vision + current_phase only.

    Reviewer evaluates objectively against the task and vision.
    No designer working memory, no decisions history.
    """
    docs = {}
    for name in ("vision.md", "current_phase.md"):
        path = state_dir / name
        if path.exists():
            docs[name] = path.read_text()
    return docs


# Backward compat alias
load_project_context = load_designer_context


def build_designer_system_prompt(context: dict[str, str]) -> str:
    """System prompt for plan_next_task — loaded from designer_plan.md."""
    base = _load_prompt("designer_plan.md")
    return _append_docs(base, context)


def build_designer_repair_system_prompt(context: dict[str, str]) -> str:
    """System prompt for repair_task — loaded from designer_repair.md."""
    base = _load_prompt("designer_repair.md")
    return _append_docs(base, context)


def build_reviewer_system_prompt(context: dict[str, str]) -> str:
    """System prompt for review — loaded from reviewer.md."""
    base = _load_prompt("reviewer.md")
    return _append_docs(base, context)


def build_document_update_system_prompt(context: dict[str, str]) -> str:
    """System prompt for update_documents — loaded from designer_update.md."""
    base = _load_prompt("designer_update.md")
    return _append_docs(base, context)


def build_bootstrap_system_prompt(vision_content: str) -> str:
    """System prompt for generating initial phase plan from vision."""
    return "\n".join([
        "You are the Designer agent bootstrapping a new software project.",
        "Read the project vision and produce the initial phase planning documents.",
        "",
        "Output EXACTLY this JSON (no prose, no markdown fences):",
        '{',
        '  "current_phase_md": "...",',
        '  "designer_context_md": "..."',
        '}',
        "",
        "=== current_phase_md REQUIRED STRUCTURE ===",
        "Use this exact section layout:",
        "",
        "# Phase 1: <phase name>",
        "",
        "## Phase Goal",
        "<one sentence>",
        "",
        "## In Scope",
        "- item",
        "",
        "## Task Queue",
        "- [ ] T001: <title>",
        "- [ ] T002: <title>",
        "(list all planned tasks in execution order)",
        "",
        "## Completed Tasks",
        "(none yet)",
        "",
        "## Current Status",
        "bootstrapped — ready to start T001",
        "",
        "## Risks / Blockers",
        "- item",
        "",
        "## Next Recommended Task",
        "T001",
        "",
        "=== designer_context_md REQUIRED STRUCTURE ===",
        "Use this exact section layout (keep under 200 words total):",
        "",
        "# Designer Context",
        "",
        "## Active Constraints",
        "- item",
        "",
        "## Working Assumptions",
        "- item",
        "",
        "## Architecture Snapshot",
        "<brief description>",
        "",
        "## Known Risks",
        "- item",
        "",
        "## Open Questions For Human",
        "- item",
        "",
        "=== PROJECT VISION ===",
        vision_content,
    ])


def _append_docs(base_prompt: str, docs: dict[str, str]) -> str:
    """Append project documents to a base prompt."""
    if not docs:
        return base_prompt
    parts = [base_prompt]
    for name, content in docs.items():
        parts.append(f"\n--- {name} ---\n{content}")
    return "\n".join(parts)
