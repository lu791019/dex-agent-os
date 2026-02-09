"""Dex Agent OS — 日記區段解析器

從 L2 精煉日記中提取「學到什麼」「卡在哪裡」「洞察 & 靈感」三個區段。
"""

import re
from pathlib import Path


def parse_sections(content: str) -> dict[str, str]:
    """將日記 markdown 按 ## heading 切割成 dict。

    Returns:
        {"學到什麼": "...", "卡在哪裡": "...", ...}
    """
    sections: dict[str, str] = {}
    current_heading = ""
    current_lines: list[str] = []

    for line in content.splitlines():
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def extract_learnings(content: str) -> str:
    """提取「學到什麼」區段原文。"""
    sections = parse_sections(content)
    return sections.get("學到什麼", "")


def extract_blockers(content: str) -> str:
    """提取「卡在哪裡」區段原文。"""
    sections = parse_sections(content)
    return sections.get("卡在哪裡", "")


def extract_insights(content: str) -> str:
    """提取「洞察 & 靈感」區段原文，跳過 blockquote 描述行。"""
    sections = parse_sections(content)
    raw = sections.get("洞察 & 靈感", "")
    if not raw:
        return ""

    # 移除 "> 可轉化為內容素材的想法" 這類 blockquote 描述行
    lines = [
        line
        for line in raw.splitlines()
        if not re.match(r"^>\s*可轉化為", line)
    ]
    return "\n".join(lines).strip()


def extract_date_from_filename(path: Path) -> str:
    """從檔名提取日期字串。

    例如 2026-02-07.md → "2026-02-07"
    """
    return path.stem.split("-dayflow")[0]
