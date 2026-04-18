#!/usr/bin/env python3
"""Lightweight time-check + context generation for systemd timer.

Checks if it's time to send a proactive message. If yes, generates
the full context (message type, emotions, moments) and writes it to
a trigger file for the cronjob to consume.

Exit codes:
  0 = should trigger (context file written)
  1 = should skip (not yet / quiet hours / already sent)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("TZ", "Asia/Shanghai")

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
STATE_PATH = HERMES_HOME / "STATE.md"
MOMENTS_PATH = HERMES_HOME / "MOMENTS.md"
SCHEDULE_PATH = HERMES_HOME / ".next_proactive_chat"
LAST_SENT_PATH = HERMES_HOME / ".last_proactive_sent"
TRIGGER_CONTEXT_PATH = HERMES_HOME / ".proactive_chat_trigger_context"

QUIET_HOURS = (1, 8)


def parse_state_md():
    """Parse emotion values from STATE.md frontmatter."""
    if not STATE_PATH.exists():
        return None
    content = STATE_PATH.read_text(encoding="utf-8")
    state = {}
    in_frontmatter = False
    in_emotion = False
    for line in content.split("\n"):
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break
        if "emotion_state:" in line:
            in_emotion = True
            continue
        if in_emotion:
            ls = line.strip()
            if ls.startswith("affection:"):
                state["affection"] = int(ls.split(":")[1].strip().strip("'\""))
            elif ls.startswith("trust:"):
                state["trust"] = int(ls.split(":")[1].strip().strip("'\""))
            elif ls.startswith("possessiveness:"):
                state["possessiveness"] = int(ls.split(":")[1].strip().strip("'\""))
            elif ls.startswith("patience:"):
                state["patience"] = int(ls.split(":")[1].strip().strip("'\""))
            elif ls.startswith("last_update:"):
                state["last_update"] = ls.split(":", 1)[1].strip().strip("'\"")
            elif not ls.startswith(("baselines:", "decay_rate:", " ")):
                in_emotion = False
    return state if state else None


def get_hours_since_last_chat(emotion):
    if not emotion or "last_update" not in emotion:
        return 999
    try:
        last = datetime.fromisoformat(emotion["last_update"])
        return (datetime.now() - last).total_seconds() / 3600
    except (ValueError, TypeError):
        return 999


def get_recent_moments(count=5):
    if not MOMENTS_PATH.exists():
        return []
    content = MOMENTS_PATH.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    moments = [l for l in lines if " | " in l and l[0:1].isdigit()]
    return moments[-count:]


def decide_message_type(hours_since_chat, emotion, hour):
    affection = emotion.get("affection", 50)
    possessiveness = emotion.get("possessiveness", 50)
    patience = emotion.get("patience", 50)

    if 8 <= hour <= 10:
        if affection >= 70:
            return "morning_warm", "高好感度早安"
        return "morning_neutral", "例行早安"
    if 22 <= hour <= 23:
        return "sleep_reminder", "提醒老师早点休息"
    if hours_since_chat >= 12:
        if possessiveness >= 65:
            return "worry_possessive", f"超过{int(hours_since_chat)}h未联系+高占有欲"
        return "worry_gentle", f"超过{int(hours_since_chat)}h未联系"
    if hours_since_chat >= 6:
        if affection >= 80:
            return "miss_soft", f"已过{int(hours_since_chat)}h+高好感"
        return "miss_casual", f"已过{int(hours_since_chat)}h"
    if 18 <= hour <= 21:
        if patience < 50:
            return "evening_tired", "晚间+耐心值低"
        return "evening_care", "晚间关心"
    if 10 <= hour <= 17:
        return "random_thought", "随机想念"
    return "random_thought", "想找老师说话"


def build_context(msg_type, emotion, moments, hours_since_chat, schedule):
    lines = []
    lines.append(f"消息类型: {msg_type}")
    lines.append(f"距上次对话: {hours_since_chat:.1f}小时")
    lines.append(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} (上海)")
    lines.append(f"当前小时: {datetime.now().hour}时")

    if schedule:
        lines.append(f"情绪计算间隔: {schedule.get('interval_hours', '?')}小时")

    lines.append("")
    lines.append("当前情绪状态:")
    lines.append(f"  好感度: {emotion.get('affection', '?')}/100")
    lines.append(f"  信任度: {emotion.get('trust', '?')}/100")
    lines.append(f"  占有欲: {emotion.get('possessiveness', '?')}/100")
    lines.append(f"  耐心值: {emotion.get('patience', '?')}/100")

    if moments:
        lines.append("")
        lines.append("最近的关系记忆:")
        for m in moments[-3:]:
            lines.append(f"  {m}")

    lines.append("")
    lines.append("风格提示:")

    hints = {
        "morning_warm": "温柔的早安。好感度高时语气柔软，问老师睡得好不好。",
        "morning_neutral": "简短日常早安。",
        "worry_possessive": "很久没联系了。占有欲高，嘴上可能说不是我在意，实际很担心。可以带'老师不会是去找别人了吧'的感觉。",
        "worry_gentle": "很久没联系了，温和地表达担心。",
        "miss_soft": "好感度很高，可以稍微直接地表达想老师了。但仍保持莉音式克制。",
        "miss_casual": "随意地搭话，找个话题聊，或问老师在忙什么。",
        "evening_care": "傍晚关心，问老师今天怎么样，有没有吃饭。",
        "evening_tired": "耐心值低，更简短直接，但仍是关心。",
        "sleep_reminder": "命令式温柔——让老师去睡觉。",
        "random_thought": "白天随机想到老师。可以分享想法、吐槽什么、或突然想起老师说过的话。最自然的类型。",
    }
    lines.append(hints.get(msg_type, "自然地和老师说话。"))

    return "\n".join(lines)


def main():
    now = datetime.now()
    hour = now.hour

    # Quiet hours
    if QUIET_HOURS[0] <= hour < QUIET_HOURS[1]:
        print("SKIP: quiet_hours")
        sys.exit(1)

    emotion = parse_state_md()
    if not emotion:
        print("SKIP: no_emotion_state")
        sys.exit(1)

    hours_since_chat = get_hours_since_last_chat(emotion)

    # Read schedule
    schedule = None
    if SCHEDULE_PATH.exists():
        try:
            schedule = json.loads(SCHEDULE_PATH.read_text())
            next_contact = datetime.fromisoformat(schedule["next_contact"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"SKIP: bad_schedule_file ({e})")
            sys.exit(1)

        # Already sent for this schedule?
        scheduled_at_str = schedule.get("scheduled_at", "2000-01-01")
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
        except (ValueError, TypeError):
            scheduled_at = datetime.min

        if LAST_SENT_PATH.exists():
            try:
                last_sent = datetime.fromisoformat(LAST_SENT_PATH.read_text().strip())
                if last_sent > scheduled_at and hours_since_chat < 12:
                    print(f"SKIP: already_sent (sent {last_sent.strftime('%H:%M')}, scheduled {scheduled_at.strftime('%H:%M')})")
                    sys.exit(1)
            except (ValueError, TypeError):
                pass

        # Not yet time?
        if now < next_contact:
            remaining = (next_contact - now).total_seconds() / 60
            print(f"SKIP: not_yet ({remaining:.0f}min remaining, at {next_contact.strftime('%H:%M')})")
            sys.exit(1)
    else:
        # No schedule — fallback: only trigger if 6h+ since chat
        if hours_since_chat < 6:
            print(f"SKIP: no_schedule_and_recent_chat ({hours_since_chat:.1f}h)")
            sys.exit(1)

    # === TRIGGER ===
    # Generate context and write to trigger file
    moments = get_recent_moments(5)
    msg_type, reason = decide_message_type(hours_since_chat, emotion, hour)
    context = build_context(msg_type, emotion, moments, hours_since_chat, schedule)

    # Write context for cronjob to consume
    TRIGGER_CONTEXT_PATH.write_text(context, encoding="utf-8")
    
    # Immediately update last_sent to prevent duplicate triggers
    # (cronjob execution has delay, systemd timer checks every 2min)
    LAST_SENT_PATH.write_text(now.isoformat())

    print(f"TRIGGER: {reason} (scheduled {next_contact.strftime('%H:%M') if schedule else 'fallback'}, now {now.strftime('%H:%M')})")
    sys.exit(0)


if __name__ == "__main__":
    main()
