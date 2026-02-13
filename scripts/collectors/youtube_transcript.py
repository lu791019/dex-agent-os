#!/usr/bin/env python3
"""YouTube Transcript Collector — 取得 YouTube 字幕並產出結構化學習筆記

使用方式：
  ./bin/agent youtube-add "https://youtube.com/watch?v=xxx"
  ./bin/agent youtube-add "https://youtube.com/watch?v=xxx" --force
  ./bin/agent youtube-add "https://youtube.com/watch?v=xxx" --date 2026-02-10
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import YOUTUBE_DIR, TEMPLATES_DIR
from lib.file_utils import ensure_dir, read_text, today_str, write_text
from lib.llm import ask_claude


# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 助理，負責將 YouTube 影片逐字稿轉為結構化學習筆記。

你需要做的：
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


# ── 工具函式 ──────────────────────────────────────────

def extract_video_id(url: str) -> str:
    """從 YouTube URL 提取 video ID。"""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError(f"無法從 URL 提取 video ID: {url}")


def fetch_video_title(video_id: str) -> str:
    """透過 YouTube 頁面取得影片標題（無需 API key）。"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    req = urllib.request.Request(url, headers={"Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        m = re.search(r"<title>(.+?)</title>", content)
        if m:
            title = html.unescape(m.group(1))
            # 移除 " - YouTube" 後綴
            title = re.sub(r"\s*-\s*YouTube\s*$", "", title)
            return title.strip()
    except Exception:
        pass
    return ""


def fetch_transcript(video_id: str) -> tuple[str, str, bool]:
    """取得逐字稿。回傳 (text, language_code, is_generated)。"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("[youtube] ERROR: 請先安裝 youtube-transcript-api", file=sys.stderr)
        print("  pip3 install youtube-transcript-api", file=sys.stderr)
        sys.exit(1)

    ytt = YouTubeTranscriptApi()
    transcript = ytt.fetch(video_id, languages=["zh-Hant", "zh", "en"])
    text = " ".join(snippet.text for snippet in transcript)
    return text, transcript.language_code, transcript.is_generated


def slugify(text: str) -> str:
    """將標題轉為 URL-safe slug。"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:50] if text else "untitled"


# ── Prompt 組裝 ──────────────────────────────────────

def build_prompt(
    title: str,
    video_url: str,
    transcript_text: str,
    language: str,
    template: str,
    date_str: str,
) -> str:
    """組裝送給 LLM 的提示。"""
    # 截斷過長的逐字稿（避免超出 context window）
    max_chars = 80000
    if len(transcript_text) > max_chars:
        transcript_text = transcript_text[:max_chars] + "\n\n[... 逐字稿過長，已截斷 ...]"

    return f"""\
請根據以下 YouTube 影片逐字稿，產出一份結構化學習筆記。

## 影片資訊
- 標題：{title}
- 來源：{video_url}
- 日期：{date_str}
- 語言：{language}

## 逐字稿
{transcript_text}

## 輸出格式
請嚴格按照以下模板格式輸出（替換 {{{{佔位符}}}} 為實際內容）：

{template}

## 注意事項
- title 使用影片原始標題
- channel 填寫頻道名稱（如能從逐字稿推斷）
- duration 如無法確定請留空
- source 使用提供的 YouTube URL
- tags 至少填 2-3 個相關標籤
- 「我的想法」保留 <!-- 手動補充 --> 不要填寫
"""


# ── 主程式 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="YouTube Transcript Collector — 取字幕產筆記")
    parser.add_argument("url", help="YouTube URL 或 video ID")
    parser.add_argument("--title", type=str, default=None, help="手動指定標題")
    parser.add_argument("--date", type=str, default=None, help="指定日期 (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的筆記")
    args = parser.parse_args()

    # 1. 提取 video ID
    video_id = extract_video_id(args.url)
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    date_str = args.date or today_str()
    print(f"[youtube] Video ID: {video_id}")

    # 2. 取得標題
    title = args.title or fetch_video_title(video_id)
    if not title:
        title = f"youtube-{video_id}"
    print(f"[youtube] Title: {title}")

    # 3. 檢查輸出是否已存在
    slug = slugify(title)
    output_path = YOUTUBE_DIR / f"{date_str}-{slug}.md"
    if output_path.exists() and not args.force:
        print(f"[youtube] {output_path.name} 已存在，使用 --force 覆蓋", file=sys.stderr)
        sys.exit(1)

    # 4. 取得逐字稿
    print("[youtube] Fetching transcript...")
    try:
        transcript_text, lang_code, is_generated = fetch_transcript(video_id)
    except Exception as e:
        print(f"[youtube] ERROR: 無法取得逐字稿 — {e}", file=sys.stderr)
        sys.exit(1)

    sub_type = "自動產生" if is_generated else "人工字幕"
    print(f"[youtube] Transcript: {lang_code} ({sub_type}), {len(transcript_text)} chars")

    # 5. 讀取模板
    template = read_text(TEMPLATES_DIR / "youtube-note-template.md")

    # 6. LLM 產出結構化筆記
    print("[youtube] Generating structured note...")
    prompt = build_prompt(title, video_url, transcript_text, lang_code, template, date_str)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 7. 清理 — 確保以 frontmatter 或標題開頭
    if result and not result.startswith("---") and not result.startswith("#"):
        # 嘗試找到 frontmatter 或標題的起始位置
        for marker in ["---", "# "]:
            pos = result.find(marker)
            if pos != -1:
                result = result[pos:]
                break

    # 8. 寫入
    ensure_dir(YOUTUBE_DIR)
    write_text(output_path, result.strip() + "\n")
    print(f"[youtube] Done: {output_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
