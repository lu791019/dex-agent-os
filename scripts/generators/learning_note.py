#!/usr/bin/env python3
"""Learning Note Generator — 多來源學習筆記產生器

使用方式：
  # URL 模式：擷取網頁文章
  ./bin/agent learning-note --url "URL" [--type TYPE] [--force]

  # 本地檔案模式
  ./bin/agent learning-note --file PATH --title "..." [--type TYPE] [--force]

  # Readwise 模式：v2 highlights 或 v3 Reader 文件
  ./bin/agent learning-note --readwise [--latest N] [--all] [--type TYPE] [--force]
  ./bin/agent learning-note --readwise --reader [--latest N] [--type TYPE] [--force]

  # RSS 模式：從 feed 取文章
  ./bin/agent learning-note --rss "FEED_URL" [--latest N] [--type TYPE] [--force]

  # Anybox 模式：從書籤取文章
  ./bin/agent learning-note --anybox [--tag TAG] [--starred] [--latest N] [--type TYPE] [--force]

  # --type：articles（預設）/ books / courses / tech
  # 輸出：300_Learning/input/<type>/YYYY-MM-DD-<slug>.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import LEARNING_INPUT_DIR, TEMPLATES_DIR
from lib.file_utils import ensure_dir, read_text, today_str, write_text
from lib.llm import ask_claude
from lib.readwise_api import (
    book_to_text,
    check_readwise_setup,
    reader_doc_to_text,
    reader_list,
    readwise_export,
    slugify,
)


# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 助理，負責將閱讀素材轉為結構化學習筆記。

你需要做的：
- 用一句話精準摘要（不超過 30 字）
- 提煉核心觀點（3-5 個）
- 挑出值得記住的關鍵引述（原文）
- 列出可實作的技術筆記（如有）
- 列出可轉化為 Threads/Newsletter 的素材

輸出規則：
- 使用繁體中文
- 嚴格按照指定的模板格式輸出
- 只輸出筆記內容，不要加額外說明
- 「我的想法」區塊保留 <!-- 手動補充 --> 不要填寫
"""

VALID_TYPES = ["articles", "books", "courses", "tech"]


# ── LLM 結構化 ──────────────────────────────────────

def build_prompt(title: str, content: str, template: str, date_str: str, source: str, note_type: str) -> str:
    """組裝送給 LLM 的提示。"""
    max_chars = 80000
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[... 內容過長，已截斷 ...]"

    return f"""\
請根據以下閱讀素材，產出一份結構化學習筆記。

## 素材資訊
- 標題：{title}
- 日期：{date_str}
- 來源：{source}
- 類型：{note_type}

## 素材內容
{content}

## 輸出格式
請嚴格按照以下模板格式輸出（替換 {{{{佔位符}}}} 為實際內容）：

{template}

## 注意事項
- tags 至少填 2-3 個相關標籤
- 「我的想法」保留 <!-- 手動補充 --> 不要填寫
"""


def generate_note(title: str, content: str, date_str: str, source: str, note_type: str, force: bool = False) -> Path:
    """用 LLM 產出結構化學習筆記並寫入檔案。"""
    slug = slugify(title)
    output_dir = LEARNING_INPUT_DIR / note_type
    output_path = output_dir / f"{date_str}-{slug}.md"

    if output_path.exists() and not force:
        print(f"[learning-note] {output_path.name} 已存在，使用 --force 覆蓋", file=sys.stderr)
        sys.exit(1)

    template = read_text(TEMPLATES_DIR / "learning-note-template.md")
    prompt = build_prompt(title, content, template, date_str, source, note_type)

    print("[learning-note] Generating structured learning note...")
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 清理 — 確保以 frontmatter 或標題開頭
    if result and not result.startswith("---") and not result.startswith("#"):
        for marker in ["---", "# "]:
            pos = result.find(marker)
            if pos != -1:
                result = result[pos:]
                break

    ensure_dir(output_dir)
    write_text(output_path, result.strip() + "\n")
    return output_path


# ── 模式處理 ──────────────────────────────────────────

def handle_url(args) -> None:
    """--url 模式：擷取網頁文章。"""
    from lib.web_extract import extract_url_content

    print(f"[learning-note] Extracting: {args.url}")
    title, text = extract_url_content(args.url)

    if not text:
        print("[learning-note] 無法擷取內容", file=sys.stderr)
        sys.exit(1)

    title = args.title or title or "Untitled"
    date_str = args.date or today_str()

    output = generate_note(
        title=title,
        content=text,
        date_str=date_str,
        source=args.url,
        note_type=args.type,
        force=args.force,
    )
    print(f"[learning-note] Done: {output.relative_to(ROOT_DIR)}")


def handle_file(args) -> None:
    """--file 模式：讀取本地檔案。"""
    path = Path(args.file).expanduser()
    if not path.exists():
        print(f"[learning-note] ERROR: 找不到檔案 {path}", file=sys.stderr)
        sys.exit(1)

    if not args.title:
        print("[learning-note] ERROR: --file 模式需要搭配 --title", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")
    date_str = args.date or today_str()

    output = generate_note(
        title=args.title,
        content=content,
        date_str=date_str,
        source=str(path),
        note_type=args.type,
        force=args.force,
    )
    print(f"[learning-note] Done: {output.relative_to(ROOT_DIR)}")


def handle_readwise(args) -> None:
    """--readwise 模式：從 Readwise v2 highlights 或 v3 Reader 產出學習筆記。"""
    if not check_readwise_setup():
        sys.exit(1)

    date_str = args.date or today_str()
    limit = args.latest if args.latest > 0 else 0

    if args.reader:
        # v3 Reader 模式
        print("[learning-note] Querying Readwise Reader...")
        docs = reader_list(category="rss", limit=limit, fetch_all=args.all)

        if not docs:
            print("[learning-note] Reader 中沒有找到文件", file=sys.stderr)
            return

        if args.latest == 0 and not args.all:
            print(f"\n[learning-note] 找到 {len(docs)} 篇 Reader 文件：\n")
            for i, doc in enumerate(docs[:20], 1):
                title = doc.get("title", "Untitled")
                site = doc.get("site_name", "")
                print(f"  {i:2d}. {title}" + (f" ({site})" if site else ""))
            print(f"\n使用 --latest N 匯入最新 N 篇，或 --all 匯入全部")
            return

        _process_reader_docs(docs, date_str, args)

    else:
        # v2 highlights 模式
        print("[learning-note] Querying Readwise highlights...")
        books = readwise_export(category="articles", limit=limit, fetch_all=args.all)

        if not books:
            print("[learning-note] Readwise 中沒有找到 articles highlights", file=sys.stderr)
            return

        if args.latest == 0 and not args.all:
            print(f"\n[learning-note] 找到 {len(books)} 篇 articles：\n")
            for i, book in enumerate(books[:20], 1):
                title = book.get("title", "Untitled")
                hl_count = len(book.get("highlights", []))
                print(f"  {i:2d}. {title} ({hl_count} highlights)")
            print(f"\n使用 --latest N 匯入最新 N 篇，或 --all 匯入全部")
            return

        _process_readwise_books(books, date_str, args)


def _process_readwise_books(books: list[dict], date_str: str, args) -> None:
    """處理 Readwise v2 books 列表。"""
    print(f"[learning-note] 準備產出 {len(books)} 篇學習筆記...")
    for book in books:
        title = book.get("title", "Untitled")
        updated = book.get("updated", "")
        book_date = updated[:10] if updated else date_str

        slug = slugify(title)
        output_dir = LEARNING_INPUT_DIR / args.type
        output_path = output_dir / f"{book_date}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[learning-note] SKIP: {output_path.name} 已存在")
            continue

        content = book_to_text(book)
        if len(content) < 50:
            print(f"[learning-note] SKIP: {title} 內容太短")
            continue

        print(f"\n[learning-note] Processing: {title}")
        output = generate_note(
            title=title,
            content=content,
            date_str=args.date or book_date,
            source=f"Readwise ({title})",
            note_type=args.type,
            force=args.force,
        )
        print(f"[learning-note] Done: {output.relative_to(ROOT_DIR)}")


def _process_reader_docs(docs: list[dict], date_str: str, args) -> None:
    """處理 Reader v3 文件列表。"""
    from lib.web_extract import extract_url_content

    print(f"[learning-note] 準備產出 {len(docs)} 篇學習筆記...")
    for doc in docs:
        title = doc.get("title", "Untitled")
        updated = doc.get("updated_at", "")
        doc_date = updated[:10] if updated else date_str
        source_url = doc.get("source_url", "")

        slug = slugify(title)
        output_dir = LEARNING_INPUT_DIR / args.type
        output_path = output_dir / f"{doc_date}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[learning-note] SKIP: {output_path.name} 已存在")
            continue

        # Reader list API 不含全文，用 web_extract 取全文
        content = reader_doc_to_text(doc)
        if source_url and len(content) < 200:
            print(f"[learning-note] Reader 摘要不足，擷取全文: {source_url}")
            _, full_text = extract_url_content(source_url)
            if full_text:
                content = f"# {title}\nSource: {source_url}\n\n{full_text}"

        if len(content) < 50:
            print(f"[learning-note] SKIP: {title} 內容太短")
            continue

        print(f"\n[learning-note] Processing: {title}")
        output = generate_note(
            title=title,
            content=content,
            date_str=args.date or doc_date,
            source=source_url or f"Readwise Reader ({title})",
            note_type=args.type,
            force=args.force,
        )
        print(f"[learning-note] Done: {output.relative_to(ROOT_DIR)}")


def handle_rss(args) -> None:
    """--rss 模式：從 RSS feed 取文章。"""
    import feedparser
    from lib.web_extract import extract_url_content

    print(f"[learning-note] Fetching RSS: {args.rss}")
    feed = feedparser.parse(args.rss)

    if not feed.entries:
        print("[learning-note] RSS feed 中沒有找到文章", file=sys.stderr)
        sys.exit(1)

    limit = args.latest if args.latest > 0 else 1
    entries = feed.entries[:limit]
    date_str = args.date or today_str()

    print(f"[learning-note] 準備處理 {len(entries)} 篇文章...")
    for entry in entries:
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")

        if not link:
            print(f"[learning-note] SKIP: {title} 沒有連結")
            continue

        slug = slugify(title)
        output_dir = LEARNING_INPUT_DIR / args.type
        output_path = output_dir / f"{date_str}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[learning-note] SKIP: {output_path.name} 已存在")
            continue

        print(f"\n[learning-note] Extracting: {title}")
        _, text = extract_url_content(link)

        if not text or len(text) < 50:
            # fallback: 用 RSS 的 summary/content
            text = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "")
            if len(text) < 50:
                print(f"[learning-note] SKIP: {title} 內容太短")
                continue

        output = generate_note(
            title=title,
            content=text,
            date_str=date_str,
            source=link,
            note_type=args.type,
            force=args.force,
        )
        print(f"[learning-note] Done: {output.relative_to(ROOT_DIR)}")


def handle_anybox(args) -> None:
    """--anybox 模式：從 Anybox 書籤取文章。"""
    import json
    import os
    from lib.web_extract import extract_url_content

    api_key = os.getenv("ANYBOX_API_KEY", "")
    if not api_key:
        print("[learning-note] ANYBOX_API_KEY 未設定。請先完成設定：", file=sys.stderr)
        print("", file=sys.stderr)
        print("  1. 開啟 Anybox → Preferences → General → API Key", file=sys.stderr)
        print("  2. 存入 .env：ANYBOX_API_KEY=xxxxxxxxxxxx", file=sys.stderr)
        sys.exit(1)

    base_url = "http://127.0.0.1:6391"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # 構建搜尋參數
    search_url = f"{base_url}/search"
    params: dict = {}
    if args.tag:
        params["tag"] = args.tag
    if args.starred:
        params["starred"] = True
    if args.folder:
        params["folder"] = args.folder

    try:
        try:
            import requests
            resp = requests.get(search_url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            bookmarks = resp.json()
        except ImportError:
            import urllib.request
            from urllib.parse import urlencode
            url = f"{search_url}?{urlencode(params)}" if params else search_url
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                bookmarks = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[learning-note] Anybox 連線失敗: {e}", file=sys.stderr)
        print("  請確認 Anybox app 已開啟", file=sys.stderr)
        sys.exit(1)

    if not bookmarks:
        print("[learning-note] Anybox 中沒有找到書籤", file=sys.stderr)
        return

    limit = args.latest if args.latest > 0 else len(bookmarks)
    bookmarks = bookmarks[:limit]
    date_str = args.date or today_str()

    print(f"[learning-note] 準備處理 {len(bookmarks)} 個書籤...")
    for bm in bookmarks:
        title = bm.get("title", "") or bm.get("name", "Untitled")
        url = bm.get("url", "")

        if not url:
            print(f"[learning-note] SKIP: {title} 沒有 URL")
            continue

        slug = slugify(title)
        output_dir = LEARNING_INPUT_DIR / args.type
        output_path = output_dir / f"{date_str}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[learning-note] SKIP: {output_path.name} 已存在")
            continue

        print(f"\n[learning-note] Extracting: {title}")
        _, text = extract_url_content(url)

        if not text or len(text) < 50:
            print(f"[learning-note] SKIP: {title} 內容太短")
            continue

        output = generate_note(
            title=title,
            content=text,
            date_str=date_str,
            source=url,
            note_type=args.type,
            force=args.force,
        )
        print(f"[learning-note] Done: {output.relative_to(ROOT_DIR)}")


# ── 主程式 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Learning Note Generator — 多來源學習筆記")

    # 輸入模式
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--url", type=str, help="網頁 URL 模式")
    mode.add_argument("--file", type=str, help="本地檔案模式")
    mode.add_argument("--readwise", action="store_true", help="Readwise highlights / Reader 模式")
    mode.add_argument("--rss", type=str, help="RSS feed URL 模式")
    mode.add_argument("--anybox", action="store_true", help="Anybox 書籤模式")

    # 共用參數
    parser.add_argument("--title", type=str, default=None, help="手動指定標題")
    parser.add_argument("--date", type=str, default=None, help="指定日期 (YYYY-MM-DD)")
    parser.add_argument("--type", type=str, default="articles", choices=VALID_TYPES, help="筆記類型 (預設: articles)")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的筆記")
    parser.add_argument("--latest", type=int, default=0, help="匯入最新 N 篇")
    parser.add_argument("--all", action="store_true", help="匯入全部（不限日期）")

    # Readwise 專用
    parser.add_argument("--reader", action="store_true", help="使用 Readwise Reader v3（搭配 --readwise）")

    # Anybox 專用
    parser.add_argument("--tag", type=str, default=None, help="Anybox 標籤過濾")
    parser.add_argument("--folder", type=str, default=None, help="Anybox 資料夾過濾")
    parser.add_argument("--starred", action="store_true", help="Anybox 只抓星號書籤")

    args = parser.parse_args()

    if args.url:
        handle_url(args)
    elif args.file:
        handle_file(args)
    elif args.readwise:
        handle_readwise(args)
    elif args.rss:
        handle_rss(args)
    elif args.anybox:
        handle_anybox(args)


if __name__ == "__main__":
    main()
