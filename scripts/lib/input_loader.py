#!/usr/bin/env python3
"""共用輸入載入 — 支援逐字稿/筆記/Google Doc/Fireflies 四種模式"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))


def load_from_transcript(path: str) -> str:
    """從檔案讀取逐字稿內容。

    Args:
        path: 逐字稿檔案路徑

    Returns:
        檔案內容文字
    """
    p = Path(path)
    if not p.exists():
        print(f"[input-loader] 找不到逐字稿檔案：{path}", file=sys.stderr)
        sys.exit(1)
    content = p.read_text(encoding="utf-8", errors="replace").strip()
    if not content:
        print(f"[input-loader] 逐字稿檔案為空：{path}", file=sys.stderr)
        sys.exit(1)
    print(f"[input-loader] 已讀取逐字稿（{len(content)} 字元）")
    return content


def load_from_notes(text: str) -> str:
    """直接回傳筆記文字。

    Args:
        text: 筆記內容

    Returns:
        筆記文字
    """
    if not text or not text.strip():
        print("[input-loader] 筆記內容為空", file=sys.stderr)
        sys.exit(1)
    return text.strip()


def load_from_google_doc(url: str) -> str:
    """從 Google Doc URL 讀取內容。

    Args:
        url: Google Doc URL

    Returns:
        文件純文字內容
    """
    from lib.google_api import read_google_doc

    content = read_google_doc(url)
    if content is None:
        print(f"[input-loader] 無法讀取 Google Doc：{url}", file=sys.stderr)
        sys.exit(1)
    return content


def load_from_fireflies(fireflies_id: str | None = None) -> str:
    """從 Fireflies.ai 取得逐字稿。

    Args:
        fireflies_id: 指定的 transcript ID（None 時取最新一筆）

    Returns:
        格式化的逐字稿文字
    """
    from lib.fireflies_api import check_fireflies_setup, get_transcript, list_transcripts

    if not check_fireflies_setup():
        sys.exit(1)

    if fireflies_id:
        transcript = get_transcript(fireflies_id)
    else:
        # 取最新一筆
        transcripts = list_transcripts(limit=1)
        if not transcripts:
            print("[input-loader] 找不到任何 Fireflies 逐字稿", file=sys.stderr)
            sys.exit(1)
        transcript = get_transcript(transcripts[0]["id"])

    if transcript is None:
        print("[input-loader] 無法取得 Fireflies 逐字稿", file=sys.stderr)
        sys.exit(1)

    # 格式化為可讀文字
    lines = []
    title = transcript.get("title", "Untitled")
    lines.append(f"會議標題：{title}")
    participants = transcript.get("participants") or []
    if participants:
        lines.append(f"與會者：{', '.join(participants)}")
    lines.append("")

    sentences = transcript.get("sentences") or []
    for s in sentences:
        speaker = s.get("speaker_name", "Unknown")
        text = s.get("text", "").strip()
        if text:
            lines.append(f"{speaker}：{text}")

    content = "\n".join(lines)
    print(f"[input-loader] 已取得 Fireflies 逐字稿：{title}（{len(sentences)} sentences）")
    return content


def add_input_args(parser) -> None:
    """新增輸入模式參數到 argparse parser。

    四種互斥的輸入模式：
      --transcript  從檔案讀取逐字稿
      --notes       直接傳入筆記文字
      --google-doc  從 Google Doc URL 讀取
      --fireflies   使用 Fireflies.ai 最新逐字稿
      --fireflies-id  指定 Fireflies transcript ID

    Args:
        parser: argparse.ArgumentParser 實例
    """
    group = parser.add_argument_group("輸入來源（擇一）")
    group.add_argument("--transcript", metavar="FILE", help="逐字稿檔案路徑")
    group.add_argument("--notes", metavar="TEXT", help="直接傳入筆記文字")
    group.add_argument("--google-doc", metavar="URL", help="Google Doc URL")
    group.add_argument("--fireflies", action="store_true", help="使用 Fireflies.ai 最新逐字稿")
    group.add_argument("--fireflies-id", metavar="ID", help="指定 Fireflies transcript ID")


def load_input(args) -> str:
    """根據 args 統一載入輸入內容。

    Args:
        args: argparse 解析後的 namespace（需包含 transcript/notes/google_doc/fireflies/fireflies_id）

    Returns:
        載入的輸入文字
    """
    if args.transcript:
        return load_from_transcript(args.transcript)
    elif args.notes:
        return load_from_notes(args.notes)
    elif args.google_doc:
        return load_from_google_doc(args.google_doc)
    elif args.fireflies or args.fireflies_id:
        return load_from_fireflies(args.fireflies_id)
    else:
        print("[input-loader] 請指定輸入來源：--transcript / --notes / --google-doc / --fireflies", file=sys.stderr)
        sys.exit(1)
