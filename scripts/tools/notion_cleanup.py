#!/usr/bin/env python3
"""清理 Notion 測試資料 — archive 標題含 [測試] 的頁面

使用方式：
  python3 scripts/tools/notion_cleanup.py              # 預覽模式
  python3 scripts/tools/notion_cleanup.py --execute    # 實際 archive
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import ROOT_DIR as _  # noqa: F401 — trigger .env auto-load
from lib.notion_api import archive_page, query_database


# 所有 Notion DB 環境變數
DB_VARS = {
    "NOTION_CONTENT_DB": "內容 DB",
    "NOTION_LEARNING_DB": "學習 DB",
    "NOTION_MEETING_DB": "會議記錄 DB",
    "NOTION_WEEKLY_DB": "週報 DB",
    "NOTION_PODWISE_DB_ID": "Podwise DB",
    "NOTION_CONSULTATION_DB": "諮詢紀錄 DB",
}


def _get_page_title(page: dict) -> str:
    """從 Notion page 取得標題。"""
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            title_arr = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in title_arr)
    return ""


def find_test_pages() -> list[tuple[str, str, str, str]]:
    """查詢所有 DB，回傳 (db_label, db_id, page_id, title) 列表。"""
    results = []
    for env_var, label in DB_VARS.items():
        db_id = os.environ.get(env_var, "")
        if not db_id:
            continue

        try:
            pages = query_database(
                db_id,
                filter_obj={
                    "property": "標題",
                    "title": {"contains": "[測試]"},
                },
            )
            for page in pages:
                title = _get_page_title(page)
                page_id = page.get("id", "")
                if title and page_id:
                    results.append((label, db_id, page_id, title))
        except Exception as e:
            print(f"[cleanup] {label} 查詢失敗: {e}", file=sys.stderr)

    return results


def main() -> None:
    execute = "--execute" in sys.argv

    print("[cleanup] 掃描所有 Notion DB 中 [測試] 頁面...\n")
    pages = find_test_pages()

    if not pages:
        print("[cleanup] 沒有找到測試資料，乾淨！")
        return

    print(f"[cleanup] 找到 {len(pages)} 筆測試資料：\n")
    for label, _, page_id, title in pages:
        print(f"  [{label}] {title}  (id: {page_id[:8]}...)")

    if not execute:
        print(f"\n[cleanup] 預覽模式 — 加 --execute 參數實際 archive")
        return

    print(f"\n[cleanup] 開始 archive...")
    archived = 0
    for label, _, page_id, title in pages:
        try:
            archive_page(page_id)
            print(f"  ✓ [{label}] {title}")
            archived += 1
        except Exception as e:
            print(f"  ✗ [{label}] {title} — {e}", file=sys.stderr)

    print(f"\n[cleanup] 完成！已 archive {archived}/{len(pages)} 筆")


if __name__ == "__main__":
    main()
