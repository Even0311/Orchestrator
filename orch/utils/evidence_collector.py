"""External evidence collection via git — orchestrator-side, independent of Executor self-report."""
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitEvidence:
    """Git-based evidence collected by orchestrator after Executor runs.

    This is the authoritative evidence source. Executor self-report is supplementary.
    """
    files_modified: list[str] = field(default_factory=list)   # tracked files changed
    files_added: list[str] = field(default_factory=list)      # new untracked files on disk
    files_deleted: list[str] = field(default_factory=list)    # deleted files
    diff_stat: str = ""             # git diff HEAD --stat (compact summary of line changes)
    diff_patch_truncated: str = ""  # first ~3000 chars of actual git diff
    has_changes: bool = False
    error: str = ""                 # non-empty if collection failed


def collect_git_evidence(repo_path: Path, baseline_commit: str | None = None, diff_max_chars: int = 3000) -> GitEvidence:
    """Collect objective evidence of what changed in repo_path after Executor ran.

    Runs git commands directly — does not depend on Executor cooperation.

    If *baseline_commit* is provided, evidence includes both uncommitted changes
    AND any new commits made since that baseline (``git diff <baseline>..HEAD``).
    Without it, only uncommitted working-tree changes are detected (legacy mode).
    """
    if not repo_path.exists():
        return GitEvidence(error=f"path does not exist: {repo_path}")
    if not _is_git_repo(repo_path):
        return GitEvidence(error="not a git repo")

    # --- Uncommitted changes (working tree + index) ---
    status_out = _run(repo_path, ["git", "status", "--porcelain", "-uall"])
    if status_out is None:
        return GitEvidence(error="git status failed")

    wt_modified, wt_added, wt_deleted = _parse_status(status_out)

    # --- Committed changes since baseline ---
    cm_modified: list[str] = []
    cm_added: list[str] = []
    cm_deleted: list[str] = []
    committed_diff_stat = ""
    committed_diff_full = ""

    if baseline_commit:
        committed_status = _run(repo_path, [
            "git", "diff", "--name-status", f"{baseline_commit}..HEAD",
        ])
        if committed_status:
            cm_modified, cm_added, cm_deleted = _parse_name_status(committed_status)

        committed_diff_stat = _run(repo_path, [
            "git", "diff", f"{baseline_commit}..HEAD", "--stat",
        ]) or ""

        committed_diff_full = _run(repo_path, [
            "git", "diff", f"{baseline_commit}..HEAD",
        ]) or ""

    # Merge: committed changes + uncommitted working-tree changes
    files_modified = sorted(set(cm_modified + wt_modified))
    files_added = sorted(set(cm_added + wt_added))
    files_deleted = sorted(set(cm_deleted + wt_deleted))

    # Prefer committed diff stat if present; fall back to working-tree diff
    diff_stat = committed_diff_stat or _run(repo_path, ["git", "diff", "HEAD", "--stat"]) or ""

    # Build full diff
    diff_full = committed_diff_full
    # Append uncommitted changes on top of committed diff
    wt_diff = _run(repo_path, ["git", "diff", "HEAD"]) or ""
    if wt_diff:
        diff_full += f"\n{wt_diff}"

    # For untracked (new) files, capture their content
    for new_file in wt_added:
        file_path = repo_path / new_file
        if file_path.is_file():
            untracked_diff = _run(
                repo_path,
                ["git", "diff", "--no-index", "/dev/null", new_file],
            )
            if untracked_diff is None:
                untracked_diff = _run_no_index_diff(repo_path, new_file)
            if untracked_diff:
                diff_full += f"\n{untracked_diff}"

    if len(diff_full) > diff_max_chars:
        diff_patch = diff_full[:diff_max_chars] + "\n...(truncated)"
    else:
        diff_patch = diff_full

    has_changes = bool(files_modified or files_added or files_deleted)

    return GitEvidence(
        files_modified=files_modified,
        files_added=files_added,
        files_deleted=files_deleted,
        diff_stat=diff_stat.strip(),
        diff_patch_truncated=diff_patch,
        has_changes=has_changes,
    )


def _is_git_repo(path: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=str(path), capture_output=True,
    )
    return result.returncode == 0


def _run(path: Path, cmd: list[str]) -> str | None:
    """Run a git command; return stdout text or None on failure."""
    try:
        result = subprocess.run(
            cmd, cwd=str(path), capture_output=True, text=True, timeout=30
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None


def _run_no_index_diff(path: Path, filename: str) -> str:
    """Run git diff --no-index for an untracked file.

    git diff --no-index exits with code 1 when files differ (which is always
    the case for /dev/null vs a real file), so we accept returncode 1 as success.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--no-index", "/dev/null", filename],
            cwd=str(path), capture_output=True, text=True, timeout=30,
        )
        if result.returncode in (0, 1) and result.stdout:
            return result.stdout
        return ""
    except Exception:
        return ""


def _parse_name_status(output: str) -> tuple[list[str], list[str], list[str]]:
    """Parse ``git diff --name-status`` output into (modified, added, deleted)."""
    modified: list[str] = []
    added: list[str] = []
    deleted: list[str] = []
    for line in output.splitlines():
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        status, filename = parts[0].strip(), parts[1].strip()
        if status.startswith("A"):
            added.append(filename)
        elif status.startswith("D"):
            deleted.append(filename)
        else:
            modified.append(filename)
    return modified, added, deleted


def _parse_status(status_output: str) -> tuple[list[str], list[str], list[str]]:
    """Parse `git status --porcelain` lines into (modified, added, deleted) lists."""
    modified: list[str] = []
    added: list[str] = []
    deleted: list[str] = []

    for line in status_output.splitlines():
        if len(line) < 3:
            continue
        xy = line[:2]
        filename = line[3:].strip().strip('"')

        if xy.strip() == "??":
            added.append(filename)
        elif "D" in xy:
            deleted.append(filename)
        else:
            modified.append(filename)

    return modified, added, deleted
