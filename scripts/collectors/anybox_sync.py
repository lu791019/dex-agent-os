#!/usr/bin/env python3
"""Anybox Sync — Anybox 書籤批次匯入（API 路線）

使用方式：
  ./bin/agent anybox-sync --starred --latest 3 --force
  ./bin/agent anybox-sync --tag "to-read" --latest 5 --force
  ./bin/agent anybox-sync --folder "Tech" --force

  輸出：000_Inbox/readings/YYYY-MM-DD-<slug>.md
  無 LLM，用 web_extract.py 取全文 → 存原文 + metadata

  需要：
  - Anybox app 運行中
  - .env 中設定 ANYBOX_API_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import READINGS_DIR
from lib.file_utils import ensure_dir, today_str, write_text
from lib.readwise_api import slugify


ANYBOX_BASE_URL = "http://127.0.0.1:6391"


def _check_anybox_setup() -> str | None:
    """檢查 Anybox 設定，回傳 API key 或 None。"""
    api_key = os.getenv("ANYBOX_API_KEY", "")
    if not api_key:
        print("[anybox-sync] ANYBOX_API_KEY 未設定。請先完成設定：", file=sys.stderr)
        print("", file=sys.stderr)
        print("  1. 開啟 Anybox → Preferences → General → API Key", file=sys.stderr)
        print("  2. 存入 .env：ANYBOX_API_KEY=xxxxxxxxxxxx", file=sys.stderr)
        print("", file=sys.stderr)
        print("  詳細步驟見 GUIDE.md", file=sys.stderr)
        return None
    return api_key


def _anybox_request(endpoint: str, api_key: str, params: dict | None = None) -> list[dict]:
    """呼叫 Anybox 本地 API。"""
    headers = {"X-API-Key": api_key}
    url = f"{ANYBOX_BASE_URL}/{endpoint}"

    try:
        try:
            import requests
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except ImportError:
            import urllib.request
            from urllib.parse import urlencode
            full_url = f"{url}?{urlencode(params)}" if params else url
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
    except ConnectionRefusedError:
        print("[anybox-sync] 連線失敗：Anybox app 未開啟", file=sys.stderr)
        print("  請先啟動 Anybox app", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[anybox-sync] API 錯誤: {e}", file=sys.stderr)
        print("  請確認 Anybox app 已開啟且 API Key 正確", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Anybox Sync — 書籤批次匯入")

    parser.add_argument("--tag", type=str, default=None, help="標籤過濾")
    parser.add_argument("--folder", type=str, default=None, help="資料夾過濾")
    parser.add_argument("--starred", action="store_true", help="只抓星號書籤")
    parser.add_argument("--latest", type=int, default=0, help="匯入最新 N 筆")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的檔案")

    args = parser.parse_args()

    api_key = _check_anybox_setup()
    if not api_key:
        sys.exit(1)

    # 構建搜尋參數
    params: dict = {}
    if args.tag:
        params["tag"] = args.tag
    if args.starred:
        params["starred"] = True
    if args.folder:
        params["folder"] = args.folder

    print("[anybox-sync] Querying Anybox bookmarks...")
    bookmarks = _anybox_request("search", api_key, params)

    if not bookmarks:
        print("[anybox-sync] 沒有找到書籤", file=sys.stderr)
        return

    # 無 --latest：列出
    if args.latest == 0:
        print(f"\n[anybox-sync] 找到 {len(bookmarks)} 個書籤：\n")
        for i, bm in enumerate(bookmarks[:20], 1):
            title = bm.get("title", "") or bm.get("name", "Untitled")
            url = bm.get("url", "")[:60]
            print(f"  {i:2d}. {title}")
            if url:
                print(f"      {url}")
        print(f"\n使用 --latest N 匯入最新 N 筆")
        return

    bookmarks = bookmarks[:args.latest]
    date_str = today_str()
    ensure_dir(READINGS_DIR)
    count = 0

    from lib.web_extract import extract_url_content

    print(f"[anybox-sync] 準備匯入 {len(bookmarks)} 個書籤...")
    for bm in bookmarks:
        title = bm.get("title", "") or bm.get("name", "Untitled")
        url = bm.get("url", "")
        tags = bm.get("tags", [])

        if not url:
            print(f"[anybox-sync] SKIP: {title} 沒有 URL")
            continue

        slug = slugify(title)
        output_path = READINGS_DIR / f"{date_str}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[anybox-sync] SKIP: {output_path.name} 已存在")
            continue

        print(f"\n[anybox-sync] Extracting: {title}")
        _, text = extract_url_content(url)

        if not text or len(text) < 50:
            print(f"[anybox-sync] SKIP: {title} 擷取失敗或內容太短")
            continue

        tag_str = ", ".join(t.get("name", str(t)) if isinstance(t, dict) else str(t) for t in tags) if tags else ""
        frontmatter = f"""---
title: "{title}"
source: anybox
url: "{url}"
tags: [{tag_str}]
date: {date_str}
---
"""
        full_content = f"# {title}\n\nSource: {url}\n\n{text}"
        write_text(output_path, frontmatter + full_content + "\n")
        print(f"[anybox-sync] Saved: {output_path.name}")
        count += 1

    print(f"\n[anybox-sync] 完成：匯入 {count} 筆")


if __name__ == "__main__":
    main()
