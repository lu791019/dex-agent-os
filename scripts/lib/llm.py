"""Dex Agent OS — claude --print 封裝

透過 Claude Code CLI 呼叫 LLM，走 Pro 訂閱額度（不花 API 費用）。
"""

import subprocess
import sys


def ask_claude(
    user_prompt: str,
    system_prompt: str = "",
    model: str = "",
    max_turns: int = 0,
) -> str:
    """呼叫 claude --print，回傳 LLM 回應文字。

    Args:
        user_prompt: 使用者提示（必填）
        system_prompt: 系統提示（選填）
        model: 指定模型（選填，預設由 CLI 決定）
        max_turns: 最大回合數（選填，0 = 不限制）

    Returns:
        LLM 回應文字

    Raises:
        RuntimeError: claude --print 執行失敗
    """
    cmd = ["claude", "--print"]

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    if model:
        cmd.extend(["--model", model])
    if max_turns > 0:
        cmd.extend(["--max-turns", str(max_turns)])

    result = subprocess.run(
        cmd,
        input=user_prompt,
        capture_output=True,
        text=True,
        timeout=300,  # 5 分鐘超時
    )

    if result.returncode != 0:
        print(f"[llm] stderr: {result.stderr}", file=sys.stderr)
        raise RuntimeError(f"claude --print failed (exit {result.returncode})")

    return result.stdout.strip()
