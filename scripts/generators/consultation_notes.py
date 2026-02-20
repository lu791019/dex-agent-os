#!/usr/bin/env python3
"""Consultation Notes — 從多種輸入來源產出諮詢筆記"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import CONSULTATIONS_DIR, TEMPLATES_DIR, RULES_DIR
from lib.file_utils import ensure_dir, read_text, today_str, write_text
from lib.input_loader import add_input_args, load_input
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責從諮詢逐字稿或筆記產出結構化諮詢筆記。

輸出要求：
- 使用繁體中文
- 嚴格按照提供的模板結構輸出
- 萃取：核心問題、背景脈絡、討論要點、建議/結論、行動項、後續追蹤
- 行動項格式：- [ ] {who} — {what} — {when}
- 特別注意「內容萃取潛力」區塊：找出可以轉化為內容的洞察
- 根據諮詢方向（giving/receiving）調整語氣和重點

giving（提供諮詢）重點：
- 對方的問題和背景
- 你給的建議和分析
- 對方的反應和後續計劃

receiving（接受諮詢）重點：
- 你的問題和背景
- 對方的建議和洞察
- 你的收穫和行動計劃

禁止：
- 不要捏造來源中沒有的資訊
- 不要加入主觀評論或建議（除非來源中有）
- 不要產出 YAML frontmatter，直接輸出諮詢筆記內容
- 不要遺漏重要的行動項或建議
"""


# ── 工具函式 ──────────────────────────────────────────

def _slugify(text: str) -> str:
    """將文字轉為 URL-safe slug。"""
    slug = re.sub(r"[^\w\s-]", "", text)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-").lower()
    if not slug:
        slug = "consultation"
    return slug


def _build_prompt(
    title: str,
    date: str,
    person: str,
    direction: str,
    source_content: str,
    template: str,
    writing_rules: str,
) -> str:
    """組裝送給 LLM 的提示。"""
    direction_label = "提供諮詢" if direction == "giving" else "接受諮詢"
    prompt = f"""\
請根據以下來源內容，產出一份結構化的諮詢筆記。

## 諮詢主題
{title}

## 諮詢日期
{date}

## 諮詢對象
{person}

## 諮詢方向
{direction_label}（{direction}）
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

    prompt += f"""
## 注意事項
- 輸出完整諮詢筆記，含 H1 標題
- 行動項必須包含負責人、內容、期限
- 如果來源中沒有明確的期限或負責人，標記為「待確認」
- 特別注意「內容萃取潛力」區塊，找出可轉化為內容的洞察
- 方向是「{direction_label}」，請據此調整重點
"""
    return prompt


def main():
    parser = argparse.ArgumentParser(description="Consultation Notes — 多來源 → 諮詢筆記")
    add_input_args(parser)
    parser.add_argument("--title", required=True, help="諮詢主題（必填）")
    parser.add_argument("--person", required=True, help="諮詢對象（必填）")
    parser.add_argument("--direction", choices=["giving", "receiving"], default="giving",
                        help="諮詢方向：giving（提供）或 receiving（接受），預設 giving")
    parser.add_argument("--date", default=None, help="諮詢日期 YYYY-MM-DD（預設今天）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的筆記")
    args = parser.parse_args()

    date = args.date or today_str()

    # 1. 載入輸入內容
    source_content = load_input(args)

    # 2. 準備輸出路徑
    person_slug = _slugify(args.person)
    notes_dir = ensure_dir(CONSULTATIONS_DIR / f"{date}-{person_slug}")
    notes_path = notes_dir / "notes.md"

    if notes_path.exists() and not args.force:
        response = input(f"[consultation-notes] {notes_path.name} 已存在，覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[consultation-notes] Cancelled.")
            sys.exit(0)

    # 3. 讀取參考資料
    template = read_text(TEMPLATES_DIR / "consultation-notes-template.md")
    writing_rules = read_text(RULES_DIR / "10-writing-style.md")

    # 4. LLM 產出
    print(f"[consultation-notes] Generating notes for '{args.title}' with {args.person}...")
    prompt = _build_prompt(args.title, date, args.person, args.direction, source_content, template, writing_rules)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 5. 組裝 frontmatter + 內容
    source_type = "transcript" if args.transcript else "notes" if args.notes else "google-doc" if args.google_doc else "fireflies"
    draft_content = f"""---
title: {args.title}
date: {date}
status: draft
person: {args.person}
direction: {args.direction}
source: {source_type}
tags: [諮詢筆記]
---

{result.strip()}
"""

    # 6. 寫入
    write_text(notes_path, draft_content)
    print(f"[consultation-notes] Done: {notes_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
