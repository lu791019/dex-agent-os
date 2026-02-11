#!/usr/bin/env python3
"""Podcast Digest — 週度消化報告（合併 YouTube + Podcast episodes）

使用方式：
  ./bin/agent podcast-digest                    # 本週
  ./bin/agent podcast-digest 2026-02-10         # 指定日期所在週
  ./bin/agent podcast-digest --pptx             # 同時產出簡報
  ./bin/agent podcast-digest --force            # 強制覆蓋
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import (
    PODCAST_EPISODES_DIR,
    PODCAST_WEEKLY_DIR,
    PRESENTATIONS_DIR,
    TEMPLATES_DIR,
    YOUTUBE_DIR,
)
from lib.file_utils import ensure_dir, read_text, week_date_range, write_text
from lib.llm import ask_claude


# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 助理，負責產出每週的 Podcast & YouTube 消化報告。

你需要做的：
- 從本週所有 episode 筆記中，提煉一份整合性的週度消化報告
- 跨集辨識共同趨勢和主題
- 挑出最值得記住的洞察
- 標出可轉化為內容的素材

輸出規則：
- 使用繁體中文
- 嚴格按照指定的模板格式輸出
- 只輸出報告內容，不要加額外說明
- 「本週一句話」要有衝擊力，不超過 30 字
"""

PPTX_SYSTEM_PROMPT = """\
你是簡報內容策劃師。根據 Podcast 週度消化報告，產出簡報的結構化內容。

輸出規則：
- 使用繁體中文
- 嚴格按照簡報模板格式輸出
- 每頁 Slide 的內容要精簡有力
- 用條列式，每點不超過 2 行
"""


# ── 素材收集 ──────────────────────────────────────────

def collect_episodes(start_date: str, end_date: str) -> list[tuple[str, str, str]]:
    """收集日期範圍內的 Podcast episode 筆記。回傳 [(filename, source_type, content)]。"""
    results = []
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # Podcast episodes
    if PODCAST_EPISODES_DIR.exists():
        for f in sorted(PODCAST_EPISODES_DIR.glob("*.md")):
            if f.name == ".gitkeep":
                continue
            # 從檔名取日期 YYYY-MM-DD-slug.md
            date_part = f.name[:10]
            try:
                file_date = datetime.strptime(date_part, "%Y-%m-%d")
            except ValueError:
                continue
            if start <= file_date <= end:
                content = read_text(f)
                if content.strip():
                    results.append((f.name, "podcast", content))

    # YouTube notes
    if YOUTUBE_DIR.exists():
        for f in sorted(YOUTUBE_DIR.glob("*.md")):
            if f.name == ".gitkeep":
                continue
            date_part = f.name[:10]
            try:
                file_date = datetime.strptime(date_part, "%Y-%m-%d")
            except ValueError:
                continue
            if start <= file_date <= end:
                content = read_text(f)
                if content.strip():
                    results.append((f.name, "youtube", content))

    return results


# ── Prompt 組裝 ──────────────────────────────────────

def build_digest_prompt(
    episodes: list[tuple[str, str, str]],
    template: str,
    year: int,
    iso_week: int,
    week_range: str,
) -> str:
    """組裝週度消化報告的 prompt。"""
    episode_section = ""
    for filename, source_type, content in episodes:
        label = "🎧 Podcast" if source_type == "podcast" else "📺 YouTube"
        episode_section += f"\n### [{label}] {filename}\n{content}\n"

    return f"""\
請根據以下本週的 Podcast & YouTube episode 筆記，產出一份週度消化報告。

## 基本資訊
- 年份：{year}
- ISO 週數：W{iso_week:02d}
- 日期範圍：{week_range}
- 本週共 {len(episodes)} 集（{sum(1 for _, t, _ in episodes if t == 'podcast')} Podcast + {sum(1 for _, t, _ in episodes if t == 'youtube')} YouTube）

## Episode 筆記
{episode_section}

## 輸出格式
請嚴格按照以下模板格式輸出（替換 {{{{佔位符}}}} 為實際內容）：

{template}

## 注意事項
- 「本週聽了/看了什麼」用列表呈現，標註來源類型（🎧 / 📺）
- 「市場趨勢觀察」要跨集歸納，找出 2-3 個共同趨勢
- 「內容種子」標註適合的頻道（Threads / Newsletter / 簡報）
- 用 {{YEAR}}, {{WEEK}}, {{WEEK_RANGE}} 的實際值替換
"""


def build_pptx_prompt(digest_content: str, pptx_template: str, week_range: str) -> str:
    """組裝簡報內容的 prompt。"""
    return f"""\
請根據以下 Podcast 週度消化報告，產出簡報的結構化內容。

## 消化報告
{digest_content}

## 日期範圍
{week_range}

## 簡報結構
請按照以下模板輸出：

{pptx_template}

## 注意事項
- 每頁 Slide 用 ## 標題區隔
- 內容用條列式，每點簡潔有力
- 趨勢觀察頁要標註來源 episode
"""


# ── 主程式 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Podcast Digest — 週度消化報告")
    parser.add_argument("date", nargs="?", default=None, help="該週任一天 (YYYY-MM-DD)")
    parser.add_argument("--pptx", action="store_true", help="同時產出簡報內容")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的報告")
    args = parser.parse_args()

    # 1. 計算週日期範圍
    start, end, iso_week, _ = week_date_range(args.date)
    year = datetime.strptime(start, "%Y-%m-%d").year
    week_range = f"{start} ~ {end}"

    # 2. 收集素材
    episodes = collect_episodes(start, end)
    if not episodes:
        print(f"[podcast-digest] 找不到 {week_range} 的任何 episode 筆記", file=sys.stderr)
        print("[podcast-digest] 請先用 youtube-add 或 podcast-add 新增 episode", file=sys.stderr)
        sys.exit(1)

    podcast_count = sum(1 for _, t, _ in episodes if t == "podcast")
    youtube_count = sum(1 for _, t, _ in episodes if t == "youtube")
    print(f"[podcast-digest] {year} W{iso_week:02d}（{week_range}）")
    print(f"[podcast-digest] 找到 {len(episodes)} 集（{podcast_count} Podcast + {youtube_count} YouTube）")

    # 3. 檢查輸出
    output_path = PODCAST_WEEKLY_DIR / f"{year}-W{iso_week:02d}-podcast-digest.md"
    if output_path.exists() and not args.force:
        print(f"[podcast-digest] {output_path.name} 已存在，使用 --force 覆蓋", file=sys.stderr)
        sys.exit(1)

    # 4. 讀取模板
    template = read_text(TEMPLATES_DIR / "podcast-digest-template.md")

    # 5. LLM 產出消化報告
    print("[podcast-digest] Generating weekly digest...")
    prompt = build_digest_prompt(episodes, template, year, iso_week, week_range)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 清理
    if result and not result.startswith("#"):
        pos = result.find("# ")
        if pos != -1:
            result = result[pos:]

    ensure_dir(PODCAST_WEEKLY_DIR)
    write_text(output_path, result.strip() + "\n")
    print(f"[podcast-digest] Done: {output_path.relative_to(ROOT_DIR)}")

    # 6. 簡報產出（可選）
    if args.pptx:
        print("[podcast-digest] Generating presentation content...")
        pptx_template = read_text(TEMPLATES_DIR / "podcast-pptx-template.md")
        pptx_prompt = build_pptx_prompt(result, pptx_template, week_range)
        pptx_result = ask_claude(user_prompt=pptx_prompt, system_prompt=PPTX_SYSTEM_PROMPT)

        pptx_md_path = PRESENTATIONS_DIR / f"{year}-W{iso_week:02d}-market-trends.md"
        ensure_dir(PRESENTATIONS_DIR)
        write_text(pptx_md_path, pptx_result.strip() + "\n")
        print(f"[podcast-digest] Presentation content: {pptx_md_path.relative_to(ROOT_DIR)}")
        print("[podcast-digest] 提示：用 /pptx skill 將 .md 轉為 .pptx 簡報")


if __name__ == "__main__":
    main()
