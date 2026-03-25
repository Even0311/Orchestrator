import re
from pathlib import Path
from typing import Optional

import yaml

from src.models import WorkingState, DecisionLog


# Matches **bold**, *italic*, ***both*** — captures inner text
_MD_EMPHASIS = re.compile(r'\*{1,3}([^*\n]+?)\*{1,3}')
# Matches `inline code`
_MD_INLINE_CODE = re.compile(r'`([^`\n]+)`')


def _clean_markdown_inline(text: str) -> str:
    """Strip inline markdown markers (bold, italic, inline code) from a line."""
    text = _MD_EMPHASIS.sub(r'\1', text)
    text = _MD_INLINE_CODE.sub(r'\1', text)
    return text


class FileReader:
    def __init__(self, project_dir):
        self.project_path = Path(project_dir)
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

    def read_charter(self) -> str:
        charter_file = self.project_path / "project_charter.md"
        if not charter_file.exists():
            raise FileNotFoundError(f"project_charter.md not found in {self.project_path}")
        return charter_file.read_text(encoding="utf-8")

    def read_working_state(self) -> WorkingState:
        state_file = self.project_path / "working_state.yaml"
        if not state_file.exists():
            raise FileNotFoundError(f"working_state.yaml not found in {self.project_path}")
        data = yaml.safe_load(state_file.read_text(encoding="utf-8"))
        return WorkingState(**data)

    def read_decision_log(self) -> DecisionLog:
        log_file = self.project_path / "decision_log.yaml"
        if not log_file.exists():
            return DecisionLog()
        data = yaml.safe_load(log_file.read_text(encoding="utf-8"))
        if not data:
            return DecisionLog()
        return DecisionLog(**data)

    def _extract_section(self, charter: str, *heading_patterns: str) -> Optional[str]:
        """Extract text content under the first heading that matches any of the patterns."""
        lines = charter.splitlines()
        in_section = False
        section_lines = []
        for line in lines:
            stripped = line.strip()
            if not in_section:
                for pat in heading_patterns:
                    if re.match(rf"^#+\s+.*{pat}.*", stripped, re.IGNORECASE):
                        in_section = True
                        break
            else:
                if re.match(r"^#+\s+", stripped):
                    break
                section_lines.append(line)
        if not section_lines:
            return None
        # Drop trailing blank lines, then horizontal rules (--- or ***), then blanks again
        for _ in range(2):
            while section_lines and not section_lines[-1].strip():
                section_lines.pop()
            while section_lines and re.match(r"^[-*]{3,}\s*$", section_lines[-1].strip()):
                section_lines.pop()
        text = "\n".join(section_lines).strip()
        return text or None

    def build_charter_summary(self, charter: str) -> str:
        """Build a clean, closed-form summary from the charter's overview section.

        Prefers a named overview section (项目概述, overview, etc.).
        Falls back to the first non-heading paragraph.
        Strips inline markdown markers. No mid-sentence truncation.
        """
        text = (
            self._extract_section(charter, "项目概述", "概述")
            or self._extract_section(charter, "overview", "project overview", "about")
        )
        if not text:
            # Fallback: first non-empty, non-heading paragraph
            for block in charter.split("\n\n"):
                block = block.strip()
                if block and not block.startswith("#"):
                    text = block
                    break
        if not text:
            return ""
        cleaned = "\n".join(_clean_markdown_inline(line) for line in text.splitlines())
        return cleaned.strip()

    def extract_out_of_scope(self, charter: str) -> list[str]:
        """Extract bullet items from an Out of Scope section."""
        items = []
        in_section = False
        for line in charter.splitlines():
            stripped = line.strip()
            if re.match(
                r"^#+\s+.*(out[\s\-_]*of[\s\-_]*scope|不在范围|非目标)",
                stripped,
                re.IGNORECASE,
            ):
                in_section = True
                continue
            if in_section:
                if re.match(r"^#+\s+", stripped):
                    break
                if stripped.startswith(("-", "*", "•")):
                    raw = stripped.lstrip("-*• ").strip()
                    clean = re.sub(r"\*+", "", raw).strip()
                    if clean:
                        items.append(clean)
        return items

    def extract_core_principles(self, charter: str) -> list[str]:
        """Extract lines under a 'Core Principles' or 'Principles' heading.

        Returns a clean list of plain strings with no markdown markers or empty entries.
        """
        principles = []
        in_section = False
        for line in charter.splitlines():
            stripped = line.strip()
            if re.match(r"^#+\s*(core\s+principles|principles)", stripped, re.IGNORECASE):
                in_section = True
                continue
            if in_section:
                if re.match(r"^#+\s+", stripped):
                    break
                if stripped.startswith(("-", "*", "•")):
                    raw = stripped.lstrip("-*• ").strip()
                    clean = re.sub(r"\*+", "", raw).strip()
                    if clean:
                        principles.append(clean)
        return principles
