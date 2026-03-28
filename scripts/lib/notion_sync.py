"""Notion 同步工具 — 提供各管道寫入 Notion 的函式

供 workflow / Python 腳本呼叫：
  sync_insight_to_notion()  — Insight → 內容 DB
  sync_learning_to_notion() — 學習筆記 → 學習 DB
  sync_meeting_to_notion()  — 會議紀錄 → 會議記錄 DB
  sync_weekly_to_notion()   — 週報/電子報 → 週報 DB
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))


def sync_insight_to_notion(
    title: str,
    content: str,
    date_str: str,
    source: str = "",
    tags: list[str] | None = None,
    status: str = "seed",
) -> str:
    """Insight → Notion 內容 DB。回傳 page ID。"""
    db_id = os.environ.get("NOTION_CONTENT_DB", "")
    if not db_id:
        print("[notion-sync] NOTION_CONTENT_DB 未設定", file=sys.stderr)
        return ""

    from lib.notion_api import (
        add_page, prop_title, prop_rich_text, prop_select,
        prop_multi_select, prop_date, prop_checkbox, block_paragraph,
    )

    props = {
        "標題": prop_title(title),
        "狀態": prop_select(status),
        "核心觀點": prop_rich_text(content[:2000]),
        "素材": prop_rich_text(source[:2000]),
        "建立日期": prop_date(date_str),
        "Threads": prop_checkbox(False),
        "Facebook": prop_checkbox(False),
        "Blog": prop_checkbox(False),
        "短影音": prop_checkbox(False),
        "電子報": prop_checkbox(False),
    }
    if tags:
        props["標籤"] = prop_multi_select(tags)

    # 全文放 body
    children = []
    if content:
        for i in range(0, min(len(content), 20000), 2000):
            children.append(block_paragraph(content[i:i+2000]))

    page_id = add_page(db_id, properties=props, children=children if children else None)
    print(f"[notion-sync] Insight → Notion: {title[:40]}...")
    return page_id


def sync_learning_to_notion(
    title: str,
    full_text: str,
    date_str: str,
    source_type: str = "文章",
    author: str = "",
    url: str = "",
    summary: str = "",
    topic: str = "",
) -> str:
    """學習筆記 → Notion 學習 DB。回傳 page ID。"""
    db_id = os.environ.get("NOTION_LEARNING_DB", "")
    if not db_id:
        return ""

    from lib.notion_api import (
        add_page, prop_title, prop_rich_text, prop_select,
        prop_date, prop_url, prop_checkbox, block_paragraph,
    )

    props = {
        "標題": prop_title(title),
        "日期": prop_date(date_str),
        "來源類型": prop_select(source_type),
        "作者": prop_rich_text(author),
        "URL": prop_url(url) if url else prop_url(""),
        "摘要": prop_rich_text(summary[:2000]),
        "⭐": prop_checkbox(False),
    }
    if topic:
        props["主題"] = prop_select(topic)

    children = []
    if full_text:
        for i in range(0, min(len(full_text), 20000), 2000):
            children.append(block_paragraph(full_text[i:i+2000]))

    page_id = add_page(db_id, properties=props, children=children if children else None)
    return page_id


def sync_meeting_to_notion(
    title: str,
    content: str,
    date_str: str,
    source: str = "手動",
    speakers: str = "",
    summary: str = "",
) -> str:
    """會議紀錄 → Notion 會議記錄 DB。回傳 page ID。"""
    db_id = os.environ.get("NOTION_MEETING_DB", "")
    if not db_id:
        return ""

    from lib.notion_api import (
        add_page, prop_title, prop_rich_text, prop_select,
        prop_date, block_paragraph,
    )

    props = {
        "標題": prop_title(title),
        "日期": prop_date(date_str),
        "來源": prop_select(source),
        "講者": prop_rich_text(speakers),
        "摘要": prop_rich_text(summary[:2000]),
    }

    children = []
    if content:
        for i in range(0, min(len(content), 40000), 2000):
            children.append(block_paragraph(content[i:i+2000]))

    return add_page(db_id, properties=props, children=children if children else None)


def sync_weekly_to_notion(
    title: str,
    content: str,
    week_str: str,
    nl_type: str = "weekly-review",
    date_range: str = "",
    date_str: str = "",
) -> str:
    """週報/電子報 → Notion 週報 DB。回傳 page ID。"""
    db_id = os.environ.get("NOTION_WEEKLY_DB", "")
    if not db_id:
        return ""

    from lib.notion_api import (
        add_page, prop_title, prop_rich_text, prop_select,
        prop_date, block_paragraph,
    )

    props = {
        "標題": prop_title(title),
        "週次": prop_rich_text(week_str),
        "類型": prop_select(nl_type),
        "日期範圍": prop_rich_text(date_range),
    }
    if date_str:
        props["建立日期"] = prop_date(date_str)

    children = []
    if content:
        for i in range(0, min(len(content), 40000), 2000):
            children.append(block_paragraph(content[i:i+2000]))

    return add_page(db_id, properties=props, children=children if children else None)
