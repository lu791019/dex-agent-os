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
