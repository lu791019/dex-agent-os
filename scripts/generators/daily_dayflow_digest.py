#!/usr/bin/env python3
"""Dex Agent OS — Dayflow 活動摘要日記生成器

從 Dayflow SQLite 讀取 timeline cards + observations → 用 claude --print 整理 → 產出活動摘要日記。

Usage:
    python3 scripts/generators/daily_dayflow_digest.py [YYYY-MM-DD] [--force]
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# 將專案根目錄加入 sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import DAYFLOW_DB, JOURNAL_DIR, TEMPLATES_DIR
from lib.file_utils import ensure_dir, read_text, today_str
from lib.llm import ask_claude


SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責將 Dayflow 的螢幕活動記錄和 AI 觀察整理成一份活動摘要日記。

整理原則：
- 行為導向：不只列活動，要分析「你怎麼度過這一天」
- 誠實客觀：閒置就寫閒置，不美化
- 可行動：洞察要指向「明天可以怎麼調整」
- 合併碎片：將相似或連續的短活動合併為有意義的區段
- 使用繁體中文
"""


def query_timeline_cards(db_path: Path, date_str: str) -> list[dict]:
    """查詢指定日期的 timeline cards。"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        """
        SELECT start, end, title, summary, category, subcategory, detailed_summary
        FROM timeline_cards
        WHERE day = ? AND is_deleted = 0
        ORDER BY start_ts
        """,
        (date_str,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def query_observations(db_path: Path, date_str: str) -> list[dict]:
    """查詢指定日期的 observations。"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        """
        SELECT datetime(start_ts, 'unixepoch', 'localtime') as start_time,
               datetime(end_ts, 'unixepoch', 'localtime') as end_time,
               observation
        FROM observations
        WHERE date(start_ts, 'unixepoch', 'localtime') = ?
        ORDER BY start_ts
        """,
        (date_str,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def format_timeline_cards(cards: list[dict]) -> str:
    """將 timeline cards 格式化為 Markdown 文字。"""
    if not cards:
        return "（無 timeline cards 資料）"

    lines = ["| 時間 | 活動 | 分類 | 摘要 |", "|------|------|------|------|"]
    for card in cards:
        start = card["start"] or ""
        end = card["end"] or ""
        time_range = f"{start} - {end}" if start and end else start or end
        title = card["title"] or ""
        category = card["category"] or ""
        summary = card["summary"] or card["detailed_summary"] or ""
        # 截斷過長摘要
        if len(summary) > 100:
            summary = summary[:97] + "..."
        lines.append(f"| {time_range} | {title} | {category} | {summary} |")
    return "\n".join(lines)


def format_observations(observations: list[dict]) -> str:
    """將 observations 格式化為 Markdown 文字。"""
    if not observations:
        return "（無 observations 資料）"

    lines = []
    for obs in observations:
        start = obs["start_time"] or ""
        # 只取時間部分 HH:MM
        if start and len(start) > 10:
            start = start[11:16]
        text = obs["observation"] or ""
        lines.append(f"- [{start}] {text}")
    return "\n".join(lines)


def build_prompt(date_str: str, cards_text: str, obs_text: str, template_content: str) -> str:
    """組裝送給 LLM 的提示。"""
    return f"""\
請根據以下 Dayflow 螢幕活動記錄和 AI 觀察，產出一份活動摘要日記。

## 日期
{date_str}

## 輸出格式
請嚴格按照以下模板格式輸出，將佔位符替換為實際內容：

{template_content}

## 原始資料

### Timeline Cards（螢幕活動記錄）
{cards_text}

### Observations（AI 觀察）
{obs_text}

## 注意事項
- 「今日節奏」用一句話描述整天的工作節奏（例如「上午學習、下午開發、晚上規劃」）
- 「時間分布」按活動類別統計大約時間和佔比，只列有意義的類別
- 「活動時間軸」要合併碎片活動，去掉純閒置，呈現簡化有意義的時間軸
- 「AI 觀察摘要」從 observations 中提取有意義的行為模式，去重、合併相似觀察
- 「行為模式 & 洞察」跨活動分析模式（例如「頻繁切換視窗」「深度工作時段集中在晚上」）
- 「值得注意的事」列出異常行為、有趣發現、可以改進的習慣
- 不要留下任何佔位符，每個欄位都要填入實際內容
"""


def main():
    parser = argparse.ArgumentParser(description="產出 Dayflow 活動摘要日記")
    parser.add_argument(
        "date",
        nargs="?",
        default=today_str(),
        help="日期 YYYY-MM-DD（預設：今天）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="強制覆蓋已存在的日記",
    )
    args = parser.parse_args()

    date_str = args.date

    # 1. 檢查 Dayflow 資料庫
    if not DAYFLOW_DB.exists():
        print(f"[dayflow] Dayflow 資料庫不存在：{DAYFLOW_DB}")
        sys.exit(1)

    # 2. 查詢資料
    print(f"[dayflow] 查詢 {date_str} 的 Dayflow 資料...")

    cards = query_timeline_cards(DAYFLOW_DB, date_str)
    observations = query_observations(DAYFLOW_DB, date_str)

    print(f"[dayflow] Timeline cards: {len(cards)} 筆")
    print(f"[dayflow] Observations: {len(observations)} 筆")

    if not cards and not observations:
        print(f"[dayflow] {date_str} 無 Dayflow 記錄。")
        sys.exit(0)

    # 3. 格式化資料
    cards_text = format_timeline_cards(cards)
    obs_text = format_observations(observations)

    # 4. 讀取模板
    template_path = TEMPLATES_DIR / "dayflow-digest-template.md"
    template_content = read_text(template_path)

    if not template_content.strip():
        print(f"[dayflow] 警告：模板不存在 {template_path}，使用預設格式")
        template_content = "（使用預設格式輸出活動摘要）"

    # 5. 檢查輸出檔案
    output_path = JOURNAL_DIR / f"{date_str}-dayflow.md"
    if output_path.exists() and not args.force:
        print(f"[dayflow] 日記已存在：{output_path}")
        response = input("[dayflow] 覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[dayflow] 已取消。")
            sys.exit(0)

    # 6. 呼叫 LLM 整理
    prompt = build_prompt(date_str, cards_text, obs_text, template_content)
    print("[dayflow] 正在呼叫 claude --print 整理活動摘要...")

    digest_content = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 清理 LLM 回應：移除開頭的思考過程殘留（取 # 標題之前的部分丟棄）
    if digest_content and not digest_content.startswith("#"):
        marker = digest_content.find("\n#")
        if marker != -1:
            digest_content = digest_content[marker + 1:]

    # 7. 寫入檔案
    ensure_dir(JOURNAL_DIR)
    output_path.write_text(digest_content, encoding="utf-8")

    print(f"[dayflow] 活動摘要日記已產出：{output_path}")
    print(f"[dayflow] 長度：{len(digest_content)} 字元")


if __name__ == "__main__":
    main()
