#!/usr/bin/env python3
"""Podcast Transcript Collector — 收集 podcast 逐字稿並產出結構化 episode 筆記

使用方式：
  # P4: 手動文字稿
  ./bin/agent podcast-add --transcript ~/transcript.txt --title "Hard Fork: AI Agents"

  # P3: Apple Podcast TTML 快取
  ./bin/agent podcast-add --apple              # 列出最近聽過的集數
  ./bin/agent podcast-add --apple --latest 3   # 自動匯入最新 3 集

  # P5: Notion（Podwise 匯出）
  ./bin/agent podcast-add --notion             # 列出最近 7 天 episodes
  ./bin/agent podcast-add --notion --latest 5  # 匯入最新 5 集
  ./bin/agent podcast-add --notion --all       # 匯入全部

  # P6: Readwise（Podwise 匯出）
  ./bin/agent podcast-add --readwise           # 列出最近 7 天 highlights
  ./bin/agent podcast-add --readwise --latest 5

  # 共用參數
  --date YYYY-MM-DD    指定日期（預設今天）
  --force              覆蓋已存在的 episode
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import (
    APPLE_PODCAST_TTML_DIR,
    NOTION_PODWISE_DB_ID,
    NOTION_TOKEN,
    PODCAST_EPISODES_DIR,
    PODCAST_TRANSCRIPTS_DIR,
    READWISE_TOKEN,
    TEMPLATES_DIR,
)
from lib.file_utils import ensure_dir, read_text, today_str, write_text
from lib.llm import ask_claude


# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 助理，負責將 Podcast 逐字稿轉為結構化 episode 筆記。

你需要做的：
- 辨識 podcast 名稱和 episode 標題（如能從內容推斷）
- 從逐字稿中提煉核心觀點（3-5 個）
- 挑出值得記住的關鍵引述（原文）
- 辨識與市場趨勢相關的內容（如有）
- 列出可轉化為 Threads/Newsletter 的素材

輸出規則：
- 使用繁體中文
- 嚴格按照指定的模板格式輸出
- 只輸出筆記內容，不要加額外說明
- 一句話摘要要精準，不超過 30 字
- 「我的想法」區塊保留 <!-- 手動補充 --> 不要填寫
"""

NOTION_API_VERSION = "2022-06-28"
NOTION_API_BASE = "https://api.notion.com/v1"
READWISE_API_BASE = "https://readwise.io/api/v2"


# ── 工具函式 ──────────────────────────────────────────

def slugify(text: str) -> str:
    """將標題轉為 URL-safe slug。"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:50] if text else "untitled"


def _get_requests():
    """取得 requests 模組，fallback 到 urllib。"""
    try:
        import requests
        return requests
    except ImportError:
        return None


def _api_request(method: str, url: str, headers: dict, json_data: dict | None = None, params: dict | None = None) -> dict:
    """統一 API 請求：優先用 requests，fallback 到 urllib。"""
    requests = _get_requests()

    if requests:
        for attempt in range(3):
            resp = requests.request(method, url, headers=headers, json=json_data, params=params, timeout=30)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2))
                print(f"[podcast] Rate limited, waiting {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            if resp.status_code == 401:
                print("[podcast] ERROR: Token 無效或 Integration 未連接 database", file=sys.stderr)
                print("  請確認 token 正確，且 Integration 已連接到 database", file=sys.stderr)
                print("  設定步驟見 GUIDE.md", file=sys.stderr)
                sys.exit(1)
            resp.raise_for_status()
            return resp.json()
        print("[podcast] ERROR: API 重試 3 次仍失敗", file=sys.stderr)
        sys.exit(1)
    else:
        # fallback: urllib
        import urllib.request
        import urllib.error

        req_headers = dict(headers)
        body = None
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    retry_after = int(e.headers.get("Retry-After", 2))
                    print(f"[podcast] Rate limited, waiting {retry_after}s...", file=sys.stderr)
                    time.sleep(retry_after)
                    continue
                if e.code == 401:
                    print("[podcast] ERROR: Token 無效或 Integration 未連接 database", file=sys.stderr)
                    print("  設定步驟見 GUIDE.md", file=sys.stderr)
                    sys.exit(1)
                raise
        print("[podcast] ERROR: API 重試 3 次仍失敗", file=sys.stderr)
        sys.exit(1)


# ── 模式 P4：手動文字稿 ──────────────────────────────

def read_transcript_file(path: str) -> str:
    """讀取使用者提供的文字稿檔案。"""
    p = Path(path).expanduser()
    if not p.exists():
        print(f"[podcast] ERROR: 找不到檔案 {p}", file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8", errors="replace")


# ── 模式 P3：Apple Podcast TTML 快取 ──────────────────

def parse_ttml(ttml_path: Path) -> str:
    """解析 TTML 檔案，回傳純文字。"""
    tree = ET.parse(ttml_path)
    root = tree.getroot()

    # TTML 命名空間
    ns = {"tt": "http://www.w3.org/ns/ttml"}
    body = root.find(".//tt:body", ns)
    if body is None:
        # 嘗試不帶命名空間
        body = root.find(".//body")

    if body is None:
        return ttml_path.read_text(encoding="utf-8", errors="replace")

    texts = []
    for p_elem in body.iter():
        if p_elem.text and p_elem.text.strip():
            texts.append(p_elem.text.strip())
        if p_elem.tail and p_elem.tail.strip():
            texts.append(p_elem.tail.strip())

    return " ".join(texts)


def list_apple_podcasts() -> list[tuple[Path, datetime]]:
    """列出 Apple Podcast TTML 快取檔案，按修改時間排序。"""
    if not APPLE_PODCAST_TTML_DIR.exists():
        print("[podcast] Apple Podcast TTML 快取目錄不存在", file=sys.stderr)
        print(f"  預期路徑：{APPLE_PODCAST_TTML_DIR}", file=sys.stderr)
        return []

    ttml_files = list(APPLE_PODCAST_TTML_DIR.rglob("*.ttml"))
    if not ttml_files:
        ttml_files = list(APPLE_PODCAST_TTML_DIR.rglob("*.xml"))

    results = []
    for f in ttml_files:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        results.append((f, mtime))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ── 模式 P5：Notion（Podwise 匯出） ─────────────────

def _check_notion_setup() -> bool:
    """檢查 Notion 設定，未設定時顯示引導。"""
    if not NOTION_TOKEN:
        print("[podcast] Notion token 未設定。請先完成設定：", file=sys.stderr)
        print("", file=sys.stderr)
        print("  1. 到 https://www.notion.so/my-integrations → 建立新 Integration", file=sys.stderr)
        print("  2. 複製 Internal Integration Secret", file=sys.stderr)
        print("  3. 存入 .env：NOTION_TOKEN=secret_xxxxxxxxxxxx", file=sys.stderr)
        print("", file=sys.stderr)
        print("  詳細步驟見 GUIDE.md", file=sys.stderr)
        return False
    if not NOTION_PODWISE_DB_ID:
        print("[podcast] Notion database ID 未設定。請先完成設定：", file=sys.stderr)
        print("", file=sys.stderr)
        print("  1. 在 Podwise 匯出的 Notion database → '...' → 'Connect to' → 選 Integration", file=sys.stderr)
        print("  2. 複製 database URL 中的 32 碼 ID", file=sys.stderr)
        print("  3. 存入 .env：NOTION_PODWISE_DB_ID=xxxxxxxx", file=sys.stderr)
        print("", file=sys.stderr)
        print("  詳細步驟見 GUIDE.md", file=sys.stderr)
        return False
    return True


def _notion_headers() -> dict:
    """Notion API request headers。"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def notion_query_database(limit: int = 0, fetch_all: bool = False) -> list[dict]:
    """查詢 Notion Podwise database，回傳 page 列表。

    Args:
        limit: 限制回傳筆數（0=預設 7 天內）
        fetch_all: 取得全部
    """
    headers = _notion_headers()
    url = f"{NOTION_API_BASE}/databases/{NOTION_PODWISE_DB_ID}/query"

    body: dict = {
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
    }

    # 非 fetch_all 且無 limit 時，預設只抓 7 天內
    if not fetch_all and limit == 0:
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        body["filter"] = {
            "timestamp": "created_time",
            "created_time": {"on_or_after": seven_days_ago},
        }

    if limit > 0 and limit <= 100:
        body["page_size"] = limit

    pages = []
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            body["start_cursor"] = next_cursor

        data = _api_request("POST", url, headers, json_data=body)
        pages.extend(data.get("results", []))

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

        # 已達到 limit 就停
        if limit > 0 and len(pages) >= limit:
            pages = pages[:limit]
            break

        # Rate limit：Notion 建議 3 req/s
        time.sleep(0.35)

    return pages


def notion_read_page_blocks(page_id: str) -> str:
    """讀取 Notion page 的所有 blocks，轉為純文字。"""
    headers = _notion_headers()
    url = f"{NOTION_API_BASE}/blocks/{page_id}/children"

    all_blocks = []
    has_more = True
    next_cursor = None

    while has_more:
        params = {"page_size": 100}
        if next_cursor:
            params["start_cursor"] = next_cursor

        data = _api_request("GET", url, headers, params=params)
        all_blocks.extend(data.get("results", []))

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
        time.sleep(0.35)

    return _blocks_to_text(all_blocks)


def _blocks_to_text(blocks: list[dict]) -> str:
    """將 Notion blocks 轉為純文字。"""
    lines = []
    for block in blocks:
        block_type = block.get("type", "")
        block_data = block.get(block_type, {})

        if block_type in ("paragraph", "quote", "callout", "toggle"):
            text = _rich_text_to_str(block_data.get("rich_text", []))
            if text:
                lines.append(text)

        elif block_type.startswith("heading_"):
            level = block_type[-1]  # "heading_1" → "1"
            text = _rich_text_to_str(block_data.get("rich_text", []))
            if text:
                lines.append(f"{'#' * int(level)} {text}")

        elif block_type == "bulleted_list_item":
            text = _rich_text_to_str(block_data.get("rich_text", []))
            if text:
                lines.append(f"- {text}")

        elif block_type == "numbered_list_item":
            text = _rich_text_to_str(block_data.get("rich_text", []))
            if text:
                lines.append(f"1. {text}")

        elif block_type == "to_do":
            text = _rich_text_to_str(block_data.get("rich_text", []))
            checked = block_data.get("checked", False)
            if text:
                lines.append(f"- [{'x' if checked else ' '}] {text}")

        elif block_type == "code":
            text = _rich_text_to_str(block_data.get("rich_text", []))
            lang = block_data.get("language", "")
            if text:
                lines.append(f"```{lang}\n{text}\n```")

        elif block_type == "divider":
            lines.append("---")

    return "\n\n".join(lines)


def _rich_text_to_str(rich_text: list[dict]) -> str:
    """將 Notion rich_text 陣列轉為純文字。"""
    return "".join(item.get("plain_text", "") for item in rich_text)


def _notion_page_title(page: dict) -> str:
    """從 Notion page 中提取標題。"""
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            return _rich_text_to_str(prop.get("title", []))
    return "Untitled"


def _notion_page_date(page: dict) -> str:
    """從 Notion page 提取日期（created_time）。"""
    created = page.get("created_time", "")
    if created:
        return created[:10]  # "2026-02-10T..." → "2026-02-10"
    return today_str()


def handle_notion(args) -> None:
    """P5: 從 Notion Podwise DB 匯入 episode 筆記。"""
    if not _check_notion_setup():
        sys.exit(1)

    date_str = args.date or today_str()
    limit = args.latest if args.latest > 0 else 0

    print("[podcast] Querying Notion Podwise database...")
    pages = notion_query_database(limit=limit, fetch_all=args.all)

    if not pages:
        print("[podcast] Notion database 中沒有找到 episode", file=sys.stderr)
        print("  如果你剛設定完成，請確認：", file=sys.stderr)
        print("  1. Podwise 已匯出至 Notion", file=sys.stderr)
        print("  2. Integration 已連接到正確的 database", file=sys.stderr)
        return

    # 無 --latest 且非 --all：列出讓使用者選擇
    if args.latest == 0 and not args.all:
        print(f"\n[podcast] 找到 {len(pages)} 個 episode：\n")
        for i, page in enumerate(pages[:20], 1):
            title = _notion_page_title(page)
            date = _notion_page_date(page)
            print(f"  {i:2d}. [{date}] {title}")
        print(f"\n使用 --latest N 匯入最新 N 集，或 --all 匯入全部")
        return

    print(f"[podcast] 準備匯入 {len(pages)} 個 episode...")
    for page in pages:
        title = _notion_page_title(page)
        page_date = _notion_page_date(page)
        page_id = page["id"]

        slug = slugify(title)
        output_path = PODCAST_EPISODES_DIR / f"{page_date}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[podcast] SKIP: {output_path.name} 已存在")
            continue

        print(f"\n[podcast] Reading: {title}")
        content = notion_read_page_blocks(page_id)
        print(f"[podcast] Content: {len(content)} chars")

        if len(content) < 50:
            print("[podcast] SKIP: 內容太短，跳過")
            continue

        output = generate_episode_note(
            title=title,
            transcript_text=content,
            date_str=args.date or page_date,
            source=f"Notion Podwise ({title})",
            force=args.force,
        )
        print(f"[podcast] Done: {output.relative_to(ROOT_DIR)}")


# ── 模式 P6：Readwise（Podwise 匯出） ───────────────

def _check_readwise_setup() -> bool:
    """檢查 Readwise 設定，未設定時顯示引導。"""
    if not READWISE_TOKEN:
        print("[podcast] Readwise token 未設定。請先完成設定：", file=sys.stderr)
        print("", file=sys.stderr)
        print("  1. 到 https://readwise.io/access_token → 複製 token", file=sys.stderr)
        print("  2. 存入 .env：READWISE_TOKEN=xxxxxxxxxxxx", file=sys.stderr)
        print("", file=sys.stderr)
        print("  詳細步驟見 GUIDE.md", file=sys.stderr)
        return False
    return True


def _readwise_headers() -> dict:
    """Readwise API request headers。"""
    return {
        "Authorization": f"Token {READWISE_TOKEN}",
    }


def readwise_export_podcasts(limit: int = 0, fetch_all: bool = False) -> list[dict]:
    """從 Readwise 匯出 podcast highlights，回傳按 book 分組的列表。

    Args:
        limit: 限制回傳筆數（0=預設 7 天內）
        fetch_all: 取得全部
    """
    headers = _readwise_headers()
    url = f"{READWISE_API_BASE}/export/"

    params: dict = {}

    # 非 fetch_all 且無 limit 時，預設只抓 7 天內
    if not fetch_all and limit == 0:
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        params["updatedAfter"] = seven_days_ago

    all_books = []
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            params["pageCursor"] = next_cursor

        data = _api_request("GET", url, headers, params=params)
        results = data.get("results", [])

        # 過濾只留 podcast 類別
        for book in results:
            if book.get("category") == "podcasts":
                all_books.append(book)

        next_cursor = data.get("nextPageCursor")
        has_more = next_cursor is not None

        # 已達到 limit 就停
        if limit > 0 and len(all_books) >= limit:
            all_books = all_books[:limit]
            break

        time.sleep(0.35)

    return all_books


def _readwise_book_to_text(book: dict) -> str:
    """將 Readwise book（episode）的 highlights 合併為文字。"""
    lines = []

    # Episode 基本資訊
    title = book.get("title", "Untitled")
    author = book.get("author", "")
    source_url = book.get("source_url", "")

    lines.append(f"# {title}")
    if author:
        lines.append(f"Host/Author: {author}")
    if source_url:
        lines.append(f"Source: {source_url}")
    lines.append("")

    # Highlights
    highlights = book.get("highlights", [])
    if highlights:
        lines.append("## Highlights & Notes")
        for hl in highlights:
            text = hl.get("text", "")
            note = hl.get("note", "")
            if text:
                lines.append(f"\n> {text}")
            if note:
                lines.append(f"\n**Note:** {note}")

    return "\n".join(lines)


def handle_readwise(args) -> None:
    """P6: 從 Readwise 匯入 podcast highlights。"""
    if not _check_readwise_setup():
        sys.exit(1)

    date_str = args.date or today_str()
    limit = args.latest if args.latest > 0 else 0

    print("[podcast] Querying Readwise podcast highlights...")
    books = readwise_export_podcasts(limit=limit, fetch_all=args.all)

    if not books:
        print("[podcast] Readwise 中沒有找到 podcast highlights", file=sys.stderr)
        print("  如果你剛設定完成，請確認：", file=sys.stderr)
        print("  1. Podwise 已連結到 Readwise", file=sys.stderr)
        print("  2. Readwise 中有 podcasts 類別的 highlights", file=sys.stderr)
        return

    # 無 --latest 且非 --all：列出讓使用者選擇
    if args.latest == 0 and not args.all:
        print(f"\n[podcast] 找到 {len(books)} 個 podcast episode：\n")
        for i, book in enumerate(books[:20], 1):
            title = book.get("title", "Untitled")
            hl_count = len(book.get("highlights", []))
            print(f"  {i:2d}. {title} ({hl_count} highlights)")
        print(f"\n使用 --latest N 匯入最新 N 集，或 --all 匯入全部")
        return

    print(f"[podcast] 準備匯入 {len(books)} 個 episode...")
    for book in books:
        title = book.get("title", "Untitled")
        # Readwise 的 updated 格式：ISO 8601
        updated = book.get("updated", "")
        book_date = updated[:10] if updated else date_str

        slug = slugify(title)
        output_path = PODCAST_EPISODES_DIR / f"{book_date}-{slug}.md"

        if output_path.exists() and not args.force:
            print(f"[podcast] SKIP: {output_path.name} 已存在")
            continue

        print(f"\n[podcast] Processing: {title}")
        content = _readwise_book_to_text(book)
        print(f"[podcast] Content: {len(content)} chars")

        if len(content) < 50:
            print("[podcast] SKIP: 內容太短，跳過")
            continue

        output = generate_episode_note(
            title=title,
            transcript_text=content,
            date_str=args.date or book_date,
            source=f"Readwise ({title})",
            force=args.force,
        )
        print(f"[podcast] Done: {output.relative_to(ROOT_DIR)}")


# ── LLM 結構化 ──────────────────────────────────────

def build_prompt(
    title: str,
    transcript_text: str,
    template: str,
    date_str: str,
    source: str = "",
) -> str:
    """組裝送給 LLM 的提示。"""
    max_chars = 80000
    if len(transcript_text) > max_chars:
        transcript_text = transcript_text[:max_chars] + "\n\n[... 逐字稿過長，已截斷 ...]"

    return f"""\
請根據以下 Podcast 逐字稿，產出一份結構化 episode 筆記。

## Episode 資訊
- 標題：{title}
- 日期：{date_str}
- 來源：{source or "手動匯入"}

## 逐字稿
{transcript_text}

## 輸出格式
請嚴格按照以下模板格式輸出（替換 {{{{佔位符}}}} 為實際內容）：

{template}

## 注意事項
- 如能從逐字稿推斷 podcast 名稱，填入 podcast 欄位
- duration 如無法確定請留空
- tags 至少填 2-3 個相關標籤
- 「我的想法」保留 <!-- 手動補充 --> 不要填寫
"""


def generate_episode_note(
    title: str,
    transcript_text: str,
    date_str: str,
    source: str = "",
    force: bool = False,
) -> Path:
    """用 LLM 產出結構化筆記並寫入檔案。"""
    slug = slugify(title)
    output_path = PODCAST_EPISODES_DIR / f"{date_str}-{slug}.md"

    if output_path.exists() and not force:
        print(f"[podcast] {output_path.name} 已存在，使用 --force 覆蓋", file=sys.stderr)
        sys.exit(1)

    template = read_text(TEMPLATES_DIR / "podcast-episode-template.md")
    prompt = build_prompt(title, transcript_text, template, date_str, source)

    print("[podcast] Generating structured episode note...")
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 清理 — 確保以 frontmatter 或標題開頭
    if result and not result.startswith("---") and not result.startswith("#"):
        for marker in ["---", "# "]:
            pos = result.find(marker)
            if pos != -1:
                result = result[pos:]
                break

    ensure_dir(PODCAST_EPISODES_DIR)
    write_text(output_path, result.strip() + "\n")
    return output_path


# ── 主程式 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Podcast Transcript Collector — 逐字稿 → episode 筆記")

    # 輸入模式
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--transcript", type=str, help="P4: 手動指定逐字稿文字檔路徑")
    mode.add_argument("--apple", action="store_true", help="P3: Apple Podcast TTML 快取")
    mode.add_argument("--notion", action="store_true", help="P5: 從 Notion Podwise DB 匯入")
    mode.add_argument("--readwise", action="store_true", help="P6: 從 Readwise 匯入 podcast highlights")

    # 共用參數
    parser.add_argument("--title", type=str, default=None, help="手動指定標題")
    parser.add_argument("--date", type=str, default=None, help="指定日期 (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的 episode")
    parser.add_argument("--latest", type=int, default=0, help="自動匯入最新 N 集")
    parser.add_argument("--all", action="store_true", help="匯入全部（不限日期）")

    args = parser.parse_args()
    date_str = args.date or today_str()

    # ── P4: 手動文字稿 ──
    if args.transcript:
        if not args.title:
            print("[podcast] ERROR: --transcript 模式需要搭配 --title", file=sys.stderr)
            sys.exit(1)

        print(f"[podcast] Reading transcript: {args.transcript}")
        transcript_text = read_transcript_file(args.transcript)
        print(f"[podcast] Transcript: {len(transcript_text)} chars")

        # 儲存原始逐字稿
        ensure_dir(PODCAST_TRANSCRIPTS_DIR)
        slug = slugify(args.title)
        raw_path = PODCAST_TRANSCRIPTS_DIR / f"{date_str}-{slug}.txt"
        write_text(raw_path, transcript_text)

        output = generate_episode_note(
            title=args.title,
            transcript_text=transcript_text,
            date_str=date_str,
            force=args.force,
        )
        print(f"[podcast] Done: {output.relative_to(ROOT_DIR)}")

    # ── P3: Apple Podcast TTML 快取 ──
    elif args.apple:
        episodes = list_apple_podcasts()
        if not episodes:
            print("[podcast] 找不到 Apple Podcast TTML 快取", file=sys.stderr)
            sys.exit(1)

        # 自動匯入最新 N 集
        if args.latest > 0:
            targets = episodes[: args.latest]
        else:
            # 列出讓使用者選擇
            print(f"\n[podcast] 找到 {len(episodes)} 個 TTML 快取：\n")
            for i, (path, mtime) in enumerate(episodes[:20], 1):
                print(f"  {i:2d}. [{mtime.strftime('%Y-%m-%d %H:%M')}] {path.name}")
            print(f"\n使用 --latest N 自動匯入最新 N 集")
            print(f"或手動複製 TTML 內容為 .txt，用 --transcript 模式匯入")
            return

        for ttml_path, mtime in targets:
            ttml_date = mtime.strftime("%Y-%m-%d")
            print(f"\n[podcast] Processing: {ttml_path.name}")
            transcript_text = parse_ttml(ttml_path)
            print(f"[podcast] Transcript: {len(transcript_text)} chars")

            if len(transcript_text) < 50:
                print("[podcast] SKIP: 逐字稿太短，跳過")
                continue

            title = args.title or ttml_path.stem
            output = generate_episode_note(
                title=title,
                transcript_text=transcript_text,
                date_str=args.date or ttml_date,
                source=f"Apple Podcast ({ttml_path.name})",
                force=args.force,
            )
            print(f"[podcast] Done: {output.relative_to(ROOT_DIR)}")

    # ── P5: Notion（Podwise 匯出） ──
    elif args.notion:
        handle_notion(args)

    # ── P6: Readwise（Podwise 匯出） ──
    elif args.readwise:
        handle_readwise(args)


if __name__ == "__main__":
    main()
