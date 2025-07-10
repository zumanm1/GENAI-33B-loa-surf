import hashlib
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from .db import get_conn
from werkzeug.exceptions import BadRequest, NotFound, Forbidden

bp = Blueprint("baseline", __name__)


def _current_user() -> str:
    # Fallback to session username, else raise 403
    username = session.get("username")
    if username:
        return username

    # Fallback to token header (accept any non-empty Bearer token for now)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        if token:
            return f"tok_{token[:12]}"
    raise Forbidden("User not authenticated")


@bp.route("/devices/<int:device_id>/baseline", methods=["GET"])
def get_device_baseline(device_id):
    """Return active baseline meta + config text for device."""
    conn = get_conn(True)
    sql = """SELECT b.device_id, b.snapshot_id, b.sha256, b.set_by, b.set_at, s.text
              FROM Baseline b JOIN ConfigSnapshot s ON s.id=b.snapshot_id
              WHERE b.device_id=?"""
    row = conn.execute(sql, (device_id,)).fetchone()
    conn.close()
    if not row:
        raise NotFound("No baseline for device")
    return jsonify(dict(row))


@bp.route("/devices/<int:device_id>/baseline/proposals", methods=["POST"])
def create_proposal(device_id):
    """Create proposal from provided snapshot text."""
    data = request.get_json(force=True) or {}
    text = data.get("snapshot")
    comment = data.get("comment", "")
    if not text:
        raise BadRequest("'snapshot' text required")

    user = _current_user()
    sha = hashlib.sha256(text.encode()).hexdigest()

    conn = get_conn()
    cur = conn.cursor()

    # Reject duplicate snapshot for same device+sha
    existing = cur.execute(
        "SELECT id FROM ConfigSnapshot WHERE device_id=? AND sha256=?", (device_id, sha)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "identical snapshot already exists"}), 409

    # Insert snapshot
    cur.execute(
        "INSERT INTO ConfigSnapshot (device_id, text, sha256) VALUES (?,?,?)",
        (device_id, text, sha),
    )
    snapshot_id = cur.lastrowid
    # Insert proposal
    cur.execute(
        """INSERT INTO Proposal (device_id, snapshot_id, comment, proposed_by)
            VALUES (?,?,?,?)""",
        (device_id, snapshot_id, comment, user),
    )
    proposal_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": proposal_id, "status": "pending"}), 201


@bp.route("/baseline/proposals/<int:proposal_id>", methods=["PUT"])

@bp.route("/baseline/proposals", methods=["GET"])
def get_proposals():
    """Return all proposals, optionally filtered by status."""
    status = request.args.get("status")
    conn = get_conn(True)

    sql = "SELECT p.*, s.sha256 FROM Proposal p JOIN ConfigSnapshot s ON s.id=p.snapshot_id"
    params = []
    if status:
        sql += " WHERE p.status=?"
        params.append(status)

    sql += " ORDER BY p.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    proposals = [dict(row) for row in rows]
    return jsonify(proposals)


@bp.route("/baseline/proposals/<int:proposal_id>", methods=["PUT"])
def decide_proposal(proposal_id):
    data = request.get_json(force=True) or {}
    action = data.get("action")
    if action not in {"approve", "reject"}:
        raise BadRequest("action must be 'approve' or 'reject'")
    user = _current_user()

    conn = get_conn()
    cur = conn.cursor()
    prop = cur.execute("SELECT * FROM Proposal WHERE id=?", (proposal_id,)).fetchone()
    if not prop:
        conn.close()
        raise NotFound("Proposal not found")
    if prop["status"] != "pending":
        conn.close()
        raise BadRequest("Proposal already decided")
    if prop["proposed_by"] == user:
        conn.close()
        raise Forbidden("Proposer cannot self-approve/reject")

    status = "approved" if action == "approve" else "rejected"
    decided_at = datetime.utcnow().isoformat(" ", "seconds")

    cur.execute(
        "UPDATE Proposal SET status=?, decided_by=?, decided_at=? WHERE id=?",
        (status, user, decided_at, proposal_id),
    )

    if status == "approved":
        # Archive current baseline (if any) and promote new one
        device_id = prop["device_id"]
        # fetch current baseline
        bl = cur.execute("SELECT * FROM Baseline WHERE device_id=?", (device_id,)).fetchone()
        if bl:
            cur.execute(
                "INSERT INTO BaselineHistory (device_id, snapshot_id, sha256) VALUES (?,?,?)",
                (device_id, bl["snapshot_id"], bl["sha256"]),
            )
            cur.execute("DELETE FROM Baseline WHERE device_id=?", (device_id,))
        # Insert new baseline
        snapshot_row = cur.execute("SELECT sha256 FROM ConfigSnapshot WHERE id=?", (prop["snapshot_id"],)).fetchone()
        cur.execute(
            "INSERT INTO Baseline (device_id, snapshot_id, sha256, set_by) VALUES (?,?,?,?)",
            (device_id, prop["snapshot_id"], snapshot_row["sha256"], user),
        )
    conn.commit()
    conn.close()
    return jsonify({"status": status})


@bp.route("/baseline/proposals", methods=["GET"])
def list_proposals():
    status = request.args.get("status")
    conn = get_conn(True)
    cur = conn.cursor()
    if status:
        rows = [dict(r) for r in cur.execute("SELECT * FROM Proposal WHERE status=? ORDER BY id DESC", (status,)).fetchall()]
    else:
        rows = [dict(r) for r in cur.execute("SELECT * FROM Proposal ORDER BY id DESC").fetchall()]
    conn.close()
    return jsonify(rows)


@bp.route("/devices/<int:device_id>/deviations", methods=["GET"])
def get_device_deviations(device_id):
    conn = get_conn(True)
    cur = conn.cursor()
    cur.execute("SELECT id, severity, diff_stats, created_at FROM DeviationEvent WHERE device_id=? ORDER BY id DESC", (device_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)
