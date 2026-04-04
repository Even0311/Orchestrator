"""Tests for orch.engine.hard_gates — post-Claude verification."""
import pytest
from pathlib import Path

from orch.engine.hard_gates import (
    run_hard_gates,
    _gate_has_changes,
    _gate_target_protected_files,
    _gate_allowed_files,
    _gate_forbidden_files,
    _gate_round_dir_boundary,
    validate_proposed_scope,
    snapshot_sot_dir,
    detect_sot_mutation,
    HardGateResults,
    GateResult,
    TARGET_REPO_PROTECTED,
    ALLOWED_ROUND_ARTIFACTS,
    CANONICAL_SOT_FILES,
)
from orch.utils.evidence_collector import GitEvidence


# ── Gate: has changes ────────────────────────────────────────────────────────

class TestGateHasChanges:
    def test_pass_with_changes(self):
        ev = GitEvidence(has_changes=True, files_modified=["a.py"])
        result = _gate_has_changes(ev)
        assert result.passed is True

    def test_fail_without_changes(self):
        ev = GitEvidence(has_changes=False)
        result = _gate_has_changes(ev)
        assert result.passed is False


# ── Gate: target repo protected files ────────────────────────────────────────

class TestGateTargetProtectedFiles:
    def test_pass_no_protected_touched(self):
        ev = GitEvidence(files_modified=["src/app.py"], files_added=["tests/test_new.py"])
        result = _gate_target_protected_files(ev)
        assert result.passed is True

    def test_fail_claude_md_modified(self):
        """CLAUDE.md in target repo must be protected."""
        ev = GitEvidence(files_modified=["CLAUDE.md"])
        result = _gate_target_protected_files(ev)
        assert result.passed is False
        assert "CLAUDE.md" in result.detail

    def test_fail_subagent_designer_modified(self):
        """.claude/agents/designer.md must be protected."""
        ev = GitEvidence(files_modified=[".claude/agents/designer.md"])
        result = _gate_target_protected_files(ev)
        assert result.passed is False

    def test_fail_subagent_executor_added(self):
        ev = GitEvidence(files_added=[".claude/agents/executor.md"])
        result = _gate_target_protected_files(ev)
        assert result.passed is False

    def test_fail_subagent_round_driver_modified(self):
        ev = GitEvidence(files_modified=[".claude/agents/round-driver.md"])
        result = _gate_target_protected_files(ev)
        assert result.passed is False

    def test_fail_subagent_new_agent_added(self):
        """Any file matching .claude/agents/** must be protected."""
        ev = GitEvidence(files_added=[".claude/agents/sneaky-agent.md"])
        result = _gate_target_protected_files(ev)
        assert result.passed is False

    def test_pass_unrelated_claude_dir(self):
        """Files in .claude/ but NOT agents/ should pass (e.g. .claude/settings.json)."""
        ev = GitEvidence(files_modified=[".claude/settings.json"])
        result = _gate_target_protected_files(ev)
        assert result.passed is True

    def test_pass_regular_code_files(self):
        ev = GitEvidence(
            files_modified=["back/app/engine.py", "back/tests/test_thing.py"],
            files_added=["back/tests/test_new.py"],
        )
        result = _gate_target_protected_files(ev)
        assert result.passed is True


# ── Gate: round directory boundary ───────────────────────────────────────────

class TestGateRoundDirBoundary:
    def test_pass_only_allowed_artifacts(self, tmp_path):
        """Exactly the three artifact files + round_brief.md should pass."""
        (tmp_path / "round_brief.md").write_text("# Brief")
        (tmp_path / "task_contract.json").write_text("{}")
        (tmp_path / "execution_evidence.json").write_text("{}")
        (tmp_path / "review_verdict.json").write_text("{}")
        result = _gate_round_dir_boundary(tmp_path)
        assert result.passed is True

    def test_fail_unexpected_file_in_round_dir(self, tmp_path):
        """A file not in ALLOWED_ROUND_ARTIFACTS should fail."""
        (tmp_path / "round_brief.md").write_text("# Brief")
        (tmp_path / "task_contract.json").write_text("{}")
        (tmp_path / "sneaky_payload.py").write_text("import os")
        result = _gate_round_dir_boundary(tmp_path)
        assert result.passed is False
        assert "unexpected file" in result.detail

    def test_fail_subdir_in_round_dir(self, tmp_path):
        """Files in subdirectories of round_dir should fail (path traversal attempt)."""
        (tmp_path / "round_brief.md").write_text("# Brief")
        subdir = tmp_path / "nested"
        subdir.mkdir()
        (subdir / "payload.py").write_text("# escape")
        result = _gate_round_dir_boundary(tmp_path)
        assert result.passed is False
        assert "outside round dir" in result.detail

    def test_pass_empty_dir(self, tmp_path):
        """Empty round dir should pass."""
        result = _gate_round_dir_boundary(tmp_path)
        assert result.passed is True

    def test_pass_nonexistent_dir(self, tmp_path):
        result = _gate_round_dir_boundary(tmp_path / "doesnt_exist")
        assert result.passed is True


# ── Gate: allowed / forbidden files ──────────────────────────────────────────

class TestGateAllowedFiles:
    def test_pass_all_within_pattern(self):
        ev = GitEvidence(
            files_modified=["back/app/engine.py"],
            files_added=["back/tests/test_new.py"],
        )
        result = _gate_allowed_files(ev, ["back/**/*.py"])
        assert result.passed is True

    def test_fail_file_outside_pattern(self):
        ev = GitEvidence(
            files_modified=["back/app/engine.py", "frontend/index.js"],
        )
        result = _gate_allowed_files(ev, ["back/**/*.py"])
        assert result.passed is False
        assert "frontend/index.js" in result.detail


class TestGateForbiddenFiles:
    def test_pass_no_forbidden_touched(self):
        ev = GitEvidence(files_modified=["src/app.py"])
        result = _gate_forbidden_files(ev, ["*.env", "secrets/*"])
        assert result.passed is True

    def test_fail_forbidden_touched(self):
        ev = GitEvidence(files_modified=[".env"])
        result = _gate_forbidden_files(ev, ["*.env"])
        assert result.passed is False


# ── HardGateResults aggregation ──────────────────────────────────────────────

class TestHardGateResults:
    def test_all_passed(self):
        results = HardGateResults(gates=[
            GateResult(name="a", passed=True),
            GateResult(name="b", passed=True),
        ])
        assert results.all_passed is True
        assert results.to_verdict() is None

    def test_one_failure(self):
        results = HardGateResults(gates=[
            GateResult(name="a", passed=True),
            GateResult(name="b", passed=False, detail="broken"),
        ])
        assert results.all_passed is False
        verdict = results.to_verdict()
        assert verdict is not None
        assert verdict.passed is False
        assert "broken" in verdict.rationale


# ── Scope policy validation (D) ─────────────────────────────────────────────

class TestValidateProposedScope:
    def test_reject_wildcard_star_star(self):
        """allowed_files ['**'] must be rejected."""
        ev = GitEvidence(has_changes=True, files_modified=["src/app.py"])
        result = validate_proposed_scope(["**"], [], ev)
        assert result.valid is False
        assert any("too broad" in v for v in result.violations)
        assert "**" not in result.sanitized_allowed

    def test_reject_star(self):
        """allowed_files ['*'] must be rejected."""
        ev = GitEvidence(has_changes=True, files_modified=["src/app.py"])
        result = validate_proposed_scope(["*"], [], ev)
        assert result.valid is False

    def test_reject_star_star_slash_star(self):
        ev = GitEvidence(has_changes=True, files_modified=["src/app.py"])
        result = validate_proposed_scope(["**/*"], [], ev)
        assert result.valid is False

    def test_reject_control_plane_overlap(self):
        """Patterns matching CLAUDE.md must be rejected."""
        ev = GitEvidence(has_changes=True, files_modified=["src/app.py"])
        result = validate_proposed_scope(["*.md"], [], ev)
        assert result.valid is False
        assert any("control-plane" in v for v in result.violations)

    def test_reject_claude_agents_pattern(self):
        """Patterns matching .claude/agents/ must be rejected."""
        ev = GitEvidence(has_changes=True, files_modified=["src/app.py"])
        result = validate_proposed_scope([".claude/**"], [], ev)
        assert result.valid is False

    def test_accept_narrow_valid_scope(self):
        """Narrow, valid scope should pass."""
        ev = GitEvidence(has_changes=True, files_modified=["back/app/engine.py"])
        result = validate_proposed_scope(["back/**/*.py", "back/tests/**"], [], ev)
        assert result.valid is True
        assert "back/**/*.py" in result.sanitized_allowed
        assert "back/tests/**" in result.sanitized_allowed

    def test_forbidden_always_includes_control_plane(self):
        """Sanitized forbidden must always include control-plane patterns."""
        ev = GitEvidence(has_changes=True, files_modified=["src/app.py"])
        result = validate_proposed_scope(["src/**/*.py"], [], ev)
        assert "CLAUDE.md" in result.sanitized_forbidden
        assert ".claude/agents/**" in result.sanitized_forbidden

    def test_empty_proposal_is_valid(self):
        """No allowed_files proposed — gate simply won't run."""
        ev = GitEvidence(has_changes=True, files_modified=["src/app.py"])
        result = validate_proposed_scope([], [], ev)
        assert result.valid is True
        assert result.sanitized_allowed == []

    def test_mixed_valid_and_invalid(self):
        """Valid patterns kept, invalid rejected."""
        ev = GitEvidence(has_changes=True, files_modified=["src/app.py"])
        result = validate_proposed_scope(["back/**/*.py", "**", "*.md"], [], ev)
        assert result.valid is False
        assert "back/**/*.py" in result.sanitized_allowed
        assert "**" not in result.sanitized_allowed
        assert "*.md" not in result.sanitized_allowed

    def test_out_of_scope_changed_files_still_fail(self):
        """Even with valid allowed_files, files outside scope should fail the gate."""
        ev = GitEvidence(
            has_changes=True,
            files_modified=["back/app/engine.py", "frontend/index.js"],
        )
        scope = validate_proposed_scope(["back/**/*.py"], [], ev)
        assert scope.valid is True
        # Now run the actual gate
        gate = _gate_allowed_files(ev, scope.sanitized_allowed)
        assert gate.passed is False
        assert "frontend/index.js" in gate.detail


# ── Canonical SOT mutation detection ────────────────────────────────────────

class TestSnapshotSotDir:
    def _make_sot(self, tmp_path):
        """Build a realistic SOT directory with canonical files and a round dir."""
        sot = tmp_path / "projects" / "test-project"
        sot.mkdir(parents=True)
        (sot / "vision.md").write_text("# Vision\nGoal here.")
        (sot / "road_map.md").write_text("# Road Map\nPhases here.")
        (sot / "current_phase.md").write_text("# P1: Test\n## Task Queue\n- [ ] P1-T1: Do thing")
        (sot / "decisions.md").write_text("# Decisions\n")
        return sot

    def test_snapshots_all_canonical_files(self, tmp_path):
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        for f in CANONICAL_SOT_FILES:
            assert f in snap, f"canonical file {f} not in snapshot"

    def test_excludes_allowed_write_prefix(self, tmp_path):
        sot = self._make_sot(tmp_path)
        attempt_dir = sot / "rounds" / "round-0001" / "attempt_1"
        attempt_dir.mkdir(parents=True)
        (attempt_dir / "task_contract.json").write_text("{}")
        snap = snapshot_sot_dir(sot, allowed_write_prefix=attempt_dir)
        # Canonical files present
        assert "vision.md" in snap
        # Artifact in allowed area excluded
        for key in snap:
            assert "attempt_1" not in key

    def test_empty_sot_returns_empty(self, tmp_path):
        snap = snapshot_sot_dir(tmp_path / "nonexistent")
        assert snap == {}


class TestDetectSotMutation:
    def _make_sot(self, tmp_path):
        sot = tmp_path / "projects" / "test-project"
        sot.mkdir(parents=True)
        (sot / "vision.md").write_text("# Vision\nOriginal.")
        (sot / "road_map.md").write_text("# Road Map\nOriginal.")
        (sot / "current_phase.md").write_text("# P1\n## Task Queue\n- [ ] P1-T1: Task")
        (sot / "decisions.md").write_text("# Decisions\n")
        return sot

    def test_no_mutation_passes(self, tmp_path):
        """No changes between snapshot and detection → PASS."""
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        result = detect_sot_mutation(snap, sot)
        assert result.passed is True
        assert result.name == "sot_mutation"

    def test_current_phase_mutated_fails(self, tmp_path):
        """Direct mutation of current_phase.md → FAIL."""
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        # Simulate Claude mutating current_phase.md
        (sot / "current_phase.md").write_text("# HIJACKED BY CLAUDE")
        result = detect_sot_mutation(snap, sot)
        assert result.passed is False
        assert "current_phase.md" in result.detail
        assert "mutated" in result.detail

    def test_decisions_mutated_fails(self, tmp_path):
        """Direct mutation of decisions.md → FAIL."""
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        (sot / "decisions.md").write_text("# Decisions\nInjected entry")
        result = detect_sot_mutation(snap, sot)
        assert result.passed is False
        assert "decisions.md" in result.detail

    def test_vision_mutated_fails(self, tmp_path):
        """Direct mutation of vision.md → FAIL."""
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        (sot / "vision.md").write_text("# Vision\nMutated content.")
        result = detect_sot_mutation(snap, sot)
        assert result.passed is False
        assert "vision.md" in result.detail

    def test_road_map_mutated_fails(self, tmp_path):
        """Direct mutation of road_map.md → FAIL."""
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        (sot / "road_map.md").write_text("# Road Map\nMutated.")
        result = detect_sot_mutation(snap, sot)
        assert result.passed is False
        assert "road_map.md" in result.detail

    def test_writes_inside_allowed_area_pass(self, tmp_path):
        """Files written inside allowed_write_prefix are ignored → PASS."""
        sot = self._make_sot(tmp_path)
        attempt_dir = sot / "rounds" / "round-0001" / "attempt_1"
        attempt_dir.mkdir(parents=True)
        snap = snapshot_sot_dir(sot, allowed_write_prefix=attempt_dir)
        # Claude writes artifacts inside allowed area
        (attempt_dir / "task_contract.json").write_text('{"phase_id": "P1"}')
        (attempt_dir / "execution_evidence.json").write_text('{"summary": "done"}')
        (attempt_dir / "review_verdict.json").write_text('{"verdict": "PASS"}')
        result = detect_sot_mutation(snap, sot, allowed_write_prefix=attempt_dir)
        assert result.passed is True

    def test_writes_escaping_allowed_area_fail(self, tmp_path):
        """Files created outside allowed_write_prefix → FAIL."""
        sot = self._make_sot(tmp_path)
        attempt_dir = sot / "rounds" / "round-0001" / "attempt_1"
        attempt_dir.mkdir(parents=True)
        snap = snapshot_sot_dir(sot, allowed_write_prefix=attempt_dir)
        # Claude writes outside allowed area (e.g. sibling round dir)
        escape_dir = sot / "rounds" / "round-0001" / "escape"
        escape_dir.mkdir(parents=True)
        (escape_dir / "payload.py").write_text("import os")
        result = detect_sot_mutation(snap, sot, allowed_write_prefix=attempt_dir)
        assert result.passed is False
        assert "unexpected file" in result.detail

    def test_new_file_in_sot_root_fails(self, tmp_path):
        """New file created directly in SOT root → FAIL."""
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        (sot / "injected.md").write_text("# injected")
        result = detect_sot_mutation(snap, sot)
        assert result.passed is False
        assert "unexpected file" in result.detail
        assert "injected.md" in result.detail

    def test_canonical_file_deleted_fails(self, tmp_path):
        """Deletion of a canonical SOT file → FAIL."""
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        (sot / "vision.md").unlink()
        result = detect_sot_mutation(snap, sot)
        assert result.passed is False
        assert "deleted" in result.detail
        assert "vision.md" in result.detail

    def test_orchestrator_pass_time_updates_not_blocked(self, tmp_path):
        """Orchestrator-owned PASS-time updates happen AFTER detection.

        Simulate: snapshot → Claude runs (no mutation) → detection passes →
        then orchestrator updates current_phase.md (not checked again).
        """
        sot = self._make_sot(tmp_path)
        snap = snapshot_sot_dir(sot)
        # Claude makes no SOT changes — detection should pass
        result = detect_sot_mutation(snap, sot)
        assert result.passed is True
        # NOW orchestrator updates SOT (after adjudication) — this is allowed
        # because it happens after detect_sot_mutation, not during Claude's run
        (sot / "current_phase.md").write_text("# P1\n## Task Queue\n- [x] P1-T1: Task — Round round-0001")
        (sot / "decisions.md").write_text("# Decisions\n\n## 2026-04-04 — round-0001\n")
        # A second detection would catch these, but that's fine —
        # the point is that the first detection (which gates the round) passed.

    def test_target_repo_protected_files_still_work(self):
        """Target-repo protection (CLAUDE.md, .claude/agents/**) is not broken."""
        ev = GitEvidence(files_modified=["CLAUDE.md"])
        result = _gate_target_protected_files(ev)
        assert result.passed is False

        ev2 = GitEvidence(files_added=[".claude/agents/sneaky.md"])
        result2 = _gate_target_protected_files(ev2)
        assert result2.passed is False

        ev3 = GitEvidence(files_modified=["src/app.py"])
        result3 = _gate_target_protected_files(ev3)
        assert result3.passed is True
