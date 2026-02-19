#!/usr/bin/env python3
"""Gmail Sync — Gmail 電子報批次匯入

使用方式：
  ./bin/agent gmail-sync                                # 列出最近 7 天電子報
  ./bin/agent gmail-sync --latest 5 --force             # 匯入最新 5 封
  ./bin/agent gmail-sync --label "newsletters"          # 指定 label
  ./bin/agent gmail-sync --from "newsletter@substack.com" --latest 3 --force
  ./bin/agent gmail-sync --query "from:substack.com" --latest 5 --force

  輸出：000_Inbox/readings/YYYY-MM-DD-<subject-slug>.md
  無 LLM，直接擷取 email body 為 Markdown
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

from lib.config import READINGS_DIR
from lib.file_utils import ensure_dir, write_text


# ── Gmail API ─────────────────────────────────────────

def _get_gmail_service():
    """取得 Gmail API service，使用 google_api.py 的 OAuth。"""
    try:
        from lib.google_api import authenticate
    except ImportError:
        print("[gmail-sync] 無法載入 google_api 模組", file=sys.stderr)
        return None

    creds = authenticate()
    if not creds:
        return None

    try:
        from googleapiclient.discovery import build
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        print(f"[gmail-sync] Gmail API 建立失敗：{e}", file=sys.stderr)
        return None


def _search_emails(service, query: str, max_results: int = 20) -> list[dict]:
    """搜尋 Gmail，回傳 message metadata list。"""
    try:
        result = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        return result.get("messages", [])
    except Exception as e:
        print(f"[gmail-sync] 搜尋失敗：{e}", file=sys.stderr)
        return []


def _get_message(service, msg_id: str) -> dict | None:
    """取得完整 email（含 body）。"""
    try:
        return service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()
    except Exception as e:
        print(f"[gmail-sync] 取得信件失敗：{e}", file=sys.stderr)
        return None


def _extract_header(msg: dict, name: str) -> str:
    """從 message headers 取得指定欄位。"""
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _extract_body(msg: dict) -> str:
    """從 message payload 擷取 HTML 或純文字 body。"""
    payload = msg.get("payload", {})

    # 嘗試直接取 body
    body_data = payload.get("body", {}).get("data")
    if body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    # multipart：遍歷 parts 找 text/html 或 text/plain
    parts = payload.get("parts", [])
    html_body = ""
    text_body = ""

    for part in parts:
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")

        if not data:
            # 巢狀 multipart
            for sub in part.get("parts", []):
                sub_mime = sub.get("mimeType", "")
                sub_data = sub.get("body", {}).get("data")
                if sub_data:
                    decoded = base64.urlsafe_b64decode(sub_data).decode("utf-8", errors="replace")
                    if "html" in sub_mime:
                        html_body = decoded
                    elif "plain" in sub_mime:
                        text_body = decoded
            continue

        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        if "html" in mime:
            html_body = decoded
        elif "plain" in mime:
            text_body = decoded

    # 優先用 HTML 轉 markdown，fallback 純文字
    if html_body:
        return _html_to_text(html_body)
    return text_body


def _html_to_text(html: str) -> str:
    """HTML → 純文字（簡易轉換）。"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # 移除 script/style
        for tag in soup(["script", "style"]):
            tag.decompose()

        # 取純文字
        text = soup.get_text(separator="\n")
        # 清理多餘空行
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)
    except ImportError:
        # fallback：簡易 regex 清理
        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


# ── 輸出 ──────────────────────────────────────────────

def _slugify(text: str) -> str:
    """標題轉 slug。"""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60].strip("-")


def _format_date(internal_date_ms: str) -> str:
    """Gmail internal date (ms) → YYYY-MM-DD。"""
    ts = int(internal_date_ms) / 1000
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def _save_email(msg: dict, force: bool = False) -> Path | None:
    """將 email 存為 Markdown 到 000_Inbox/readings/。"""
    subject = _extract_header(msg, "Subject") or "untitled"
    sender = _extract_header(msg, "From")
    date_str = _format_date(msg.get("internalDate", "0"))
    slug = _slugify(subject)

    ensure_dir(READINGS_DIR)
    output_path = READINGS_DIR / f"{date_str}-gmail-{slug}.md"

    if output_path.exists() and not force:
        return None

    body = _extract_body(msg)
    if not body or len(body.strip()) < 50:
        print(f"  SKIP: {subject[:50]}（內容太短或為空）")
        return None

    # 截斷過長內容
    if len(body) > 10000:
        body = body[:10000] + "\n\n... [截斷，原文更長] ..."

    content = f"""---
title: "{subject}"
source: gmail
from: "{sender}"
date: {date_str}
type: newsletter
---

# {subject}

> From: {sender}
> Date: {date_str}

{body}
"""
    write_text(output_path, content)
    return output_path


# ── 主程式 ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gmail Sync — 電子報批次匯入")
    parser.add_argument("--latest", type=int, default=10, help="最多匯入幾封（預設 10）")
    parser.add_argument("--label", default=None, help="指定 Gmail label（如 newsletters）")
    parser.add_argument("--from", dest="from_addr", default=None, help="篩選寄件者")
    parser.add_argument("--query", default=None, help="自訂 Gmail 搜尋語法")
    parser.add_argument("--days", type=int, default=7, help="搜尋最近幾天（預設 7）")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的檔案")

    args = parser.parse_args()

    # 建立搜尋條件
    if args.query:
        query = args.query
    else:
        parts = []
        if args.label:
            parts.append(f"label:{args.label}")
        if args.from_addr:
            parts.append(f"from:{args.from_addr}")
        # 預設：搜尋 category:promotions 或 category:updates（電子報常見分類）
        if not parts:
            parts.append("(category:promotions OR category:updates)")
        after_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y/%m/%d")
        parts.append(f"after:{after_date}")
        query = " ".join(parts)

    print(f"[gmail-sync] 搜尋：{query}")

    service = _get_gmail_service()
    if not service:
        return

    messages = _search_emails(service, query, max_results=args.latest)

    if not messages:
        print("[gmail-sync] 沒有找到符合條件的信件")
        return

    print(f"[gmail-sync] 找到 {len(messages)} 封信件")

    # 無 --force 時列出清單
    if not args.force:
        for i, m in enumerate(messages, 1):
            full = _get_message(service, m["id"])
            if full:
                subj = _extract_header(full, "Subject")[:60]
                sender = _extract_header(full, "From")[:40]
                date = _format_date(full.get("internalDate", "0"))
                print(f"  {i}. [{date}] {subj}")
                print(f"     From: {sender}")
        print(f"\n加 --force 匯入這些信件")
        return

    # --force：匯入
    imported = 0
    skipped = 0
    for m in messages:
        full = _get_message(service, m["id"])
        if not full:
            continue
        subj = _extract_header(full, "Subject")[:60]
        path = _save_email(full, force=args.force)
        if path:
            print(f"  ✅ {subj} → {path.name}")
            imported += 1
        else:
            skipped += 1

    print(f"\n[gmail-sync] 完成：匯入 {imported} 封，跳過 {skipped} 封")


if __name__ == "__main__":
    main()
