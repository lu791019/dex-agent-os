#!/usr/bin/env python3
"""RSS → Google Sheets — RSS feed 自動同步到 Google Sheet

使用方式：
  ./bin/agent rss-to-sheets                    # 同步所有 feed 最新文章
  ./bin/agent rss-to-sheets --dry-run          # 預覽不寫入
  ./bin/agent rss-to-sheets --no-llm           # 跳過 LLM 摘要/分類
  ./bin/agent rss-to-sheets --latest 5         # 每個 feed 最多 5 篇

讀取 config/rss-feeds.txt 的 feed URL 清單，抓取 → 寫入 Sheet「Readings」。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import GOOGLE_SHEET_ID
from lib.google_api import get_sheets_service

FEEDS_FILE = ROOT_DIR / "config" / "rss-feeds.txt"
HEADER_ROW = ["日期", "分類", "作者", "標題", "來源URL", "摘要", "主題"]
TOPIC_CATEGORIES = ["技術", "生產力", "職涯", "創作", "投資", "產業", "生活", "其他"]

# 排除的 feed title / author（模糊匹配）
EXCLUDE_SOURCES = {
    "ikea",
    "宜家家居",
    "cake team",
    "吴明光",
    "求真易学",
    "unroll.me",
    "生涯設計師",
    "凱茜女孩",
    "cathy girl",
    "南山人壽",
}


# ── 工具函式 ──────────────────────────────────────────


def _strip_html(text: str) -> str:
    """去除 HTML 標籤並壓縮空白。"""
    m = re.search(r"<article[^>]*>(.*?)</article>", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    text = re.sub(r"<(style|script|noscript)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _load_feeds() -> list[str]:
    """從 config/rss-feeds.txt 讀取 feed URL 清單。"""
    if not FEEDS_FILE.exists():
        print(f"[rss-to-sheets] Feed 清單不存在：{FEEDS_FILE}", file=sys.stderr)
        print(f"  請建立 config/rss-feeds.txt，一行一個 feed URL")
        sys.exit(1)

    feeds = []
    for line in FEEDS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        feeds.append(line)
    return feeds


def _fetch_feed(feed_url: str, latest: int, days: int) -> list[dict]:
    """抓取單一 feed，回傳文章 list。"""
    import feedparser

    feed = feedparser.parse(feed_url)
    if not feed.entries:
        return []

    feed_title = feed.feed.get("title", "Unknown Feed")
    cutoff = datetime.now() - timedelta(days=days)
    entries = []

    for entry in feed.entries[:latest] if latest > 0 else feed.entries:
        # 解析日期
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            entry_date = datetime(*published[:6])
            if entry_date < cutoff:
                continue
            date_str = entry_date.strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        title = entry.get("title", "Untitled") or "Untitled"
        link = entry.get("link", "") or ""
        author = entry.get("author", "") or ""

        # 取摘要（RSS 內建）
        summary = ""
        content_list = entry.get("content", [])
        if content_list:
            summary = _strip_html(content_list[0].get("value", ""))
        if not summary:
            summary = _strip_html(entry.get("summary", "") or "")
        if len(summary) > 500:
            summary = summary[:497] + "..."

        entries.append({
            "date": date_str,
            "category": "rss",
            "author": author,
            "title": title,
            "url": link,
            "summary": summary,
            "feed_title": feed_title,
            "full_text": _strip_html(content_list[0].get("value", "")) if content_list else "",
        })

    return entries


def _entry_to_row(entry: dict) -> list[str]:
    """將 feed entry 轉為 Sheet 行。"""
    return [
        entry["date"],
        entry["category"],
        entry["author"],
        entry["title"],
        entry["url"],
        entry["summary"],
        "",  # 主題（LLM 填）
    ]


# ── Sheet 操作（複用 reader_to_sheets 邏輯）─────────


def _ensure_sheet_exists(service, spreadsheet_id: str, sheet_name: str):
    """確保工作表存在，不存在則建立。"""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = [s["properties"]["title"] for s in meta.get("sheets", [])]
    if sheet_name not in existing:
        body = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption="RAW",
            body={"values": [HEADER_ROW]},
        ).execute()
        print(f"[rss-to-sheets] 建立工作表：{sheet_name}")


def _get_existing_titles(service, spreadsheet_id: str, sheet_name: str) -> set[str]:
    """讀取工作表中已存在的標題（D 欄）。"""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!D:D",
    ).execute()
    values = result.get("values", [])
    return {row[0].strip().lower() for row in values if row}


def _append_rows(service, spreadsheet_id: str, sheet_name: str, rows: list[list[str]]):
    """批次插入行到工作表（header 之後，最新在最上面）。"""
    if not rows:
        return
    # 取得 sheet ID
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = None
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == sheet_name:
            sheet_id = s["properties"]["sheetId"]
            break
    if sheet_id is None:
        return

    # 在第 2 行（index=1，header 下方）插入空行
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{
            "insertDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": 1,
                    "endIndex": 1 + len(rows),
                },
                "inheritFromBefore": False,
            }
        }]},
    ).execute()

    # 寫入資料到新插入的行
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A2",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()


# ── LLM 摘要 + 分類（複用 reader_to_sheets 邏輯）───


def _parse_llm_enrichment(response: str, expected_count: int) -> list[tuple[str, str]]:
    """解析 LLM 回應。"""
    results = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("<"):
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            summary_zh = "|".join(parts[1:-1]).strip()
            topic = parts[-1].strip()
            if topic not in TOPIC_CATEGORIES:
                topic = "其他"
            results.append((summary_zh, topic))
    while len(results) < expected_count:
        results.append(("", "其他"))
    return results[:expected_count]


def _fetch_url_content(url: str, max_chars: int = 1500) -> str:
    """抓取 URL 網頁內容。"""
    if not url or not url.startswith("http"):
        return ""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        return _strip_html(raw)[:max_chars]
    except Exception:
        return ""


def _enrich_rows_with_llm(rows: list[list[str]], batch_size: int = 5) -> list[list[str]]:
    """用 LLM 產中文摘要 + 主題分類。"""
    from lib.llm import ask_claude

    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"[rss-to-sheets] LLM batch {batch_num}/{total_batches}（{len(batch)} 篇）...")

        articles = []
        fetched = 0
        for j, row in enumerate(batch):
            content = _fetch_url_content(row[4])
            if content:
                fetched += 1
            entry = f"{j+1}. 標題: {row[3]} / 作者: {row[2]}"
            if content:
                entry += f"\n   內容摘錄: {content}"
            elif row[5]:
                entry += f" / 原摘要: {row[5][:300]}"
            articles.append(entry)

        if fetched:
            print(f"[rss-to-sheets]   抓到 {fetched}/{len(batch)} 篇全文")

        prompt = (
            f"以下是 {len(batch)} 篇文章，請為每篇提供繁體中文摘要和主題分類。\n\n"
            "摘要要求：2-3 句，約 100-150 字，包含核心論點和為什麼值得看。\n"
            "主題分類只能從以下選擇：技術、生產力、職涯、創作、投資、產業、生活、其他\n\n"
            "回覆格式（嚴格遵守，每篇一行，不要加任何其他文字）：\n"
            "編號|中文摘要|主題分類\n\n"
            "文章列表：\n" + "\n".join(articles)
        )

        try:
            response = ask_claude(prompt)
            results = _parse_llm_enrichment(response, len(batch))
            for j, row in enumerate(batch):
                if j < len(results):
                    summary_zh, topic = results[j]
                    if summary_zh:
                        row[5] = summary_zh
                    row[6] = topic
        except Exception as e:
            print(f"[rss-to-sheets] LLM batch {batch_num} 失敗: {e}，保留原摘要")

    return rows


# ── 主邏輯 ────────────────────────────────────────────


def sync_rss_to_sheets(latest: int = 10, days: int = 7, dry_run: bool = False, use_llm: bool = True):
    """從 RSS feeds 抓取文章並寫入 Google Sheet。"""

    if not GOOGLE_SHEET_ID:
        print("[rss-to-sheets] GOOGLE_SHEET_ID 未設定", file=sys.stderr)
        sys.exit(1)

    feeds = _load_feeds()
    print(f"[rss-to-sheets] 載入 {len(feeds)} 個 feed，抓取過去 {days} 天...")

    all_entries = []  # 保留 dict（含 full_text）
    all_rows = []
    for feed_url in feeds:
        try:
            entries = _fetch_feed(feed_url, latest, days)
            if entries:
                rows = [_entry_to_row(e) for e in entries]
                all_entries.extend(entries)
                all_rows.extend(rows)
                print(f"[rss-to-sheets]   {entries[0]['feed_title']}: {len(entries)} 篇")
        except Exception as e:
            print(f"[rss-to-sheets]   FAIL {feed_url[:50]}: {e}")

    # 過濾排除來源
    def _is_excluded(row: list[str]) -> bool:
        author_lower = (row[2] or "").lower()
        title_lower = (row[3] or "").lower()
        return any(exc in author_lower or exc in title_lower for exc in EXCLUDE_SOURCES)

    before_filter = len(all_rows)
    all_rows = [r for r in all_rows if not _is_excluded(r)]
    skipped = before_filter - len(all_rows)
    if skipped:
        print(f"[rss-to-sheets] 排除（黑名單）：{skipped} 篇")

    # 按日期倒序排列（最新的在前）
    all_rows.sort(key=lambda r: r[0], reverse=True)

    print(f"\n[rss-to-sheets] 共抓到 {len(all_rows)} 篇")

    if not all_rows:
        print("[rss-to-sheets] 無新文章")
        return

    if dry_run:
        print("[rss-to-sheets] --dry-run 模式，不寫入 Sheet")
        return

    # Sheet 寫入
    service = get_sheets_service()
    if not service:
        sys.exit(1)

    sheet_id = GOOGLE_SHEET_ID
    _ensure_sheet_exists(service, sheet_id, "Readings")

    # 去重
    existing = _get_existing_titles(service, sheet_id, "Readings")
    new_rows = [r for r in all_rows if r[3].strip().lower() not in existing]

    print(f"[rss-to-sheets] 新增（去除 Sheet 已存在）：{len(new_rows)} 篇")

    if not new_rows:
        print("[rss-to-sheets] 全部已存在，跳過")
        return

    # LLM 摘要 + 分類
    if use_llm:
        print("\n[rss-to-sheets] 開始 LLM 中文摘要 + 主題分類...")
        new_rows = _enrich_rows_with_llm(new_rows)

    _append_rows(service, sheet_id, "Readings", new_rows)
    print(f"\n[rss-to-sheets] Sheet 寫入 {len(new_rows)} 篇")

    # Notion 學習 DB 寫入（全文）
    notion_db = os.environ.get("NOTION_LEARNING_DB", "")
    if notion_db:
        try:
            from lib.notion_api import add_page, prop_title, prop_rich_text, prop_select, prop_date, prop_url, prop_checkbox, block_paragraph

            # 建 title → entry 的查找表
            entry_by_title = {e["title"].strip().lower(): e for e in all_entries}

            notion_count = 0
            for row in new_rows:
                title_key = row[3].strip().lower()
                entry = entry_by_title.get(title_key, {})
                full_text = entry.get("full_text", "")

                props = {
                    "標題": prop_title(row[3]),
                    "日期": prop_date(row[0]) if row[0] else prop_date("2026-01-01"),
                    "來源類型": prop_select("文章"),
                    "作者": prop_rich_text(row[2]),
                    "URL": prop_url(row[4]) if row[4] else prop_url(""),
                    "摘要": prop_rich_text(row[5][:2000]),
                    "⭐": prop_checkbox(False),
                }
                if row[6]:
                    props["主題"] = prop_select(row[6])

                # 全文放在 page body（children blocks）
                children = []
                if full_text:
                    for i in range(0, min(len(full_text), 20000), 1900):
                        children.append(block_paragraph(full_text[i:i+1900]))

                try:
                    add_page(notion_db, properties=props, children=children if children else None)
                    notion_count += 1
                except Exception as e:
                    print(f"[rss-to-sheets] Notion 寫入失敗: {row[3][:30]}... — {e}", file=sys.stderr)

            print(f"[rss-to-sheets] Notion 寫入 {notion_count} 篇")
        except ImportError:
            print("[rss-to-sheets] notion_api 模組不可用，跳過 Notion 寫入")
        except Exception as e:
            print(f"[rss-to-sheets] Notion 寫入失敗: {e}", file=sys.stderr)

    print(f"[rss-to-sheets] 完成！")


# ── CLI ───────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="RSS → Google Sheets 同步")
    parser.add_argument("--latest", type=int, default=10, help="每個 feed 最多 N 篇（預設 10）")
    parser.add_argument("--days", type=int, default=7, help="只抓過去 N 天（預設 7）")
    parser.add_argument("--dry-run", action="store_true", help="預覽不寫入")
    parser.add_argument("--no-llm", action="store_true", help="跳過 LLM 摘要/分類")
    args = parser.parse_args()

    sync_rss_to_sheets(latest=args.latest, days=args.days, dry_run=args.dry_run, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
