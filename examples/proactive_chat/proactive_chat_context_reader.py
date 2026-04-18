#!/usr/bin/env python3
"""Proactive chat context reader for cronjob execution.

This script is called by the Hermes cronjob (via script field).
It reads the pre-computed context from the trigger file written by
proactive_chat_check.py, outputs it, and records that we sent.

If no trigger file exists, outputs SKIP (safety net).
"""

import os
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("TZ", "Asia/Shanghai")

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
STATE_PATH = HERMES_HOME / "STATE.md"
TRIGGER_CONTEXT_PATH = HERMES_HOME / ".proactive_chat_trigger_context"
LAST_SENT_PATH = HERMES_HOME / ".last_proactive_sent"

# If user chatted within this window, cancel proactive message
RECENT_CHAT_THRESHOLD_MINUTES = 5


def parse_state_last_update():
    """Parse last_update timestamp from STATE.md."""
    if not STATE_PATH.exists():
        return None
    content = STATE_PATH.read_text(encoding="utf-8")
    for line in content.split("\n"):
        if line.strip().startswith("last_update:"):
            ts_str = line.split(":", 1)[1].strip().strip("'\"")
            try:
                return datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                return None
    return None


def main():
    if not TRIGGER_CONTEXT_PATH.exists():
        print("SKIP: no_trigger_context")
        return

    # Double-check: if user just chatted, cancel proactive message
    last_update = parse_state_last_update()
    if last_update:
        minutes_since = (datetime.now() - last_update).total_seconds() / 60
        if minutes_since < RECENT_CHAT_THRESHOLD_MINUTES:
            print(f"SKIP: user_just_chatted ({minutes_since:.1f}min ago)")
            # Clean up trigger file
            try:
                TRIGGER_CONTEXT_PATH.unlink()
            except OSError:
                pass
            return

    # Read and output the context
    context = TRIGGER_CONTEXT_PATH.read_text(encoding="utf-8").strip()
    if not context:
        print("SKIP: empty_trigger_context")
        return

    # Output the context for the cron agent
    print(context)

    # Record that we sent
    LAST_SENT_PATH.write_text(datetime.now().isoformat())

    # Clean up trigger file so it doesn't re-fire
    try:
        TRIGGER_CONTEXT_PATH.unlink()
    except OSError:
        pass


if __name__ == "__main__":
    main()
