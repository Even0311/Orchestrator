"""Builds structured context documents for agents from project state files."""
from pathlib import Path


def load_project_context(state_dir: Path) -> dict[str, str]:
    """Load all context documents for a project. Returns a dict of filename → content."""
    docs = {}
    for name in ("vision.md", "decisions.md", "current_phase.md"):
        path = state_dir / name
        if path.exists():
            docs[name] = path.read_text()
    return docs


def build_designer_system_prompt(context: dict[str, str]) -> str:
    sections = [
        "You are the Designer agent in an AI-assisted software development orchestrator.",
        "Your responsibilities:",
        "- Understand the project vision and maintain alignment with it at all times",
        "- Break work into clear, atomic tasks for the Executor agent",
        "- Review outputs and update project documents after each round",
        "- Flag direction-changing decisions for human review instead of deciding unilaterally",
        "",
        "You always reason from the project documents below. Never drift from them.",
        "When you update documents, be precise and conservative — only record what is confirmed.",
        "",
        "=== PROJECT DOCUMENTS ===",
    ]
    for name, content in context.items():
        sections.append(f"\n--- {name} ---\n{content}")
    return "\n".join(sections)


def build_reviewer_system_prompt(context: dict[str, str]) -> str:
    sections = [
        "You are the Reviewer agent in an AI-assisted software development orchestrator.",
        "Your responsibilities:",
        "- Evaluate whether the Executor's output fulfils the task definition",
        "- Check for correctness, completeness, and alignment with the project vision",
        "- Return a structured verdict: PASS or FAIL with clear reasoning",
        "- Be strict but fair — partial completion is a FAIL unless the task explicitly allowed it",
        "",
        "Output format (always use this exact structure):",
        "VERDICT: PASS | FAIL",
        "REASON: <one paragraph>",
        "ISSUES: <bullet list, or 'None'>",
        "",
        "=== PROJECT DOCUMENTS ===",
    ]
    for name, content in context.items():
        sections.append(f"\n--- {name} ---\n{content}")
    return "\n".join(sections)


def build_document_update_system_prompt(context: dict[str, str]) -> str:
    sections = [
        "You are the Designer agent performing a post-round document update.",
        "Based on the round result provided, update the project documents as needed.",
        "",
        "Rules:",
        "- Only update decisions.md if a genuinely new decision was made this round",
        "- Update current_phase.md to reflect actual progress and remaining work",
        "- Be concise and factual — no speculation",
        "- Return the updated documents in this exact JSON format:",
        '  {"decisions.md": "<full updated content>", "current_phase.md": "<full updated content>"}',
        "- If no update is needed for a document, include it unchanged",
        "",
        "=== CURRENT PROJECT DOCUMENTS ===",
    ]
    for name, content in context.items():
        sections.append(f"\n--- {name} ---\n{content}")
    return "\n".join(sections)
