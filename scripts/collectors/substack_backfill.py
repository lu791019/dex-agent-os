#!/usr/bin/env python3
"""Substack 歷史回補 — 用非官方 API 抓歷史文章寫入 Google Sheet

使用方式：
  ./bin/agent substack-backfill <subdomain> [--limit 50]     # 回補指定 Substack
  ./bin/agent substack-backfill --all [--limit 20]           # 回補所有 rss-feeds.txt 中的 Substack
  ./bin/agent substack-backfill --dry-run <subdomain>        # 預覽不寫入
  ./bin/agent substack-backfill --list                       # 列出可回補的 Substack

注意：使用 Substack 非官方 API，無需認證，但可能隨時失效。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import GOOGLE_SHEET_ID
from lib.google_api import get_sheets_service

FEEDS_FILE = ROOT_DIR / "config" / "rss-feeds.txt"
SHEET_NAME = "Readings"
TOPIC_CATEGORIES = ["技術", "生產力", "職涯", "創作", "投資", "產業", "生活", "其他"]


# ── Substack API ─────────────────────────────────────


def _fetch_archive(subdomain: str, offset: int = 0, limit: int = 12) -> list[dict]:
    """從 Substack 非官方 API 抓文章列表。"""
    url = f"https://{subdomain}.substack.com/api/v1/archive?sort=new&offset={offset}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  [WARN] {subdomain}.substack.com 不存在或 API 不可用", file=sys.stderr)
        else:
            print(f"  [WARN] HTTP {e.code} for {subdomain}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  [WARN] {subdomain}: {e}", file=sys.stderr)
        return []


def _post_to_row(post: dict, subdomain: str) -> list[str]:
    """將 Substack post 轉為 Sheet 行。"""
    date_str = ""
    if post.get("post_date"):
        try:
            dt = datetime.fromisoformat(post["post_date"].replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_str = datetime.now().strftime("%Y-%m-%d")

    author = ""
    bylines = post.get("publishedBylines", [])
    if bylines:
        author = bylines[0].get("name", "")

    title = post.get("title", "Untitled") or "Untitled"
    url = post.get("canonical_url", "") or f"https://{subdomain}.substack.com/p/{post.get('slug', '')}"

    # 摘要：用 subtitle 或 description 或 truncated_body_text
    summary = post.get("subtitle", "") or post.get("description", "") or ""
    if not summary:
        summary = (post.get("truncated_body_text", "") or "")[:500]
    if len(summary) > 500:
        summary = summary[:497] + "..."

    return [date_str, "rss", author, title, url, summary, ""]


def _get_substack_subdomains() -> list[str]:
    """從 rss-feeds.txt 提取 Substack subdomain 清單。"""
    if not FEEDS_FILE.exists():
        return []
    subdomains = []
    for line in FEEDS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.search(r"https?://([^.]+)\.substack\.com/feed", line)
        if m:
            subdomains.append(m.group(1))
    return subdomains


# ── 主邏輯 ───────────────────────────────────────────


def backfill(subdomain: str, limit: int = 50, dry_run: bool = False, use_llm: bool = True):
    """回補單一 Substack 的歷史文章。"""
    print(f"[substack-backfill] {subdomain}.substack.com (limit={limit})")

    all_posts = []
    offset = 0
    batch_size = 12  # Substack API 每頁最多 12 篇

    while len(all_posts) < limit:
        posts = _fetch_archive(subdomain, offset=offset, limit=batch_size)
        if not posts:
            break
        all_posts.extend(posts)
        offset += len(posts)
        if len(posts) < batch_size:
            break
        time.sleep(0.5)  # 避免 rate limit

    all_posts = all_posts[:limit]
    print(f"  API 回傳: {len(all_posts)} 篇")

    if not all_posts:
        return 0

    rows = [_post_to_row(p, subdomain) for p in all_posts]

    if dry_run:
        for r in rows[:5]:
            print(f"  [{r[0]}] {r[3][:60]}")
        if len(rows) > 5:
            print(f"  ... 還有 {len(rows) - 5} 篇")
        return len(rows)

    # Sheet 寫入（去重）
    service = get_sheets_service()
    if not service:
        return 0

    # 讀取已存在的標題
    result = service.spreadsheets().values().get(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{SHEET_NAME}'!D:D",
    ).execute()
    existing = {row[0].strip().lower() for row in result.get("values", []) if row}

    new_rows = [r for r in rows if r[3].strip().lower() not in existing]
    print(f"  新增（去重後）: {new_rows and len(new_rows) or 0} 篇")

    if not new_rows:
        return 0

    # 按日期倒序
    new_rows.sort(key=lambda r: r[0], reverse=True)

    # LLM 中文摘要
    if use_llm:
        from collectors.rss_to_sheets import _enrich_rows_with_llm
        print(f"  LLM 中文摘要 + 分類...")
        new_rows = _enrich_rows_with_llm(new_rows, batch_size=10)

    # 插入到 header 下方
    meta = service.spreadsheets().get(spreadsheetId=GOOGLE_SHEET_ID).execute()
    sheet_id = None
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == SHEET_NAME:
            sheet_id = s["properties"]["sheetId"]
            break

    if sheet_id is not None:
        service.spreadsheets().batchUpdate(
            spreadsheetId=GOOGLE_SHEET_ID,
            body={"requests": [{
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": 1,
                        "endIndex": 1 + len(new_rows),
                    },
                    "inheritFromBefore": False,
                }
            }]},
        ).execute()
        service.spreadsheets().values().update(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f"'{SHEET_NAME}'!A2",
            valueInputOption="RAW",
            body={"values": new_rows},
        ).execute()

    print(f"  寫入 {len(new_rows)} 篇")
    return len(new_rows)


def main():
    parser = argparse.ArgumentParser(description="Substack 歷史回補")
    parser.add_argument("subdomain", nargs="?", help="Substack subdomain（如 swyx）")
    parser.add_argument("--all", action="store_true", help="回補所有 rss-feeds.txt 中的 Substack")
    parser.add_argument("--list", action="store_true", help="列出可回補的 Substack")
    parser.add_argument("--limit", type=int, default=50, help="每個 Substack 最多抓幾篇（預設 50）")
    parser.add_argument("--dry-run", action="store_true", help="預覽不寫入")
    parser.add_argument("--no-llm", action="store_true", help="跳過 LLM 摘要")
    args = parser.parse_args()

    if args.list:
        subs = _get_substack_subdomains()
        print(f"rss-feeds.txt 中有 {len(subs)} 個 Substack：")
        for s in subs:
            print(f"  {s}.substack.com")
        return

    if args.all:
        subs = _get_substack_subdomains()
        print(f"[substack-backfill] 回補 {len(subs)} 個 Substack（每個 limit={args.limit}）\n")
        total = 0
        for sub in subs:
            total += backfill(sub, limit=args.limit, dry_run=args.dry_run, use_llm=not args.no_llm)
            time.sleep(1)
        print(f"\n[substack-backfill] 總計寫入 {total} 篇")
        return

    if not args.subdomain:
        parser.print_help()
        return

    backfill(args.subdomain, limit=args.limit, dry_run=args.dry_run, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
