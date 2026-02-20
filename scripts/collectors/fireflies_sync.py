#!/usr/bin/env python3
"""Fireflies Sync — Fireflies.ai 會議逐字稿批次匯入

使用方式：
  ./bin/agent fireflies-sync --list                    # 列出可用逐字稿
  ./bin/agent fireflies-sync --latest 3                # 匯入最新 3 筆
  ./bin/agent fireflies-sync --id abc123               # 匯入指定逐字稿

  輸出：200_Work/meetings/YYYY-MM-DD-<slug>/transcript.md
  無 LLM，直接結構化為 Markdown（含講者標記）

  注意：需要 Fireflies 付費方案 + API key
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import MEETINGS_DIR
from lib.file_utils import ensure_dir, write_text
from lib.fireflies_api import check_fireflies_setup, get_transcript, list_transcripts


# ── 工具函式 ──────────────────────────────────────────


def _slugify(title: str) -> str:
    """標題轉 slug（目錄名稱用）。"""
    text = re.sub(r"[^\w\s-]", "", title.lower())
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60].strip("-") or "untitled"


def _format_date(date_val) -> str:
    """Fireflies date → YYYY-MM-DD。

    Fireflies API 回傳的 date 可能是 epoch ms (int/str) 或 ISO 字串。
    """
    if date_val is None:
        return datetime.now().strftime("%Y-%m-%d")

    # epoch milliseconds（數字或數字字串）
    try:
        ts = int(date_val)
        # Fireflies 通常回傳 ms，若數值 > 10^12 視為 ms
        if ts > 1e12:
            ts = ts / 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        pass

    # ISO 字串
    if isinstance(date_val, str):
        return date_val[:10]

    return datetime.now().strftime("%Y-%m-%d")


def _format_duration(duration_val) -> str:
    """秒數 → 可讀時間（如 '45m 30s'）。"""
    if not duration_val:
        return "unknown"
    try:
        total = int(float(duration_val))
    except (ValueError, TypeError):
        return "unknown"

    if total < 60:
        return f"{total}s"
    minutes = total // 60
    seconds = total % 60
    if minutes < 60:
        return f"{minutes}m {seconds}s" if seconds else f"{minutes}m"
    hours = minutes // 60
    remaining_min = minutes % 60
    return f"{hours}h {remaining_min}m"


# ── 列出逐字稿 ───────────────────────────────────────


def cmd_list(args) -> None:
    """列出可用的逐字稿。"""
    transcripts = list_transcripts(limit=args.limit or 20)
    if not transcripts:
        print("[fireflies-sync] 沒有找到逐字稿")
        return

    print(f"\n[fireflies-sync] 找到 {len(transcripts)} 筆逐字稿：\n")
    print(f"  {'ID':<26} {'Date':<12} {'Duration':<10} Title")
    print(f"  {'─' * 26} {'─' * 12} {'─' * 10} {'─' * 30}")

    for t in transcripts:
        tid = t.get("id", "?")[:24]
        title = t.get("title", "Untitled")[:40]
        date = _format_date(t.get("date"))
        duration = _format_duration(t.get("duration"))
        print(f"  {tid:<26} {date:<12} {duration:<10} {title}")

    print(f"\n使用 --latest N 匯入最新 N 筆，或 --id <ID> 匯入指定逐字稿")


# ── 匯入單筆逐字稿 ────────────────────────────────────


def _save_transcript(transcript: dict, force: bool = False) -> Path | None:
    """將逐字稿存為 Markdown。

    輸出：200_Work/meetings/YYYY-MM-DD-<slug>/transcript.md
    """
    title = transcript.get("title", "Untitled")
    date_str = _format_date(transcript.get("date"))
    duration = _format_duration(transcript.get("duration"))
    participants = transcript.get("participants") or []
    sentences = transcript.get("sentences") or []
    transcript_id = transcript.get("id", "")

    slug = _slugify(title)
    meeting_dir = MEETINGS_DIR / f"{date_str}-{slug}"
    output_path = meeting_dir / "transcript.md"

    if output_path.exists() and not force:
        print(f"[fireflies-sync] SKIP: {output_path} 已存在（加 --force 覆蓋）")
        return None

    # 組裝 frontmatter
    participants_str = ", ".join(participants) if participants else "unknown"
    frontmatter = f"""---
source: fireflies
transcript_id: "{transcript_id}"
title: "{title}"
date: {date_str}
duration: "{duration}"
participants: [{participants_str}]
---"""

    # 組裝 body
    body_lines = [
        f"# {title}",
        "",
        f"> Date: {date_str}  ",
        f"> Duration: {duration}  ",
        f"> Participants: {participants_str}",
        "",
        "## Transcript",
        "",
    ]

    if sentences:
        for s in sentences:
            speaker = s.get("speaker_name", "Unknown")
            text = s.get("text", "") or s.get("raw_text", "")
            if text:
                body_lines.append(f"**{speaker}:** {text}")
                body_lines.append("")
    else:
        body_lines.append("_No transcript sentences available._")
        body_lines.append("")

    content = frontmatter + "\n\n" + "\n".join(body_lines)

    ensure_dir(meeting_dir)
    write_text(output_path, content)
    return output_path


# ── 指令：匯入最新 N 筆 ──────────────────────────────


def cmd_latest(args) -> None:
    """匯入最新 N 筆逐字稿。"""
    n = args.latest
    print(f"[fireflies-sync] 正在取得最新 {n} 筆逐字稿...")

    transcripts = list_transcripts(limit=n)
    if not transcripts:
        print("[fireflies-sync] 沒有找到逐字稿")
        return

    imported = 0
    skipped = 0

    for t in transcripts:
        tid = t.get("id")
        title = t.get("title", "Untitled")

        # 列出的資料不含 sentences，需逐筆取完整資料
        full = get_transcript(tid)
        if not full:
            print(f"[fireflies-sync] SKIP: 無法取得 {title}")
            skipped += 1
            continue

        path = _save_transcript(full, force=args.force)
        if path:
            print(f"[fireflies-sync] Saved: {path}")
            imported += 1
        else:
            skipped += 1

    print(f"\n[fireflies-sync] 完成：匯入 {imported} 筆，跳過 {skipped} 筆")


# ── 指令：匯入指定 ID ────────────────────────────────


def cmd_id(args) -> None:
    """匯入指定 ID 的逐字稿。"""
    transcript_id = args.id
    print(f"[fireflies-sync] 正在取得逐字稿 ID: {transcript_id}...")

    transcript = get_transcript(transcript_id)
    if not transcript:
        print(f"[fireflies-sync] 找不到逐字稿 ID: {transcript_id}", file=sys.stderr)
        return

    path = _save_transcript(transcript, force=args.force)
    if path:
        print(f"[fireflies-sync] Saved: {path}")
    else:
        print("[fireflies-sync] 跳過（檔案已存在，加 --force 覆蓋）")


# ── 主程式 ────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Fireflies Sync — 會議逐字稿批次匯入"
    )
    parser.add_argument("--list", action="store_true", help="列出可用逐字稿")
    parser.add_argument("--latest", type=int, default=0, help="匯入最新 N 筆逐字稿")
    parser.add_argument("--id", type=str, default=None, help="匯入指定 ID 的逐字稿")
    parser.add_argument("--limit", type=int, default=20, help="--list 時的列出上限（預設 20）")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的檔案")

    args = parser.parse_args()

    # 檢查 API key
    if not check_fireflies_setup():
        sys.exit(1)

    # 分派指令
    if args.list:
        cmd_list(args)
    elif args.latest > 0:
        cmd_latest(args)
    elif args.id:
        cmd_id(args)
    else:
        # 預設：列出
        cmd_list(args)


if __name__ == "__main__":
    main()
