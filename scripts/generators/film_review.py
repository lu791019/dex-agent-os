#!/usr/bin/env python3
"""Film Review — 從電影名稱和觀影筆記產出影評"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import FILM_REVIEWS_DIR, STYLE_DNA_DIR, RULES_DIR
from lib.file_utils import ensure_dir, read_text, today_str, write_text
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責撰寫影評。

影評風格要求：
- 結構：一句話短評 → 劇情概述（不劇透核心轉折）→ 觀點分析 → 推薦指數
- 長度：500-1000 字
- 語氣：個人化，有洞察，像跟朋友聊一部剛看完的電影
- 可以連結到自身經驗或生活感悟
- 有明確立場，不是平鋪直敘的劇情摘要

禁止：
- 不劇透核心劇情轉折
- 不假裝看過沒看過的電影
- 不過度使用專業影評術語
- 不雞湯
- 不空泛讚美

輸出規則：
- 使用繁體中文
- 輸出完整影評，包含 H1 標題
- 不要加 YAML frontmatter，直接輸出影評內容
"""


# ── 工具函式 ──────────────────────────────────────────

def _slugify(title: str) -> str:
    """將電影名稱轉為 URL-safe slug。"""
    # 移除標點符號，保留中文和英數
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-").lower()
    # 如果全是中文，直接用
    if not slug:
        slug = "film"
    return slug


def _build_prompt(title: str, notes: str, rating: Optional[int], style_dna: str, writing_rules: str) -> str:
    """組裝送給 LLM 的提示。"""
    prompt = f"""\
請為以下電影撰寫一篇影評。

## 電影名稱
{title}
"""

    if notes:
        prompt += f"""
## 觀影筆記
{notes}
"""

    if rating is not None:
        prompt += f"""
## 評分
{rating}/10
"""

    if style_dna:
        prompt += f"""
## 風格 DNA（請優先遵循這些具體模式）
{style_dna}
"""

    if writing_rules:
        prompt += f"""
## 寫作風格規則
{writing_rules}
"""

    prompt += """
## 注意事項
- 輸出完整影評，含 H1 標題
- 500-1000 字
- 不劇透核心轉折
- 有個人觀點，不只是劇情摘要
"""
    return prompt


def main():
    parser = argparse.ArgumentParser(description="Film Review — 電影名稱 + 筆記 → 影評")
    parser.add_argument("--title", required=True, help="電影名稱（必填）")
    parser.add_argument("--notes", default="", help="觀影筆記（選填）")
    parser.add_argument("--rating", type=int, default=None, choices=range(1, 11),
                        metavar="N", help="評分 1-10（選填）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的影評")
    args = parser.parse_args()

    # 1. 準備輸出路徑
    date = today_str()
    slug = _slugify(args.title)
    review_dir = ensure_dir(FILM_REVIEWS_DIR / date)
    review_path = review_dir / f"{slug}.md"

    if review_path.exists() and not args.force:
        response = input(f"[film-review] {review_path.name} 已存在，覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[film-review] Cancelled.")
            sys.exit(0)

    # 2. 讀取參考資料
    style_dna = read_text(STYLE_DNA_DIR / "film-review-dna.md")
    writing_rules = read_text(RULES_DIR / "10-writing-style.md")

    # 3. LLM 產出
    print(f"[film-review] Generating review for '{args.title}'...")
    prompt = _build_prompt(args.title, args.notes, args.rating, style_dna, writing_rules)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 4. 組裝 frontmatter + 內容
    rating_line = f"\nrating: {args.rating}" if args.rating is not None else ""
    draft_content = f"""---
title: {args.title}
status: draft{rating_line}
created: {date}
tags: [影評]
---

{result.strip()}
"""

    # 5. 寫入
    write_text(review_path, draft_content)
    print(f"[film-review] Done: {review_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
