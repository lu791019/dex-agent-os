"""Notion API 共用模組

提供：
  notion_headers()       — auth headers
  notion_request()       — 統一 API 請求（retry + error handling）
  create_database()      — 在 parent page 下建 database
  add_page()             — 在 database 中新增一筆
  query_database()       — 查詢 database
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _get_token() -> str:
    token = os.environ.get("NOTION_TOKEN", "")
    if not token:
        print("[notion] NOTION_TOKEN 未設定", file=sys.stderr)
    return token


def notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion_request(
    method: str,
    endpoint: str,
    data: dict | None = None,
) -> dict:
    """統一 Notion API 請求。"""
    url = f"{NOTION_API_BASE}/{endpoint}"
    headers = notion_headers()

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 2))
                print(f"[notion] Rate limited, waiting {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            print(f"[notion] HTTP {e.code}: {error_body[:200]}", file=sys.stderr)
            raise
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                continue
            raise

    return {}


def create_database(
    parent_page_id: str,
    title: str,
    properties: dict,
    icon_emoji: str | None = None,
) -> str:
    """在 parent page 下建立 database，回傳 database ID。"""
    body: dict = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties,
    }
    if icon_emoji:
        body["icon"] = {"type": "emoji", "emoji": icon_emoji}

    result = notion_request("POST", "databases", data=body)
    db_id = result.get("id", "")
    print(f"[notion] 建立 DB: {title} ({db_id})")
    return db_id


def add_page(
    database_id: str,
    properties: dict,
    children: list[dict] | None = None,
) -> str:
    """在 database 中新增一筆，回傳 page ID。"""
    body: dict = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    if children:
        body["children"] = children

    result = notion_request("POST", "pages", data=body)
    return result.get("id", "")


def query_database(
    database_id: str,
    filter_obj: dict | None = None,
    sorts: list[dict] | None = None,
    page_size: int = 100,
) -> list[dict]:
    """查詢 database，回傳 results list。"""
    body: dict = {"page_size": page_size}
    if filter_obj:
        body["filter"] = filter_obj
    if sorts:
        body["sorts"] = sorts

    result = notion_request("POST", f"databases/{database_id}/query", data=body)
    return result.get("results", [])


# ── Helper: 常用 property builders ──────────────────


def prop_title(text: str) -> dict:
    return {"title": [{"text": {"content": text}}]}


def _truncate_notion(text: str, limit: int = 2000) -> list[str]:
    """按 Notion 的 UTF-16 code unit 計數切分文字。"""
    chunks = []
    current = []
    current_len = 0
    for ch in text:
        # 計算 UTF-16 code units：BMP 字元 = 1，supplementary（emoji 等）= 2
        cu = 2 if ord(ch) > 0xFFFF else 1
        if current_len + cu > limit:
            chunks.append("".join(current))
            current = [ch]
            current_len = cu
        else:
            current.append(ch)
            current_len += cu
    if current:
        chunks.append("".join(current))
    return chunks if chunks else [""]


def prop_rich_text(text: str) -> dict:
    # Notion rich_text 每個 block 上限 2000 UTF-16 code units
    blocks = [{"text": {"content": chunk}} for chunk in _truncate_notion(text, 2000)]
    return {"rich_text": blocks}


def prop_select(name: str) -> dict:
    return {"select": {"name": name}}


def prop_multi_select(names: list[str]) -> dict:
    return {"multi_select": [{"name": n} for n in names]}


def prop_date(date_str: str) -> dict:
    return {"date": {"start": date_str}}


def prop_url(url: str) -> dict:
    return {"url": url}


def prop_checkbox(checked: bool) -> dict:
    return {"checkbox": checked}


def prop_relation(page_ids: list[str]) -> dict:
    """Relation value（寫入頁面時使用）：關聯到其他 DB 的 page IDs。"""
    return {"relation": [{"id": pid} for pid in page_ids]}


def prop_number(value: float | int) -> dict:
    return {"number": value}


def schema_relation(database_id: str, dual: bool = True) -> dict:
    """建 DB schema 時的 relation 欄位定義。

    dual=True 會在目標 DB 自動建立反向欄位（雙向關聯）；
    dual=False 為單向關聯。
    """
    if dual:
        return {
            "relation": {
                "database_id": database_id,
                "type": "dual_property",
                "dual_property": {},
            }
        }
    return {
        "relation": {
            "database_id": database_id,
            "type": "single_property",
            "single_property": {},
        }
    }


def update_database(database_id: str, properties: dict) -> dict:
    """更新 database schema（加/改 properties）。"""
    return notion_request("PATCH", f"databases/{database_id}", data={"properties": properties})


# ── Helper: content blocks ──────────────────────────


def block_paragraph(text: str) -> dict:
    # 每個 block 上限 2000 UTF-16 code units
    blocks = [{"type": "text", "text": {"content": chunk}} for chunk in _truncate_notion(text, 2000)]
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": blocks},
    }


def archive_page(page_id: str) -> dict:
    """Archive（軟刪除）一個 page。"""
    return notion_request("PATCH", f"pages/{page_id}", data={"archived": True})


def update_page(
    page_id: str,
    properties: dict,
) -> dict:
    """更新 page properties。"""
    return notion_request("PATCH", f"pages/{page_id}", data={"properties": properties})


def append_blocks(
    page_id: str,
    children: list[dict],
) -> dict:
    """在 page body 追加 blocks。"""
    return notion_request("PATCH", f"blocks/{page_id}/children", data={"children": children})


def block_heading(text: str, level: int = 2) -> dict:
    h_type = f"heading_{level}"
    return {
        "object": "block",
        "type": h_type,
        h_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }
