#!/usr/bin/env python3
"""Dex Agent OS — 日記知識萃取器

從 L2 精煉日記中萃取「學到什麼」「卡在哪裡」「洞察 & 靈感」，
寫入 Claude Memory（專案級）+ 歸檔（800_System/knowledge/）+ Insight 檔案。

Usage:
    python3 scripts/extractors/journal_knowledge_extract.py [date|all] \
        [--type learnings|blockers|insights|all] [--force] [--dry-run] [--global]
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# 將專案根目錄加入 sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import (
    CLAUDE_MEMORY_DIR,
    CONTENT_INSIGHTS_DIR,
    INBOX_IDEAS_DIR,
    JOURNAL_DIR,
    KNOWLEDGE_DIR,
    LIFE_PERSONAL_DIR,
)
from lib.file_utils import ensure_dir, read_text, write_text
from lib.journal_parser import (
    extract_blockers,
    extract_date_from_filename,
    extract_insights,
    extract_learnings,
)
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

PROCESSED_FILE = KNOWLEDGE_DIR / ".processed"
LEARNINGS_ARCHIVE = KNOWLEDGE_DIR / "learnings-archive.md"
REFLECTIONS_ARCHIVE = KNOWLEDGE_DIR / "reflections-archive.md"
MEMORY_LEARNINGS = CLAUDE_MEMORY_DIR / "learnings.md"
MEMORY_REFLECTIONS = CLAUDE_MEMORY_DIR / "reflections.md"
GLOBAL_CLAUDE_MD = Path.home() / "CLAUDE.md"

MEMORY_LEARNINGS_MAX_LINES = 120
MEMORY_REFLECTIONS_MAX_LINES = 80
GLOBAL_MAX_LINES = 40

# ── 冪等性 ────────────────────────────────────────────


def load_processed() -> dict:
    """載入已處理日記記錄。"""
    if PROCESSED_FILE.exists():
        return json.loads(PROCESSED_FILE.read_text(encoding="utf-8"))
    return {}


def save_processed(data: dict) -> None:
    """儲存已處理日記記錄。"""
    ensure_dir(PROCESSED_FILE.parent)
    PROCESSED_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def file_hash(path: Path) -> str:
    """計算檔案 SHA-256 hash。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def needs_processing(
    path: Path, types: list[str], processed: dict, force: bool
) -> bool:
    """判斷是否需要處理此日記。"""
    if force:
        return True
    date_str = extract_date_from_filename(path)
    record = processed.get(date_str)
    if not record:
        return True
    current_hash = file_hash(path)
    if record.get("hash") != current_hash:
        return True
    processed_types = set(record.get("types", []))
    return not set(types).issubset(processed_types)


# ── 日記掃描 ──────────────────────────────────────────


def find_journals(date_arg: str) -> list[Path]:
    """根據日期參數找到要處理的日記檔案。

    date_arg: "all" 或 "YYYY-MM-DD" 或 ""（預設 all）
    只取主日記（不含 -dayflow.md）。
    """
    if not JOURNAL_DIR.exists():
        return []

    all_journals = sorted(
        p
        for p in JOURNAL_DIR.glob("*.md")
        if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", p.name)
    )

    if date_arg and date_arg != "all":
        target = JOURNAL_DIR / f"{date_arg}.md"
        return [target] if target.exists() else []

    return all_journals


# ── LLM 處理：Learnings ──────────────────────────────


LEARNINGS_SYSTEM = """\
你是知識管理助手，負責將每日學習記錄合併成結構化的知識庫。

規則：
- 四大分類：技術 / 工具 / 方法論 / 認知
- 每條格式：「**粗體關鍵詞**：一句話說明情境和具體做法」
- 重複出現的知識點要合併成更完整的版本
- 過時或已解決的知識點要移除
- 使用繁體中文
- 精簡版有行數硬限制，必須嚴格遵守
"""


def process_learnings(new_entries: dict[str, str], dry_run: bool) -> None:
    """處理所有新日記的「學到什麼」。

    Args:
        new_entries: {date_str: learnings_text}
        dry_run: 只顯示不寫入
    """
    if not new_entries:
        print("[learnings] 無新的學習記錄")
        return

    existing_memory = read_text(MEMORY_LEARNINGS)
    existing_archive = read_text(LEARNINGS_ARCHIVE)

    # 組裝新條目
    new_text = ""
    for date_str, text in sorted(new_entries.items()):
        new_text += f"\n### {date_str}\n{text}\n"

    prompt = f"""\
請將以下新的學習記錄與現有知識庫合併。

## 現有知識庫（精簡版，≤{MEMORY_LEARNINGS_MAX_LINES} 行）
{existing_memory if existing_memory else "（空，首次建立）"}

## 新增學習記錄
{new_text}

## 輸出要求

請產出兩個區塊，用 marker 分隔：

=== OUTPUT_MEMORY ===
（合併後的精簡版知識庫，≤{MEMORY_LEARNINGS_MAX_LINES} 行）
格式：
# Learnings — 學習知識庫

## 技術
- **關鍵詞**：說明...

## 工具
- **關鍵詞**：說明...

## 方法論
- **關鍵詞**：說明...

## 認知
- **關鍵詞**：說明...

=== OUTPUT_ARCHIVE ===
（只輸出本次新增的條目，供追加到歸檔檔案）
格式：
## YYYY-MM-DD
- 學習點 1
- 學習點 2
"""

    if dry_run:
        print(f"[learnings] 將處理 {len(new_entries)} 篇日記的學習記錄")
        print(f"[learnings] 現有 memory: {len(existing_memory)} 字元")
        return

    print(f"[learnings] 處理 {len(new_entries)} 篇日記的學習記錄...")
    result = ask_claude(user_prompt=prompt, system_prompt=LEARNINGS_SYSTEM)

    memory_part, archive_part = _split_output(result)

    if memory_part:
        write_text(MEMORY_LEARNINGS, memory_part)
        line_count = len(memory_part.splitlines())
        print(f"[learnings] memory 已更新：{line_count} 行")
    if archive_part:
        _append_archive(LEARNINGS_ARCHIVE, archive_part)
        print(f"[learnings] archive 已追加")


# ── LLM 處理：Blockers ───────────────────────────────


BLOCKERS_SYSTEM = """\
你是反思教練，負責將每日「卡關」記錄轉化為有深度的反思和可執行的教訓。

規則：
- 按模式分組：資源管理 / 技術債 / 決策品質 / 流程效率 / 其他
- 重複出現的 blocker 合併為更深入的反思（例如 rate limit 出現多次 → 合成一條完整的資源管理策略）
- 每條格式：「**粗體模式名**：情境描述 → 教訓/策略」
- 已完全解決且不再有參考價值的 blocker 可移除
- 使用繁體中文
- 精簡版有行數硬限制，必須嚴格遵守
"""


def process_blockers(new_entries: dict[str, str], dry_run: bool) -> None:
    """處理所有新日記的「卡在哪裡」。"""
    if not new_entries:
        print("[blockers] 無新的卡關記錄")
        return

    existing_memory = read_text(MEMORY_REFLECTIONS)
    existing_archive = read_text(REFLECTIONS_ARCHIVE)

    new_text = ""
    for date_str, text in sorted(new_entries.items()):
        new_text += f"\n### {date_str}\n{text}\n"

    prompt = f"""\
請將以下新的卡關記錄與現有反思庫合併。

## 現有反思庫（精簡版，≤{MEMORY_REFLECTIONS_MAX_LINES} 行）
{existing_memory if existing_memory else "（空，首次建立）"}

## 新增卡關記錄
{new_text}

## 輸出要求

請產出兩個區塊，用 marker 分隔：

=== OUTPUT_MEMORY ===
（合併後的精簡版反思庫，≤{MEMORY_REFLECTIONS_MAX_LINES} 行）
格式：
# Reflections — 反思教訓庫

## 資源管理
- **模式名**：情境 → 教訓...

## 技術債
- **模式名**：情境 → 教訓...

## 決策品質
- **模式名**：情境 → 教訓...

## 流程效率
- **模式名**：情境 → 教訓...

=== OUTPUT_ARCHIVE ===
（只輸出本次新增的條目，供追加到歸檔檔案）
格式：
## YYYY-MM-DD
- 卡關點 1
- 卡關點 2
"""

    if dry_run:
        print(f"[blockers] 將處理 {len(new_entries)} 篇日記的卡關記錄")
        print(f"[blockers] 現有 memory: {len(existing_memory)} 字元")
        return

    print(f"[blockers] 處理 {len(new_entries)} 篇日記的卡關記錄...")
    result = ask_claude(user_prompt=prompt, system_prompt=BLOCKERS_SYSTEM)

    memory_part, archive_part = _split_output(result)

    if memory_part:
        write_text(MEMORY_REFLECTIONS, memory_part)
        line_count = len(memory_part.splitlines())
        print(f"[blockers] memory 已更新：{line_count} 行")
    if archive_part:
        _append_archive(REFLECTIONS_ARCHIVE, archive_part)
        print(f"[blockers] archive 已追加")


# ── LLM 處理：Insights ───────────────────────────────


INSIGHTS_SYSTEM = """\
你是內容策略師，負責將日記中的洞察和靈感分類歸檔。

規則：
- 將每條 insight 分類為：content（內容素材）、idea（原始想法）、personal（個人反思）
- content：有明確頻道標記（→ Threads / Blog / Newsletter 等）的條目
- idea：沒有明確頻道但有潛力的想法
- personal：關於個人成長、職涯、生活的反思
- 為每條 insight 產生一個英文 slug（用於檔名）
- 使用繁體中文
- 必須輸出合法 JSON array
"""


def process_insights(new_entries: dict[str, str], dry_run: bool) -> None:
    """處理所有新日記的「洞察 & 靈感」。"""
    if not new_entries:
        print("[insights] 無新的洞察記錄")
        return

    new_text = ""
    for date_str, text in sorted(new_entries.items()):
        new_text += f"\n### {date_str}\n{text}\n"

    prompt = f"""\
請將以下洞察和靈感分類並產出 JSON array。

## 洞察原文
{new_text}

## 輸出要求

請輸出一個 JSON array，每個元素格式如下：
```json
[
  {{
    "date": "2026-02-07",
    "slug": "multi-ide-sync-best-practice",
    "classification": "content",
    "channel_tags": ["Threads", "Blog"],
    "title": "多 AI IDE 協作的最佳實踐",
    "body": "canonical 單一真實來源 + sync 腳本...",
    "angles": "可以寫成教學文，比較各 IDE 規則格式的差異..."
  }}
]
```

classification 只能是 content / idea / personal 三選一。
channel_tags 只在 classification=content 時需要，其他給空 array。
只輸出 JSON，不要加其他文字。
"""

    if dry_run:
        print(f"[insights] 將處理 {len(new_entries)} 篇日記的洞察記錄")
        return

    print(f"[insights] 處理 {len(new_entries)} 篇日記的洞察記錄...")
    result = ask_claude(user_prompt=prompt, system_prompt=INSIGHTS_SYSTEM)

    # 從回應中提取 JSON
    insights = _parse_insights_json(result)

    if not insights:
        print("[insights] 警告：無法解析 LLM 回應為 JSON")
        print(f"[insights] 原始回應：{result[:500]}")
        return

    for item in insights:
        _write_insight_file(item)

    print(f"[insights] 已產出 {len(insights)} 個 insight 檔案")


def _write_insight_file(item: dict) -> None:
    """將單個 insight 寫入對應目錄。"""
    classification = item.get("classification", "idea")
    date = item.get("date", datetime.now().strftime("%Y-%m-%d"))
    slug = item.get("slug", "untitled")
    title = item.get("title", "")
    body = item.get("body", "")
    angles = item.get("angles", "")
    channel_tags = item.get("channel_tags", [])

    # 決定目標目錄
    if classification == "content":
        dest_dir = CONTENT_INSIGHTS_DIR
    elif classification == "personal":
        dest_dir = LIFE_PERSONAL_DIR
    else:
        dest_dir = INBOX_IDEAS_DIR

    filename = f"{date}-{slug}.md"
    filepath = dest_dir / filename

    if filepath.exists():
        print(f"[insights] 跳過已存在：{filepath.name}")
        return

    tags_str = json.dumps(channel_tags, ensure_ascii=False)
    content = f"""\
---
date: {date}
source: 100_Journal/daily/{date}.md
classification: {classification}
channel_tags: {tags_str}
status: raw
---

# {title}

{body}

## 潛在切入角度
{angles}
"""

    write_text(filepath, content)
    print(f"[insights] → {filepath.relative_to(ROOT_DIR)}")


def _parse_insights_json(text: str) -> list[dict]:
    """從 LLM 回應中提取 JSON array。"""
    # 嘗試直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 嘗試從 ```json ... ``` 提取
    match = re.search(r"```json\s*\n(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 嘗試找到 [ ... ] 區塊
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return []


# ── 全域更新 ──────────────────────────────────────────


GLOBAL_SYSTEM = """\
你是知識精煉師，負責將詳細的學習和反思庫壓縮成全域速查表。

規則：
- 只保留跨專案通用的知識（工具用法、平台特性、工程原則、通用教訓）
- 太專案特定的細節不放（例如某個 DB 的表結構）
- 四大分類：工具與環境 / 跨平台 / 工程原則 / 反思教訓
- 每條格式：「情境 + 具體做法/避坑」，一行就能讓 Claude 直接套用
- 使用繁體中文
- 嚴格遵守行數上限
"""


def update_global_claude_md(dry_run: bool) -> None:
    """讀取 memory 版 → LLM 精煉 → 原地替換 ~/CLAUDE.md 的「累積學習」區段。"""
    learnings = read_text(MEMORY_LEARNINGS)
    reflections = read_text(MEMORY_REFLECTIONS)

    if not learnings and not reflections:
        print("[global] memory 為空，跳過全域更新")
        return

    prompt = f"""\
請將以下學習知識庫和反思教訓庫精煉為全域速查表。

## 學習知識庫
{learnings if learnings else "（空）"}

## 反思教訓庫
{reflections if reflections else "（空）"}

## 輸出要求

產出一個 ≤{GLOBAL_MAX_LINES} 行的速查表，格式如下：

## 累積學習（自動更新，勿手動編輯）

### 工具與環境
- 具體做法 1
- 具體做法 2

### 跨平台
- 具體做法 1

### 工程原則
- 具體做法 1

### 反思教訓
- 具體教訓 1

### 深度知識庫（非每次讀取，依情境觸發）
**P1 必讀** — 進入 Plan Mode 或撰寫 implementation_plan.md 前，
  讀取 `~/.claude/projects/-Users-dex-dex-agent-os/memory/learnings.md`
  和 `~/.claude/projects/-Users-dex-dex-agent-os/memory/reflections.md`
**P2 選讀** — 同一問題連續失敗 2 次以上，讀取 `~/.claude/projects/-Users-dex-dex-agent-os/memory/reflections.md`
**不讀** — 一般 coding、內容撰寫、git 操作使用上方速查表即可

注意：
- 「深度知識庫」區段必須原封不動輸出，不可修改。只精煉上方四個分類的內容。
- 只輸出速查表本身（從 ## 累積學習 開始），不要加任何額外說明、統計或後記。
"""

    if dry_run:
        print("[global] 將更新 ~/CLAUDE.md 的「累積學習」區段")
        print(f"[global] learnings: {len(learnings)} 字元")
        print(f"[global] reflections: {len(reflections)} 字元")
        return

    print("[global] 精煉全域速查表...")
    result = ask_claude(user_prompt=prompt, system_prompt=GLOBAL_SYSTEM)

    # 確保結果以 ## 累積學習 開頭
    if not result.startswith("## 累積學習"):
        result = "## 累積學習（自動更新，勿手動編輯）\n\n" + result

    # 清理 LLM 可能的多餘輸出（統計、說明等）
    # 截斷到最後一個 --- 分隔線之前
    lines = result.splitlines()
    clean_lines = []
    for line in lines:
        # 停在獨立的 --- 分隔線（不讀」後面的附加說明）
        if line.strip() == "---":
            break
        clean_lines.append(line)
    result = "\n".join(clean_lines).rstrip()

    _replace_global_section(result)


def _replace_global_section(new_section: str) -> None:
    """在 ~/CLAUDE.md 中原地替換「累積學習」區段。"""
    content = read_text(GLOBAL_CLAUDE_MD)
    if not content:
        print("[global] 警告：~/CLAUDE.md 不存在")
        return

    marker = "## 累積學習"

    # 找到現有區段的起始位置
    idx = content.find(marker)
    if idx >= 0:
        # 替換從 marker 到檔案結尾
        new_content = content[:idx].rstrip() + "\n\n" + new_section.strip() + "\n"
    else:
        # 首次加入，附加到檔案末尾
        new_content = content.rstrip() + "\n\n" + new_section.strip() + "\n"

    write_text(GLOBAL_CLAUDE_MD, new_content)
    line_count = len(new_section.splitlines())
    print(f"[global] ~/CLAUDE.md 已更新（累積學習 {line_count} 行）")


# ── 共用工具 ──────────────────────────────────────────


def _split_output(text: str) -> tuple[str, str]:
    """用 marker 分隔 LLM 的雙輸出。"""
    memory_marker = "=== OUTPUT_MEMORY ==="
    archive_marker = "=== OUTPUT_ARCHIVE ==="

    memory_part = ""
    archive_part = ""

    if memory_marker in text and archive_marker in text:
        parts = text.split(archive_marker, 1)
        memory_part = parts[0].split(memory_marker, 1)[-1].strip()
        archive_part = parts[1].strip()
    elif memory_marker in text:
        memory_part = text.split(memory_marker, 1)[-1].strip()
    else:
        # fallback: 整個當作 memory
        memory_part = text.strip()

    return memory_part, archive_part


def _append_archive(archive_path: Path, new_content: str) -> None:
    """追加內容到歸檔檔案。"""
    existing = read_text(archive_path)
    if existing:
        combined = existing.rstrip() + "\n\n" + new_content.strip() + "\n"
    else:
        header = f"# {'Learnings' if 'learnings' in archive_path.name else 'Reflections'} Archive\n\n"
        combined = header + new_content.strip() + "\n"
    write_text(archive_path, combined)


# ── Main ──────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="萃取日記知識（學習/反思/靈感）"
    )
    parser.add_argument(
        "date",
        nargs="?",
        default="all",
        help="日期 YYYY-MM-DD 或 all（預設：all）",
    )
    parser.add_argument(
        "--type",
        choices=["learnings", "blockers", "insights", "all"],
        default="all",
        help="萃取類型（預設：all）",
    )
    parser.add_argument("--force", action="store_true", help="強制重新處理")
    parser.add_argument("--dry-run", action="store_true", help="只顯示不寫入")
    parser.add_argument("--global", dest="update_global", action="store_true",
                        help="同時更新全域 ~/CLAUDE.md")
    args = parser.parse_args()

    # 決定處理哪些類型
    if args.type == "all":
        types = ["learnings", "blockers", "insights"]
    else:
        types = [args.type]

    # 找到要處理的日記
    journals = find_journals(args.date)
    if not journals:
        print(f"[extract] 找不到日記：{args.date}")
        sys.exit(1)

    print(f"[extract] 找到 {len(journals)} 篇日記")

    # 冪等性檢查
    processed = load_processed()
    to_process = [
        j for j in journals if needs_processing(j, types, processed, args.force)
    ]

    if not to_process:
        print("[extract] 所有日記已處理過（用 --force 強制重新處理）")
        if args.update_global:
            update_global_claude_md(args.dry_run)
        return

    print(f"[extract] 需處理 {len(to_process)} 篇（跳過 {len(journals) - len(to_process)} 篇）")

    # 收集各類型的原文
    learnings_entries: dict[str, str] = {}
    blockers_entries: dict[str, str] = {}
    insights_entries: dict[str, str] = {}

    for journal_path in to_process:
        date_str = extract_date_from_filename(journal_path)
        content = journal_path.read_text(encoding="utf-8")

        if "learnings" in types:
            text = extract_learnings(content)
            if text:
                learnings_entries[date_str] = text

        if "blockers" in types:
            text = extract_blockers(content)
            if text:
                blockers_entries[date_str] = text

        if "insights" in types:
            text = extract_insights(content)
            if text:
                insights_entries[date_str] = text

    # LLM 處理（固定 3 次呼叫）
    if "learnings" in types:
        process_learnings(learnings_entries, args.dry_run)

    if "blockers" in types:
        process_blockers(blockers_entries, args.dry_run)

    if "insights" in types:
        process_insights(insights_entries, args.dry_run)

    # 更新 .processed 記錄
    if not args.dry_run:
        for journal_path in to_process:
            date_str = extract_date_from_filename(journal_path)
            existing_record = processed.get(date_str, {})
            existing_types = set(existing_record.get("types", []))
            processed[date_str] = {
                "hash": file_hash(journal_path),
                "processed_at": datetime.now().isoformat(),
                "types": sorted(existing_types | set(types)),
            }
        save_processed(processed)
        print("[extract] .processed 記錄已更新")

    # 全域更新
    if args.update_global:
        update_global_claude_md(args.dry_run)


if __name__ == "__main__":
    main()
