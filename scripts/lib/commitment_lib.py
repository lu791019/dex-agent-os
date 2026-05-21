"""承諾追蹤器核心邏輯 — queue I/O、預篩、去重、分流寫入。

純邏輯集中此檔，方便單元測試。Hook 腳本與 /承諾 workflow 呼叫這裡的函式。
"""

from __future__ import annotations

import json
from difflib import SequenceMatcher
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

QUEUE_FILE = ROOT_DIR / "data" / "commitment_queue.json"
DEV_COMMITMENTS_FILE = ROOT_DIR / "200_Work" / "commitments.md"
SITUATION_BOARD = Path.home() / "daydreamdex" / "state" / "situation-board.md"


def load_queue(path: Path | None = None) -> list[dict]:
    """讀 pending queue。檔案不存在或損壞時回空 list。

    path=None 時動態解析 QUEUE_FILE（測試可重新指派模組常數）。
    """
    path = path or QUEUE_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def save_queue(items: list[dict], path: Path | None = None) -> None:
    """寫 pending queue。path=None 時動態解析 QUEUE_FILE。"""
    path = path or QUEUE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def clear_queue(path: Path | None = None) -> None:
    """清空 pending queue。"""
    save_queue([], path=path)


# 承諾語感關鍵字 — 命中任一即觸發 LLM 抽取
_SIGNAL_KEYWORDS = (
    "我會", "我來", "我去", "下次", "之後再", "待辦", "記到", "記入",
    "排入", "排程", "承諾", "確認後", "等我", "我負責", "我處理",
    "TODO", "to-do", "下一步我", "我先", "我晚點",
)


def has_commitment_signal(text: str) -> bool:
    """便宜預篩：文字是否含承諾語感關鍵字。

    寧可誤判為有（多跑一次 LLM），不可漏判（漏掉真承諾）。
    """
    return any(kw in text for kw in _SIGNAL_KEYWORDS)


def parse_commitment_table(md: str, heading: str) -> list[dict]:
    """從 markdown 抽出指定標題下第一個表格的承諾列。

    回傳 [{"text": 第一欄, "raw": 整列原文}, ...]。
    找不到標題或表格則回空 list。
    """
    lines = md.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.lstrip("#").strip().startswith(heading):
            start = i + 1
            break
    if start is None:
        return []

    rows: list[dict] = []
    seen_separator = False
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        if set(cells[0]) <= set("-: "):
            seen_separator = True
            continue
        if not seen_separator:
            continue  # 表頭列
        rows.append({"text": cells[0], "raw": stripped})
    return rows


def read_open_commitments() -> list[dict]:
    """讀兩個 board 的未結案承諾。

    回傳 [{"text": ..., "source": "cxo"|"dev"}, ...]。
    檔案不存在則該來源略過。
    """
    result: list[dict] = []
    if SITUATION_BOARD.exists():
        md = SITUATION_BOARD.read_text(encoding="utf-8")
        for row in parse_commitment_table(md, heading="承諾"):
            result.append({"text": row["text"], "source": "cxo"})
    if DEV_COMMITMENTS_FILE.exists():
        md = DEV_COMMITMENTS_FILE.read_text(encoding="utf-8")
        for row in parse_commitment_table(md, heading="未結案"):
            result.append({"text": row["text"], "source": "dev"})
    return result


def is_duplicate(text: str, existing: list[str], threshold: float = 0.8) -> bool:
    """text 是否與 existing 任一項高度相似（相似度 >= threshold）。"""
    for other in existing:
        if SequenceMatcher(None, text, other).ratio() >= threshold:
            return True
    return False


def _situation_table_bounds(lines: list[str]) -> tuple[int, int] | None:
    """回傳 situation-board 承諾表格的 (最後一列 index, 結束 index)。

    找不到表格回 None。
    """
    start = None
    for i, line in enumerate(lines):
        if line.lstrip("#").strip().startswith("承諾"):
            start = i + 1
            break
    if start is None:
        return None
    last_row = None
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("|"):
            last_row = i
    if last_row is None:
        return None
    return last_row, last_row + 1


def append_situation_board_row(md: str, item: dict) -> str:
    """在 situation-board 承諾表格尾端插入一列。回傳新 md。

    找不到表格則原樣回傳。
    """
    lines = md.splitlines()
    bounds = _situation_table_bounds(lines)
    if bounds is None:
        return md
    insert_at = bounds[1]
    role = item.get("cxo_role") or "—"
    deadline = item.get("deadline") or "—"
    new_row = f"| {item['text']} | {role} | {deadline} | 待處理 |"
    lines.insert(insert_at, new_row)
    return "\n".join(lines) + ("\n" if md.endswith("\n") else "")


def remove_situation_board_row(md: str, text: str) -> str:
    """移除承諾表格中第一欄等於 text 的列。回傳新 md。"""
    lines = md.splitlines()
    kept = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if cells and cells[0] == text:
                continue
        kept.append(line)
    return "\n".join(kept) + ("\n" if md.endswith("\n") else "")


def _dev_table_bounds(lines: list[str]) -> tuple[int, int] | None:
    """回傳 dev commitments「未結案」表格的 (最後一列 index, 結束 index)。"""
    start = None
    for i, line in enumerate(lines):
        if line.lstrip("#").strip().startswith("未結案"):
            start = i + 1
            break
    if start is None:
        return None
    last_row = None
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("|"):
            last_row = i
    if last_row is None:
        return None
    return last_row, last_row + 1


def append_dev_commitment_row(md: str, item: dict) -> str:
    """在 dev commitments 未結案表格尾端插入一列。回傳新 md。"""
    lines = md.splitlines()
    bounds = _dev_table_bounds(lines)
    if bounds is None:
        return md
    deadline = item.get("deadline") or "—"
    source = (item.get("source_session") or "—")[:12]
    new_row = (
        f"| {item['text']} | {item.get('owner', 'Dex')} "
        f"| {deadline} | 待處理 | {source} |"
    )
    lines.insert(bounds[1], new_row)
    return "\n".join(lines) + ("\n" if md.endswith("\n") else "")


def remove_dev_commitment_row(md: str, text: str) -> str:
    """移除 dev commitments 表格中第一欄等於 text 的列。回傳新 md。"""
    lines = md.splitlines()
    kept = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if cells and cells[0] == text:
                continue
        kept.append(line)
    return "\n".join(kept) + ("\n" if md.endswith("\n") else "")
