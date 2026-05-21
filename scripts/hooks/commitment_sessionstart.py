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
