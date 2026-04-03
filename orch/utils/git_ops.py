"""Git utilities for orchestrator and target project management."""
import subprocess
from pathlib import Path


class GitError(Exception):
    pass


def is_git_repo(path: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=str(path), capture_output=True,
    )
    return result.returncode == 0


def git_init(path: Path) -> None:
    """Init a git repo and create an initial empty commit."""
    subprocess.run(["git", "init"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=str(path), capture_output=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit (orchestrator managed)"],
        cwd=str(path), capture_output=True,
    )


def get_current_commit(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_path), capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise GitError(f"Cannot get HEAD commit in {repo_path}: {result.stderr.strip()}")
    return result.stdout.strip()


def is_clean(repo_path: Path) -> bool:
    """True if there are no uncommitted changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_path), capture_output=True, text=True,
    )
    return result.stdout.strip() == ""


def commit_projects_dir(repo_path: Path, message: str) -> str:
    """Stage only the projects/ directory and commit. Returns commit hash."""
    subprocess.run(
        ["git", "add", "projects/"],
        cwd=str(repo_path), check=True, capture_output=True,
    )
    # Check if anything is staged
    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(repo_path), capture_output=True,
    )
    if diff.returncode == 0:
        # Nothing to commit — return current HEAD
        return get_current_commit(repo_path)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(repo_path), check=True, capture_output=True,
    )
    return get_current_commit(repo_path)


def commit_all(repo_path: Path, message: str) -> str:
    """Stage all changes and commit. Returns commit hash."""
    subprocess.run(["git", "add", "-A"], cwd=str(repo_path), check=True, capture_output=True)
    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(repo_path), capture_output=True,
    )
    if diff.returncode == 0:
        return get_current_commit(repo_path)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(repo_path), check=True, capture_output=True,
    )
    return get_current_commit(repo_path)


def clean_working_tree(repo_path: Path) -> None:
    """Discard all uncommitted changes and remove untracked files."""
    subprocess.run(
        ["git", "checkout", "."],
        cwd=str(repo_path), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "clean", "-fd"],
        cwd=str(repo_path), check=True, capture_output=True,
    )


def reset_hard(repo_path: Path, commit_hash: str) -> None:
    """Hard reset the current branch to a specific commit."""
    result = subprocess.run(
        ["git", "reset", "--hard", commit_hash],
        cwd=str(repo_path), capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise GitError(f"git reset --hard failed in {repo_path}: {result.stderr.strip()}")
