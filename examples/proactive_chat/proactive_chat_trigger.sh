#!/bin/bash
# Systemd timer trigger for proactive chat system.
# Runs every 2 minutes via systemd timer.
#
# Flow:
#   1. proactive_chat_check.py (lightweight) — only checks if it's time
#   2. If yes → `hermes cron run` triggers the cronjob
#   3. Gateway's internal 60s ticker picks up the job
#   4. Job runs proactive_chat.py (full version with context + record_sent)
#   5. Agent generates message and delivers to Telegram

set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
CHECK_SCRIPT="$HERMES_HOME/scripts/proactive_chat_check.py"
HERMES_BIN="$HERMES_HOME/hermes-agent/venv/bin/hermes"
JOB_ID="7fc126760c3a"
LOG_FILE="$HERMES_HOME/logs/proactive_chat_trigger.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Keep log file under 100KB
if [ -f "$LOG_FILE" ] && [ "$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)" -gt 102400 ]; then
    tail -100 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

# Timestamp for logging
ts() { date '+%Y-%m-%d %H:%M:%S'; }

# Run the lightweight check script (exit 1 = skip, exit 0 = trigger)
output=$(python3 "$CHECK_SCRIPT" 2>&1) && exit_code=0 || exit_code=$?

if [ $exit_code -ne 0 ]; then
    # SKIP — log reason (from first line of output)
    reason=$(echo "$output" | head -1)
    echo "[$(ts)] $reason" >> "$LOG_FILE"
    exit 0
fi

# TRIGGER — call hermes cron run to schedule the job
echo "[$(ts)] $output" >> "$LOG_FILE"
echo "[$(ts)] Triggering hermes cron run $JOB_ID..." >> "$LOG_FILE"

# Trigger the job and suppress the response (it contains system hints)
# The actual message will be delivered by the cronjob itself
if "$HERMES_BIN" cron run "$JOB_ID" >/dev/null 2>&1; then
    echo "[$(ts)] OK: job triggered, gateway ticker will execute within 60s" >> "$LOG_FILE"
else
    echo "[$(ts)] ERROR: hermes cron run failed (exit $?)" >> "$LOG_FILE"
fi
