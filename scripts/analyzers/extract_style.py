#!/usr/bin/env python3
"""Extract Style — 從範例文章提取風格 DNA"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import EXAMPLES_DIR, STYLE_DNA_DIR
from lib.file_utils import ensure_dir, read_text
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是一位寫作風格分析專家。你的任務是從一組真實文章範例中，提取出作者的抽象寫作模式（Style DNA）。

分析維度（每個維度都必須涵蓋）：
1. **結構模式** — 常見的段落結構（例如 Hook → 條列 → 金句）
2. **開場 Hook 模式** — 反差型、提問型、宣告型等，舉出具體範例
3. **語氣特徵** — 精準度、口語比例、用字習慣、人稱用法
4. **CTA / 收尾模式** — 金句收尾、開放提問、行動呼籲等
5. **長度 / 格式** — 典型字數、段落數、標點習慣、emoji 使用
6. **高互動特徵** — 從互動數據回推哪些模式帶來高互動（如有互動數據）
7. **禁忌** — 作者明顯避免的模式或風格

輸出規則：
- 使用繁體中文
- 每個維度用 ## 標題
- 每個維度下列出 3-5 個具體觀察，附上從範例中引用的證據
- 最後加一個「## 一句話風格概括」總結作者的獨特風格
- 只輸出分析結果，不要加任何額外說明或前言
"""

MIN_EXAMPLES = 3


# ── 主要邏輯 ──────────────────────────────────────────

def _collect_examples(channel: str) -> list[tuple[str, str]]:
    """收集指定頻道的所有範例。回傳 [(filename, content), ...]。"""
    examples_dir = EXAMPLES_DIR / channel
    if not examples_dir.exists():
        return []

    examples = []
    for f in sorted(examples_dir.glob("*.md")):
        if f.name == ".gitkeep":
            continue
        content = read_text(f)
        if content.strip():
            examples.append((f.name, content))

    return examples


def _build_prompt(channel: str, examples: list[tuple[str, str]]) -> str:
    """組裝送給 LLM 的提示。"""
    examples_text = ""
    for i, (filename, content) in enumerate(examples, 1):
        examples_text += f"\n### 範例 {i}（{filename}）\n\n{content}\n"

    return f"""\
請分析以下 {len(examples)} 篇「{channel}」頻道的真實文章範例，提取出作者的寫作風格 DNA。

{examples_text}

請嚴格按照七個分析維度輸出結果。
"""


def main():
    parser = argparse.ArgumentParser(description="Extract Style — 提取風格 DNA")
    parser.add_argument("channel", help="頻道名稱（例如 threads, facebook, blog）")
    parser.add_argument("--force", action="store_true", help="強制覆蓋已存在的 DNA 檔案")
    args = parser.parse_args()

    channel = args.channel.lower().strip()

    # 1. 收集範例
    examples = _collect_examples(channel)
    if len(examples) < MIN_EXAMPLES:
        print(f"[extract-style] ERROR: 至少需要 {MIN_EXAMPLES} 篇範例，目前只有 {len(examples)} 篇", file=sys.stderr)
        print(f"[extract-style] 請將範例放到 {EXAMPLES_DIR / channel}/", file=sys.stderr)
        sys.exit(1)

    print(f"[extract-style] Found {len(examples)} examples for '{channel}'")

    # 2. 檢查輸出
    output_path = STYLE_DNA_DIR / f"{channel}-dna.md"
    if output_path.exists() and not args.force:
        response = input(f"[extract-style] {output_path.name} 已存在，覆蓋？(y/N) ").strip().lower()
        if response != "y":
            print("[extract-style] Cancelled.")
            sys.exit(0)

    # 3. LLM 分析
    print(f"[extract-style] Analyzing style patterns...")
    prompt = _build_prompt(channel, examples)
    result = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 4. 清理 LLM 回應
    if result and not result.startswith("#"):
        marker = result.find("\n#")
        if marker != -1:
            result = result[marker + 1:]

    # 5. 加標題 + 寫入
    header = f"# {channel.title()} — Style DNA\n\n"
    header += f"> 從 {len(examples)} 篇範例提取 | 最後更新：{__import__('datetime').datetime.now().strftime('%Y-%m-%d')}\n\n---\n\n"

    ensure_dir(output_path.parent)
    output_path.write_text(header + result, encoding="utf-8")

    print(f"[extract-style] Done: {output_path}")


if __name__ == "__main__":
    main()
