"""Core data structures for the orchestrator control plane."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum


# ── TaskContract ─────────────────────────────────────────────────────────────

@dataclass
class TaskContract:
    """Contract produced by the designer subagent, consumed by executor and reviewer."""
    phase_id: str                    # e.g. "P28"
    task_key: str                    # e.g. "P28-T6"
    title: str
    objective: str
    exact_scope: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)    # glob patterns Claude must NOT touch
    review_focus: list[str] = field(default_factory=list)       # evaluator重点关注事项

    # Backward compat with old TaskDefinition
    @property
    def task_id(self) -> str:
        return self.task_key

    @property
    def description(self) -> str:
        return self.objective

    def to_dict(self) -> dict:
        return {
            "phase_id": self.phase_id,
            "task_key": self.task_key,
            "title": self.title,
            "objective": self.objective,
            "exact_scope": self.exact_scope,
            "acceptance_criteria": self.acceptance_criteria,
            "non_goals": self.non_goals,
            "constraints": self.constraints,
            "forbidden_files": self.forbidden_files,
            "review_focus": self.review_focus,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> TaskContract:
        return cls(
            phase_id=data.get("phase_id", ""),
            task_key=data.get("task_key", data.get("task_id", "")),
            title=data.get("title", ""),
            objective=data.get("objective", ""),
            exact_scope=data.get("exact_scope", ""),
            acceptance_criteria=data.get("acceptance_criteria", []),
            non_goals=data.get("non_goals", []),
            constraints=data.get("constraints", []),
            forbidden_files=data.get("forbidden_files", []),
            review_focus=data.get("review_focus", []),
        )

    @classmethod
    def from_json_file(cls, path) -> TaskContract:
        data = json.loads(path.read_text())
        return cls.from_dict(data)


# ── ContractFeedback ─────────────────────────────────────────────────────────

@dataclass
class ContractFeedback:
    """Feedback from evaluator on proposed contract (contract negotiation phase).

    Evaluator reviews the acceptance_criteria and review_focus from the designer's
    proposed contract and reports which criteria it can/cannot objectively verify,
    along with suggested modifications.
    """
    can_evaluate: list[str] = field(default_factory=list)       # criteria evaluator can verify
    cannot_evaluate: list[str] = field(default_factory=list)    # criteria too vague to verify
    suggested_changes: list[str] = field(default_factory=list)  # proposed rewrites/additions
    needs_revision: bool = False                                 # True if contract needs designer revision

    def to_dict(self) -> dict:
        return {
            "can_evaluate": self.can_evaluate,
            "cannot_evaluate": self.cannot_evaluate,
            "suggested_changes": self.suggested_changes,
            "needs_revision": self.needs_revision,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> ContractFeedback:
        return cls(
            can_evaluate=data.get("can_evaluate", []),
            cannot_evaluate=data.get("cannot_evaluate", []),
            suggested_changes=data.get("suggested_changes", []),
            needs_revision=data.get("needs_revision", False),
        )

    @classmethod
    def from_json_file(cls, path) -> ContractFeedback:
        data = json.loads(path.read_text())
        return cls.from_dict(data)


# ── ReviewVerdict ────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVISION_REQUIRED = "REVISION_REQUIRED"


@dataclass
class ReviewVerdict:
    """Verdict produced by the reviewer subagent."""
    verdict: Verdict
    confidence: str = "medium"       # "high" | "medium" | "low"
    met_criteria: list[str] = field(default_factory=list)
    unmet_criteria: list[str] = field(default_factory=list)
    scope_violations: list[str] = field(default_factory=list)
    blocker_fixes: list[str] = field(default_factory=list)
    non_blocking_suggestions: list[str] = field(default_factory=list)
    rationale: str = ""

    @property
    def passed(self) -> bool:
        return self.verdict == Verdict.PASS

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "met_criteria": self.met_criteria,
            "unmet_criteria": self.unmet_criteria,
            "scope_violations": self.scope_violations,
            "blocker_fixes": self.blocker_fixes,
            "non_blocking_suggestions": self.non_blocking_suggestions,
            "rationale": self.rationale,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> ReviewVerdict:
        raw = str(data.get("verdict", data.get("result", "FAIL"))).upper()
        if raw.startswith("PASS"):
            v = Verdict.PASS
        elif "REVISION" in raw:
            v = Verdict.REVISION_REQUIRED
        else:
            v = Verdict.FAIL
        return cls(
            verdict=v,
            confidence=data.get("confidence", "medium"),
            met_criteria=data.get("met_criteria", []),
            unmet_criteria=data.get("unmet_criteria", []),
            scope_violations=data.get("scope_violations", []),
            blocker_fixes=data.get("blocker_fixes", data.get("required_fixes", [])),
            non_blocking_suggestions=data.get("non_blocking_suggestions", []),
            rationale=data.get("rationale", ""),
        )

    @classmethod
    def from_json_file(cls, path) -> ReviewVerdict:
        data = json.loads(path.read_text())
        return cls.from_dict(data)

    @classmethod
    def hard_gate_fail(cls, reason: str) -> ReviewVerdict:
        """Create a FAIL verdict from a programmatic hard gate."""
        return cls(
            verdict=Verdict.FAIL,
            confidence="high",
            unmet_criteria=[reason],
            blocker_fixes=[reason],
            rationale=f"Hard gate failure: {reason}",
        )


# ── RoundEvidence ────────────────────────────────────────────────────────────

@dataclass
class ExecutionEvidence:
    """Self-reported evidence from executor subagent (supplementary to git evidence)."""
    summary: str = ""
    files_changed: list[str] = field(default_factory=list)
    commands_run: list[str] = field(default_factory=list)
    test_results: str = ""
    diff_summary: str = ""
    unresolved_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "files_changed": self.files_changed,
            "commands_run": self.commands_run,
            "test_results": self.test_results,
            "diff_summary": self.diff_summary,
            "unresolved_issues": self.unresolved_issues,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ExecutionEvidence:
        return cls(
            summary=data.get("summary", data.get("status", "")),
            files_changed=data.get("files_changed", data.get("changes_made", [])),
            commands_run=data.get("commands_run", []),
            test_results=data.get("test_results", ""),
            diff_summary=data.get("diff_summary", ""),
            unresolved_issues=data.get("unresolved_issues", []),
        )

    @classmethod
    def from_json_file(cls, path) -> ExecutionEvidence:
        data = json.loads(path.read_text())
        return cls.from_dict(data)


# ── RoundResult ──────────────────────────────────────────────────────────────

@dataclass
class AttemptRecord:
    """Record of a single attempt within a round."""
    attempt_number: int
    task: TaskContract
    execution_evidence: ExecutionEvidence
    git_evidence: object  # GitEvidence from evidence_collector
    review_verdict: ReviewVerdict
    claude_cost_usd: float = 0.0
    is_token_exhausted: bool = False
    claude_output: str = ""

    @property
    def passed(self) -> bool:
        return self.review_verdict.passed


@dataclass
class RoundResult:
    """Complete result of a round (1-2 attempts)."""
    round_id: str
    task: TaskContract
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_passed: bool = False
    escalation_reason: str = ""

    @property
    def total_cost_usd(self) -> float:
        return sum(a.claude_cost_usd for a in self.attempts)

    @property
    def escalated(self) -> bool:
        return not self.final_passed and bool(self.escalation_reason)
