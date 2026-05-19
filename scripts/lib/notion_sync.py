"""Notion 同步工具 — 提供各管道寫入 Notion 的函式

供 workflow / Python 腳本呼叫：
  sync_insight_to_notion()  — [v1] Insight → 內容 DB (seed) — 舊流程
  sync_topic_to_notion()    — [v1] Topic → 內容 DB (developing) — 舊流程
  sync_draft_to_notion()    — [v1] 草稿 → 內容 DB (打勾 + 追加草稿) — 舊流程
  sync_learning_to_notion() — 學習筆記 → 學習 DB
  sync_meeting_to_notion()  — 會議紀錄 → 會議記錄 DB
  sync_weekly_to_notion()   — 週報/電子報 → 週報 DB

  sync_insight_v2()         — [v2] Insight DB（新）
  sync_topic_v2()            — [v2] Topic DB（新，含 relations）
  sync_draft_v2()            — [v2] Content DB（新結構：每頻道一筆 + Channel + Related Topic）
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
        for i in range(0, min(len(content), 20000), 1900):
            children.append(block_paragraph(content[i:i+1900]))

    page_id = add_page(db_id, properties=props, children=children if children else None)
    print(f"[notion-sync] Insight → Notion: {title[:40]}...")
    return page_id


def _find_content_page(db_id: str, title: str) -> str | None:
    """在 CONTENT_DB 中找標題匹配的頁面，回傳 page_id 或 None。"""
    from lib.notion_api import query_database

    results = query_database(db_id, filter_obj={
        "property": "標題",
        "title": {"equals": title},
    }, page_size=1)
    if results:
        return results[0].get("id")
    return None


def sync_topic_to_notion(
    title: str,
    content: str,
    date_str: str,
    tags: list[str] | None = None,
) -> str:
    """Topic → Notion 內容 DB。找到同名 seed 就更新，否則建新頁面。"""
    db_id = os.environ.get("NOTION_CONTENT_DB", "")
    if not db_id:
        return ""

    from lib.notion_api import (
        add_page, update_page, append_blocks, prop_title, prop_rich_text,
        prop_select, prop_multi_select, prop_date, prop_checkbox,
        block_heading, block_paragraph,
    )

    existing_id = _find_content_page(db_id, title)

    if existing_id:
        # 更新現有 seed → developing
        update_page(existing_id, {
            "狀態": prop_select("developing"),
            "核心觀點": prop_rich_text(content[:2000]),
        })
        # 追加 Topic 內容
        blocks = [block_heading("Topic 企劃", level=2)]
        for i in range(0, min(len(content), 20000), 1900):
            blocks.append(block_paragraph(content[i:i+1900]))
        append_blocks(existing_id, blocks)
        print(f"[notion-sync] Topic 更新: {title[:40]}...")
        return existing_id
    else:
        # 建新頁面
        props = {
            "標題": prop_title(title),
            "狀態": prop_select("developing"),
            "核心觀點": prop_rich_text(content[:2000]),
            "建立日期": prop_date(date_str),
            "Threads": prop_checkbox(False),
            "Facebook": prop_checkbox(False),
            "Blog": prop_checkbox(False),
            "短影音": prop_checkbox(False),
            "電子報": prop_checkbox(False),
        }
        if tags:
            props["標籤"] = prop_multi_select(tags)

        children = [block_heading("Topic 企劃", level=2)]
        for i in range(0, min(len(content), 20000), 1900):
            children.append(block_paragraph(content[i:i+1900]))

        page_id = add_page(db_id, properties=props, children=children)
        print(f"[notion-sync] Topic 新建: {title[:40]}...")
        return page_id


def sync_draft_to_notion(
    title: str,
    channel: str,
    draft_content: str,
) -> str:
    """草稿 → Notion 內容 DB。找到同名頁面，打勾 + 追加草稿。"""
    db_id = os.environ.get("NOTION_CONTENT_DB", "")
    if not db_id:
        return ""

    from lib.notion_api import (
        update_page, append_blocks, prop_select, prop_checkbox,
        block_heading, block_paragraph,
    )

    page_id = _find_content_page(db_id, title)
    if not page_id:
        print(f"[notion-sync] 找不到 Content 頁面: {title[:40]}", file=sys.stderr)
        return ""

    # 打勾對應頻道 + 更新狀態
    channel_map = {
        "threads": "Threads",
        "facebook": "Facebook",
        "blog": "Blog",
        "short-video": "短影音",
        "newsletter": "電子報",
    }
    prop_name = channel_map.get(channel, channel)
    props = {
        prop_name: prop_checkbox(True),
        "狀態": prop_select("drafting"),
    }
    update_page(page_id, props)

    # 追加草稿內容
    blocks = [block_heading(f"{prop_name} 草稿", level=2)]
    for i in range(0, min(len(draft_content), 20000), 1900):
        blocks.append(block_paragraph(draft_content[i:i+1900]))
    append_blocks(page_id, blocks)

    print(f"[notion-sync] {prop_name} 草稿追加: {title[:40]}...")
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
        for i in range(0, min(len(full_text), 20000), 1900):
            children.append(block_paragraph(full_text[i:i+1900]))

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
        for i in range(0, min(len(content), 40000), 1900):
            children.append(block_paragraph(content[i:i+1900]))

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
        for i in range(0, min(len(content), 40000), 1900):
            children.append(block_paragraph(content[i:i+1900]))

    return add_page(db_id, properties=props, children=children if children else None)


# ══════════════════════════════════════════════════════════
# v2: Content Pipeline v3 (Insight DB / Topic DB / Content DB 新結構)
# ══════════════════════════════════════════════════════════


def sync_insight_v2(
    title: str,
    angle: str,
    date_str: str,
    source: str = "",
    tags: list[str] | None = None,
    status: str = "raw",
    knowledge_ids: list[str] | None = None,
) -> str:
    """Insight → 新 Insight DB。回傳 page ID。

    status: raw / curated / topicized / archived
    """
    db_id = os.environ.get("NOTION_INSIGHT_DB", "")
    if not db_id:
        print("[notion-sync] NOTION_INSIGHT_DB 未設定", file=sys.stderr)
        return ""

    from lib.notion_api import (
        add_page, prop_title, prop_rich_text, prop_select,
        prop_multi_select, prop_date, prop_relation,
    )

    props: dict = {
        "Title": prop_title(title),
        "Angle": prop_rich_text(angle),
        "Status": prop_select(status),
        "Source": prop_rich_text(source),
        "Source Date": prop_date(date_str),
    }
    if tags:
        props["Tags"] = prop_multi_select(tags)
    if knowledge_ids:
        props["Related Knowledge"] = prop_relation(knowledge_ids)

    page_id = add_page(db_id, properties=props)
    print(f"[notion-sync] Insight v2: {title[:40]}...")
    return page_id


def sync_topic_v2(
    title: str,
    core_message: str,
    date_str: str,
    status: str = "draft",
    outline: str = "",
    insight_ids: list[str] | None = None,
    template_id: str | None = None,
) -> str:
    """Topic → 新 Topic DB。回傳 page ID。

    status: draft / writing / published / dropped
    """
    db_id = os.environ.get("NOTION_TOPIC_DB", "")
    if not db_id:
        print("[notion-sync] NOTION_TOPIC_DB 未設定", file=sys.stderr)
        return ""

    from lib.notion_api import (
        add_page, prop_title, prop_rich_text, prop_select,
        prop_date, prop_relation,
    )

    props: dict = {
        "Title": prop_title(title),
        "Core Message": prop_rich_text(core_message),
        "Status": prop_select(status),
    }
    if date_str:
        props["Created Date"] = prop_date(date_str)
    if outline:
        props["Outline"] = prop_rich_text(outline)
    if insight_ids:
        props["Related Insights"] = prop_relation(insight_ids)
    if template_id:
        props["Template"] = prop_relation([template_id])

    page_id = add_page(db_id, properties=props)
    print(f"[notion-sync] Topic v2: {title[:40]}...")
    return page_id


def sync_draft_v2(
    title: str,
    channel: str,
    draft_content: str,
    date_str: str,
    topic_id: str | None = None,
    core_message: str = "",
    tags: list[str] | None = None,
    source: str = "",
) -> str:
    """草稿 → Content DB（新結構：每頻道一筆 + Channel 欄位 + Related Topic）。

    channel: threads / facebook / blog / newsletter / shortvideo
    source: 素材來源（URL 或描述），寫入 Content DB「素材」欄位
    """
    db_id = os.environ.get("NOTION_CONTENT_DB", "")
    if not db_id:
        print("[notion-sync] NOTION_CONTENT_DB 未設定", file=sys.stderr)
        return ""

    from lib.notion_api import (
        add_page, prop_title, prop_rich_text, prop_select,
        prop_multi_select, prop_date, prop_relation, block_heading, block_paragraph,
    )

    valid_channels = {"threads", "facebook", "blog", "newsletter", "shortvideo"}
    if channel not in valid_channels:
        print(f"[notion-sync] 無效的 channel: {channel}（應為 {valid_channels}）", file=sys.stderr)
        return ""

    props: dict = {
        "標題": prop_title(title),
        "狀態": prop_select("drafting"),
        "建立日期": prop_date(date_str),
        "Channel": prop_select(channel),
    }
    if core_message:
        props["核心觀點"] = prop_rich_text(core_message)
    if source:
        props["素材"] = prop_rich_text(source)
    if tags:
        props["標籤"] = prop_multi_select(tags)
    if topic_id:
        props["Related Topic"] = prop_relation([topic_id])

    # Body: 草稿內容
    children = [block_heading(f"{channel} 草稿", level=2)]
    if draft_content:
        for i in range(0, min(len(draft_content), 20000), 1900):
            children.append(block_paragraph(draft_content[i:i+1900]))

    page_id = add_page(db_id, properties=props, children=children)
    print(f"[notion-sync] Draft v2 [{channel}]: {title[:40]}...")
    return page_id
