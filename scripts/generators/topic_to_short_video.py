#!/usr/bin/env python3
"""Topic to Short Video — 從主題產出短影音腳本草稿"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import TOPICS_DIR, SHORT_VIDEO_DIR, RULES_DIR
from lib.file_utils import ensure_dir, extract_created_date, read_text, today_str, write_text
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責將主題檔案轉化為短影音腳本草稿。

短影音腳本風格要求：
- 長度：15-60 秒（約 80-250 字口語稿）
- 結構：Hook（前 3 秒）→ 核心內容 → CTA
- 每段搭配 `[畫面]` 視覺提示，方便拍攝
- 口語化，適合鏡頭前唸出來
- 一個影片只講一個核心觀點

禁止：
- 不假裝做了沒做過的事
- 不過度行銷
- 不用書面語，要口語
- 不堆疊 emoji
- 不雞湯

輸出規則：
- 使用繁體中文
- 只輸出腳本本身，不要加任何格式框架、說明或前綴
- 不要加 YAML frontmatter，直接輸出腳本內容
- 用 `[畫面]` 標記視覺提示（如 `[畫面：對著鏡頭]`、`[畫面：螢幕錄製]`）
"""


# ── 主要邏輯 ──────────────────────────────────────────

def _list_topics() -> list[tuple[str, str]]:
    """列出所有可用的主題。回傳 [(slug, title), ...]。"""
    if not TOPICS_DIR.exists():
        return []

    topics = []
    for topic_dir in sorted(TOPICS_DIR.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name.startswith("."):
            continue
        topic_file = topic_dir / "TOPIC.md"
        if topic_file.exists():
            title = topic_dir.name
            for line in read_text(topic_file).splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            topics.append((topic_dir.name, title))

    return topics


def _build_prompt(topic_content: str, writing_rules: str) -> str:
    """組裝送給 LLM 的提示。"""
    prompt = f"""\
請根據以下主題，產出一段短影音腳本（15-60 秒）。

## 主題內容
{topic_content}
"""

    if writing_rules:
        prompt += f"""
## 寫作風格規則
{writing_rules}
"""

    prompt += """
## 注意事項
- 只輸出腳本本身，不要加框架或說明
- 15-60 秒（約 80-250 字）
- 前 3 秒必須有 Hook
- 每段用 `[畫面]` 標記視覺提示
- 結尾明確 CTA
- 口語化，像在跟朋友說話
"""
    return prompt


def _update_topic_checklist(topic_file: Path):
    """更新 TOPIC.md 的 ShortVideo checklist 為已完成。"""
    content = read_text(topic_file)
    updated = content.replace("- [ ] ShortVideo", "- [x] ShortVideo")
    if updated != content:
        topic_file.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Topic to Short Video — 主題 → 短影音腳本")
    parser.add_argument("slug", nargs="?", default=None, help="主題 slug（目錄名）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的草稿")
    args = parser.parse_args()

    # 1. 決定主題
    if not args.slug:
        topics = _list_topics()
        if not topics:
            print("[topic-to-short-video] 沒有可用的主題", file=sys.stderr)
            print("[topic-to-short-video] 先執行 ./bin/agent topic-create 建立主題", file=sys.stderr)
            sys.exit(1)

        print("[topic-to-short-video] 可用的主題：\n")
        for slug, title in topics:
            print(f"  {slug}")
            print(f"    {title}")
        print(f"\n用法：./bin/agent topic-to-short-video <slug>")
        return

    slug = args.slug.strip("/")
    topic_dir = TOPICS_DIR / slug
    topic_file = topic_dir / "TOPIC.md"

    if not topic_file.exists():
        print(f"[topic-to-short-video] ERROR: 找不到 {topic_file.relative_to(ROOT_DIR)}", file=sys.stderr)
        sys.exit(1)

    # 2. 讀取主題 + 決定輸出路徑
    topic_content = read_text(topic_file)
    created_date = extract_created_date(topic_content)
    draft_dir = ensure_dir(SHORT_VIDEO_DIR / created_date)
    draft_path = draft_dir / f"{slug}.md"

    if draft_path.exists() and not args.force:
        response = input(f"[topic-to-short-video] {draft_path.name} 已存在，覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[topic-to-short-video] Cancelled.")
            sys.exit(0)

    # 3. 讀取參考資料（短影音不使用 DNA）
    writing_rules = read_text(RULES_DIR / "10-writing-style.md")

    # 4. LLM 產出
    print(f"[topic-to-short-video] Generating short video script for '{slug}'...")
    prompt = _build_prompt(topic_content, writing_rules)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 5. 組裝 frontmatter + 內容
    date = today_str()
    draft_content = f"""---
topic: {slug}
channel: short-video
status: draft
duration: 15-60s
created: {date}
---

{result.strip()}
"""

    # 6. 寫入
    write_text(draft_path, draft_content)
    print(f"[topic-to-short-video] Done: {draft_path.relative_to(ROOT_DIR)}")

    # 7. 更新 TOPIC.md checklist
    _update_topic_checklist(topic_file)
    print(f"[topic-to-short-video] Updated TOPIC.md checklist")


if __name__ == "__main__":
    main()
