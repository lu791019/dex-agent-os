#!/usr/bin/env python3
"""Gmail → Google Sheets — Gmail 電子報同步到 Google Sheet

使用方式：
  ./bin/agent gmail-to-sheets                    # 同步過去 7 天電子報
  ./bin/agent gmail-to-sheets --days 3           # 同步過去 3 天
  ./bin/agent gmail-to-sheets --dry-run          # 預覽不寫入
  ./bin/agent gmail-to-sheets --no-llm           # 跳過 LLM 摘要/分類

過濾促銷信，只保留有價值的電子報，寫入 Sheet「Readings」。
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import GOOGLE_SHEET_ID

# ── 過濾清單 ─────────────────────────────────────────

# 排除的寄件者（from 地址包含這些字串就排除）
EXCLUDE_SENDERS = {
    # 平台通知
    "uber.com",
    "ubereats.com",
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "apple.com",
    "microsoft.com",
    "amazon.com",
    "netflix.com",
    "spotify.com",
    "google.com",
    # 系統類
    "noreply@",
    "no-reply@",
    "marketing@",
    "promo@",
    "deals@",
    "notifications@",
    "donotreply@",
    "billing@",
    "receipt@",
    "order@",
    "shipping@",
    "alert@",
    "info@",
    # 台灣本地促銷 / 非電子報
    "fubon.com",
    "富邦",
    "eslite.com",
    "誠品",
    "edom.com",
    "shopee.com",
    "momo.com",
    "pchome.com",
    "klook.com",
    "agoda.com",
    "booking.com",
    # 課程平台通知（非內容）
    "shifu.team",
    "hahow.in",
    "udemy.com",
    # 風水 / 非相關
    "吳明光",
    "求真易學",
    # 聯盟行銷
    "通路王",
    "ichannels",
}

# 排除的 subject 關鍵字
EXCLUDE_SUBJECTS = {
    "優惠", "折扣", "促銷", "coupon", "discount", "sale",
    "expires", "expiring", "unsubscribe", "verify your",
    "receipt", "invoice", "order confirmation", "shipping",
    "password reset", "security alert",
    "成交回報", "對帳單", "繳費", "帳單",
    "免運", "滿額", "限時", "搶購", "特價",
    "enroll now", "last chance", "don't miss",
    "activate your", "confirm your", "welcome to",
}

HEADER_ROW = ["日期", "分類", "作者", "標題", "來源URL", "摘要", "主題"]
TOPIC_CATEGORIES = ["技術", "生產力", "職涯", "創作", "投資", "產業", "生活", "其他"]


# ── Gmail API（複用 gmail_sync.py 邏輯）─────────────


def _get_gmail_service():
    """取得 Gmail API service。"""
    try:
        from lib.google_api import authenticate
    except ImportError:
        print("[gmail-to-sheets] 無法載入 google_api 模組", file=sys.stderr)
        return None
    creds = authenticate()
    if not creds:
        return None
    try:
        from googleapiclient.discovery import build
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        print(f"[gmail-to-sheets] Gmail API 失敗：{e}", file=sys.stderr)
        return None


def _search_emails(service, query: str, max_results: int = 50) -> list[dict]:
    """搜尋 Gmail。"""
    try:
        result = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        return result.get("messages", [])
    except Exception as e:
        print(f"[gmail-to-sheets] 搜尋失敗：{e}", file=sys.stderr)
        return []


def _get_message(service, msg_id: str) -> dict | None:
    """取得完整 email。"""
    try:
        return service.users().messages().get(
            userId="me", id=msg_id, format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()
    except Exception:
        return None


def _extract_header(msg: dict, name: str) -> str:
    """從 message headers 取指定欄位。"""
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _format_date(internal_date_ms: str) -> str:
    """Gmail internal date → YYYY-MM-DD。"""
    ts = int(internal_date_ms) / 1000
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


# ── 過濾邏輯 ─────────────────────────────────────────


def _is_excluded_sender(sender: str) -> bool:
    """檢查寄件者是否在排除清單中。"""
    lower = sender.lower()
    return any(exc in lower for exc in EXCLUDE_SENDERS)


def _is_excluded_subject(subject: str) -> bool:
    """檢查主旨是否包含排除關鍵字。"""
    lower = subject.lower()
    return any(exc in lower for exc in EXCLUDE_SUBJECTS)


# ── Sheet 操作 ───────────────────────────────────────


def _get_sheets_service_and_check():
    """取得 Sheets service。"""
    from lib.google_api import get_sheets_service
    service = get_sheets_service()
    if not service:
        print("[gmail-to-sheets] Google Sheets API 失敗", file=sys.stderr)
        sys.exit(1)
    return service


def _ensure_sheet_exists(service, spreadsheet_id: str, sheet_name: str):
    """確保工作表存在。"""
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
    """讀取已存在的標題。"""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!D:D",
    ).execute()
    values = result.get("values", [])
    return {row[0].strip().lower() for row in values if row}


def _append_rows(service, spreadsheet_id: str, sheet_name: str, rows: list[list[str]]):
    """批次 append 行。"""
    if not rows:
        return
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


# ── LLM 摘要 + 分類 ─────────────────────────────────


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


def _enrich_rows_with_llm(rows: list[list[str]], batch_size: int = 5) -> list[list[str]]:
    """用 LLM 產中文摘要 + 主題分類。"""
    from lib.llm import ask_claude

    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"[gmail-to-sheets] LLM batch {batch_num}/{total_batches}（{len(batch)} 篇）...")

        articles = []
        for j, row in enumerate(batch):
            entry = f"{j+1}. 標題: {row[3]} / 作者: {row[2]}"
            if row[5]:
                entry += f" / 原摘要: {row[5][:300]}"
            articles.append(entry)

        prompt = (
            f"以下是 {len(batch)} 封電子報，請為每篇提供繁體中文摘要和主題分類。\n\n"
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
            print(f"[gmail-to-sheets] LLM batch {batch_num} 失敗: {e}")

    return rows


# ── 主邏輯 ────────────────────────────────────────────


def sync_gmail_to_sheets(days: int = 7, dry_run: bool = False, use_llm: bool = True):
    """從 Gmail 搜尋電子報並寫入 Google Sheet。"""

    if not GOOGLE_SHEET_ID:
        print("[gmail-to-sheets] GOOGLE_SHEET_ID 未設定", file=sys.stderr)
        sys.exit(1)

    gmail = _get_gmail_service()
    if not gmail:
        return

    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f"(category:promotions OR category:updates) after:{after_date}"
    print(f"[gmail-to-sheets] 搜尋：{query}")

    messages = _search_emails(gmail, query, max_results=100)
    if not messages:
        print("[gmail-to-sheets] 沒有信件")
        return

    print(f"[gmail-to-sheets] 找到 {len(messages)} 封，過濾中...")

    # 取 metadata 並過濾
    rows = []
    skipped_sender = 0
    skipped_subject = 0

    for m in messages:
        full = _get_message(gmail, m["id"])
        if not full:
            continue

        subject = _extract_header(full, "Subject") or "Untitled"
        sender = _extract_header(full, "From") or ""
        date_str = _format_date(full.get("internalDate", "0"))

        if _is_excluded_sender(sender):
            skipped_sender += 1
            continue
        if _is_excluded_subject(subject):
            skipped_subject += 1
            continue

        # 從 sender 擷取名稱
        author = sender
        match = re.match(r'"?([^"<]+)"?\s*<', sender)
        if match:
            author = match.group(1).strip()

        rows.append([date_str, "email", author, subject, "", subject, ""])

    print(f"\n[gmail-to-sheets] 過濾結果：")
    print(f"  保留：{len(rows)} 封")
    print(f"  排除（寄件者）：{skipped_sender} 封")
    print(f"  排除（主旨）：{skipped_subject} 封")

    if not rows:
        print("[gmail-to-sheets] 無有效電子報")
        return

    if dry_run:
        print("\n[gmail-to-sheets] --dry-run 模式，不寫入")
        for r in rows[:10]:
            print(f"  [{r[0]}] {r[2][:20]} — {r[3][:50]}")
        if len(rows) > 10:
            print(f"  ... 還有 {len(rows) - 10} 封")
        return

    # Sheet 寫入
    sheets = _get_sheets_service_and_check()
    sheet_id = GOOGLE_SHEET_ID
    _ensure_sheet_exists(sheets, sheet_id, "Readings")

    existing = _get_existing_titles(sheets, sheet_id, "Readings")
    new_rows = [r for r in rows if r[3].strip().lower() not in existing]

    print(f"\n[gmail-to-sheets] 新增（去除 Sheet 已存在）：{len(new_rows)} 封")

    if not new_rows:
        print("[gmail-to-sheets] 全部已存在")
        return

    if use_llm:
        print("\n[gmail-to-sheets] 開始 LLM 中文摘要 + 主題分類...")
        new_rows = _enrich_rows_with_llm(new_rows)

    _append_rows(sheets, sheet_id, "Readings", new_rows)
    print(f"\n[gmail-to-sheets] 完成！寫入 {len(new_rows)} 封")


# ── CLI ───────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Gmail → Google Sheets 同步")
    parser.add_argument("--days", type=int, default=7, help="搜尋過去 N 天（預設 7）")
    parser.add_argument("--dry-run", action="store_true", help="預覽不寫入")
    parser.add_argument("--no-llm", action="store_true", help="跳過 LLM 摘要/分類")
    args = parser.parse_args()

    sync_gmail_to_sheets(days=args.days, dry_run=args.dry_run, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
