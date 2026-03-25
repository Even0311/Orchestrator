"""Tests for FileReader extraction logic (no filesystem access needed)."""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.services.file_reader import FileReader, _clean_markdown_inline


# ---------------------------------------------------------------------------
# Helper: build a FileReader without touching the filesystem
# ---------------------------------------------------------------------------

def make_reader() -> FileReader:
    with patch.object(Path, "exists", return_value=True):
        return FileReader("/fake/project")


SAMPLE_CHARTER = """\
# 项目章程

## 项目概述

MyProject 是一个用于测试的示范项目。

它不是聊天工具，也不是 dashboard。核心体验是自动化状态管理。

从长期架构看，系统会走向 **LLM 负责 appraisal、engine 负责 settlement** 的形态。

---

## 目标

1. 构建稳定骨干。
2. 保持可审计性。

---

## Core Principles

- **原则一**：保持确定性。
- **原则二**：可解释性优先。
- **原则三**：小切片演进。
-

---

## Out of Scope

- 不做 dashboard。
- 不让 LLM 直接写 ledger。
"""

CHARTER_WITH_BOLD_INLINE = """\
## Core Principles

- **玩家是照料者，不是控制者**：玩家提供有限引导，而不是实时遥控 Agent。
- **确定性优先**：相同输入必须产生相同输出。
- **LLM 只负责 appraisal，不直接做 settlement**：ledger 仍由 engine 负责。
-
-
"""


# ---------------------------------------------------------------------------
# _clean_markdown_inline
# ---------------------------------------------------------------------------

class TestCleanMarkdownInline:
    def test_strips_bold(self):
        assert _clean_markdown_inline("**bold text**") == "bold text"

    def test_strips_italic(self):
        assert _clean_markdown_inline("*italic*") == "italic"

    def test_strips_inline_code(self):
        assert _clean_markdown_inline("`some_code`") == "some_code"

    def test_strips_mixed(self):
        result = _clean_markdown_inline("MyProject（仓库名：`cyber-v2`）是一个 **AI 项目**。")
        assert "**" not in result
        assert "`" not in result
        assert "MyProject" in result
        assert "AI 项目" in result

    def test_plain_text_unchanged(self):
        text = "plain text without markers"
        assert _clean_markdown_inline(text) == text


# ---------------------------------------------------------------------------
# extract_core_principles
# ---------------------------------------------------------------------------

class TestExtractCorePrinciples:
    def setup_method(self):
        self.reader = make_reader()

    def test_no_markdown_markers_in_output(self):
        principles = self.reader.extract_core_principles(CHARTER_WITH_BOLD_INLINE)
        for p in principles:
            assert "**" not in p, f"Principle still contains **: {p!r}"

    def test_no_empty_entries(self):
        principles = self.reader.extract_core_principles(CHARTER_WITH_BOLD_INLINE)
        assert all(p.strip() for p in principles), "Empty principle found"
        assert "" not in principles

    def test_correct_count(self):
        # 3 real principles, 2 empty bullet lines → should yield 3
        principles = self.reader.extract_core_principles(CHARTER_WITH_BOLD_INLINE)
        assert len(principles) == 3

    def test_content_preserved(self):
        principles = self.reader.extract_core_principles(CHARTER_WITH_BOLD_INLINE)
        assert any("照料者" in p for p in principles)
        assert any("确定性优先" in p for p in principles)
        assert any("appraisal" in p for p in principles)

    def test_standard_charter(self):
        principles = self.reader.extract_core_principles(SAMPLE_CHARTER)
        assert len(principles) == 3
        assert "**" not in " ".join(principles)
        assert "" not in principles

    def test_no_principles_section(self):
        charter = "## Overview\n\nSome text.\n"
        assert self.reader.extract_core_principles(charter) == []


# ---------------------------------------------------------------------------
# build_charter_summary
# ---------------------------------------------------------------------------

class TestBuildCharterSummary:
    def setup_method(self):
        self.reader = make_reader()

    def test_extracts_overview_section(self):
        summary = self.reader.build_charter_summary(SAMPLE_CHARTER)
        assert "MyProject" in summary
        assert "自动化状态管理" in summary

    def test_no_markdown_bold_in_output(self):
        summary = self.reader.build_charter_summary(SAMPLE_CHARTER)
        assert "**" not in summary

    def test_no_markdown_inline_code_in_output(self):
        charter = "## 项目概述\n\n名称是 `cyber-v2`，用于测试。\n"
        reader = make_reader()
        summary = reader.build_charter_summary(charter)
        assert "`" not in summary
        assert "cyber-v2" in summary

    def test_preserves_architecture_direction(self):
        # Long-term architecture note in overview must not be dropped
        summary = self.reader.build_charter_summary(SAMPLE_CHARTER)
        assert "appraisal" in summary or "LLM" in summary

    def test_no_heading_markers_in_output(self):
        summary = self.reader.build_charter_summary(SAMPLE_CHARTER)
        assert not any(line.startswith("#") for line in summary.splitlines())

    def test_not_truncated_mid_sentence(self):
        summary = self.reader.build_charter_summary(SAMPLE_CHARTER)
        # Must end at a sentence boundary, not with "..."
        assert not summary.endswith("...")

    def test_fallback_to_first_paragraph(self):
        charter = "# Title\n\nFirst paragraph text here.\n\n## Section\n\nOther content.\n"
        summary = make_reader().build_charter_summary(charter)
        assert "First paragraph text here" in summary

    def test_empty_charter_returns_empty_string(self):
        assert make_reader().build_charter_summary("") == ""
