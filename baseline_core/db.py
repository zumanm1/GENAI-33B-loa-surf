import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "baseline.db"

_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ---------------------------------------------------------------------
-- Core tables
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ConfigSnapshot (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Baseline (
    device_id INTEGER PRIMARY KEY,
    snapshot_id INTEGER UNIQUE,
    sha256 TEXT NOT NULL,
    set_by TEXT NOT NULL,
    set_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES ConfigSnapshot(id)
);

CREATE TABLE IF NOT EXISTS BaselineHistory (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    snapshot_id INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    replaced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Proposal (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    snapshot_id INTEGER,
    snippet_text TEXT,
    comment TEXT,
    proposed_by TEXT NOT NULL,
    proposed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('pending','approved','rejected')) DEFAULT 'pending',
    decided_by TEXT,
    decided_at DATETIME
);
CREATE INDEX IF NOT EXISTS proposal_status_idx ON Proposal(status);

CREATE TABLE IF NOT EXISTS DeviationEvent (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    snapshot_id INTEGER NOT NULL,
    severity TEXT CHECK(severity IN ('info','warn','critical')),
    diff_stats TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS dev_sev_time_idx ON DeviationEvent(severity, created_at DESC);

CREATE TABLE IF NOT EXISTS IgnorePattern (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    regex TEXT NOT NULL,
    added_by TEXT NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Triggers & constraints
-- ---------------------------------------------------------------------
-- Allow exactly ONE row in Baseline per device
CREATE TRIGGER IF NOT EXISTS baseline_singleton
BEFORE INSERT ON Baseline
WHEN (SELECT COUNT(*) FROM Baseline WHERE device_id = NEW.device_id) > 0
BEGIN
    SELECT RAISE(ABORT, 'baseline exists');
END;
"""


def get_conn(readonly: bool = False) -> sqlite3.Connection:
    """Return SQLite connection to baseline DB.  readonly uses URI mode."""
    if readonly:
        uri = f"file:{DB_PATH}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=30)
    else:
        conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables & triggers if not present (idempotent)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    conn.close()
