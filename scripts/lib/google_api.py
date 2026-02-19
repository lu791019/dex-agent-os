"""Dex Agent OS — Google Workspace API（Docs + Gmail）

提供 OAuth2 認證、Google Doc 建立、Gmail 寄信。
未設定時優雅 fallback（印提示，不 crash）。

需要：
  pip install google-auth google-auth-oauthlib google-api-python-client markdown

GCP 設定步驟：
  1. GCP Console → 建立專案 → 啟用 Google Docs API + Gmail API
  2. OAuth 同意畫面 → External → 加測試者（自己的 Gmail）
  3. 建立 OAuth 桌面應用程式憑證 → 下載 JSON
  4. 存為 config/google-credentials.json
  5. 首次執行 --send 會開瀏覽器授權，token 存在 config/google-token.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

CREDENTIALS_PATH = ROOT_DIR / "config" / "google-credentials.json"
TOKEN_PATH = ROOT_DIR / "config" / "google-token.json"

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def check_google_setup() -> bool:
    """檢查 Google API 是否已設定。未設定時印提示並回傳 False。"""
    if not CREDENTIALS_PATH.exists():
        print("[google-api] Google API 未設定。", file=sys.stderr)
        print("", file=sys.stderr)
        print("  設定步驟：", file=sys.stderr)
        print("  1. GCP Console → 建立專案 → 啟用 Docs API + Gmail API", file=sys.stderr)
        print("  2. OAuth 同意畫面 → External → 加測試者", file=sys.stderr)
        print("  3. 建立 OAuth 桌面應用程式憑證", file=sys.stderr)
        print(f"  4. 下載 JSON 存為 {CREDENTIALS_PATH}", file=sys.stderr)
        print("", file=sys.stderr)
        print("  詳細步驟見 GUIDE.md", file=sys.stderr)
        return False
    return True


def authenticate():
    """OAuth2 認證，回傳 credentials。首次會開瀏覽器。

    Returns:
        google.oauth2.credentials.Credentials or None
    """
    if not check_google_setup():
        return None

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("[google-api] 缺少套件。執行：pip3 install google-auth google-auth-oauthlib google-api-python-client", file=sys.stderr)
        return None

    creds = None

    # 讀取已存的 token
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            pass

    # Token 無效或過期 → refresh 或重新授權
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        # 存 token
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return creds


def create_google_doc(title: str, markdown_content: str) -> str | None:
    """建立 Google Doc，回傳文件 URL。

    Args:
        title: 文件標題
        markdown_content: Markdown 格式內容（會轉為純文字插入）

    Returns:
        Google Doc URL or None（失敗時）
    """
    creds = authenticate()
    if not creds:
        return None

    try:
        from googleapiclient.discovery import build

        # 建立空文件
        docs_service = build("docs", "v1", credentials=creds)
        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]

        # 插入內容（純文字，Google Docs 不直接支援 Markdown）
        requests_body = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": markdown_content,
                }
            }
        ]
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests_body}
        ).execute()

        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        print(f"[google-api] Google Doc 已建立：{url}")
        return url

    except Exception as e:
        print(f"[google-api] 建立 Google Doc 失敗：{e}", file=sys.stderr)
        return None


def send_gmail(to: str, subject: str, body_md: str, doc_url: str | None = None) -> bool:
    """寄送 Gmail（Markdown → HTML）。

    Args:
        to: 收件者 email
        subject: 信件主旨
        body_md: Markdown 格式內容
        doc_url: Google Doc 連結（選填，會附在信尾）

    Returns:
        True if sent successfully
    """
    creds = authenticate()
    if not creds:
        return False

    try:
        import base64
        from email.mime.text import MIMEText

        import markdown as md
        from googleapiclient.discovery import build

        # Markdown → HTML
        html_body = md.markdown(body_md, extensions=["tables", "fenced_code"])

        if doc_url:
            html_body += f'\n<hr>\n<p>📄 <a href="{doc_url}">完整版 Google Doc</a></p>'

        msg = MIMEText(html_body, "html", "utf-8")
        msg["to"] = to
        msg["subject"] = subject

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        gmail_service = build("gmail", "v1", credentials=creds)
        gmail_service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

        print(f"[google-api] Gmail 已寄出 → {to}")
        return True

    except Exception as e:
        print(f"[google-api] 寄送 Gmail 失敗：{e}", file=sys.stderr)
        return False
