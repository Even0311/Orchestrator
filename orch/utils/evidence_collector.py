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


def collect_git_evidence(repo_path: Path, diff_max_chars: int = 3000) -> GitEvidence:
    """Collect objective evidence of what changed in repo_path after Executor ran.

    Runs git commands directly — does not depend on Executor cooperation.
    """
    if not repo_path.exists():
        return GitEvidence(error=f"path does not exist: {repo_path}")
    if not _is_git_repo(repo_path):
        return GitEvidence(error="not a git repo")

    # git status --porcelain: all changed/new/deleted files
    status_out = _run(repo_path, ["git", "status", "--porcelain"])
    if status_out is None:
        return GitEvidence(error="git status failed")

    files_modified, files_added, files_deleted = _parse_status(status_out)

    # git diff HEAD --stat: line-level summary of tracked changes
    diff_stat = _run(repo_path, ["git", "diff", "HEAD", "--stat"]) or ""

    # git diff HEAD: actual patch for tracked changes (truncated)
    diff_full = _run(repo_path, ["git", "diff", "HEAD"]) or ""
    if len(diff_full) > diff_max_chars:
        diff_patch = diff_full[:diff_max_chars] + "\n...(truncated)"
    else:
        diff_patch = diff_full

    return GitEvidence(
        files_modified=files_modified,
        files_added=files_added,
        files_deleted=files_deleted,
        diff_stat=diff_stat.strip(),
        diff_patch_truncated=diff_patch,
        has_changes=bool(status_out.strip()),
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
