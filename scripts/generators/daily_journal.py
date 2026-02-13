#!/usr/bin/env python3
"""Dex Agent OS — 每日精煉日記生成器

讀取 L1 工作日誌（+ Dayflow 活動摘要，如存在）→ 用 claude --print 提煉 → 產出 L2 精煉日記。

Usage:
    python3 scripts/generators/daily_journal.py [YYYY-MM-DD]
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# 將專案根目錄加入 sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import JOURNAL_DIR, TEMPLATES_DIR
from lib.file_utils import ensure_dir, read_text, today_str, work_log_path
from lib.llm import ask_claude


SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責將詳細的工作日誌（L1）和 Dayflow 活動摘要提煉成簡潔的每日精煉日記（L2）。

提煉原則：
- 簡潔：L2 是 L1 的 1/3~1/5 長度
- 洞察導向：不只記錄做了什麼，更要抓出「值得深入的想法」
- 內容潛力：每條洞察標註適合轉化的頻道（Threads / Newsletter / Blog）
- 行為洞察：如果有 Dayflow 活動摘要，將其中的行為模式、時間分布洞察融入日記（特別是「行為模式 & 洞察」和「值得注意的事」）
- 誠實：能量和狀態要從工作量和卡關程度如實推測，不美化
- 使用繁體中文
"""


def build_prompt(
    date_str: str,
    work_log_content: str,
    template_content: str,
    dayflow_content: Optional[str] = None,
) -> str:
    """組裝送給 LLM 的提示。"""
    dayflow_section = ""
    if dayflow_content:
        dayflow_section = f"""
## Dayflow 活動摘要

以下是 Dayflow 自動記錄的螢幕活動分析，請將其中的行為模式洞察融入精煉日記：

{dayflow_content}
"""

    return f"""\
請根據以下工作日誌{" 和 Dayflow 活動摘要" if dayflow_content else ""}，產出一份精煉日記。

## 日期
{date_str}

## 輸出格式
請嚴格按照以下模板格式輸出，將佔位符替換為實際內容：

{template_content}

## 工作日誌原文（L1）

{work_log_content}
{dayflow_section}
## 注意事項
- 「今日一句話」要精煉有力，一句話概括今天最重要的事
- 「洞察 & 靈感」每條後面用括號標註適合的頻道，例如：（→ Threads）
- 如果有 Dayflow 資料，將行為模式洞察（如時間分布、專注模式、切換頻率）融入「卡在哪裡」或「洞察 & 靈感」
- 「明天優先」最多 3 項，按重要性排序
- 「能量 & 狀態」從工作量、卡關次數、完成度推測，1-5 分；如果有 Dayflow 時間分布可作為客觀佐證
- 不要留下任何佔位符，每個欄位都要填入實際內容
"""


def main():
    parser = argparse.ArgumentParser(description="產出每日精煉日記（L2）")
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

    # 1. 檢查 L1 工作日誌
    wl_path = work_log_path(date_str)
    work_log_content = read_text(wl_path)

    if not work_log_content.strip():
        print(f"[journal] 找不到 {date_str} 的工作日誌：{wl_path}")
        print("[journal] 請先執行 /work-log 產出 L1 工作日誌。")
        sys.exit(1)

    print(f"[journal] 讀取工作日誌：{wl_path}")
    print(f"[journal] 工作日誌長度：{len(work_log_content)} 字元")

    # 1.5 讀取 Dayflow 活動摘要（如存在）
    dayflow_path = JOURNAL_DIR / f"{date_str}-dayflow.md"
    dayflow_content: Optional[str] = None
    if dayflow_path.exists():
        dayflow_content = read_text(dayflow_path)
        if dayflow_content.strip():
            print(f"[journal] 讀取 Dayflow 摘要：{dayflow_path}")
            print(f"[journal] Dayflow 長度：{len(dayflow_content)} 字元")
        else:
            dayflow_content = None
    else:
        print("[journal] 無 Dayflow 摘要，僅使用 L1 工作日誌")

    # 2. 讀取模板
    template_path = TEMPLATES_DIR / "journal-template.md"
    template_content = read_text(template_path)

    if not template_content.strip():
        print(f"[journal] 警告：模板不存在 {template_path}，使用預設格式")
        template_content = "（使用預設格式輸出精煉日記）"

    # 3. 檢查輸出檔案
    output_path = JOURNAL_DIR / f"{date_str}.md"
    if output_path.exists() and not args.force:
        print(f"[journal] 日記已存在：{output_path}")
        response = input("[journal] 覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[journal] 已取消。")
            sys.exit(0)

    # 4. 呼叫 LLM 提煉
    prompt = build_prompt(date_str, work_log_content, template_content, dayflow_content)
    print("[journal] 正在呼叫 claude --print 提煉日記...")

    journal_content = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 5. 寫入檔案
    ensure_dir(JOURNAL_DIR)
    output_path.write_text(journal_content, encoding="utf-8")

    print(f"[journal] 精煉日記已產出：{output_path}")
    print(f"[journal] 長度：{len(journal_content)} 字元")
    print(f"[journal] 壓縮比：{len(journal_content) / len(work_log_content):.0%}")


if __name__ == "__main__":
    main()
