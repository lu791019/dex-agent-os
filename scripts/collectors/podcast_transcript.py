#!/usr/bin/env python3
"""Podcast Transcript Collector — 收集 podcast 逐字稿並產出結構化 episode 筆記

使用方式：
  # P4: 手動文字稿
  ./bin/agent podcast-add --transcript ~/transcript.txt --title "Hard Fork: AI Agents"

  # P3: Apple Podcast TTML 快取
  ./bin/agent podcast-add --apple              # 列出最近聽過的集數
  ./bin/agent podcast-add --apple --latest 3   # 自動匯入最新 3 集

  # 共用參數
  --date YYYY-MM-DD    指定日期（預設今天）
  --force              覆蓋已存在的 episode
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import (
    APPLE_PODCAST_TTML_DIR,
    PODCAST_EPISODES_DIR,
    PODCAST_TRANSCRIPTS_DIR,
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


# ── 工具函式 ──────────────────────────────────────────

def slugify(text: str) -> str:
    """將標題轉為 URL-safe slug。"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:50] if text else "untitled"


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

    # 共用參數
    parser.add_argument("--title", type=str, default=None, help="手動指定標題")
    parser.add_argument("--date", type=str, default=None, help="指定日期 (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="覆蓋已存在的 episode")
    parser.add_argument("--latest", type=int, default=0, help="--apple 模式：自動匯入最新 N 集")

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


if __name__ == "__main__":
    main()
