#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# bootstrap_tmux.sh
# -----------------------------------------------------------------------------
# Creates a detached tmux session with five windows, each wired to a dedicated
# monitoring or development task.  All pane output is piped to timestamped log
# files under log-sessions/.
# -----------------------------------------------------------------------------
set -euo pipefail

SESSION="net-swf"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="log-sessions/session-${TIMESTAMP}"

mkdir -p "${LOG_DIR}"

# Kill any existing session with the same name
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  tmux kill-session -t "${SESSION}"
fi

# ---------------- Window 1: interactive shell ----------------

tmux new-session -d -s "${SESSION}" -n main
# Log window 1
tmux pipe-pane -t "${SESSION}:main" -o "cat >> '${LOG_DIR}/terminal-1-main.log'"

# ---------------- Window 2: htop ----------------

tmux new-window -t "${SESSION}:2" -n app-monitor \
  "htop"
# Log window 2
tmux pipe-pane -t "${SESSION}:app-monitor" -o "cat >> '${LOG_DIR}/terminal-2-app.log'"

# ---------------- Window 3: tail logs ----------------

tmux new-window -t "${SESSION}:3" -n logs \
  "tail -F backend_mock/mock_ai_service.log"
# Log window 3
tmux pipe-pane -t "${SESSION}:logs" -o "cat >> '${LOG_DIR}/terminal-3-logs.log'"

# ---------------- Window 4: system metrics ----------------

tmux new-window -t "${SESSION}:4" -n sys-resources \
  "vmstat 2"
# Log window 4
tmux pipe-pane -t "${SESSION}:sys-resources" -o "cat >> '${LOG_DIR}/terminal-4-system.log'"

# ---------------- Window 5: pytest watcher ----------------

tmux new-window -t "${SESSION}:5" -n tests \
  "pytest -q --color=yes --maxfail=1 --failed-first -f"
# Log window 5
tmux pipe-pane -t "${SESSION}:tests" -o "cat >> '${LOG_DIR}/terminal-5-tests.log'"

# Metadata for the session
cat > "${LOG_DIR}/session-metadata.json" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "tmux_session": "${SESSION}",
  "windows": [
    "main", "app-monitor", "logs", "sys-resources", "tests"
  ]
}
EOF

echo "[bootstrap_tmux] Session '${SESSION}' created. Attach with: tmux attach -t ${SESSION}"
