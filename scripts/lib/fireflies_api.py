"""Fireflies.ai GraphQL API 共用模組

提供：
  check_fireflies_setup()   — API key 檢查 + 引導訊息
  list_transcripts(limit)   — 列出最近的會議逐字稿
  get_transcript(id)        — 取得完整逐字稿（含講者標記）

需要設定：
  FIREFLIES_API_KEY 環境變數（存入 config/.env）

API 文件：https://docs.fireflies.ai/graphql-api/
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import FIREFLIES_API_KEY

FIREFLIES_GRAPHQL_URL = "https://api.fireflies.ai/graphql"


# ── 設定檢查 ──────────────────────────────────────────


def check_fireflies_setup() -> bool:
    """檢查 Fireflies API key，未設定時顯示引導。"""
    if not FIREFLIES_API_KEY:
        print("[fireflies] API key 未設定。請先完成設定：", file=sys.stderr)
        print("", file=sys.stderr)
        print("  1. 到 https://app.fireflies.ai/integrations/custom/fireflies → 建立 API key", file=sys.stderr)
        print("  2. 存入 config/.env：FIREFLIES_API_KEY=your_api_key_here", file=sys.stderr)
        print("", file=sys.stderr)
        print("  注意：需要 Fireflies 付費方案才能使用 API", file=sys.stderr)
        print("  詳細步驟見 GUIDE.md", file=sys.stderr)
        return False
    return True


# ── GraphQL 請求 ──────────────────────────────────────


def _graphql_request(query: str, variables: dict | None = None) -> dict | None:
    """發送 GraphQL 請求到 Fireflies API。

    Args:
        query: GraphQL query 字串
        variables: GraphQL 變數（可選）

    Returns:
        回應的 data 欄位，或 None（失敗時）
    """
    headers = {
        "Authorization": f"Bearer {FIREFLIES_API_KEY}",
        "Content-Type": "application/json",
    }

    payload: dict = {"query": query}
    if variables:
        payload["variables"] = variables

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        FIREFLIES_GRAPHQL_URL,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("[fireflies] ERROR: API key 無效，請確認 FIREFLIES_API_KEY 設定正確", file=sys.stderr)
        elif e.code == 403:
            print("[fireflies] ERROR: 權限不足，可能需要升級 Fireflies 方案", file=sys.stderr)
        else:
            print(f"[fireflies] ERROR: HTTP {e.code} — {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"[fireflies] ERROR: 無法連線 — {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[fireflies] ERROR: {e}", file=sys.stderr)
        return None

    # 檢查 GraphQL 錯誤
    if "errors" in result:
        for err in result["errors"]:
            print(f"[fireflies] GraphQL error: {err.get('message', err)}", file=sys.stderr)
        return None

    return result.get("data")


# ── 公開 API ──────────────────────────────────────────


def list_transcripts(limit: int = 10) -> list[dict] | None:
    """列出最近的會議逐字稿。

    Args:
        limit: 回傳筆數上限（預設 10）

    Returns:
        逐字稿列表，每筆包含 id, title, date, duration, participants。
        失敗時回傳 None。
    """
    query = """
    query ListTranscripts($limit: Int) {
        transcripts(limit: $limit) {
            id
            title
            date
            duration
            participants
        }
    }
    """
    data = _graphql_request(query, variables={"limit": limit})
    if data is None:
        return None

    transcripts = data.get("transcripts")
    if transcripts is None:
        print("[fireflies] 回應中沒有 transcripts 欄位", file=sys.stderr)
        return None

    print(f"[fireflies] 取得 {len(transcripts)} 筆逐字稿")
    return transcripts


def get_transcript(transcript_id: str) -> dict | None:
    """取得完整逐字稿（含講者標記）。

    Args:
        transcript_id: Fireflies transcript ID

    Returns:
        逐字稿資料，包含 id, title, date, duration, participants,
        sentences（含 speaker_name, text, raw_text）。
        失敗時回傳 None。
    """
    query = """
    query GetTranscript($id: String!) {
        transcript(id: $id) {
            id
            title
            date
            duration
            participants
            sentences {
                speaker_name
                text
                raw_text
            }
        }
    }
    """
    data = _graphql_request(query, variables={"id": transcript_id})
    if data is None:
        return None

    transcript = data.get("transcript")
    if transcript is None:
        print(f"[fireflies] 找不到逐字稿 ID: {transcript_id}", file=sys.stderr)
        return None

    sentence_count = len(transcript.get("sentences") or [])
    print(f"[fireflies] 取得逐字稿: {transcript.get('title', 'Untitled')} ({sentence_count} sentences)")
    return transcript
