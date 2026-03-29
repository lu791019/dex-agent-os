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
    "shifu｜",
    "hahow.in",
    "udemy.com",
    "codecademy",
    "lim 先鋒",
    # 風水 / 非相關
    "吳明光",
    "求真易學",
    "terriah",
    # 聯盟行銷
    "通路王",
    "ichannels",
    # 金融 / 銀行 / 投資平台
    "台新銀行",
    "taishinbank",
    "cathaybank",
    "esunbank",
    "鉅亨",
    "cnyes.com",
    "haru",
    "gamma",
    # 求職 / 人力
    "my104",
    "104.com",
    # 研討會 / 培訓通知
    "恆逸",
    "iiiedu",
    # 電子書 / 出版平台通知
    "readmoo",
    "方格子",
    "vocus.cc",
    # 郵政
    "網路郵局",
    "行動郵局",
    "post.gov",
    # SaaS 行銷
    "simplymeet",
    "calendly.com",
    # 品牌 / 保險 / 雜項
    "ikea",
    "宜家家居",
    "cake team",
    "unroll.me",
    "生涯設計師",
    "凱茜女孩",
    "cathy girl",
    "南山人壽",
    "soler風格",
    # 軟體 / 工具通知
    "adobe",
    "tactiq",
    "read assistant",
    "scribbl",
    "trello",
    "feedspot",
    "playstation",
    # 政府 / 發票
    "einvoice",
    "伊莉",
    # 環境 / 非核心
    "環境資訊中心",
    "eden",
    "吴明光",
    "求真易学",
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


def _get_message_metadata(service, msg_id: str) -> dict | None:
    """取得 email metadata（快速，用於過濾）。"""
    try:
        return service.users().messages().get(
            userId="me", id=msg_id, format="metadata",
            metadataHeaders=["Subject", "From", "Date", "List-Id"],
        ).execute()
    except Exception:
        return None


def _get_message_full(service, msg_id: str) -> dict | None:
    """取得完整 email（含 body，較慢）。"""
    try:
        return service.users().messages().get(
            userId="me", id=msg_id, format="full",
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


def _extract_body(msg: dict, max_chars: int = 2000) -> str:
    """從 email payload 提取純文字 body，截斷至 max_chars。"""
    payload = msg.get("payload", {})

    # 嘗試直接取 body
    body_data = payload.get("body", {}).get("data")
    if body_data:
        raw = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
        return _strip_html(raw)[:max_chars]

    # multipart：遍歷找 text/html 或 text/plain
    html_body = ""
    text_body = ""
    for part in payload.get("parts", []):
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if not data:
            for sub in part.get("parts", []):
                sub_data = sub.get("body", {}).get("data")
                if sub_data:
                    decoded = base64.urlsafe_b64decode(sub_data).decode("utf-8", errors="replace")
                    if "html" in sub.get("mimeType", ""):
                        html_body = decoded
                    elif "plain" in sub.get("mimeType", ""):
                        text_body = decoded
            continue
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        if "html" in mime:
            html_body = decoded
        elif "plain" in mime:
            text_body = decoded

    content = html_body if html_body else text_body
    if content:
        return _strip_html(content)[:max_chars]
    return ""


def _strip_html(text: str) -> str:
    """去除 HTML 標籤並壓縮空白。"""
    text = re.sub(r"<(style|script|noscript)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _guess_substack_url(list_id: str, sender: str) -> str:
    """從 List-Id header 組裝 Substack 公開 URL。

    List-Id 格式: <xxx.substack.com> → https://xxx.substack.com/
    """
    # 優先用 List-Id（最準確）
    if list_id:
        m = re.search(r"<([^>]+\.substack\.com)>", list_id, re.IGNORECASE)
        if m:
            domain = m.group(1)
            if domain != "www.substack.com":
                return f"https://{domain}/"

    # Fallback: 從 sender email domain 嘗試
    email_match = re.search(r"<([^>]+)>", sender)
    if email_match:
        email_addr = email_match.group(1).lower()
        parts = email_addr.split("@")
        if len(parts) == 2 and parts[1].endswith(".substack.com"):
            domain = parts[1]
            if domain != "substack.com":
                return f"https://{domain}/"

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
            if row[5] and row[5] != row[3]:
                # body 內容（非 subject 重複）
                entry += f"\n   內容摘錄: {row[5][:500]}"
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

    # 第一階段：metadata 過濾（快速）
    filtered_ids = []
    for m in messages:
        meta = _get_message_metadata(gmail, m["id"])
        if not meta:
            continue

        subject = _extract_header(meta, "Subject") or "Untitled"
        sender = _extract_header(meta, "From") or ""

        if _is_excluded_sender(sender):
            skipped_sender += 1
            continue
        if _is_excluded_subject(subject):
            skipped_subject += 1
            continue

        list_id = _extract_header(meta, "List-Id") or ""
        date_str = _format_date(meta.get("internalDate", "0"))

        # 從 sender 擷取名稱
        author = sender
        match = re.match(r'"?([^"<]+)"?\s*<', sender)
        if match:
            author = match.group(1).strip()

        # Substack URL（用 List-Id），fallback 到 Gmail 連結
        url = _guess_substack_url(list_id, sender)
        if not url:
            url = f"https://mail.google.com/mail/u/0/#inbox/{m['id']}"

        filtered_ids.append({
            "id": m["id"], "date": date_str, "author": author,
            "subject": subject, "url": url, "sender": sender,
        })

    print(f"\n[gmail-to-sheets] 過濾結果：")
    print(f"  保留：{len(filtered_ids)} 封")
    print(f"  排除（寄件者）：{skipped_sender} 封")
    print(f"  排除（主旨）：{skipped_subject} 封")

    if not filtered_ids:
        print("[gmail-to-sheets] 無有效電子報")
        return

    if dry_run:
        print("\n[gmail-to-sheets] --dry-run 模式，不寫入")
        for item in filtered_ids[:10]:
            url_flag = "🔗" if item["url"] else "  "
            print(f"  [{item['date']}] {url_flag} {item['author'][:20]} — {item['subject'][:50]}")
        if len(filtered_ids) > 10:
            print(f"  ... 還有 {len(filtered_ids) - 10} 封")
        return

    # 第二階段：拉 body（只對通過過濾的）
    print(f"\n[gmail-to-sheets] 拉取 {len(filtered_ids)} 封 email body...")
    for item in filtered_ids:
        full = _get_message_full(gmail, item["id"])
        body = _extract_body(full) if full else ""
        summary_input = body if body else item["subject"]
        rows.append([item["date"], "email", item["author"], item["subject"], item["url"], summary_input, ""])

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
    print(f"\n[gmail-to-sheets] Sheet 寫入 {len(new_rows)} 封")

    # Notion 學習 DB 寫入
    import os as _os
    notion_db = _os.environ.get("NOTION_LEARNING_DB", "")
    if notion_db:
        try:
            from lib.notion_api import add_page, prop_title, prop_rich_text, prop_select, prop_date, prop_url, prop_checkbox, block_paragraph

            notion_count = 0
            for row in new_rows:
                props = {
                    "標題": prop_title(row[3]),
                    "日期": prop_date(row[0]) if row[0] else prop_date("2026-01-01"),
                    "來源類型": prop_select("電子報"),
                    "作者": prop_rich_text(row[2]),
                    "URL": prop_url(row[4]) if row[4] else prop_url(""),
                    "摘要": prop_rich_text(row[5][:2000]),
                    "⭐": prop_checkbox(False),
                }
                if row[6]:
                    props["主題"] = prop_select(row[6])

                # body 放在 page body（children blocks）
                children = []
                body_text = row[5] if row[5] else ""
                if body_text:
                    for i in range(0, min(len(body_text), 20000), 1900):
                        children.append(block_paragraph(body_text[i:i+1900]))

                try:
                    add_page(notion_db, properties=props, children=children if children else None)
                    notion_count += 1
                except Exception as e:
                    print(f"[gmail-to-sheets] Notion 寫入失敗: {row[3][:30]}... — {e}", file=sys.stderr)

            print(f"[gmail-to-sheets] Notion 寫入 {notion_count} 封")
        except ImportError:
            print("[gmail-to-sheets] notion_api 模組不可用，跳過 Notion 寫入")
        except Exception as e:
            print(f"[gmail-to-sheets] Notion 寫入失敗: {e}", file=sys.stderr)

    print(f"\n[gmail-to-sheets] 完成！")


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
