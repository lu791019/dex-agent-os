#!/usr/bin/env python3
"""Reader → Google Sheets — Readwise Reader 內容同步到 Google Sheet

使用方式：
  ./bin/agent reader-to-sheets                    # 同步過去 7 天
  ./bin/agent reader-to-sheets --days 14          # 同步過去 14 天
  ./bin/agent reader-to-sheets --since 2026-03-15 # 同步指定日期後
  ./bin/agent reader-to-sheets --dry-run          # 預覽不寫入

結構：
  主工作表「Readings」：email（全部）+ podcast（全部）+ RSS（白名單）
  獨立工作表「Seeking Alpha」：Seeking Alpha 文章

去重：email 先寫，RSS 寫入時 skip 已存在的 title
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import GOOGLE_SHEET_ID
from lib.google_api import get_sheets_service
from lib.readwise_api import check_readwise_setup, reader_list

# ── 排除清單（site_name 模糊匹配）──────────────────────

EXCLUDE_SITES = {
    "reddit.com",
    "google cloud documentation",
    "idealist.org",
    "betweengos",
    "thecaringtechie.com",
    "kill-the-newsletter.com",
    "tom's hardware",
    "bbc news afrique",
    "claude.com",
    "mistral.ai",
    "kagi.com",
    "notimenocode.com",
    "manager-tools.com",
    "karpathy.ai",
    "x (formerly twitter)",
    "financial times",
    "apple newsroom",
    "chiukaun.com",
}

SEEKING_ALPHA_KEY = "seeking alpha"

# RSS 白名單（site_name 模糊匹配，只有這些 RSS 來源會進主工作表）
RSS_WHITELIST = {
    "medium",
    "techcrunch",
    "the verge",
    "youtube",
    "systemdesign.one",
    "pragmaticengineer.com",
    "substack.com",
    "dataengineeringweekly.com",
    "strategizeyourcareer.com",
    "bytebytego.com",
    "閱讀前哨站",
    "stratechery",
    "the github blog",
    "the pragmatic engineer",
    "datagibberish.com",
    "churchtechtod",
    "github",
    "雷蒙三十",
    "dataexpert.io",
    "創作者經濟",
    "engineering at meta",
    "notboring.co",
    "uber blog",
    "領先時代",
    "informalwriting.cc",
    "design.systems",
    "techchange",
    "algomaster.io",
    "workplace insights",
}

HEADER_ROW = ["日期", "分類", "作者", "標題", "來源URL", "摘要"]


# ── 工具函式 ──────────────────────────────────────────


def _is_excluded(site_name: str) -> bool:
    """檢查 site_name 是否在排除清單中。"""
    lower = (site_name or "").lower().strip()
    return any(exc in lower for exc in EXCLUDE_SITES)


def _is_seeking_alpha(site_name: str) -> bool:
    return SEEKING_ALPHA_KEY in (site_name or "").lower()


def _is_rss_whitelisted(site_name: str) -> bool:
    """RSS 來源是否在白名單中。"""
    lower = (site_name or "").lower().strip()
    return any(w in lower for w in RSS_WHITELIST)


def _doc_to_row(doc: dict) -> list[str]:
    """將 Reader 文件轉為 Sheet 行。"""
    updated = (doc.get("updated_at", "") or "")[:10]
    category = doc.get("category", "unknown")
    author = doc.get("author", "") or ""
    title = doc.get("title", "") or "Untitled"
    source_url = doc.get("source_url", "") or ""
    if source_url.startswith("mailto:"):
        source_url = ""
    summary = (doc.get("summary", "") or "").replace("\n", " ").strip()
    if len(summary) > 500:
        summary = summary[:497] + "..."
    return [updated, category, author, title, source_url, summary]


def _ensure_sheet_exists(service, spreadsheet_id: str, sheet_name: str):
    """確保工作表存在，不存在則建立。"""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = [s["properties"]["title"] for s in meta.get("sheets", [])]
    if sheet_name not in existing:
        body = {
            "requests": [
                {"addSheet": {"properties": {"title": sheet_name}}}
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()
        # 寫 header
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption="RAW",
            body={"values": [HEADER_ROW]},
        ).execute()
        print(f"[reader-to-sheets] 建立工作表：{sheet_name}")


def _get_existing_titles(service, spreadsheet_id: str, sheet_name: str) -> set[str]:
    """讀取工作表中已存在的標題（D 欄）。"""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!D:D",
    ).execute()
    values = result.get("values", [])
    return {row[0].strip().lower() for row in values if row}


def _append_rows(service, spreadsheet_id: str, sheet_name: str, rows: list[list[str]]):
    """批次 append 行到工作表。"""
    if not rows:
        return
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


# ── 主邏輯 ────────────────────────────────────────────


def sync_to_sheets(days: int = 7, since: str | None = None, dry_run: bool = False):
    """從 Reader API 拉資料並寫入 Google Sheet。"""

    if not GOOGLE_SHEET_ID:
        print("[reader-to-sheets] GOOGLE_SHEET_ID 未設定。請在 .env 中加入。", file=sys.stderr)
        sys.exit(1)

    if not check_readwise_setup():
        sys.exit(1)

    # 計算日期範圍（Reader API 需要完整 ISO 8601）
    if since:
        updated_after = f"{since}T00:00:00"
    else:
        updated_after = (datetime.now() - timedelta(days=days)).isoformat()

    print(f"[reader-to-sheets] 拉取 {updated_after} 之後的內容...")

    # 拉 email + podcast + rss
    all_docs = []
    for cat in ("email", "podcast", "rss"):
        print(f"[reader-to-sheets] 拉取 {cat}...")
        docs = reader_list(category=cat, updated_after=updated_after, fetch_all=True)
        print(f"[reader-to-sheets]   {cat}: {len(docs)} 篇")
        for doc in docs:
            doc["_category"] = cat
        all_docs.extend(docs)

    # 分類
    main_rows = []
    sa_rows = []
    skipped_exclude = 0
    skipped_dup = 0

    # email 先處理（去重用）
    email_docs = [d for d in all_docs if d["_category"] == "email"]
    other_docs = [d for d in all_docs if d["_category"] != "email"]

    seen_titles: set[str] = set()

    for doc in email_docs:
        site = doc.get("site_name", "") or ""
        if _is_excluded(site):
            skipped_exclude += 1
            continue
        title_lower = (doc.get("title", "") or "").strip().lower()
        seen_titles.add(title_lower)
        row = _doc_to_row(doc)
        if _is_seeking_alpha(site):
            sa_rows.append(row)
        else:
            main_rows.append(row)

    skipped_rss_nowhitelist = 0

    for doc in other_docs:
        site = doc.get("site_name", "") or ""
        if _is_excluded(site):
            skipped_exclude += 1
            continue
        # RSS 走白名單（podcast 全收）
        if doc["_category"] == "rss" and not _is_seeking_alpha(site) and not _is_rss_whitelisted(site):
            skipped_rss_nowhitelist += 1
            continue
        title_lower = (doc.get("title", "") or "").strip().lower()
        if title_lower in seen_titles:
            skipped_dup += 1
            continue
        seen_titles.add(title_lower)
        row = _doc_to_row(doc)
        if _is_seeking_alpha(site):
            sa_rows.append(row)
        else:
            main_rows.append(row)

    print(f"\n[reader-to-sheets] 結果：")
    print(f"  主工作表：{len(main_rows)} 篇")
    print(f"  Seeking Alpha：{len(sa_rows)} 篇")
    print(f"  排除（黑名單）：{skipped_exclude} 篇")
    print(f"  排除（RSS 非白名單）：{skipped_rss_nowhitelist} 篇")
    print(f"  去重：{skipped_dup} 篇")

    if dry_run:
        print("\n[reader-to-sheets] --dry-run 模式，不寫入 Sheet")
        return

    # 寫入 Google Sheet
    service = get_sheets_service()
    if not service:
        sys.exit(1)

    sheet_id = GOOGLE_SHEET_ID

    # 確保工作表存在
    _ensure_sheet_exists(service, sheet_id, "Readings")
    _ensure_sheet_exists(service, sheet_id, "Seeking Alpha")

    # 讀取已存在的標題避免重複寫入
    existing_main = _get_existing_titles(service, sheet_id, "Readings")
    existing_sa = _get_existing_titles(service, sheet_id, "Seeking Alpha")

    new_main = [r for r in main_rows if r[3].strip().lower() not in existing_main]
    new_sa = [r for r in sa_rows if r[3].strip().lower() not in existing_sa]

    print(f"\n[reader-to-sheets] 新增（去除 Sheet 已存在）：")
    print(f"  主工作表：{len(new_main)} 篇")
    print(f"  Seeking Alpha：{len(new_sa)} 篇")

    _append_rows(service, sheet_id, "Readings", new_main)
    _append_rows(service, sheet_id, "Seeking Alpha", new_sa)

    print(f"\n[reader-to-sheets] 完成！")


# ── CLI ───────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Reader → Google Sheets 同步")
    parser.add_argument("--days", type=int, default=7, help="拉取過去 N 天（預設 7）")
    parser.add_argument("--since", type=str, default=None, help="拉取指定日期後 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="預覽不寫入")
    args = parser.parse_args()

    sync_to_sheets(days=args.days, since=args.since, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
