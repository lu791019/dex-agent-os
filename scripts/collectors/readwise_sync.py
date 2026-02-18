#!/usr/bin/env python3
"""Readwise Sync — Readwise v2 highlights + v3 Reader 批次匯入

使用方式：
  # v2 Highlights（已標註的文章/書籍）
  ./bin/agent readwise-sync                              # 列出最近 7 天
  ./bin/agent readwise-sync --latest 3 --force           # 匯入最新 3 筆
  ./bin/agent readwise-sync --category books --force     # 只匯入書籍
  ./bin/agent readwise-sync --all --force                # 匯入全部
  ./bin/agent readwise-sync --since 2026-02-01 --force   # 匯入指定日期後

  # v3 Reader（RSS / 閱讀清單）— 加 --reader flag
  ./bin/agent readwise-sync --reader                     # 列出最近 Reader 文件
  ./bin/agent readwise-sync --reader --latest 5 --force  # 匯入最新 5 篇

  輸出：000_Inbox/readings/YYYY-MM-DD-<slug>.md
  無 LLM，直接結構化 highlights/文件為 Markdown
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import READINGS_DIR
from lib.file_utils import ensure_dir, today_str, write_text
from lib.readwise_api import (
    book_to_text,
    check_readwise_setup,
    reader_doc_to_text,
    reader_list,
    readwise_export,
    slugify,
)


# ── v2 Highlights ─────────────────────────────────────

def sync_highlights(args) -> None:
    """v2: 匯入 Readwise highlights。"""
    limit = args.latest if args.latest > 0 else 0
    category = None if args.category == "all" else args.category
    updated_after = args.since

    print(f"[readwise-sync] Querying Readwise v2 highlights (category={args.category})...")
    books = readwise_export(
        category=category,
        limit=limit,
        fetch_all=args.all or bool(updated_after),
    )

    # --since 手動過濾
    if updated_after and books:
        books = [b for b in books if (b.get("updated", "") or "") >= updated_after]

    if not books:
        print("[readwise-sync] 沒有找到 highlights", file=sys.stderr)
        return

    # 無 --latest 且非 --all 且非 --since：列出
    if args.latest == 0 and not args.all and not updated_after:
        print(f"\n[readwise-sync] 找到 {len(books)} 筆 highlights：\n")
        for i, book in enumerate(books[:20], 1):
            title = book.get("title", "Untitled")
            cat = book.get("category", "?")
            hl_count = len(book.get("highlights", []))
            print(f"  {i:2d}. [{cat}] {title} ({hl_count} highlights)")
        print(f"\n使用 --latest N 匯入最新 N 筆，或 --all 匯入全部")
        return

    print(f"[readwise-sync] 準備匯入 {len(books)} 筆...")
    ensure_dir(READINGS_DIR)
    count = 0

    for book in books:
        title = book.get("title", "Untitled")
        updated = book.get("updated", "")
        book_date = updated[:10] if updated else today_str()

        slug = slugify(title)
        output_path = READINGS_DIR / f"{book_date}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[readwise-sync] SKIP: {output_path.name} 已存在")
            continue

        content = book_to_text(book)
        if len(content) < 20:
            print(f"[readwise-sync] SKIP: {title} 內容太短")
            continue

        # 加上 frontmatter
        category_val = book.get("category", "unknown")
        author = book.get("author", "")
        source_url = book.get("source_url", "")
        hl_count = len(book.get("highlights", []))

        frontmatter = f"""---
title: "{title}"
source: readwise-v2
category: {category_val}
author: "{author}"
url: "{source_url}"
highlights: {hl_count}
date: {book_date}
---
"""
        write_text(output_path, frontmatter + content + "\n")
        print(f"[readwise-sync] Saved: {output_path.name}")
        count += 1

    print(f"\n[readwise-sync] 完成：匯入 {count} 筆")


# ── v3 Reader ─────────────────────────────────────────

def sync_reader(args) -> None:
    """v3: 匯入 Readwise Reader 文件。"""
    limit = args.latest if args.latest > 0 else 0
    updated_after = args.since

    print("[readwise-sync] Querying Readwise Reader v3...")
    docs = reader_list(
        limit=limit,
        fetch_all=args.all or bool(updated_after),
        updated_after=updated_after,
    )

    if not docs:
        print("[readwise-sync] Reader 中沒有找到文件", file=sys.stderr)
        return

    # 無 --latest 且非 --all 且非 --since：列出
    if args.latest == 0 and not args.all and not updated_after:
        print(f"\n[readwise-sync] 找到 {len(docs)} 篇 Reader 文件：\n")
        for i, doc in enumerate(docs[:20], 1):
            title = doc.get("title", "Untitled")
            cat = doc.get("category", "?")
            site = doc.get("site_name", "")
            label = f" ({site})" if site else ""
            print(f"  {i:2d}. [{cat}] {title}{label}")
        print(f"\n使用 --latest N 匯入最新 N 篇，或 --all 匯入全部")
        return

    print(f"[readwise-sync] 準備匯入 {len(docs)} 篇...")
    ensure_dir(READINGS_DIR)
    count = 0

    for doc in docs:
        title = doc.get("title", "Untitled")
        updated = doc.get("updated_at", "")
        doc_date = updated[:10] if updated else today_str()
        source_url = doc.get("source_url", "")
        category = doc.get("category", "unknown")
        author = doc.get("author", "")
        site_name = doc.get("site_name", "")

        slug = slugify(title)
        output_path = READINGS_DIR / f"{doc_date}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[readwise-sync] SKIP: {output_path.name} 已存在")
            continue

        content = reader_doc_to_text(doc)
        if len(content) < 20:
            print(f"[readwise-sync] SKIP: {title} 內容太短")
            continue

        frontmatter = f"""---
title: "{title}"
source: readwise-reader
category: {category}
author: "{author}"
site: "{site_name}"
url: "{source_url}"
date: {doc_date}
---
"""
        write_text(output_path, frontmatter + content + "\n")
        print(f"[readwise-sync] Saved: {output_path.name}")
        count += 1

    print(f"\n[readwise-sync] 完成：匯入 {count} 篇")


# ── 主程式 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Readwise Sync — v2 highlights + v3 Reader 批次匯入")

    parser.add_argument("--reader", action="store_true", help="使用 Readwise Reader v3（預設 v2 highlights）")
    parser.add_argument("--category", type=str, default="all", choices=["articles", "books", "podcasts", "all"],
                        help="v2 highlights 類別過濾 (預設: all)")
    parser.add_argument("--latest", type=int, default=0, help="匯入最新 N 筆")
    parser.add_argument("--all", action="store_true", help="匯入全部（不限日期）")
    parser.add_argument("--since", type=str, default=None, help="匯入指定日期後 (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的檔案")

    args = parser.parse_args()

    if not check_readwise_setup():
        sys.exit(1)

    if args.reader:
        sync_reader(args)
    else:
        sync_highlights(args)


if __name__ == "__main__":
    main()
