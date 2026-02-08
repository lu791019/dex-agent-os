#!/usr/bin/env python3
"""Extract today's Claude Code session conversations across all project directories.

Scans ~/.claude/projects/*//*.jsonl for sessions with activity on the target date,
extracts user and assistant text messages, and outputs a Markdown summary.

Usage:
    python3 ~/work-logs/scripts/extract-sessions.py [--date YYYY-MM-DD] [--exclude SESSION_ID]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"

# Size limits to avoid blowing up the context window
MAX_USER_MSG_CHARS = 2000
MAX_ASSISTANT_MSG_CHARS = 500
MAX_SESSION_CHARS = 5000
MAX_TOTAL_CHARS = 30000


def parse_args():
    parser = argparse.ArgumentParser(description="Extract today's Claude Code sessions")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Target date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="Session ID to exclude (e.g. current session)",
    )
    return parser.parse_args()


def parse_timestamp(ts_str):
    """Parse an ISO 8601 timestamp string to a datetime object."""
    if not ts_str:
        return None
    try:
        # Handle Z suffix and various formats
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def extract_user_text(message_obj):
    """Extract text from a user message, skipping tool_result content."""
    content = message_obj.get("content")
    if content is None:
        return None
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "tool_result":
                    continue
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
            elif isinstance(block, str):
                texts.append(block)
        result = "\n".join(texts).strip()
        return result if result else None
    return None


def extract_assistant_text(message_obj):
    """Extract text blocks from an assistant message, skipping thinking/tool_use."""
    content = message_obj.get("content")
    if content is None:
        return None
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "").strip()
                if text:
                    texts.append(text)
        result = "\n".join(texts).strip()
        return result if result else None
    return None


def truncate(text, max_len):
    """Truncate text to max_len characters, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def process_session_file(filepath, target_date, exclude_session_id):
    """Process a single JSONL session file.

    Returns a dict with session info and messages if the session has activity
    on the target date, or None otherwise.
    """
    session_id = filepath.stem
    if exclude_session_id and session_id == exclude_session_id:
        return None

    messages = []
    session_cwd = None
    first_ts = None
    last_ts = None
    has_today_activity = False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_type = obj.get("type")
                timestamp = parse_timestamp(obj.get("timestamp"))

                if timestamp is None:
                    continue

                # Check if this message is on the target date (in local time)
                local_ts = timestamp.astimezone()
                msg_date = local_ts.strftime("%Y-%m-%d")

                if msg_date != target_date:
                    continue

                has_today_activity = True

                # Track time range
                if first_ts is None or timestamp < first_ts:
                    first_ts = timestamp
                if last_ts is None or timestamp > last_ts:
                    last_ts = timestamp

                # Track cwd
                if session_cwd is None and obj.get("cwd"):
                    session_cwd = obj["cwd"]

                # Extract messages
                if msg_type == "user":
                    msg_obj = obj.get("message", {})
                    text = extract_user_text(msg_obj)
                    if text:
                        messages.append(
                            {
                                "role": "user",
                                "text": truncate(text, MAX_USER_MSG_CHARS),
                                "time": local_ts.strftime("%H:%M"),
                            }
                        )
                elif msg_type == "assistant":
                    msg_obj = obj.get("message", {})
                    text = extract_assistant_text(msg_obj)
                    if text:
                        messages.append(
                            {
                                "role": "assistant",
                                "text": truncate(text, MAX_ASSISTANT_MSG_CHARS),
                                "time": local_ts.strftime("%H:%M"),
                            }
                        )

    except (OSError, PermissionError) as e:
        print(f"Warning: cannot read {filepath}: {e}", file=sys.stderr)
        return None

    if not has_today_activity or not messages:
        return None

    return {
        "session_id": session_id,
        "cwd": session_cwd or "unknown",
        "first_ts": first_ts.astimezone().strftime("%H:%M") if first_ts else "?",
        "last_ts": last_ts.astimezone().strftime("%H:%M") if last_ts else "?",
        "messages": messages,
        "project_dir": filepath.parent.name,
    }


def format_session_markdown(session):
    """Format a single session as Markdown, respecting MAX_SESSION_CHARS."""
    lines = []
    header = (
        f"### Session: `{session['session_id'][:8]}...`\n"
        f"- **專案目錄:** `{session['project_dir']}`\n"
        f"- **工作目錄:** `{session['cwd']}`\n"
        f"- **時間範圍:** {session['first_ts']} ~ {session['last_ts']}\n"
    )
    lines.append(header)

    current_len = len(header)
    msg_count = 0

    for msg in session["messages"]:
        role_label = "👤 使用者" if msg["role"] == "user" else "🤖 助手"
        entry = f"\n**[{msg['time']}] {role_label}:**\n{msg['text']}\n"

        if current_len + len(entry) > MAX_SESSION_CHARS:
            lines.append(
                f"\n_(此 session 還有更多對話，已截斷以控制大小)_\n"
            )
            break

        lines.append(entry)
        current_len += len(entry)
        msg_count += 1

    return "".join(lines)


def main():
    args = parse_args()
    target_date = args.date
    exclude_session_id = args.exclude

    if not CLAUDE_PROJECTS_DIR.exists():
        print(f"Error: {CLAUDE_PROJECTS_DIR} does not exist", file=sys.stderr)
        sys.exit(1)

    # Scan all project directories for JSONL files
    jsonl_files = sorted(CLAUDE_PROJECTS_DIR.glob("*/*.jsonl"))

    if not jsonl_files:
        print("No session files found.", file=sys.stderr)
        sys.exit(0)

    sessions = []
    for filepath in jsonl_files:
        session = process_session_file(filepath, target_date, exclude_session_id)
        if session:
            sessions.append(session)

    if not sessions:
        print(f"# 今日 Claude Code 對話摘要 ({target_date})\n")
        print("今日無其他對話視窗的記錄。")
        sys.exit(0)

    # Sort sessions by first timestamp
    sessions.sort(key=lambda s: s["first_ts"])

    # Build output with total size control
    output_parts = []
    output_parts.append(f"# 今日 Claude Code 對話摘要 ({target_date})\n")
    output_parts.append(f"共找到 **{len(sessions)}** 個有活動的對話視窗。\n")

    total_len = sum(len(p) for p in output_parts)

    for i, session in enumerate(sessions):
        session_md = format_session_markdown(session)

        if total_len + len(session_md) > MAX_TOTAL_CHARS:
            output_parts.append(
                f"\n---\n_(還有 {len(sessions) - i} 個 session 未顯示，已達輸出大小上限)_\n"
            )
            break

        entry = f"\n---\n{session_md}"
        output_parts.append(entry)
        total_len += len(entry)

    print("".join(output_parts))


if __name__ == "__main__":
    main()
