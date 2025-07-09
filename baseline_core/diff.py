import hashlib
import difflib
import json
from .db import get_conn

CRITICAL_KEYS = ("interface ", "access-list", "acl ", "route-map", "ip access")
WARN_KEYS = ("hostname", "banner")
INFO_KEYS = ("clock-period",)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def classify_severity(diff_lines: list[str]) -> str:
    """Return severity based on presence of keywords in added/removed lines."""
    for line in diff_lines:
        l = line.lower()
        if any(k in l for k in CRITICAL_KEYS):
            return "critical"
    for line in diff_lines:
        l = line.lower()
        if any(k in l for k in WARN_KEYS):
            return "warn"
    return "info"


def diff_and_record(device_id: int, snapshot_text: str, actor: str | None = None):
    """Compare snapshot_text to current baseline, record DeviationEvent if needed.

    Returns dict with severity, diff_stats, added, removed counts.
    """
    conn = get_conn()
    cur = conn.cursor()
    # Insert snapshot first
    sha = _sha(snapshot_text)
    cur.execute(
        "INSERT INTO ConfigSnapshot (device_id, text, sha256) VALUES (?,?,?)",
        (device_id, snapshot_text, sha),
    )
    snapshot_id = cur.lastrowid

    # Get baseline
    bl = cur.execute("SELECT snapshot_id FROM Baseline WHERE device_id=?", (device_id,)).fetchone()
    if not bl:
        conn.commit()
        conn.close()
        return {
            "severity": "info",
            "diff_stats": {"added": 0, "removed": 0},
            "snapshot_id": snapshot_id,
        }
    base_text = cur.execute(
        "SELECT text FROM ConfigSnapshot WHERE id=?", (bl["snapshot_id"],)
    ).fetchone()["text"]

    diff = list(difflib.unified_diff(base_text.splitlines(), snapshot_text.splitlines(), lineterm=""))
    added = sum(1 for ln in diff if ln.startswith("+") and not ln.startswith("+++"))
    removed = sum(1 for ln in diff if ln.startswith("-") and not ln.startswith("---"))
    severity = classify_severity(diff)

    if severity != "info":
        cur.execute(
            """INSERT INTO DeviationEvent (device_id, snapshot_id, severity, diff_stats)
               VALUES (?,?,?,?)""",
            (device_id, snapshot_id, severity, json.dumps({"added": added, "removed": removed})),
        )
    conn.commit()
    conn.close()
    return {"severity": severity, "diff_stats": {"added": added, "removed": removed}, "snapshot_id": snapshot_id}
