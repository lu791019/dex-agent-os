#!/usr/bin/env python3
"""Meeting Notes — 從多種輸入來源產出會議筆記"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import MEETINGS_DIR, TEMPLATES_DIR, RULES_DIR
from lib.file_utils import ensure_dir, read_text, today_str, write_text
from lib.input_loader import add_input_args, load_input
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責從會議逐字稿或筆記產出結構化會議筆記。

輸出要求：
- 使用繁體中文
- 嚴格按照提供的模板結構輸出
- 萃取：討論要點、決策、行動項、後續追蹤
- 行動項格式：- [ ] {who} — {what} — {when}
- 討論要點需簡明扼要，抓住核心論點
- 決策要明確標記「決定了什麼」和「為什麼」

禁止：
- 不要捏造來源中沒有的資訊
- 不要加入主觀評論或建議（除非來源中有）
- 不要產出 YAML frontmatter，直接輸出會議筆記內容
- 不要遺漏重要的行動項或決策
"""


# ── 工具函式 ──────────────────────────────────────────

def _slugify(title: str) -> str:
    """將會議標題轉為 URL-safe slug。"""
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-").lower()
    if not slug:
        slug = "meeting"
    return slug


def _build_prompt(
    title: str,
    date: str,
    source_content: str,
    attendees: Optional[str],
    template: str,
    writing_rules: str,
) -> str:
    """組裝送給 LLM 的提示。"""
    prompt = f"""\
請根據以下來源內容，產出一份結構化的會議筆記。

## 會議標題
{title}

## 會議日期
{date}
"""

    if attendees:
        prompt += f"""
## 與會者
{attendees}
"""

    prompt += f"""
## 來源內容
{source_content}
"""

    if template:
        prompt += f"""
## 輸出模板（請依此結構輸出）
{template}
"""

    if writing_rules:
        prompt += f"""
## 寫作風格規則
{writing_rules}
"""

    prompt += """
## 注意事項
- 輸出完整會議筆記，含 H1 標題
- 行動項必須包含負責人、內容、期限
- 如果來源中沒有明確的期限或負責人，標記為「待確認」
- 討論要點按重要性排序
"""
    return prompt


def main():
    parser = argparse.ArgumentParser(description="Meeting Notes — 多來源 → 會議筆記")
    add_input_args(parser)
    parser.add_argument("--title", required=True, help="會議標題（必填）")
    parser.add_argument("--date", default=None, help="會議日期 YYYY-MM-DD（預設今天）")
    parser.add_argument("--attendees", default=None, help="與會者（選填，逗號分隔）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的筆記")
    args = parser.parse_args()

    date = args.date or today_str()

    # 1. 載入輸入內容
    source_content = load_input(args)

    # 2. 準備輸出路徑
    slug = _slugify(args.title)
    notes_dir = ensure_dir(MEETINGS_DIR / f"{date}-{slug}")
    notes_path = notes_dir / "notes.md"

    if notes_path.exists() and not args.force:
        response = input(f"[meeting-notes] {notes_path.name} 已存在，覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[meeting-notes] Cancelled.")
            sys.exit(0)

    # 3. 讀取參考資料
    template = read_text(TEMPLATES_DIR / "meeting-notes-template.md")
    writing_rules = read_text(RULES_DIR / "10-writing-style.md")

    # 4. LLM 產出
    print(f"[meeting-notes] Generating notes for '{args.title}'...")
    prompt = _build_prompt(args.title, date, source_content, args.attendees, template, writing_rules)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 5. 組裝 frontmatter + 內容
    attendees_line = f"\nattendees: {args.attendees}" if args.attendees else ""
    source_type = "transcript" if args.transcript else "notes" if args.notes else "google-doc" if args.google_doc else "fireflies"
    draft_content = f"""---
title: {args.title}
date: {date}
status: draft{attendees_line}
source: {source_type}
tags: [會議筆記]
---

{result.strip()}
"""

    # 6. 寫入
    write_text(notes_path, draft_content)
    print(f"[meeting-notes] Done: {notes_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
