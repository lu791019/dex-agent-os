#!/usr/bin/env python3
"""Daily Digest — 每日學習消化報告

使用方式：
  ./bin/agent daily-digest [YYYY-MM-DD] [--send] [--force]

  掃描指定日期（預設昨天）的所有學習內容：
    000_Inbox/readings/         （readwise-sync / rss-sync / anybox-sync 原文）
    300_Learning/input/**/      （learning-note 產出）
    300_Learning/youtube/       （youtube-add 產出）
    300_Learning/podcasts/episodes/（podcast-add 產出）

  → LLM 產出每日消化摘要 → 本地存檔
  → --send：建立 Google Doc + 寄 Gmail（需先設定 Google API）

  輸出：100_Journal/digest/YYYY-MM-DD-digest.md
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import (
    DIGEST_DIR,
    LEARNING_INPUT_DIR,
    PODCAST_EPISODES_DIR,
    READINGS_DIR,
    TEMPLATES_DIR,
    YOUTUBE_DIR,
)
from lib.file_utils import ensure_dir, read_text, write_text
from lib.llm import ask_claude


# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 助理，負責產出每日學習消化報告。

你需要做的：
- 對每篇內容寫 5-8 句精練摘要（保留重要細節與數據）
- 提取 1-2 個關鍵 takeaway
- 在最後綜合分析今日所有內容的共同主題與趨勢

輸出規則：
- 使用繁體中文
- 保持專業但不官腔
- 保留所有原始連結
- 嚴格依照提供的模板格式輸出
"""

CATEGORY_MAP = {
    "readings": "文章",
    "articles": "文章",
    "books": "書籍",
    "courses": "課程",
    "tech": "技術",
    "youtube": "YouTube",
    "podcasts": "Podcast",
}


# ── 掃描邏輯 ──────────────────────────────────────────

def _extract_frontmatter(text: str) -> dict:
    """從 Markdown 文件擷取 YAML frontmatter 的簡易欄位。"""
    meta = {}
    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        return meta
    for line in fm_match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            meta[key] = val
    return meta


def _scan_date_files(date_str: str) -> list[dict]:
    """掃描指定日期的所有學習內容檔案。

    Returns:
        list of dict: [{path, title, url, category, source_dir, content}]
    """
    items = []
    prefix = date_str

    # 1. 000_Inbox/readings/ — 原文（readwise-sync / rss-sync / anybox-sync）
    if READINGS_DIR.exists():
        for f in sorted(READINGS_DIR.glob(f"{prefix}-*.md")):
            text = read_text(f)
            meta = _extract_frontmatter(text)
            items.append({
                "path": f,
                "title": meta.get("title", f.stem),
                "url": meta.get("url", ""),
                "category": "readings",
                "source_dir": "readings",
                "content": text,
            })

    # 2. 300_Learning/input/**/ — learning-note 產出（已消化）
    if LEARNING_INPUT_DIR.exists():
        for f in sorted(LEARNING_INPUT_DIR.rglob(f"{prefix}-*.md")):
            text = read_text(f)
            meta = _extract_frontmatter(text)
            note_type = meta.get("type", f.parent.name)
            items.append({
                "path": f,
                "title": meta.get("title", f.stem),
                "url": meta.get("source", ""),
                "category": note_type,
                "source_dir": "input",
                "content": text,
            })

    # 3. 300_Learning/youtube/ — youtube-add 產出
    if YOUTUBE_DIR.exists():
        for f in sorted(YOUTUBE_DIR.glob(f"{prefix}-*.md")):
            text = read_text(f)
            meta = _extract_frontmatter(text)
            items.append({
                "path": f,
                "title": meta.get("title", f.stem),
                "url": meta.get("source", meta.get("url", "")),
                "category": "youtube",
                "source_dir": "youtube",
                "content": text,
            })

    # 4. 300_Learning/podcasts/episodes/ — podcast-add 產出
    if PODCAST_EPISODES_DIR.exists():
        for f in sorted(PODCAST_EPISODES_DIR.glob(f"{prefix}-*.md")):
            text = read_text(f)
            meta = _extract_frontmatter(text)
            items.append({
                "path": f,
                "title": meta.get("title", f.stem),
                "url": meta.get("source", meta.get("url", "")),
                "category": "podcasts",
                "source_dir": "podcasts",
                "content": text,
            })

    return items


def _dedup_items(items: list[dict]) -> list[dict]:
    """去重：同一 URL 出現在 readings/ 和 input/ 時，優先保留 input/ 版本。"""
    seen_urls: dict[str, dict] = {}
    no_url = []

    for item in items:
        url = item["url"].rstrip("/")
        if not url:
            no_url.append(item)
            continue

        if url in seen_urls:
            existing = seen_urls[url]
            # input/ 優先於 readings/
            if item["source_dir"] == "input" and existing["source_dir"] == "readings":
                seen_urls[url] = item
        else:
            seen_urls[url] = item

    return list(seen_urls.values()) + no_url


def _group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    """按類別分組。"""
    groups: dict[str, list[dict]] = {}
    for item in items:
        cat = CATEGORY_MAP.get(item["category"], item["category"])
        groups.setdefault(cat, []).append(item)
    return groups


# ── LLM 消化 ─────────────────────────────────────────

def _build_llm_prompt(items: list[dict], date_str: str, template: str) -> str:
    """組合 LLM prompt：所有內容 + 模板。"""
    parts = [f"今天是 {date_str}，以下是今日所有學習內容（共 {len(items)} 篇）：\n"]

    for i, item in enumerate(items, 1):
        cat = CATEGORY_MAP.get(item["category"], item["category"])
        parts.append(f"--- 第 {i} 篇 [{cat}] ---")
        parts.append(f"標題：{item['title']}")
        if item["url"]:
            parts.append(f"連結：{item['url']}")
        parts.append(f"檔案：{item['path'].name}")

        # 內容截斷（每篇最多 3000 字，避免 token 爆量）
        content = item["content"]
        if len(content) > 3000:
            content = content[:3000] + "\n\n... [截斷，原文更長] ..."
        parts.append(f"\n{content}\n")

    parts.append("---\n\n請依照以下模板格式產出今日消化報告：\n")
    parts.append(template)

    return "\n".join(parts)


def _clean_llm_output(text: str) -> str:
    """清理 LLM 思考殘留（claude --print 偶爾帶 chain-of-thought prefix）。

    策略：如果輸出不以 `---` 或 `#` 開頭，找到第一個 `---` 或 `# ` 並截取之後的內容。
    """
    stripped = text.strip()
    if stripped.startswith("---") or stripped.startswith("#"):
        return stripped

    # 找第一個 frontmatter 或 heading
    for marker in ["---\n", "# "]:
        idx = stripped.find(marker)
        if idx > 0:
            return stripped[idx:]

    return stripped


# ── 主程式 ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Daily Digest — 每日學習消化報告")
    parser.add_argument("date", nargs="?", default=None, help="日期 YYYY-MM-DD（預設昨天）")
    parser.add_argument("--send", action="store_true", help="建立 Google Doc + 寄 Gmail")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的 digest")
    parser.add_argument("--today", action="store_true", help="掃描今天（而非昨天）")

    args = parser.parse_args()

    # 決定日期
    if args.date:
        date_str = args.date
    elif args.today:
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"[daily-digest] 掃描日期：{date_str}")

    # 檢查輸出是否已存在
    ensure_dir(DIGEST_DIR)
    output_path = DIGEST_DIR / f"{date_str}-digest.md"

    if output_path.exists() and not args.force:
        print(f"[daily-digest] 已存在：{output_path.name}（使用 --force 覆蓋）")
        return

    # 掃描檔案
    items = _scan_date_files(date_str)
    if not items:
        print(f"[daily-digest] {date_str} 沒有找到任何學習內容")
        print(f"  檢查以下目錄是否有 {date_str}-*.md 檔案：")
        print(f"    {READINGS_DIR}")
        print(f"    {LEARNING_INPUT_DIR}")
        print(f"    {YOUTUBE_DIR}")
        print(f"    {PODCAST_EPISODES_DIR}")
        return

    # 去重
    deduped = _dedup_items(items)
    groups = _group_by_category(deduped)

    print(f"[daily-digest] 找到 {len(items)} 個檔案，去重後 {len(deduped)} 篇：")
    for cat, cat_items in groups.items():
        print(f"  {cat}：{len(cat_items)} 篇")

    # 讀取模板
    template_path = TEMPLATES_DIR / "daily-digest-template.md"
    template = read_text(template_path)
    if not template:
        template = _default_template()

    # LLM 消化
    print(f"\n[daily-digest] LLM 消化中...")
    prompt = _build_llm_prompt(deduped, date_str, template)
    result = ask_claude(prompt, system_prompt=SYSTEM_PROMPT)

    if not result:
        print("[daily-digest] LLM 回應為空", file=sys.stderr)
        return

    # 清理 LLM 思考殘留（claude --print 偶爾帶 chain-of-thought）
    result = _clean_llm_output(result)

    # 儲存
    write_text(output_path, result + "\n")
    print(f"\n[daily-digest] 已儲存：{output_path}")

    # --send：Google Doc + Gmail
    if args.send:
        _handle_send(date_str, result, output_path)


def _handle_send(date_str: str, digest_content: str, local_path: Path):
    """建立 Google Doc + 寄 Gmail。"""
    try:
        from lib.google_api import check_google_setup, create_google_doc, send_gmail
    except ImportError:
        print("[daily-digest] 無法載入 google_api 模組", file=sys.stderr)
        return

    if not check_google_setup():
        print("\n[daily-digest] 跳過 --send（Google API 未設定）")
        print(f"  本地檔案已儲存：{local_path}")
        return

    # 建立 Google Doc
    title = f"Daily Digest — {date_str}"
    doc_url = create_google_doc(title, digest_content)

    # 寄 Gmail
    import os
    to_email = os.getenv("DIGEST_EMAIL", "")
    if not to_email:
        print("[daily-digest] DIGEST_EMAIL 未設定，跳過寄信")
        if doc_url:
            print(f"  Google Doc：{doc_url}")
        return

    # 摘要信：前 500 字 + Google Doc 連結
    summary = digest_content[:500] + "\n\n..." if len(digest_content) > 500 else digest_content
    send_gmail(to_email, f"📚 Daily Digest — {date_str}", summary, doc_url)


def _default_template() -> str:
    """預設模板（模板檔不存在時使用）。"""
    return """\
---
title: "Daily Digest — {date}"
date: {date}
type: digest
count: {count}
---
# Daily Digest — {date}

## 今日摘要

（對每篇內容寫 5-8 句摘要 + 1-2 個 takeaway）

### 文章
（列出所有文章類內容）

### Podcast
（如有）

### YouTube
（如有）

### 課程 / 技術
（如有）

## 今日洞察

（綜合分析：共同主題、趨勢、可行動項目）
"""


if __name__ == "__main__":
    main()
