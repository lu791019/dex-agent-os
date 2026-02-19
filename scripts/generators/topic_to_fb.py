#!/usr/bin/env python3
"""Topic to Facebook — 從主題產出 Facebook 貼文草稿"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import TOPICS_DIR, FACEBOOK_DIR, STYLE_DNA_DIR, RULES_DIR
from lib.file_utils import ensure_dir, extract_created_date, read_text, today_str, write_text
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責將主題檔案轉化為 Facebook 貼文草稿。

Facebook 貼文風格要求：
- 結構：Hook → 故事/觀點展開 → 開放式提問收尾
- 長度：300-500 字
- 語氣：社群感，像跟朋友分享心得
- 用「你」直接對話，鼓勵留言互動
- 結尾以開放式提問邀請討論

禁止：
- 不假裝做了沒做過的事
- 不過度行銷，CTA 保持自然
- 不用空泛開場如「今天來聊聊...」
- 不堆疊 emoji 或 hashtag
- 不雞湯

輸出規則：
- 使用繁體中文
- 只輸出 Facebook 貼文本身，不要加任何格式框架、說明或前綴
- 不要加 YAML frontmatter，直接輸出貼文內容
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
請根據以下主題，產出一篇 Facebook 貼文草稿。

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
- 只輸出貼文本身，不要加框架或說明
- 300-500 字
- 結尾用開放式提問邀請互動
"""
    return prompt


def _update_topic_checklist(topic_file: Path):
    """更新 TOPIC.md 的 Facebook checklist 為已完成。"""
    content = read_text(topic_file)
    updated = content.replace("- [ ] Facebook", "- [x] Facebook")
    if updated != content:
        topic_file.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Topic to Facebook — 主題 → Facebook 貼文草稿")
    parser.add_argument("slug", nargs="?", default=None, help="主題 slug（目錄名）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的草稿")
    args = parser.parse_args()

    # 1. 決定主題
    if not args.slug:
        topics = _list_topics()
        if not topics:
            print("[topic-to-fb] 沒有可用的主題", file=sys.stderr)
            print("[topic-to-fb] 先執行 ./bin/agent topic-create 建立主題", file=sys.stderr)
            sys.exit(1)

        print("[topic-to-fb] 可用的主題：\n")
        for slug, title in topics:
            print(f"  {slug}")
            print(f"    {title}")
        print(f"\n用法：./bin/agent topic-to-fb <slug>")
        return

    slug = args.slug.strip("/")
    topic_dir = TOPICS_DIR / slug
    topic_file = topic_dir / "TOPIC.md"

    if not topic_file.exists():
        print(f"[topic-to-fb] ERROR: 找不到 {topic_file.relative_to(ROOT_DIR)}", file=sys.stderr)
        sys.exit(1)

    # 2. 讀取主題 + 決定輸出路徑
    topic_content = read_text(topic_file)
    created_date = extract_created_date(topic_content)
    draft_dir = ensure_dir(FACEBOOK_DIR / created_date)
    draft_path = draft_dir / f"{slug}.md"

    if draft_path.exists() and not args.force:
        response = input(f"[topic-to-fb] {draft_path.name} 已存在，覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[topic-to-fb] Cancelled.")
            sys.exit(0)

    # 3. 讀取參考資料
    style_dna = read_text(STYLE_DNA_DIR / "facebook-dna.md")
    writing_rules = read_text(RULES_DIR / "10-writing-style.md")

    # 4. LLM 產出
    print(f"[topic-to-fb] Generating Facebook draft for '{slug}'...")
    prompt = _build_prompt(topic_content, style_dna, writing_rules)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 5. 組裝 frontmatter + 內容
    date = today_str()
    draft_content = f"""---
topic: {slug}
channel: facebook
status: draft
created: {date}
---

{result.strip()}
"""

    # 6. 寫入
    write_text(draft_path, draft_content)
    print(f"[topic-to-fb] Done: {draft_path.relative_to(ROOT_DIR)}")

    # 7. 更新 TOPIC.md checklist
    _update_topic_checklist(topic_file)
    print(f"[topic-to-fb] Updated TOPIC.md checklist")


if __name__ == "__main__":
    main()
