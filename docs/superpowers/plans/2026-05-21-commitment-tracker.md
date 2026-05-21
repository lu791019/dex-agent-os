# 承諾追蹤器（Commitment Tracker）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一個不依賴維護紀律的承諾追蹤機制——Stop hook 自動從 session 抽取明確交付物承諾，經 `/承諾` 確認後分流寫入 situation-board.md（CXO）或 200_Work/commitments.md（dev）。

**Architecture:** Stop hook 在 session 結束時跑便宜預篩，有承諾語感才背景啟動 LLM 抽取，結果寫入 `data/commitment_queue.json`。下次 SessionStart hook 偵測 queue 非空就提示使用者跑 `/承諾`，由 LLM workflow 逐筆確認後分流寫入兩個 board。純邏輯集中在 `commitment_lib.py` 方便測試。

**Tech Stack:** Python 3（標準庫 only：json / difflib / subprocess / pathlib）、`scripts/lib/llm.py` 的 `ask_claude`（claude --print，走 Pro 額度）、Claude Code hooks（Stop + SessionStart）、canonical → bin/sync 的 slash command 機制。

---

## File Structure

| 檔案 | 動作 | 職責 |
|------|------|------|
| `scripts/lib/commitment_lib.py` | Create | 純邏輯：queue I/O、預篩 heuristic、讀現有承諾、去重、分流寫入 |
| `scripts/hooks/commitment_extract.py` | Create | Stop hook 入口：解析 payload、預篩、背景啟動 LLM 抽取 |
| `scripts/hooks/commitment_sessionstart.py` | Create | SessionStart hook：queue 非空則印提示 |
| `canonical/workflows/承諾.md` | Create | `/承諾` slash command（LLM workflow，bin/sync 同步到 .claude/commands/） |
| `200_Work/commitments.md` | Create | dev 承諾追蹤檔（種子空檔） |
| `data/commitment_queue.json` | Create | pending queue（種子 `[]`） |
| `~/.claude/settings.json` | Modify | 註冊 Stop + SessionStart hook |
| `scripts/tools/test_commitment_lib.py` | Create | commitment_lib 單元測試（runnable script，沿用 test_sync_v2.py 風格） |
| `scripts/tools/test_commitment_extract.py` | Create | 抽取端對端整合測試（餵 fixture transcript） |

**測試慣例**：本專案無 pytest，既有測試（`test_sync_v2.py`）是 `def main()` + `sys.exit(main())` 的可執行腳本，逐項 assert 並印結果。新測試沿用此模式。

---

## Task 1: commitment_lib 基礎 — 路徑常數與 queue I/O

**Files:**
- Create: `scripts/lib/commitment_lib.py`
- Test: `scripts/tools/test_commitment_lib.py`

- [ ] **Step 1: 寫失敗測試**

Create `scripts/tools/test_commitment_lib.py`:

```python
"""commitment_lib 單元測試（可執行腳本，非 pytest）。"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib import commitment_lib as cl


def test_queue_roundtrip() -> bool:
    """save_queue 寫入後 load_queue 讀回相同內容。"""
    with tempfile.TemporaryDirectory() as tmp:
        qf = Path(tmp) / "q.json"
        cl.save_queue([{"id": "c-1", "text": "x"}], path=qf)
        loaded = cl.load_queue(path=qf)
        assert loaded == [{"id": "c-1", "text": "x"}], loaded
        return True


def test_load_queue_missing_returns_empty() -> bool:
    """檔案不存在時 load_queue 回空 list，不丟例外。"""
    with tempfile.TemporaryDirectory() as tmp:
        assert cl.load_queue(path=Path(tmp) / "nope.json") == []
        return True


def test_load_queue_corrupt_returns_empty() -> bool:
    """JSON 損壞時 load_queue 回空 list，不丟例外。"""
    with tempfile.TemporaryDirectory() as tmp:
        qf = Path(tmp) / "bad.json"
        qf.write_text("{ not json", encoding="utf-8")
        assert cl.load_queue(path=qf) == []
        return True


TESTS = [
    test_queue_roundtrip,
    test_load_queue_missing_returns_empty,
    test_load_queue_corrupt_returns_empty,
]


def main() -> int:
    passed, failed = 0, 0
    for t in TESTS:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed += 1
    print(f"\n📊 {passed} passed / {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.commitment_lib'`

- [ ] **Step 3: 寫最小實作**

Create `scripts/lib/commitment_lib.py`:

```python
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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: PASS — 3 passed / 0 failed

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/commitment_lib.py scripts/tools/test_commitment_lib.py
git commit -m "feat: commitment_lib 基礎 — queue I/O"
```

---

## Task 2: commitment_lib — 預篩 heuristic

判斷一段 transcript 文字是否有「承諾語感」，避免每個 session 結束都燒 LLM。

**Files:**
- Modify: `scripts/lib/commitment_lib.py`
- Modify: `scripts/tools/test_commitment_lib.py`

- [ ] **Step 1: 寫失敗測試**

在 `test_commitment_lib.py` 的 `test_load_queue_corrupt_returns_empty` 之後加入：

```python
def test_prefilter_detects_signal() -> bool:
    """含承諾語感的文字回 True。"""
    assert cl.has_commitment_signal("好，我會去審閱那份長文") is True
    assert cl.has_commitment_signal("這個我記到 Phase 7") is True
    return True


def test_prefilter_no_signal() -> bool:
    """純討論無承諾語感回 False。"""
    assert cl.has_commitment_signal("這個架構看起來不錯，你覺得呢") is False
    return True
```

並把 `TESTS` list 改為：

```python
TESTS = [
    test_queue_roundtrip,
    test_load_queue_missing_returns_empty,
    test_load_queue_corrupt_returns_empty,
    test_prefilter_detects_signal,
    test_prefilter_no_signal,
]
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: FAIL — `AttributeError: module 'lib.commitment_lib' has no attribute 'has_commitment_signal'`

- [ ] **Step 3: 寫最小實作**

在 `commitment_lib.py` 末端加入：

```python
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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: PASS — 5 passed / 0 failed

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/commitment_lib.py scripts/tools/test_commitment_lib.py
git commit -m "feat: commitment_lib 預篩 heuristic"
```

---

## Task 3: commitment_lib — 讀現有承諾

抽取時要比對既有承諾才能偵測完成。讀 situation-board.md 與 commitments.md 的未結案承諾。

**Files:**
- Modify: `scripts/lib/commitment_lib.py`
- Modify: `scripts/tools/test_commitment_lib.py`

- [ ] **Step 1: 寫失敗測試**

在 `test_commitment_lib.py` 加入：

```python
def test_parse_board_commitments() -> bool:
    """從 markdown 表格抽出承諾文字。"""
    md = (
        "## 承諾（Dex 確認要做的）\n"
        "| 事項 | 誰提的 | 期限 | 狀態 |\n"
        "|------|--------|------|------|\n"
        "| 審閱 AI-First DE 長文版 | CMO | — | 待處理 |\n"
        "| 收集學員回饋 | EDU | — | 待排程 |\n"
        "\n## 現況\n- 別的東西\n"
    )
    rows = cl.parse_commitment_table(md, heading="承諾")
    texts = [r["text"] for r in rows]
    assert "審閱 AI-First DE 長文版" in texts, texts
    assert "收集學員回饋" in texts, texts
    assert len(rows) == 2, rows
    return True


def test_parse_board_no_heading() -> bool:
    """找不到指定標題時回空 list。"""
    assert cl.parse_commitment_table("# 隨便\n內文", heading="承諾") == []
    return True
```

加進 `TESTS` list。

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: FAIL — `AttributeError: ... has no attribute 'parse_commitment_table'`

- [ ] **Step 3: 寫最小實作**

在 `commitment_lib.py` 末端加入：

```python
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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: PASS — 7 passed / 0 failed

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/commitment_lib.py scripts/tools/test_commitment_lib.py
git commit -m "feat: commitment_lib 讀現有承諾"
```

---

## Task 4: commitment_lib — 去重

跨 session 可能抽到同一承諾。用 difflib 文字相似度去重。

**Files:**
- Modify: `scripts/lib/commitment_lib.py`
- Modify: `scripts/tools/test_commitment_lib.py`

- [ ] **Step 1: 寫失敗測試**

在 `test_commitment_lib.py` 加入：

```python
def test_dedup_exact_match() -> bool:
    """文字完全相同視為重複。"""
    assert cl.is_duplicate("審閱長文版", ["審閱長文版"]) is True
    return True


def test_dedup_near_match() -> bool:
    """高度相似（>0.8）視為重複。"""
    assert cl.is_duplicate(
        "審閱 AI-First DE 長文版並決定發布管道",
        ["審閱 AI-First DE 長文版，決定發布管道"],
    ) is True
    return True


def test_dedup_distinct() -> bool:
    """不相似則非重複。"""
    assert cl.is_duplicate("審閱長文版", ["收集學員回饋"]) is False
    return True
```

加進 `TESTS` list。

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: FAIL — `AttributeError: ... has no attribute 'is_duplicate'`

- [ ] **Step 3: 寫最小實作**

在 `commitment_lib.py` 頂端 import 區加 `from difflib import SequenceMatcher`，並在末端加入：

```python
def is_duplicate(text: str, existing: list[str], threshold: float = 0.8) -> bool:
    """text 是否與 existing 任一項高度相似（相似度 >= threshold）。"""
    for other in existing:
        if SequenceMatcher(None, text, other).ratio() >= threshold:
            return True
    return False
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: PASS — 10 passed / 0 failed

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/commitment_lib.py scripts/tools/test_commitment_lib.py
git commit -m "feat: commitment_lib 文字相似度去重"
```

---

## Task 5: commitment_lib — 寫入 situation-board.md

確認後的 CXO 承諾 append 到 situation-board.md 既有「承諾」表格；結案則移除。

**Files:**
- Modify: `scripts/lib/commitment_lib.py`
- Modify: `scripts/tools/test_commitment_lib.py`

- [ ] **Step 1: 寫失敗測試**

在 `test_commitment_lib.py` 加入：

```python
def test_append_situation_board_row() -> bool:
    """append_situation_board_row 在承諾表格尾端插入新列。"""
    md = (
        "# Board\n> 最近更新：2026-04-15\n\n"
        "## 承諾（Dex 確認要做的）\n"
        "| 事項 | 誰提的 | 期限 | 狀態 |\n"
        "|------|--------|------|------|\n"
        "| 舊承諾 | CMO | — | 待處理 |\n\n"
        "## 現況\n- x\n"
    )
    item = {"text": "新承諾", "cxo_role": "CTO", "deadline": "2026-06-01"}
    out = cl.append_situation_board_row(md, item)
    assert "| 新承諾 | CTO | 2026-06-01 | 待處理 |" in out, out
    assert "| 舊承諾 | CMO | — | 待處理 |" in out, out
    assert out.index("舊承諾") < out.index("新承諾"), "新列應在舊列之後"
    return True


def test_mark_done_situation_board() -> bool:
    """remove_situation_board_row 移除指定承諾列。"""
    md = (
        "## 承諾（Dex 確認要做的）\n"
        "| 事項 | 誰提的 | 期限 | 狀態 |\n"
        "|------|--------|------|------|\n"
        "| 完成的承諾 | CMO | — | 待處理 |\n"
        "| 保留的承諾 | EDU | — | 待處理 |\n"
    )
    out = cl.remove_situation_board_row(md, "完成的承諾")
    assert "完成的承諾" not in out, out
    assert "保留的承諾" in out, out
    return True
```

加進 `TESTS` list。

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: FAIL — `AttributeError: ... has no attribute 'append_situation_board_row'`

- [ ] **Step 3: 寫最小實作**

在 `commitment_lib.py` 末端加入：

```python
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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: PASS — 12 passed / 0 failed

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/commitment_lib.py scripts/tools/test_commitment_lib.py
git commit -m "feat: commitment_lib 寫入/移除 situation-board 承諾列"
```

---

## Task 6: commitment_lib — 寫入 dev commitments.md

dev 承諾寫入 `200_Work/commitments.md` 的「未結案」表格。先種子化該檔。

**Files:**
- Create: `200_Work/commitments.md`
- Modify: `scripts/lib/commitment_lib.py`
- Modify: `scripts/tools/test_commitment_lib.py`

- [ ] **Step 1: 建種子檔**

Create `200_Work/commitments.md`:

```markdown
# Dev Commitments

> dex-agent-os 開發承諾追蹤。由承諾追蹤器自動維護，經 /承諾 確認後寫入。
> 最近更新：2026-05-21

## 未結案

| 事項 | 負責人 | 期限 | 狀態 | 來源 |
|------|--------|------|------|------|

## 近期結案（保留 30 天）
```

- [ ] **Step 2: 寫失敗測試**

在 `test_commitment_lib.py` 加入：

```python
def test_append_dev_row() -> bool:
    """append_dev_commitment_row 在未結案表格尾端插入新列。"""
    md = (
        "# Dev Commitments\n> 最近更新：2026-05-21\n\n"
        "## 未結案\n\n"
        "| 事項 | 負責人 | 期限 | 狀態 | 來源 |\n"
        "|------|--------|------|------|------|\n\n"
        "## 近期結案（保留 30 天）\n"
    )
    item = {"text": "改 generator", "owner": "AI", "deadline": "",
            "source_session": "abc12345"}
    out = cl.append_dev_commitment_row(md, item)
    assert "| 改 generator | AI | — | 待處理 | abc12345 |" in out, out
    return True


def test_remove_dev_row() -> bool:
    """remove_dev_commitment_row 移除指定承諾列。"""
    md = (
        "## 未結案\n\n"
        "| 事項 | 負責人 | 期限 | 狀態 | 來源 |\n"
        "|------|--------|------|------|------|\n"
        "| 完成項 | AI | — | 待處理 | s1 |\n"
        "| 保留項 | Dex | — | 待處理 | s2 |\n"
    )
    out = cl.remove_dev_commitment_row(md, "完成項")
    assert "完成項" not in out and "保留項" in out, out
    return True
```

加進 `TESTS` list。

- [ ] **Step 3: 跑測試確認失敗**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: FAIL — `AttributeError: ... has no attribute 'append_dev_commitment_row'`

- [ ] **Step 4: 寫最小實作**

在 `commitment_lib.py` 末端加入：

```python
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
```

- [ ] **Step 5: 跑測試確認通過**

Run: `python3 scripts/tools/test_commitment_lib.py`
Expected: PASS — 14 passed / 0 failed

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/commitment_lib.py scripts/tools/test_commitment_lib.py 200_Work/commitments.md
git commit -m "feat: commitment_lib 寫入 dev commitments + 種子檔"
```

---

## Task 7: 抽取邏輯 — LLM prompt + JSON 解析

`commitment_extract.py` 的 `--extract` 模式：讀 transcript、組 prompt、呼叫 ask_claude、解析 JSON、去重、寫 queue。

**Files:**
- Create: `scripts/hooks/commitment_extract.py`
- Test: `scripts/tools/test_commitment_extract.py`

- [ ] **Step 1: 寫失敗測試**

Create `scripts/tools/test_commitment_extract.py`:

```python
"""commitment_extract 解析邏輯測試（可執行腳本）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from hooks import commitment_extract as ce


def test_parse_llm_json_block() -> bool:
    """從 LLM 回應的 ```json fenced block 抽出承諾 list。"""
    response = (
        "這是我抽到的承諾：\n\n"
        "```json\n"
        '[{"type": "new", "text": "審閱長文", "owner": "Dex", '
        '"category": "cxo", "cxo_role": "CMO", "deadline": ""}]\n'
        "```\n"
        "以上。"
    )
    items = ce.parse_llm_response(response)
    assert len(items) == 1, items
    assert items[0]["text"] == "審閱長文", items
    return True


def test_parse_llm_empty() -> bool:
    """LLM 回空陣列時回空 list。"""
    assert ce.parse_llm_response("```json\n[]\n```") == []
    return True


def test_parse_llm_malformed() -> bool:
    """無 json block 或損壞時回空 list，不丟例外。"""
    assert ce.parse_llm_response("沒有 json") == []
    assert ce.parse_llm_response("```json\n{壞掉\n```") == []
    return True


def test_extract_transcript_text() -> bool:
    """從 JSONL transcript 抽出純文字內容。"""
    import json as _json
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tf = Path(tmp) / "t.jsonl"
        lines = [
            _json.dumps({"type": "user", "message": {"role": "user",
                         "content": "我會去審閱"}}),
            _json.dumps({"type": "assistant", "message": {"role": "assistant",
                         "content": [{"type": "text", "text": "好的"}]}}),
        ]
        tf.write_text("\n".join(lines), encoding="utf-8")
        text = ce.extract_transcript_text(tf)
        assert "我會去審閱" in text, text
        assert "好的" in text, text
        return True


TESTS = [
    test_parse_llm_json_block,
    test_parse_llm_empty,
    test_parse_llm_malformed,
    test_extract_transcript_text,
]


def main() -> int:
    passed, failed = 0, 0
    for t in TESTS:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed += 1
    print(f"\n📊 {passed} passed / {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 scripts/tools/test_commitment_extract.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'hooks'`

- [ ] **Step 3: 寫最小實作**

> `hooks` 沿用專案既有的 namespace package 機制（`from lib.config import ...` 即無 `__init__.py`），不需建 `__init__.py`。

Create `scripts/hooks/commitment_extract.py`:

```python
"""承諾抽取 — Stop hook 入口 + --extract 背景模式。

兩種執行模式：
  1. 無參數（Stop hook 呼叫）：讀 stdin payload → 預篩 → 背景啟動 --extract
  2. --extract <transcript_path>：跑 LLM 抽取 → 去重 → 寫 queue

LLM 走 claude --print（Pro 額度）。抽取失敗一律靜默退出，絕不卡 session 結束。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib import commitment_lib as cl
from lib.llm import ask_claude

_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.+?)\n```", re.DOTALL)

EXTRACT_SYSTEM_PROMPT = """\
你是承諾抽取器。從對話 transcript 中抽出「明確交付物承諾」。

嚴格標準 — 只抽符合以下全部條件的承諾：
- 有明確動作（審閱 X / 寫 Y / 決定 Z），不是模糊的「我來看看」
- 可驗證完成（做完了能明確判斷）
- 是 Dex 或 AI 對未來的承諾，不是已完成的事

同時偵測「完成」：若 transcript 顯示某個「現有承諾」已被完成，標為 completion。

分類每筆承諾：
- category=cxo：與 DayDreamDex CXO（內容/品牌/產品/諮詢/課程/技術顧問/營運/財務）相關
- category=dev：與 dex-agent-os 系統開發相關

只輸出一個 ```json fenced block，格式為陣列，每筆物件欄位：
  type: "new" | "completion"
  text: 承諾文字（一句話，繁體中文）
  owner: "Dex" | "AI"
  category: "cxo" | "dev"
  cxo_role: CXO 角色英文縮寫（category=cxo 時）或 null
  deadline: "YYYY-MM-DD" 或 ""
  matched_board_item: completion 型才有，指回現有承諾文字
  evidence: completion 型才有，這次做了什麼

沒有任何承諾就輸出 ```json\\n[]\\n```。
"""


def extract_transcript_text(transcript_path: Path) -> str:
    """從 Claude Code JSONL transcript 抽出 user/assistant 純文字。"""
    if not transcript_path.exists():
        return ""
    parts: list[str] = []
    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = obj.get("message", {})
        content = msg.get("content", "")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
    return "\n".join(parts)


def parse_llm_response(response: str) -> list[dict]:
    """從 LLM 回應抽出 ```json block 並解析。損壞回空 list。"""
    m = _JSON_BLOCK_RE.search(response)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def run_extraction(transcript_path: Path, session_id: str = "") -> None:
    """跑 LLM 抽取，去重後 append 到 queue。失敗靜默退出。"""
    try:
        text = extract_transcript_text(transcript_path)
        if not text or not cl.has_commitment_signal(text):
            return

        open_commitments = cl.read_open_commitments()
        user_prompt = (
            f"## 現有承諾（用於偵測完成）\n"
            + "\n".join(f"- {c['text']}" for c in open_commitments)
            + f"\n\n## 對話 transcript\n{text[:40000]}"
        )
        response = ask_claude(
            user_prompt=user_prompt,
            system_prompt=EXTRACT_SYSTEM_PROMPT,
        )
        items = parse_llm_response(response)
        if not items:
            return

        queue = cl.load_queue()
        existing_texts = [q["text"] for q in queue] + [
            c["text"] for c in open_commitments
        ]
        added = 0
        for item in items:
            txt = item.get("text", "").strip()
            if not txt:
                continue
            if item.get("type") != "completion" and cl.is_duplicate(
                txt, existing_texts
            ):
                continue
            item["id"] = f"c-{date.today():%Y%m%d}-{uuid.uuid4().hex[:6]}"
            item["source_session"] = session_id
            item["extracted_at"] = date.today().isoformat()
            queue.append(item)
            existing_texts.append(txt)
            added += 1
        if added:
            cl.save_queue(queue)
    except Exception:
        # 抽取失敗絕不影響 session — 靜默退出
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", metavar="TRANSCRIPT_PATH")
    parser.add_argument("--session-id", default="")
    args = parser.parse_args()

    # 模式 2：背景抽取
    if args.extract:
        run_extraction(Path(args.extract), session_id=args.session_id)
        return 0

    # 模式 1：Stop hook — 讀 payload、預篩、背景啟動
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    transcript_path = payload.get("transcript_path", "")
    session_id = payload.get("session_id", "")
    if not transcript_path or not Path(transcript_path).exists():
        return 0

    text = extract_transcript_text(Path(transcript_path))
    if not cl.has_commitment_signal(text):
        return 0  # 無承諾語感，省下 LLM 呼叫

    # 背景啟動抽取，hook 立即返回
    subprocess.Popen(
        [
            sys.executable, str(Path(__file__).resolve()),
            "--extract", transcript_path,
            "--session-id", session_id,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 scripts/tools/test_commitment_extract.py`
Expected: PASS — 4 passed / 0 failed

- [ ] **Step 5: Commit**

```bash
git add scripts/hooks/commitment_extract.py scripts/tools/test_commitment_extract.py
git commit -m "feat: 承諾抽取 — LLM prompt + JSON 解析 + Stop hook 入口"
```

---

## Task 8: SessionStart hook — queue 提示

session 開始時若 queue 非空，印提示給使用者。

**Files:**
- Create: `scripts/hooks/commitment_sessionstart.py`

- [ ] **Step 1: 寫實作**

Create `scripts/hooks/commitment_sessionstart.py`:

```python
"""SessionStart hook — queue 非空時提示使用者跑 /承諾。

輸出 hookSpecificOutput.additionalContext（model 看得到）。
queue 空則無輸出。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib import commitment_lib as cl


def main() -> int:
    queue = cl.load_queue()
    if not queue:
        return 0

    new_count = sum(1 for q in queue if q.get("type") != "completion")
    done_count = len(queue) - new_count
    summary = f"📌 {len(queue)} 筆待確認承諾"
    if done_count:
        summary += f"（{new_count} 新承諾 / {done_count} 偵測完成）"
    msg = f"{summary} — 跑 /承諾 review"

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 手動驗證 — queue 空時無輸出**

Run: `echo '[]' > /tmp/empty_q.json && python3 -c "
import sys; sys.path.insert(0, 'scripts')
from lib import commitment_lib as cl
print('queue 空 → 應無輸出')
print(repr(cl.load_queue(path=__import__('pathlib').Path('/tmp/empty_q.json'))))
"`
Expected: 印出 `[]`

- [ ] **Step 3: 手動驗證 — queue 非空時有輸出**

Run:
```bash
python3 -c "
import sys, json; sys.path.insert(0, 'scripts')
from lib import commitment_lib as cl
cl.save_queue([{'id':'c-1','type':'new','text':'測試承諾'}])
" && python3 scripts/hooks/commitment_sessionstart.py && python3 -c "
import sys; sys.path.insert(0, 'scripts')
from lib import commitment_lib as cl
cl.clear_queue()
"
```
Expected: 印出含 `📌 1 筆待確認承諾` 的 JSON，最後 queue 被清空

- [ ] **Step 4: Commit**

```bash
git add scripts/hooks/commitment_sessionstart.py
git commit -m "feat: SessionStart hook — queue 提示"
```

---

## Task 9: `/承諾` slash command workflow

LLM-driven workflow，逐筆 review queue 並分流寫入。

**Files:**
- Create: `canonical/workflows/承諾.md`

- [ ] **Step 1: 寫 workflow**

Create `canonical/workflows/承諾.md`:

````markdown
# 承諾 — 確認待處理承諾並寫入 board

逐筆 review `data/commitment_queue.json` 的待確認承諾，經 Dex 確認後分流寫入 situation-board.md（CXO）或 200_Work/commitments.md（dev）。

## 觸發方式

- IDE 內：`/承諾`
- SessionStart 提示「📌 N 筆待確認承諾」後執行

## Step 1：讀 queue

讀 `data/commitment_queue.json`。空陣列就回報「無待確認承諾」並結束。

## Step 2：逐筆呈現

對每一筆 queue item：

**type=new（新承諾）** — 呈現：
- 承諾文字 `text`
- 負責人 `owner`、分類 `category`（cxo 顯示 `cxo_role`）、期限 `deadline`

問 Dex：**確認 / 編輯文字 / 刪除（誤報）**

**type=completion（偵測完成）** — 呈現：
- `matched_board_item`（對應的現有承諾）
- `evidence`（這次 session 做了什麼）

問 Dex：**確認結案 / 否決**

一次問一筆，不要批次。

## Step 3：分流寫入

review 完所有筆數後，用 `scripts/lib/commitment_lib.py` 的函式一次寫入：

- **確認的 new + category=cxo**：
  讀 `~/daydreamdex/state/situation-board.md` → `append_situation_board_row(md, item)` → 寫回
- **確認的 new + category=dev**：
  讀 `200_Work/commitments.md` → `append_dev_commitment_row(md, item)` → 寫回
- **確認結案 + 來源 cxo**：
  `remove_situation_board_row(md, matched_board_item)` → 寫回 situation-board.md
- **確認結案 + 來源 dev**：
  `remove_dev_commitment_row(md, matched_board_item)` → 寫回 commitments.md
- 被刪除/否決的：不寫入

寫入後更新兩個檔的「最近更新：YYYY-MM-DD」為今天。

## Step 4：清空 queue

全部處理完，呼叫 `commitment_lib.clear_queue()`。

回報摘要：寫入 N 筆 CXO 承諾、M 筆 dev 承諾、結案 K 筆。

## 注意

- 一次一筆問，讓 Dex 能逐筆判斷
- 編輯文字時，改 item['text'] 再寫入
- situation-board.md 在 ~/daydreamdex/（repo 外），commitments.md 在 dex-agent-os repo 內
````

- [ ] **Step 2: 跑 sync 產生 .claude/commands/**

Run: `bin/sync`
Expected: 輸出含 `[1/2] 同步 Workflows → .claude/commands/`，無錯誤

- [ ] **Step 3: 驗證 command 已產生**

Run: `test -f .claude/commands/承諾.md && echo "✅ 已同步" || echo "❌ 缺檔"`
Expected: `✅ 已同步`

- [ ] **Step 4: Commit**

```bash
git add canonical/workflows/承諾.md .claude/commands/承諾.md
git commit -m "feat: /承諾 slash command workflow"
```

---

## Task 10: 註冊 Stop + SessionStart hooks

在 `~/.claude/settings.json` 加兩個 hook entry。

**Files:**
- Modify: `~/.claude/settings.json`

- [ ] **Step 1: 備份現有 settings**

Run: `cp ~/.claude/settings.json ~/.claude/settings.json.bak`
Expected: 無輸出（成功）

- [ ] **Step 2: 加入 Stop hook**

`~/.claude/settings.json` 現有 `hooks` 物件已含 `SessionStart` / `UserPromptSubmit` / `PostToolUse`。新增 `Stop` key（與其他 hook 同層）：

```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 /Users/dex/dex-agent-os/scripts/hooks/commitment_extract.py",
        "timeout": 10
      }
    ]
  }
]
```

- [ ] **Step 3: 把 SessionStart hook 加進現有 SessionStart 陣列**

現有 `SessionStart` 陣列已有一個 `gsd-check-update.js` entry。**追加**第二個 entry（不要覆蓋）：

```json
"SessionStart": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "node .claude/hooks/gsd-check-update.js"
      }
    ]
  },
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 /Users/dex/dex-agent-os/scripts/hooks/commitment_sessionstart.py"
      }
    ]
  }
]
```

- [ ] **Step 4: 驗證 JSON 合法**

Run: `python3 -c "import json; json.load(open('/Users/dex/.claude/settings.json')); print('✅ JSON 合法')"`
Expected: `✅ JSON 合法`

- [ ] **Step 5: 驗證 Stop hook 可被觸發（模擬 payload）**

Run:
```bash
echo '{"transcript_path":"/nonexistent","session_id":"test"}' | python3 /Users/dex/dex-agent-os/scripts/hooks/commitment_extract.py; echo "exit=$?"
```
Expected: `exit=0`（transcript 不存在 → 靜默退出）

- [ ] **Step 6: 確認兩個 hook 都已註冊**

`~/.claude/settings.json` 在 repo 外、不進 git，所以本 task 無 git commit。新環境需手動補設定——這一點會在「收尾」步驟記入 MEMORY.md。本步驟僅確認註冊成功：

Run: `grep -c "commitment_extract\|commitment_sessionstart" ~/.claude/settings.json`
Expected: `2`

確認後可刪除備份：`rm ~/.claude/settings.json.bak`

---

## Task 11: 端對端整合測試

用 fixture transcript 跑完整 loop，驗證抽取 → queue → 寫入。

**Files:**
- Create: `tests/fixtures/commitment-transcript.jsonl`
- Create: `scripts/tools/test_commitment_e2e.py`

- [ ] **Step 1: 建 fixture transcript**

Create `tests/fixtures/commitment-transcript.jsonl`:

```
{"type":"user","message":{"role":"user","content":"我們來討論 v3 generator 遷移"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"好，我會把 topic_to_short_video.py 也接上 sync_draft_v2，這個我負責，下週前完成。"}]}}
{"type":"user","message":{"role":"user","content":"好，另外我會去審閱 AI-First DE 長文版並決定發布管道"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"了解，這兩筆都記下來。"}]}}
```

- [ ] **Step 2: 寫端對端測試**

Create `scripts/tools/test_commitment_e2e.py`:

```python
"""承諾追蹤器端對端測試 — 餵 fixture transcript 跑完整抽取。

需要 claude --print 可用（Pro 額度）。會實際呼叫 LLM。
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from hooks import commitment_extract as ce
from lib import commitment_lib as cl

FIXTURE = ROOT / "tests" / "fixtures" / "commitment-transcript.jsonl"


def test_e2e_extraction() -> bool:
    """fixture transcript 跑抽取，queue 應有 ≥1 筆 new 承諾。"""
    with tempfile.TemporaryDirectory() as tmp:
        qf = Path(tmp) / "queue.json"
        # 暫時改寫 QUEUE_FILE
        original = cl.QUEUE_FILE
        cl.QUEUE_FILE = qf
        try:
            ce.run_extraction(FIXTURE, session_id="e2e-test")
            queue = cl.load_queue(path=qf)
        finally:
            cl.QUEUE_FILE = original

        assert len(queue) >= 1, f"預期 ≥1 筆，實際 {len(queue)}：{queue}"
        texts = " ".join(q.get("text", "") for q in queue)
        # fixture 有兩個明確承諾，至少抓到其一
        assert ("審閱" in texts or "short_video" in texts
                or "short-video" in texts or "shortvideo" in texts), texts
        for q in queue:
            assert q.get("id"), f"缺 id：{q}"
            assert q.get("category") in ("cxo", "dev"), f"category 異常：{q}"
        print(f"     抽到 {len(queue)} 筆：{[q['text'] for q in queue]}")
        return True


TESTS = [test_e2e_extraction]


def main() -> int:
    passed, failed = 0, 0
    for t in TESTS:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed += 1
    print(f"\n📊 {passed} passed / {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: 跑端對端測試**

Run: `python3 scripts/tools/test_commitment_e2e.py`
Expected: PASS — 1 passed / 0 failed，並印出抽到的承諾文字

- [ ] **Step 4: 跑全部單元測試確認無回歸**

Run: `python3 scripts/tools/test_commitment_lib.py && python3 scripts/tools/test_commitment_extract.py`
Expected: 兩支都 PASS（14 passed、4 passed）

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/commitment-transcript.jsonl scripts/tools/test_commitment_e2e.py
git commit -m "test: 承諾追蹤器端對端整合測試"
```

---

## 收尾

- [ ] 更新 `MEMORY.md`：Phase 6 P3 完成；記錄 `~/.claude/settings.json` 新增了 Stop + SessionStart hook（repo 外設定，需在新環境手動補）
- [ ] 更新 `docs/superpowers/specs/2026-05-21-commitment-tracker-design.md` 狀態為「已實作」

## Self-Review 對照 spec

| spec 要求 | 對應 task |
|-----------|-----------|
| Stop hook 抽取 | Task 7、Task 10 |
| 便宜預篩 | Task 2、Task 7（main 模式 1） |
| 背景執行不卡 session | Task 7（subprocess.Popen start_new_session） |
| LLM 嚴格抽取明確交付物 | Task 7（EXTRACT_SYSTEM_PROMPT） |
| 偵測完成 | Task 3（read_open_commitments）、Task 7（prompt） |
| 分類 cxo/dev | Task 7（prompt） |
| queue 格式 | Task 1、Task 7（id/source_session/extracted_at 補齊） |
| SessionStart 提示 | Task 8、Task 10 |
| `/承諾` review + 分流 | Task 9 |
| 寫 situation-board / commitments.md | Task 5、Task 6、Task 9 |
| 去重 | Task 4、Task 7 |
| 邊界：queue 空/損壞 | Task 1（load_queue） |
| 邊界：抽取失敗靜默 | Task 7（run_extraction try/except） |
| 邊界：transcript 不存在 | Task 7（main 模式 1 檢查） |
| 測試 單元/整合/E2E | Task 1-6、Task 7、Task 11 |
