#!/usr/bin/env python3
"""RSS Sync — RSS 批次匯入

使用方式：
  # 單一 feed
  ./bin/agent rss-sync --feed "https://jvns.ca/atom.xml" --latest 3 --force

  # OPML 批次
  ./bin/agent rss-sync --opml config/subscriptions.opml --latest 5 --force

  # 列出 feed 內容
  ./bin/agent rss-sync --feed "URL"   # 無 --latest 時列出文章

  輸出：000_Inbox/readings/YYYY-MM-DD-<slug>.md
  無 LLM，直接存原文 + metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import READINGS_DIR
from lib.file_utils import ensure_dir, today_str, write_text
from lib.readwise_api import slugify


def parse_opml(opml_path: Path) -> list[str]:
    """解析 OPML 檔案，回傳 feed URL 列表。"""
    if not opml_path.exists():
        print(f"[rss-sync] ERROR: OPML 檔案不存在: {opml_path}", file=sys.stderr)
        sys.exit(1)

    tree = ET.parse(opml_path)
    root = tree.getroot()
    urls = []
    for outline in root.iter("outline"):
        xml_url = outline.get("xmlUrl")
        if xml_url:
            urls.append(xml_url)
    return urls


def fetch_and_save_entries(feed_url: str, limit: int, force: bool) -> int:
    """擷取 RSS feed 並存檔，回傳成功筆數。"""
    import feedparser

    print(f"\n[rss-sync] Fetching: {feed_url}")
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        print(f"[rss-sync] 沒有找到文章: {feed_url}", file=sys.stderr)
        return 0

    feed_title = feed.feed.get("title", "Unknown Feed")

    # 無 limit：列出
    if limit == 0:
        print(f"\n[rss-sync] {feed_title} — {len(feed.entries)} 篇文章：\n")
        for i, entry in enumerate(feed.entries[:20], 1):
            title = entry.get("title", "Untitled")
            published = entry.get("published", "")[:16]
            print(f"  {i:2d}. [{published}] {title}")
        print(f"\n使用 --latest N 匯入最新 N 篇")
        return 0

    entries = feed.entries[:limit]
    ensure_dir(READINGS_DIR)
    count = 0
    date_str = today_str()

    for entry in entries:
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")
        published = entry.get("published", "")
        author = entry.get("author", "")

        slug = slugify(title)
        output_path = READINGS_DIR / f"{date_str}-{slug}.md"

        if output_path.exists() and not force:
            print(f"[rss-sync] SKIP: {output_path.name} 已存在")
            continue

        # 取全文：先試 web_extract，fallback 到 RSS summary
        content = ""
        if link:
            from lib.web_extract import extract_url_content
            _, full_text = extract_url_content(link)
            if full_text and len(full_text) >= 100:
                content = full_text

        if not content:
            # Fallback: RSS 內建 content 或 summary
            content_list = entry.get("content", [])
            if content_list:
                content = content_list[0].get("value", "")
            if not content:
                content = entry.get("summary", "")

        if len(content) < 20:
            print(f"[rss-sync] SKIP: {title} 內容太短")
            continue

        frontmatter = f"""---
title: "{title}"
source: rss
feed: "{feed_title}"
author: "{author}"
url: "{link}"
published: "{published}"
date: {date_str}
---
"""
        full_content = f"# {title}\n\n"
        if link:
            full_content += f"Source: {link}\n\n"
        full_content += content

        write_text(output_path, frontmatter + full_content + "\n")
        print(f"[rss-sync] Saved: {output_path.name}")
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="RSS Sync — RSS 批次匯入")

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--feed", type=str, help="單一 RSS feed URL")
    source.add_argument("--opml", type=str, help="OPML 檔案路徑")

    parser.add_argument("--latest", type=int, default=0, help="每個 feed 匯入最新 N 篇")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的檔案")

    args = parser.parse_args()

    if args.feed:
        count = fetch_and_save_entries(args.feed, args.latest, args.force)
        if args.latest > 0:
            print(f"\n[rss-sync] 完成：匯入 {count} 篇")
    else:
        opml_path = Path(args.opml).expanduser()
        if not opml_path.is_absolute():
            opml_path = ROOT_DIR / args.opml
        feeds = parse_opml(opml_path)
        if not feeds:
            print("[rss-sync] OPML 中沒有找到 feed", file=sys.stderr)
            sys.exit(1)

        print(f"[rss-sync] 找到 {len(feeds)} 個 feed")
        total = 0
        for feed_url in feeds:
            total += fetch_and_save_entries(feed_url, args.latest, args.force)

        if args.latest > 0:
            print(f"\n[rss-sync] 完成：共匯入 {total} 篇")


if __name__ == "__main__":
    main()
