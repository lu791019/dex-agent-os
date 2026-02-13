#!/usr/bin/env python3
"""Threads Collector — 透過 Threads API 抓取貼文並存為結構化範例

使用方式：
  1. 在 Meta Developer Dashboard 用「用戶權杖產生器」取得 access token
  2. 在 .env 中設定 THREADS_ACCESS_TOKEN=你的token
  3. 執行 ./bin/agent collect-threads
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import EXAMPLES_DIR, THREADS_TOKEN_PATH
from lib.file_utils import ensure_dir, write_text

# ── 常數 ──────────────────────────────────────────────

THREADS_API_BASE = "https://graph.threads.net/v1.0"

POST_FIELDS = "id,text,timestamp,permalink,media_type"
INSIGHT_METRICS = "views,likes,replies,reposts,quotes"


# ── .env 讀取 ──────────────────────────────────────────

def _load_env() -> dict:
    """從 .env 讀取環境變數。"""
    env = {}
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


# ── Token 管理 ──────────────────────────────────────────

def _save_token(token_data: dict):
    """儲存 token 到 config/.threads-token。"""
    ensure_dir(THREADS_TOKEN_PATH.parent)
    THREADS_TOKEN_PATH.write_text(
        json.dumps(token_data, indent=2), encoding="utf-8"
    )


def _load_token() -> Optional[dict]:
    """讀取已儲存的 token，回傳 None 如不存在。"""
    if not THREADS_TOKEN_PATH.exists():
        return None
    try:
        return json.loads(THREADS_TOKEN_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _get_access_token(env: dict) -> str:
    """取得 access token：優先 .env，其次 cached token file。"""
    # 1. 優先使用 .env 中的 token
    env_token = env.get("THREADS_ACCESS_TOKEN", "").strip()
    if env_token:
        # 快取到 config/.threads-token
        _save_token({
            "access_token": env_token,
            "source": "env",
            "saved_at": datetime.now().isoformat(),
        })
        return env_token

    # 2. 嘗試讀取已快取的 token
    cached = _load_token()
    if cached and cached.get("access_token"):
        return cached["access_token"]

    # 3. 都沒有
    print("[threads] ERROR: 找不到 access token", file=sys.stderr)
    print("[threads] 請按以下步驟取得 token：", file=sys.stderr)
    print("  1. 前往 https://developers.facebook.com/apps/", file=sys.stderr)
    print("  2. 選擇你的 Threads App → 左側「使用案例」→ Threads API", file=sys.stderr)
    print("  3. 點擊「用戶權杖產生器」(User Token Generator)", file=sys.stderr)
    print("  4. 勾選所需權限 → 點擊「產生權杖」", file=sys.stderr)
    print("  5. 複製 token，貼到 .env：", file=sys.stderr)
    print("     THREADS_ACCESS_TOKEN=你的token", file=sys.stderr)
    sys.exit(1)


# ── API 呼叫 ──────────────────────────────────────────

def _api_get(endpoint: str, access_token: str, params: Optional[dict] = None) -> dict:
    """呼叫 Threads API GET endpoint。"""
    from urllib.parse import urlencode

    url = f"{THREADS_API_BASE}/{endpoint}"
    if params is None:
        params = {}
    params["access_token"] = access_token
    url = f"{url}?{urlencode(params)}"

    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def _fetch_user_id(access_token: str) -> str:
    """透過 /me 取得使用者 ID。"""
    data = _api_get("me", access_token, {"fields": "id,username"})
    user_id = data.get("id", "")
    username = data.get("username", "")
    if username:
        print(f"[threads] Authenticated as @{username} (ID: {user_id})")
    return user_id


def _fetch_threads(access_token: str, limit: int = 50, since: Optional[str] = None) -> list:
    """取得使用者的所有 Threads 貼文。"""
    params = {"fields": POST_FIELDS, "limit": min(limit, 100)}
    if since:
        params["since"] = since

    all_posts = []
    data = _api_get("me/threads", access_token, params)
    all_posts.extend(data.get("data", []))

    # 分頁
    while len(all_posts) < limit and "paging" in data and "next" in data["paging"]:
        req = urllib.request.Request(data["paging"]["next"], method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        all_posts.extend(data.get("data", []))

    return all_posts[:limit]


def _fetch_insights(post_id: str, access_token: str) -> dict:
    """取得單篇貼文的互動數據。"""
    try:
        data = _api_get(f"{post_id}/insights", access_token, {"metric": INSIGHT_METRICS})
        metrics = {}
        for item in data.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [{}])
            metrics[name] = values[0].get("value", 0) if values else 0
        return metrics
    except Exception:
        return {}


# ── 格式轉換 ──────────────────────────────────────────

def _slugify(text: str) -> str:
    """將中英文標題轉為 URL-safe slug。"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:60] if text else "untitled"


def _format_post(post: dict, insights: dict, index: int):
    """將 API 回應轉為結構化 Markdown。回傳 (filename, content)。"""
    text = post.get("text", "").strip()
    if not text:
        return None, None

    timestamp = post.get("timestamp", "")
    date_str = timestamp[:10] if timestamp else "unknown"
    permalink = post.get("permalink", "")

    # 從文字前 30 字產生 slug
    first_line = text.split("\n")[0][:30]
    slug = _slugify(first_line)
    filename = f"{index:03d}-{slug}.md"

    # 互動數據
    likes = insights.get("likes", 0)
    replies = insights.get("replies", 0)
    reposts = insights.get("reposts", 0)
    views = insights.get("views", 0)
    quotes = insights.get("quotes", 0)

    # 評估互動表現
    total_engagement = likes + replies + reposts + quotes
    if total_engagement >= 50:
        performance = "高互動"
    elif total_engagement >= 15:
        performance = "中互動"
    else:
        performance = "低互動"

    content = f"""## 元資料
- 發布日期：{date_str}
- 互動數據：❤️ {likes} 💬 {replies} 🔄 {reposts} 👁️ {views}
- 表現評估：{performance}
- 連結：{permalink}

## 原文
{text}
"""
    return filename, content


# ── 主程式 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Threads Collector — 抓取 Threads 貼文")
    parser.add_argument("--limit", type=int, default=50, help="抓取數量上限（預設 50）")
    parser.add_argument("--since", type=str, default=None, help="只抓取此日期之後的貼文（YYYY-MM-DD）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的檔案")
    parser.add_argument("--token", type=str, default=None, help="直接傳入 access token（覆蓋 .env）")
    args = parser.parse_args()

    # 1. 讀取 .env
    env = _load_env()

    # 命令列 --token 覆蓋 .env
    if args.token:
        env["THREADS_ACCESS_TOKEN"] = args.token

    # 2. 取得 token
    access_token = _get_access_token(env)

    # 3. 驗證 token + 取得使用者資訊
    print("[threads] Verifying token...")
    try:
        _fetch_user_id(access_token)
    except Exception as e:
        error_msg = str(e)
        if "190" in error_msg or "expired" in error_msg.lower() or "invalid" in error_msg.lower():
            print(f"[threads] ERROR: Token 無效或已過期", file=sys.stderr)
            print("[threads] 請到 Meta Developer Dashboard 重新產生 token", file=sys.stderr)
            print("[threads] 並更新 .env 中的 THREADS_ACCESS_TOKEN", file=sys.stderr)
        else:
            print(f"[threads] ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. 抓取貼文
    print(f"[threads] Fetching threads (limit={args.limit})...")
    posts = _fetch_threads(access_token, limit=args.limit, since=args.since)
    print(f"[threads] Found {len(posts)} posts")

    if not posts:
        print("[threads] No posts found.")
        return

    # 5. 取得互動數據 + 轉換格式
    output_dir = ensure_dir(EXAMPLES_DIR / "threads")
    written = 0
    skipped = 0

    for i, post in enumerate(posts, 1):
        insights = _fetch_insights(post["id"], access_token)
        filename, content = _format_post(post, insights, i)

        if not filename:
            continue

        output_path = output_dir / filename
        if output_path.exists() and not args.force:
            skipped += 1
            continue

        write_text(output_path, content)
        written += 1
        print(f"  [{i}/{len(posts)}] {filename}")

    print(f"\n[threads] Done: {written} written, {skipped} skipped")
    print(f"[threads] Output: {output_dir}")


if __name__ == "__main__":
    main()
