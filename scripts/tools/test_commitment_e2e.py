"""承諾追蹤器端對端測試 — 餵 fixture transcript 跑完整抽取。

需要 claude --print 可用（Pro 額度）。會實際呼叫 LLM。
測試把 QUEUE_FILE / SITUATION_BOARD / DEV_COMMITMENTS_FILE 全導向 temp，
與真實 board 隔離，確保去重不受真實資料影響。
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
        # 三個路徑全導向 temp（board 檔不存在 → read_open_commitments 回空 → 不受真實資料干擾）
        orig_q = cl.QUEUE_FILE
        orig_sb = cl.SITUATION_BOARD
        orig_dev = cl.DEV_COMMITMENTS_FILE
        cl.QUEUE_FILE = Path(tmp) / "queue.json"
        cl.SITUATION_BOARD = Path(tmp) / "situation-board.md"
        cl.DEV_COMMITMENTS_FILE = Path(tmp) / "commitments.md"
        try:
            ce.run_extraction(FIXTURE, session_id="e2e-test")
            queue = cl.load_queue()
        finally:
            cl.QUEUE_FILE = orig_q
            cl.SITUATION_BOARD = orig_sb
            cl.DEV_COMMITMENTS_FILE = orig_dev

        assert len(queue) >= 1, f"預期 ≥1 筆，實際 {len(queue)}：{queue}"
        for q in queue:
            assert q.get("id"), f"缺 id：{q}"
            assert q.get("category") in ("cxo", "dev"), f"category 異常：{q}"
            assert q.get("text"), f"缺 text：{q}"
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
