#!/usr/bin/env python3
"""Topic to Blog — 從主題產出部落格文章草稿"""

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import TOPICS_DIR, STYLE_DNA_DIR, RULES_DIR
from lib.file_utils import read_text, today_str, write_text
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責將主題檔案轉化為部落格文章草稿。

部落格文章風格要求：
- 結構：SEO 標題 → 前言 Hook → H2/H3 段落 → 結論
- 長度：800-1500 字
- 標題含關鍵字，適合搜尋引擎
- H2/H3 層次分明，每段有明確觀點
- 技術主題適當穿插程式碼區塊（標註語言）
- 語氣：專業、有深度、有故事感

禁止：
- 不假裝做了沒做過的事
- 不過度行銷
- 不用空泛開場如「今天來聊聊...」
- 不灌水，每段都要有實質內容
- 不雞湯

輸出規則：
- 使用繁體中文
- 輸出完整文章，包含 H1 標題
- 不要加 YAML frontmatter，直接輸出文章內容
- 程式碼區塊請標註語言（如 ```python）
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


def _build_prompt(topic_content: str, style_dna: str, writing_rules: str) -> str:
    """組裝送給 LLM 的提示。"""
    prompt = f"""\
請根據以下主題，產出一篇部落格文章草稿。

## 主題內容
{topic_content}
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
- 輸出完整文章，含 H1 標題
- 800-1500 字
- 使用 H2/H3 結構化段落
- 技術主題穿插程式碼區塊
- 前言要有 Hook，結論要有 takeaway
"""
    return prompt


def _extract_title(content: str) -> str:
    """從 LLM 輸出中提取 H1 標題。"""
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _extract_tags(topic_content: str) -> str:
    """從 TOPIC.md frontmatter 提取 tags。"""
    match = re.search(r"^tags:\s*(.+)$", topic_content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def _update_topic_checklist(topic_file: Path):
    """更新 TOPIC.md 的 Blog checklist 為已完成。"""
    content = read_text(topic_file)
    updated = content.replace("- [ ] Blog", "- [x] Blog")
    if updated != content:
        topic_file.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Topic to Blog — 主題 → 部落格文章草稿")
    parser.add_argument("slug", nargs="?", default=None, help="主題 slug（目錄名）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的草稿")
    args = parser.parse_args()

    # 1. 決定主題
    if not args.slug:
        topics = _list_topics()
        if not topics:
            print("[topic-to-blog] 沒有可用的主題", file=sys.stderr)
            print("[topic-to-blog] 先執行 ./bin/agent topic-create 建立主題", file=sys.stderr)
            sys.exit(1)

        print("[topic-to-blog] 可用的主題：\n")
        for slug, title in topics:
            draft_exists = (TOPICS_DIR / slug / "blog-draft.md").exists()
            status = " [已有草稿]" if draft_exists else ""
            print(f"  {slug}{status}")
            print(f"    {title}")
        print(f"\n用法：./bin/agent topic-to-blog <slug>")
        return

    slug = args.slug.strip("/")
    topic_dir = TOPICS_DIR / slug
    topic_file = topic_dir / "TOPIC.md"

    if not topic_file.exists():
        print(f"[topic-to-blog] ERROR: 找不到 {topic_file.relative_to(ROOT_DIR)}", file=sys.stderr)
        sys.exit(1)

    # 2. 檢查輸出
    draft_path = topic_dir / "blog-draft.md"
    if draft_path.exists() and not args.force:
        response = input(f"[topic-to-blog] blog-draft.md 已存在，覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[topic-to-blog] Cancelled.")
            sys.exit(0)

    # 3. 讀取參考資料
    topic_content = read_text(topic_file)
    style_dna = read_text(STYLE_DNA_DIR / "blog-dna.md")
    writing_rules = read_text(RULES_DIR / "10-writing-style.md")

    # 4. LLM 產出
    print(f"[topic-to-blog] Generating blog draft for '{slug}'...")
    prompt = _build_prompt(topic_content, style_dna, writing_rules)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 5. 組裝 frontmatter + 內容
    date = today_str()
    title = _extract_title(result)
    tags = _extract_tags(topic_content)
    draft_content = f"""---
topic: {slug}
channel: blog
status: draft
created: {date}
tags: {tags}
---

{result.strip()}
"""

    # 6. 寫入
    write_text(draft_path, draft_content)
    print(f"[topic-to-blog] Done: {draft_path.relative_to(ROOT_DIR)}")

    # 7. 更新 TOPIC.md checklist
    _update_topic_checklist(topic_file)
    print(f"[topic-to-blog] Updated TOPIC.md checklist")


if __name__ == "__main__":
    main()
