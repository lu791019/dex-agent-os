#!/usr/bin/env python3
"""Anybox → Google Sheets — Anybox 書籤同步到 Google Sheet

使用方式：
  ./bin/agent anybox-to-sheets                    # 同步星號書籤
  ./bin/agent anybox-to-sheets --dry-run          # 預覽不寫入
  ./bin/agent anybox-to-sheets --no-llm           # 跳過 LLM 摘要/分類
  ./bin/agent anybox-to-sheets --latest 10        # 最多 10 筆

需要 Anybox app 開啟。未開啟 → graceful skip。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import GOOGLE_SHEET_ID

ANYBOX_BASE_URL = "http://127.0.0.1:6391"
HEADER_ROW = ["日期", "分類", "作者", "標題", "來源URL", "摘要", "主題"]
TOPIC_CATEGORIES = ["技術", "生產力", "職涯", "創作", "投資", "產業", "生活", "其他"]


# ── Anybox API ───────────────────────────────────────


def _anybox_request(endpoint: str, api_key: str, params: dict | None = None) -> list[dict] | None:
    """呼叫 Anybox API，失敗回傳 None（graceful）。"""
    headers = {"X-API-Key": api_key}
    url = f"{ANYBOX_BASE_URL}/{endpoint}"

    try:
        import requests
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except ImportError:
        import urllib.request
        from urllib.parse import urlencode
        try:
            full_url = f"{url}?{urlencode(params)}" if params else url
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
    except Exception:
        return None


# ── Sheet 操作 ───────────────────────────────────────


def _ensure_sheet_exists(service, spreadsheet_id: str, sheet_name: str):
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


def _get_existing_titles(service, spreadsheet_id: str, sheet_name: str) -> set[str]:
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!D:D",
    ).execute()
    values = result.get("values", [])
    return {row[0].strip().lower() for row in values if row}


def _append_rows(service, spreadsheet_id: str, sheet_name: str, rows: list[list[str]]):
    if not rows:
        return
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


# ── LLM（複用邏輯）─────────────────────────────────


def _strip_html(text: str) -> str:
    text = re.sub(r"<(style|script|noscript)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_llm_enrichment(response: str, expected_count: int) -> list[tuple[str, str]]:
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
    if not url or not url.startswith("http"):
        return ""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        return _strip_html(raw)[:max_chars]
    except Exception:
        return ""


def _enrich_rows_with_llm(rows: list[list[str]], batch_size: int = 5) -> list[list[str]]:
    from lib.llm import ask_claude

    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"[anybox-to-sheets] LLM batch {batch_num}/{total_batches}（{len(batch)} 篇）...")

        articles = []
        fetched = 0
        for j, row in enumerate(batch):
            content = _fetch_url_content(row[4])
            if content:
                fetched += 1
            entry = f"{j+1}. 標題: {row[3]} / URL: {row[4]}"
            if content:
                entry += f"\n   內容摘錄: {content}"
            articles.append(entry)

        if fetched:
            print(f"[anybox-to-sheets]   抓到 {fetched}/{len(batch)} 篇全文")

        prompt = (
            f"以下是 {len(batch)} 個書籤，請為每個提供繁體中文摘要和主題分類。\n\n"
            "摘要要求：2-3 句，約 100-150 字。\n"
            "主題分類只能從以下選擇：技術、生產力、職涯、創作、投資、產業、生活、其他\n\n"
            "回覆格式（每篇一行，不加其他文字）：\n"
            "編號|中文摘要|主題分類\n\n"
            "書籤列表：\n" + "\n".join(articles)
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
            print(f"[anybox-to-sheets] LLM batch {batch_num} 失敗: {e}")

    return rows


# ── 主邏輯 ────────────────────────────────────────────


def sync_anybox_to_sheets(latest: int = 20, dry_run: bool = False, use_llm: bool = True):
    """從 Anybox 取星號書籤並寫入 Sheet。"""

    if not GOOGLE_SHEET_ID:
        print("[anybox-to-sheets] GOOGLE_SHEET_ID 未設定", file=sys.stderr)
        sys.exit(1)

    api_key = os.getenv("ANYBOX_API_KEY", "")
    if not api_key:
        print("[anybox-to-sheets] ANYBOX_API_KEY 未設定，跳過")
        return

    # 嘗試連線
    print("[anybox-to-sheets] 連線 Anybox...")
    result = _anybox_request("search", api_key, params={"limit": latest, "starred": "true"})

    if result is None:
        print("[anybox-to-sheets] Anybox app 未開啟，跳過")
        return

    if not result:
        print("[anybox-to-sheets] 無星號書籤")
        return

    print(f"[anybox-to-sheets] 找到 {len(result)} 筆書籤")

    from lib.file_utils import today_str
    today = today_str()

    rows = []
    for item in result:
        title = item.get("title", "") or item.get("name", "") or "Untitled"
        url = item.get("url", "") or ""
        comment = item.get("comment", "") or ""
        rows.append([today, "bookmark", "", title, url, comment, ""])

    if dry_run:
        print("[anybox-to-sheets] --dry-run 模式")
        for r in rows[:10]:
            print(f"  {r[3][:50]} — {r[4][:40]}")
        return

    from lib.google_api import get_sheets_service
    sheets = get_sheets_service()
    if not sheets:
        sys.exit(1)

    sheet_id = GOOGLE_SHEET_ID
    _ensure_sheet_exists(sheets, sheet_id, "Readings")

    existing = _get_existing_titles(sheets, sheet_id, "Readings")
    new_rows = [r for r in rows if r[3].strip().lower() not in existing]

    print(f"[anybox-to-sheets] 新增：{len(new_rows)} 筆")

    if not new_rows:
        print("[anybox-to-sheets] 全部已存在")
        return

    if use_llm:
        print("\n[anybox-to-sheets] LLM 中文摘要 + 主題分類...")
        new_rows = _enrich_rows_with_llm(new_rows)

    _append_rows(sheets, sheet_id, "Readings", new_rows)
    print(f"\n[anybox-to-sheets] 完成！寫入 {len(new_rows)} 筆")


def main():
    parser = argparse.ArgumentParser(description="Anybox → Google Sheets 同步")
    parser.add_argument("--latest", type=int, default=20, help="最多 N 筆（預設 20）")
    parser.add_argument("--dry-run", action="store_true", help="預覽不寫入")
    parser.add_argument("--no-llm", action="store_true", help="跳過 LLM")
    args = parser.parse_args()

    sync_anybox_to_sheets(latest=args.latest, dry_run=args.dry_run, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
