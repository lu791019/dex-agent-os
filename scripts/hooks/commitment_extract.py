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
