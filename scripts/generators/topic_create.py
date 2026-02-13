#!/usr/bin/env python3
"""Topic Create — 從 insight 或手動描述建立主題檔案"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import TOPICS_DIR, CONTENT_INSIGHTS_DIR, TEMPLATES_DIR
from lib.file_utils import ensure_dir, read_text, today_str, write_text
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責將洞察或靈感擴展為完整的內容主題檔案。

你的任務是根據輸入的 insight 或主題描述，產出一份結構化的 TOPIC.md。

輸出規則：
- 使用繁體中文
- 嚴格按照指定的模板格式輸出
- 「核心論點」必須是一句可直接使用的話，有觀點、有立場
- 「關鍵素材」列出 3-5 個支撐論點的具體素材
- 「頻道適合度」要具體說明為什麼適合/不適合，不是只打勾
- 保留 insight 原文的觀點，不過度延伸
- 只輸出 TOPIC.md 內容，不要加任何額外說明
"""


# ── 主要邏輯 ──────────────────────────────────────────

def _slugify(text: str) -> str:
    """將標題轉為 URL-safe slug。"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:60] if text else "untitled"


def _list_insights() -> list[Path]:
    """列出所有可用的 insight 檔案。"""
    if not CONTENT_INSIGHTS_DIR.exists():
        return []
    return sorted(
        f for f in CONTENT_INSIGHTS_DIR.glob("*.md")
        if f.name != ".gitkeep"
    )


def _build_prompt(source_content: str, source_path: str, date: str) -> str:
    """組裝送給 LLM 的提示。"""
    template = read_text(TEMPLATES_DIR / "topic-template.md")

    return f"""\
請根據以下 insight 內容，產出一份完整的 TOPIC.md。

## 日期
{date}

## 來源
{source_path}

## Insight 原文
{source_content}

## 輸出格式
請嚴格按照以下模板格式輸出（替換 {{{{佔位符}}}} 為實際內容）：

{template}

## 注意事項
- tags 用 YAML array 格式：[tag1, tag2, tag3]
- 頻道適合度要涵蓋：Threads、Facebook、Newsletter、Blog
- 每個頻道用 ✅ 或 ❌ 開頭，後面附簡短原因
"""


def main():
    parser = argparse.ArgumentParser(description="Topic Create — 建立主題檔案")
    parser.add_argument("insight", nargs="?", default=None, help="insight 檔案路徑")
    parser.add_argument("--title", type=str, default=None, help="手動指定主題名稱（不使用 insight）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的主題")
    args = parser.parse_args()

    date = today_str()

    # 1. 決定輸入來源
    if args.title:
        # 手動模式
        source_content = f"# {args.title}\n\n（由使用者手動建立的主題）"
        source_path = "manual"
        slug = _slugify(args.title)
    elif args.insight:
        # 從 insight 檔案
        insight_path = Path(args.insight)
        if not insight_path.is_absolute():
            insight_path = ROOT_DIR / insight_path
        if not insight_path.exists():
            print(f"[topic-create] ERROR: 找不到 {args.insight}", file=sys.stderr)
            sys.exit(1)
        source_content = read_text(insight_path)
        source_path = str(insight_path.relative_to(ROOT_DIR))
        # 從 insight 檔名取 slug
        stem = insight_path.stem
        # 移除日期前綴（YYYY-MM-DD-）
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    else:
        # 列出可用 insights
        insights = _list_insights()
        if not insights:
            print("[topic-create] 沒有可用的 insight 檔案", file=sys.stderr)
            print(f"[topic-create] 先執行 ./bin/agent extract 產生 insight", file=sys.stderr)
            sys.exit(1)

        print("[topic-create] 可用的 insight 檔案：\n")
        for i, f in enumerate(insights, 1):
            title_line = ""
            for line in read_text(f).splitlines():
                if line.startswith("# "):
                    title_line = line[2:].strip()
                    break
            print(f"  {i}. {f.name}")
            if title_line:
                print(f"     {title_line}")
        print(f"\n用法：./bin/agent topic-create <insight-file>")
        return

    # 2. 檢查輸出目錄
    topic_dir = TOPICS_DIR / slug
    topic_file = topic_dir / "TOPIC.md"

    if topic_file.exists() and not args.force:
        response = input(f"[topic-create] {slug}/TOPIC.md 已存在，覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[topic-create] Cancelled.")
            sys.exit(0)

    # 3. LLM 擴展
    print(f"[topic-create] Creating topic '{slug}'...")
    prompt = _build_prompt(source_content, source_path, date)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 4. 清理 LLM 回應
    if result and not result.startswith("---"):
        # 找到 YAML frontmatter 開頭
        fm_start = result.find("---")
        if fm_start != -1:
            result = result[fm_start:]

    # 5. 寫入
    ensure_dir(topic_dir)
    write_text(topic_file, result)
    print(f"[topic-create] Done: {topic_file.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
