"""Readwise API 共用模組

支援兩個 API：
  - Readwise v2（classic）：highlights 匯出（podcasts / articles / books）
  - Readwise Reader v3：閱讀清單（RSS / articles / emails / epubs）

共用：
  check_readwise_setup()       — token 檢查 + 引導訊息
  readwise_headers()           — auth headers（v2 & v3 共用同一 token）
  api_request()                — 統一 API 請求（retry + rate limit + urllib fallback）
  slugify(text)                — 標題 → URL-safe slug

v2 Highlights：
  readwise_export(category)    — 匯出 highlights（category: podcasts/articles/books）
  book_to_text(book)           — highlights → text

v3 Reader：
  reader_list(category, ...)   — 列出 Reader 文件（category: rss/article/email/epub/...）
  reader_doc_to_text(doc)      — Reader 文件 → text（metadata + summary/notes）
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import READWISE_TOKEN

READWISE_API_BASE = "https://readwise.io/api/v2"
READER_API_BASE = "https://readwise.io/api/v3"


# ── 工具函式 ──────────────────────────────────────────


def slugify(text: str) -> str:
    """將標題轉為 URL-safe slug。"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:50] if text else "untitled"


def _get_requests():
    """取得 requests 模組，fallback 到 urllib。"""
    try:
        import requests
        return requests
    except ImportError:
        return None


def api_request(
    method: str,
    url: str,
    headers: dict,
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict:
    """統一 API 請求：優先用 requests，fallback 到 urllib。"""
    requests = _get_requests()

    if requests:
        for attempt in range(3):
            resp = requests.request(
                method, url, headers=headers, json=json_data, params=params, timeout=30
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2))
                print(f"[api] Rate limited, waiting {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            if resp.status_code == 401:
                print("[api] ERROR: Token 無效或 Integration 未連接 database", file=sys.stderr)
                print("  請確認 token 正確，且 Integration 已連接到 database", file=sys.stderr)
                print("  設定步驟見 GUIDE.md", file=sys.stderr)
                sys.exit(1)
            resp.raise_for_status()
            return resp.json()
        print("[api] ERROR: API 重試 3 次仍失敗", file=sys.stderr)
        sys.exit(1)
    else:
        # fallback: urllib
        import urllib.error
        import urllib.request

        req_headers = dict(headers)
        body = None
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    retry_after = int(e.headers.get("Retry-After", 2))
                    print(f"[api] Rate limited, waiting {retry_after}s...", file=sys.stderr)
                    time.sleep(retry_after)
                    continue
                if e.code == 401:
                    print("[api] ERROR: Token 無效或 Integration 未連接 database", file=sys.stderr)
                    print("  設定步驟見 GUIDE.md", file=sys.stderr)
                    sys.exit(1)
                raise
        print("[api] ERROR: API 重試 3 次仍失敗", file=sys.stderr)
        sys.exit(1)


# ── Readwise 專用 ─────────────────────────────────────


def check_readwise_setup() -> bool:
    """檢查 Readwise 設定，未設定時顯示引導。"""
    if not READWISE_TOKEN:
        print("[readwise] Token 未設定。請先完成設定：", file=sys.stderr)
        print("", file=sys.stderr)
        print("  1. 到 https://readwise.io/access_token → 複製 token", file=sys.stderr)
        print("  2. 存入 .env：READWISE_TOKEN=xxxxxxxxxxxx", file=sys.stderr)
        print("", file=sys.stderr)
        print("  詳細步驟見 GUIDE.md", file=sys.stderr)
        return False
    return True


def readwise_headers() -> dict:
    """Readwise API request headers。"""
    return {
        "Authorization": f"Token {READWISE_TOKEN}",
    }


def readwise_export(
    category: str | None = None,
    limit: int = 0,
    fetch_all: bool = False,
) -> list[dict]:
    """從 Readwise 匯出 highlights，支援 category 過濾。

    Args:
        category: 過濾類別（podcasts / articles / books / tweets 等），None 表示全部
        limit: 限制回傳筆數（0=預設 7 天內）
        fetch_all: 取得全部（不限日期）
    """
    headers = readwise_headers()
    url = f"{READWISE_API_BASE}/export/"

    params: dict = {}

    # 非 fetch_all 且無 limit 時，預設只抓 7 天內
    if not fetch_all and limit == 0:
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        params["updatedAfter"] = seven_days_ago

    all_books: list[dict] = []
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            params["pageCursor"] = next_cursor

        data = api_request("GET", url, headers, params=params)
        results = data.get("results", [])

        for book in results:
            if category is None or book.get("category") == category:
                all_books.append(book)

        next_cursor = data.get("nextPageCursor")
        has_more = next_cursor is not None

        # 已達到 limit 就停
        if limit > 0 and len(all_books) >= limit:
            all_books = all_books[:limit]
            break

        time.sleep(0.35)

    return all_books


def book_to_text(book: dict) -> str:
    """將 Readwise v2 book 的 highlights 合併為文字。"""
    lines = []

    title = book.get("title", "Untitled")
    author = book.get("author", "")
    source_url = book.get("source_url", "")

    lines.append(f"# {title}")
    if author:
        lines.append(f"Host/Author: {author}")
    if source_url:
        lines.append(f"Source: {source_url}")
    lines.append("")

    highlights = book.get("highlights", [])
    if highlights:
        lines.append("## Highlights & Notes")
        for hl in highlights:
            text = hl.get("text", "")
            note = hl.get("note", "")
            if text:
                lines.append(f"\n> {text}")
            if note:
                lines.append(f"\n**Note:** {note}")

    return "\n".join(lines)


# ── Readwise Reader v3 ────────────────────────────────


def reader_list(
    category: str | None = None,
    location: str | None = None,
    limit: int = 0,
    fetch_all: bool = False,
    updated_after: str | None = None,
) -> list[dict]:
    """從 Readwise Reader v3 列出文件。

    Args:
        category: 過濾類別（rss / article / email / epub / tweet / video / pdf / highlight），None 全部
        location: 過濾位置（new / later / archive / feed），None 全部
        limit: 限制回傳筆數（0=預設 7 天內）
        fetch_all: 取得全部（不限日期）
        updated_after: ISO 8601 日期字串，只抓此日期之後更新的
    """
    headers = readwise_headers()
    url = f"{READER_API_BASE}/list/"

    params: dict = {"page_size": 100}
    if category:
        params["category"] = category
    if location:
        params["location"] = location

    # 日期過濾
    if updated_after:
        params["updatedAfter"] = updated_after
    elif not fetch_all and limit == 0:
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        params["updatedAfter"] = seven_days_ago

    all_docs: list[dict] = []
    next_cursor = None

    while True:
        if next_cursor:
            params["pageCursor"] = next_cursor

        data = api_request("GET", url, headers, params=params)
        results = data.get("results", [])
        all_docs.extend(results)

        next_cursor = data.get("nextPageCursor")

        # 已達到 limit 就停
        if limit > 0 and len(all_docs) >= limit:
            all_docs = all_docs[:limit]
            break

        if not next_cursor:
            break

        time.sleep(0.35)

    return all_docs


def reader_doc_to_text(doc: dict) -> str:
    """將 Reader v3 文件轉為文字（metadata + summary + notes）。"""
    lines = []

    title = doc.get("title", "Untitled")
    author = doc.get("author", "")
    source_url = doc.get("source_url", "")
    site_name = doc.get("site_name", "")
    summary = doc.get("summary", "")
    content = doc.get("content", "")
    notes = doc.get("notes", "")

    lines.append(f"# {title}")
    if author:
        lines.append(f"Author: {author}")
    if site_name:
        lines.append(f"Site: {site_name}")
    if source_url:
        lines.append(f"Source: {source_url}")
    lines.append("")

    if summary:
        lines.append("## Summary")
        lines.append(summary)
        lines.append("")

    if content:
        lines.append("## Content")
        lines.append(content)
        lines.append("")

    if notes:
        lines.append("## Notes")
        lines.append(notes)
        lines.append("")

    return "\n".join(lines)
