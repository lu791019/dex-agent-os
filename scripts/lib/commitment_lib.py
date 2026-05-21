"""承諾追蹤器核心邏輯 — queue I/O、預篩、去重、分流寫入。

純邏輯集中此檔，方便單元測試。Hook 腳本與 /承諾 workflow 呼叫這裡的函式。
"""

from __future__ import annotations

import json
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
