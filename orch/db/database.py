import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ORCH_HOME = Path.home() / ".orch"
DB_PATH = ORCH_HOME / "orchestrator.db"


def get_connection() -> sqlite3.Connection:
    ORCH_HOME.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id            TEXT PRIMARY KEY,
                name          TEXT UNIQUE NOT NULL,
                codebase_path TEXT NOT NULL,
                state_dir     TEXT NOT NULL,
                is_active     INTEGER DEFAULT 0,
                created_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS phases (
                id          TEXT PRIMARY KEY,
                project_id  TEXT NOT NULL,
                name        TEXT NOT NULL,
                description TEXT,
                status      TEXT NOT NULL DEFAULT 'pending',
                created_at  TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS rounds (
                id                   TEXT PRIMARY KEY,
                project_id           TEXT NOT NULL,
                phase_id             TEXT,
                status               TEXT NOT NULL DEFAULT 'pending',
                attempt_count        INTEGER DEFAULT 0,
                task_description     TEXT,
                executor_result      TEXT,
                reviewer_verdict     TEXT,
                escalation_reason    TEXT,
                cost_usd             REAL DEFAULT 0,
                orchestrator_commit  TEXT,
                target_commit        TEXT,
                created_at           TEXT NOT NULL,
                updated_at           TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (phase_id)   REFERENCES phases(id)
            );
        """)
        # Migrate: add commit columns if upgrading from older schema
        for col in ("orchestrator_commit", "target_commit"):
            try:
                conn.execute(f"ALTER TABLE rounds ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass  # column already exists


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Project operations ----------

def create_project(project_id: str, name: str, codebase_path: str, state_dir: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO projects (id, name, codebase_path, state_dir, created_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, name, codebase_path, state_dir, now_iso()),
        )


def get_all_projects() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM projects ORDER BY created_at").fetchall()


def get_project_by_name(name: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM projects WHERE name = ?", (name,)).fetchone()


def get_active_project() -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM projects WHERE is_active = 1").fetchone()


def set_active_project(project_id: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE projects SET is_active = 0")
        conn.execute("UPDATE projects SET is_active = 1 WHERE id = ?", (project_id,))


def update_project_path(project_id: str, new_path: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE projects SET codebase_path = ? WHERE id = ?",
            (new_path, project_id),
        )


def delete_project(project_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM rounds WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM phases WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))


# ---------- Round operations ----------

def get_round(round_id: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM rounds WHERE id = ?", (round_id,)).fetchone()


def update_round_commits(round_id: str, orchestrator_commit: str, target_commit: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE rounds SET orchestrator_commit = ?, target_commit = ?, updated_at = ? WHERE id = ?",
            (orchestrator_commit, target_commit, now_iso(), round_id),
        )
