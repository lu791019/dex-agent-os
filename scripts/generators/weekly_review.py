#!/usr/bin/env python3
"""Weekly Review — 產出個人週回顧"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import JOURNAL_DIR, WEEKLY_DIR, TEMPLATES_DIR
from lib.file_utils import ensure_dir, read_text, week_date_range, write_text
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 助理，負責週度回顧。

你的任務是從 7 天的日記中提煉出一份結構化的週回顧。

你需要做的：
- 辨識本週完成了哪些重要事項
- 提煉學到的關鍵知識和技能
- 找出跨天重複出現的模式和趨勢
- 誠實記錄卡住的地方和尚未解決的問題
- 根據本週的節奏和能量分布，建議下週的重點

輸出規則：
- 使用繁體中文
- 不雞湯、不空泛，要有具體的觀察和建議
- 嚴格按照指定的模板格式輸出
- 只輸出週回顧內容，不要加任何額外說明
"""


# ── 素材收集 ──────────────────────────────────────────

def collect_journals(start_date: str, end_date: str) -> list[tuple[str, str]]:
    """收集日期範圍內的 L2 日記。"""
    results = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        path = JOURNAL_DIR / f"{date_str}.md"
        content = read_text(path)
        if content.strip():
            results.append((date_str, content))
        current += timedelta(days=1)
    return results


def collect_dayflows(start_date: str, end_date: str) -> list[tuple[str, str]]:
    """收集日期範圍內的 Dayflow 摘要。"""
    results = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        path = JOURNAL_DIR / f"{date_str}-dayflow.md"
        content = read_text(path)
        if content.strip():
            results.append((date_str, content))
        current += timedelta(days=1)
    return results


# ── Prompt 組裝 ──────────────────────────────────────

def build_prompt(
    journals: list[tuple[str, str]],
    dayflows: list[tuple[str, str]],
    template: str,
    year: int,
    iso_week: int,
    week_range: str,
) -> str:
    """組裝送給 LLM 的提示。"""
    journal_section = ""
    for date_str, content in journals:
        journal_section += f"\n### {date_str}\n{content}\n"

    dayflow_section = ""
    for date_str, content in dayflows:
        dayflow_section += f"\n### {date_str}\n{content}\n"

    prompt = f"""\
請根據以下 7 天的日記資料，產出一份週回顧。

## 基本資訊
- 年份：{year}
- ISO 週數：W{iso_week:02d}
- 日期範圍：{week_range}

## L2 精煉日記
{journal_section if journal_section else "（本週無 L2 日記）"}

## Dayflow 活動摘要
{dayflow_section if dayflow_section else "（本週無 Dayflow 摘要）"}

## 輸出格式
請嚴格按照以下模板格式輸出（替換 {{{{佔位符}}}} 為實際內容）：

{template}

## 注意事項
- 「本週一句話」用一句話總結本週最重要的收穫或感受
- 「完成了什麼」列出具體事項，不要只寫「工作」
- 「本週數據」量化可量化的（幾天寫日記、幾篇文章、幾個 commit 等）
- 「模式與趨勢」觀察跨天重複出現的主題或行為模式
- 「能量曲線」描述一週中能量高低的分布，什麼時候最有生產力
- 用 {{YEAR}}, {{WEEK}}, {{WEEK_RANGE}} 的實際值替換
"""
    return prompt


# ── 主程式 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Weekly Review — 產出週回顧")
    parser.add_argument("date", nargs="?", default=None, help="該週任一天 (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的週回顧")
    args = parser.parse_args()

    # 1. 計算週日期範圍
    start, end, iso_week, _ = week_date_range(args.date)
    year = datetime.strptime(start, "%Y-%m-%d").year
    week_range = f"{start} ~ {end}"

    # 2. 收集素材
    journals = collect_journals(start, end)
    dayflows = collect_dayflows(start, end)

    if not journals and not dayflows:
        print(f"[weekly-review] 找不到 {week_range} 的任何日記", file=sys.stderr)
        sys.exit(1)

    print(f"[weekly-review] {year} W{iso_week:02d}（{week_range}）")
    print(f"[weekly-review] 找到 {len(journals)} 篇 L2 日記 + {len(dayflows)} 篇 Dayflow 摘要")

    # 3. 檢查輸出
    output_path = WEEKLY_DIR / f"{year}-W{iso_week:02d}.md"
    if output_path.exists() and not args.force:
        print(f"[weekly-review] {output_path.name} 已存在，使用 --force 覆蓋", file=sys.stderr)
        sys.exit(1)

    # 4. 讀取模板
    template = read_text(TEMPLATES_DIR / "weekly-review-template.md")

    # 5. LLM 產出
    print("[weekly-review] Generating weekly review...")
    prompt = build_prompt(journals, dayflows, template, year, iso_week, week_range)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 6. 清理 — 確保以標題開頭
    if result and not result.startswith("#"):
        heading_pos = result.find("# ")
        if heading_pos != -1:
            result = result[heading_pos:]

    # 7. 寫入
    ensure_dir(WEEKLY_DIR)
    write_text(output_path, result.strip() + "\n")
    print(f"[weekly-review] Done: {output_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
