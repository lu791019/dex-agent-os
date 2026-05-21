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
