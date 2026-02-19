#!/usr/bin/env python3
"""Weekly Newsletter — 產出電子報草稿（4 種月度輪替類型）"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import (
    JOURNAL_DIR,
    WEEKLY_DIR,
    NEWSLETTER_DIR,
    TEMPLATES_DIR,
    TOPICS_DIR,
    INSIGHTS_DIR,
    STYLE_DNA_DIR,
    RULES_DIR,
)
from lib.file_utils import (
    ensure_dir,
    read_text,
    week_date_range,
    newsletter_type_for_week,
    write_text,
)
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

VALID_TYPES = ("curated", "deep-dive", "mixed", "monthly-reflection")

TYPE_LABELS = {
    "curated": "主題策展",
    "deep-dive": "長篇深度",
    "mixed": "混合",
    "monthly-reflection": "月度心得反思",
}

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責撰寫每週電子報草稿。

Dex 是一位資深資料工程師，同時經營個人品牌，分享技術洞察、職涯心得和 AI 工具使用經驗。
電子報的讀者是對科技職涯、AI 工具、資料工程有興趣的專業人士。

寫作風格：
- 繁體中文
- 口語化但有深度，像在寫給朋友的信
- 用「你」直接對話讀者
- 有觀點、有立場，不做中立派
- 不雞湯、不空泛、不過度行銷
- 段落短，1-2 句就換行
- 技術用語自然穿插不額外解釋

輸出規則：
- 只輸出電子報正文（markdown 格式），不要加 YAML frontmatter
- 不要加任何額外說明或前綴
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


def collect_topics(start_date: str, end_date: str) -> list[tuple[str, str]]:
    """收集日期範圍內建立的 topics。"""
    results = []
    if not TOPICS_DIR.exists():
        return results
    for topic_dir in sorted(TOPICS_DIR.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name.startswith("."):
            continue
        topic_file = topic_dir / "TOPIC.md"
        if not topic_file.exists():
            continue
        dir_name = topic_dir.name
        if len(dir_name) >= 10 and start_date <= dir_name[:10] <= end_date:
            results.append((dir_name, read_text(topic_file)))
    return results


def collect_insights(start_date: str, end_date: str) -> list[tuple[str, str]]:
    """收集日期範圍內的 insights。"""
    results = []
    if not INSIGHTS_DIR.exists():
        return results
    for f in sorted(INSIGHTS_DIR.glob("*.md")):
        if f.name == ".gitkeep":
            continue
        if len(f.stem) >= 10 and start_date <= f.stem[:10] <= end_date:
            results.append((f.stem, read_text(f)))
    return results


def collect_monthly_reviews(year: int, month: int) -> list[tuple[str, str]]:
    """收集整個月的週回顧。"""
    results = []
    if not WEEKLY_DIR.exists():
        return results
    for f in sorted(WEEKLY_DIR.glob(f"{year}-W*.md")):
        content = read_text(f)
        if content.strip():
            results.append((f.stem, content))
    return results


def collect_monthly_journals(year: int, month: int) -> list[tuple[str, str]]:
    """收集整個月的 L2 日記。"""
    start = f"{year}-{month:02d}-01"
    # 算月底
    if month == 12:
        end_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_dt = datetime(year, month + 1, 1) - timedelta(days=1)
    end = end_dt.strftime("%Y-%m-%d")
    return collect_journals(start, end)


# ── Prompt 組裝 ──────────────────────────────────────

def build_prompt(
    nl_type: str,
    journals: list[tuple[str, str]],
    topics: list[tuple[str, str]],
    insights: list[tuple[str, str]],
    template: str,
    newsletter_dna: str,
    writing_rules: str,
    iso_week: int,
    week_range: str,
    monthly_journals: list[tuple[str, str]] | None = None,
    monthly_reviews: list[tuple[str, str]] | None = None,
) -> str:
    """根據類型組裝不同的 prompt。"""

    # 共用素材區段
    journal_section = ""
    for date_str, content in journals:
        journal_section += f"\n### {date_str}\n{content}\n"

    topic_section = ""
    for name, content in topics:
        topic_section += f"\n### {name}\n{content}\n"

    insight_section = ""
    for name, content in insights:
        insight_section += f"\n### {name}\n{content}\n"

    # 類型特定指示
    type_instructions = {
        "curated": f"""\
## 任務
產出一份「主題策展」型電子報。

## 要求
- 從本週素材中選 3-5 個最有價值的主題
- 每個主題展開 1-2 段，有觀點、有分析
- 主題之間用分隔線區分
- 結語要串起所有主題的共同脈絡
""",
        "deep-dive": f"""\
## 任務
產出一份「長篇深度」型電子報。

## 要求
- 從本週素材中選 1 個最有深度的主題，深入展開（800-1200 字）
- 另外挑 2-3 個短 highlight（每個 2-3 句話）
- 深度主題要有論點、有反例、有結論
- 短 highlight 用條列式呈現
""",
        "mixed": f"""\
## 任務
產出一份「混合」型電子報。

## 要求
- 1 個深度主題（400-600 字）
- 3-4 個短洞察（每個 1-2 句話，條列式）
- 推薦本週看到的好資源或工具（從日記中提取，如果有的話）
- 結語保持簡短
""",
        "monthly-reflection": f"""\
## 任務
產出一份「月度心得反思」型電子報。

## 要求
- 回顧整個月：做了什麼、成長了什麼
- 分享個人感受和心境變化
- 提煉月度的核心學習
- 展望下個月的方向
- 語氣可以更個人化、更感性一些
""",
    }

    prompt = f"""\
{type_instructions[nl_type]}

## 基本資訊
- ISO 週數：W{iso_week:02d}
- 日期範圍：{week_range}
- 電子報類型：{nl_type}（{TYPE_LABELS[nl_type]}）

## 本週 L2 日記
{journal_section if journal_section else "（本週無 L2 日記）"}

## 本週 Topics
{topic_section if topic_section else "（本週無 topic）"}

## 本週 Insights
{insight_section if insight_section else "（本週無 insight）"}
"""

    # monthly-reflection 額外加整月資料
    if nl_type == "monthly-reflection" and monthly_journals:
        monthly_j_section = ""
        for date_str, content in monthly_journals:
            monthly_j_section += f"\n### {date_str}\n{content}\n"
        prompt += f"""
## 整月 L2 日記（補充素材）
{monthly_j_section}
"""

    if nl_type == "monthly-reflection" and monthly_reviews:
        review_section = ""
        for name, content in monthly_reviews:
            review_section += f"\n### {name}\n{content}\n"
        prompt += f"""
## 本月週回顧（補充素材）
{review_section}
"""

    # 參考資料
    if newsletter_dna:
        prompt += f"""
## 電子報風格 DNA（請優先遵循這些具體模式）
{newsletter_dna}
"""

    if writing_rules:
        prompt += f"""
## 寫作風格規則
{writing_rules}
"""

    prompt += f"""
## 模板參考
{template}

## 注意事項
- 標題要吸引人，不要用「週報」或「Newsletter」開頭
- 開場直接進入有價值的內容，不要寒暄
- 結語要有記憶點，可以是金句或開放提問
- 只輸出電子報正文，markdown 格式，不要加 YAML frontmatter
"""
    return prompt


# ── 主程式 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Weekly Newsletter — 產出電子報草稿")
    parser.add_argument("date", nargs="?", default=None, help="該週任一天 (YYYY-MM-DD)")
    parser.add_argument("--type", type=str, default=None, choices=VALID_TYPES, help="電子報類型")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的草稿")
    args = parser.parse_args()

    # 1. 計算週日期範圍
    start, end, iso_week, week_of_month = week_date_range(args.date)
    year = datetime.strptime(start, "%Y-%m-%d").year
    month = datetime.strptime(start, "%Y-%m-%d").month
    week_range = f"{start} ~ {end}"

    # 2. 決定類型
    nl_type = args.type or newsletter_type_for_week(week_of_month)

    # 3. 收集素材
    journals = collect_journals(start, end)
    topics = collect_topics(start, end)
    insights = collect_insights(start, end)

    if not journals and not topics and not insights:
        print(f"[weekly-newsletter] 找不到 {week_range} 的任何素材", file=sys.stderr)
        sys.exit(1)

    print(f"[weekly-newsletter] {year} W{iso_week:02d}（{week_range}）")
    print(f"[weekly-newsletter] 類型：{nl_type}（{TYPE_LABELS[nl_type]}）")
    print(f"[weekly-newsletter] 素材：{len(journals)} 篇日記 + {len(topics)} 個 topic + {len(insights)} 個 insight")

    # 4. monthly-reflection 收集整月資料
    monthly_journals = None
    monthly_reviews = None
    if nl_type == "monthly-reflection":
        monthly_journals = collect_monthly_journals(year, month)
        monthly_reviews = collect_monthly_reviews(year, month)
        print(f"[weekly-newsletter] 月度補充：{len(monthly_journals)} 篇月日記 + {len(monthly_reviews)} 篇週回顧")

    # 5. 檢查輸出
    output_path = NEWSLETTER_DIR / f"{year}-W{iso_week:02d}-{nl_type}.md"
    if output_path.exists() and not args.force:
        print(f"[weekly-newsletter] {output_path.name} 已存在，使用 --force 覆蓋", file=sys.stderr)
        sys.exit(1)

    # 6. 讀取參考資料
    template = read_text(TEMPLATES_DIR / "newsletter-template.md")
    newsletter_dna = read_text(STYLE_DNA_DIR / "newsletter-dna.md")
    writing_rules = read_text(RULES_DIR / "10-writing-style.md")

    # 7. LLM 產出
    print("[weekly-newsletter] Generating newsletter draft...")
    prompt = build_prompt(
        nl_type=nl_type,
        journals=journals,
        topics=topics,
        insights=insights,
        template=template,
        newsletter_dna=newsletter_dna,
        writing_rules=writing_rules,
        iso_week=iso_week,
        week_range=week_range,
        monthly_journals=monthly_journals,
        monthly_reviews=monthly_reviews,
    )
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 8. 組裝 frontmatter + 內容
    from lib.file_utils import today_str

    draft_content = f"""---
type: {nl_type}
week: W{iso_week:02d}
year: {year}
date_range: "{week_range}"
status: draft
created: {today_str()}
---

{result.strip()}
"""

    # 9. 寫入
    ensure_dir(NEWSLETTER_DIR)
    write_text(output_path, draft_content)
    print(f"[weekly-newsletter] Done: {output_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
