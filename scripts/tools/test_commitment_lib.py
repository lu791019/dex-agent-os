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


def test_prefilter_detects_signal() -> bool:
    """含承諾語感的文字回 True。"""
    assert cl.has_commitment_signal("好，我會去審閱那份長文") is True
    assert cl.has_commitment_signal("這個我記到 Phase 7") is True
    return True


def test_prefilter_no_signal() -> bool:
    """純討論無承諾語感回 False。"""
    assert cl.has_commitment_signal("這個架構看起來不錯，你覺得呢") is False
    return True


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


TESTS = [
    test_queue_roundtrip,
    test_load_queue_missing_returns_empty,
    test_load_queue_corrupt_returns_empty,
    test_prefilter_detects_signal,
    test_prefilter_no_signal,
    test_parse_board_commitments,
    test_parse_board_no_heading,
    test_dedup_exact_match,
    test_dedup_near_match,
    test_dedup_distinct,
    test_append_situation_board_row,
    test_mark_done_situation_board,
    test_append_dev_row,
    test_remove_dev_row,
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
