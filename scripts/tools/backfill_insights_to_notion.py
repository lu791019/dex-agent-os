"""Backfill 510_Insights/*.md → Notion Insight DB（v3 架構）。

解析每個 .md：
  - YAML frontmatter: date / source / channel_tags / status
  - 第一個 H1（# ...）→ title
  - 「## 潛在切入角度」段落內容 → angle

防呆：
  - --dry-run 不寫 Notion，印解析結果前 3 筆
  - --limit N 只處理前 N 筆
  - data/insight_notion_map.json 紀錄已 backfill 的檔案（slug → page_id）
  - 成功後寫回 notion_id 到原檔 frontmatter（雙向綁定）
  - 失敗紀錄到 data/insight_backfill_failed.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lib.config  # noqa: F401 — 觸發 .env 載入
from lib.notion_sync import sync_insight_v2

INSIGHTS_DIR = ROOT / "510_Insights"
MAP_FILE = ROOT / "data" / "insight_notion_map.json"
FAIL_FILE = ROOT / "data" / "insight_backfill_failed.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
ANGLE_RE = re.compile(r"^## 潛在切入角度\s*\n(.+?)(?=\n##\s|\Z)", re.DOTALL | re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_without_frontmatter)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_text = m.group(1)
    body = text[m.end():]

    fm: dict = {}
    for line in fm_text.split("\n"):
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            try:
                fm[key] = json.loads(val)
                continue
            except json.JSONDecodeError:
                pass
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        fm[key] = val
    return fm, body


def parse_insight(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    h1 = H1_RE.search(body)
    if not h1:
        return None
    title = h1.group(1).strip()

    angle_match = ANGLE_RE.search(body)
    angle = angle_match.group(1).strip() if angle_match else ""

    tags = fm.get("channel_tags", [])
    if isinstance(tags, str):
        tags = [tags]

    return {
        "slug": path.stem,
        "title": title,
        "angle": angle,
        "date_str": fm.get("date", ""),
        "source": fm.get("source", ""),
        "tags": tags,
        "status": fm.get("status", "raw"),
        "notion_id": fm.get("notion_id", ""),
    }


def load_map() -> dict[str, str]:
    if MAP_FILE.exists():
        return json.loads(MAP_FILE.read_text())
    return {}


def save_map(m: dict[str, str]) -> None:
    MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    MAP_FILE.write_text(json.dumps(m, ensure_ascii=False, indent=2))


def write_notion_id(path: Path, page_id: str) -> None:
    """在 frontmatter 加 notion_id（若已存在則更新）。"""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return
    fm_text = m.group(1)
    if re.search(r"^notion_id:", fm_text, re.MULTILINE):
        new_fm = re.sub(
            r"^notion_id:.*$", f"notion_id: {page_id}", fm_text, flags=re.MULTILINE
        )
    else:
        new_fm = fm_text.rstrip() + f"\nnotion_id: {page_id}"
    new_text = f"---\n{new_fm}\n---\n{text[m.end():]}"
    path.write_text(new_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="只處理前 N 筆（0=全部）")
    parser.add_argument("--sleep", type=float, default=0.35, help="每筆間 sleep 秒數")
    args = parser.parse_args()

    if not os.environ.get("NOTION_INSIGHT_DB"):
        print("❌ NOTION_INSIGHT_DB 未設定", file=sys.stderr)
        return 1

    files = sorted(INSIGHTS_DIR.glob("*.md"))
    if args.limit > 0:
        files = files[: args.limit]
    print(f"📖 找到 {len(files)} 個 Insight 檔案")

    existing_map = load_map()

    if args.dry_run:
        print("\n[dry-run] 前 3 筆解析結果：")
        for path in files[:3]:
            ins = parse_insight(path)
            if not ins:
                print(f"  ⚠️  {path.name}: 解析失敗（缺 H1）")
                continue
            print(f"\n  --- {ins['slug']} ---")
            print(f"  title:  {ins['title']}")
            print(f"  date:   {ins['date_str']}")
            print(f"  source: {ins['source']}")
            print(f"  tags:   {ins['tags']}")
            print(f"  status: {ins['status']}")
            print(f"  angle[:100]: {ins['angle'][:100]!r}")
        print(f"\n📊 已 backfill 過：{len(existing_map)} 筆（會自動跳過）")
        return 0

    created, skipped, failed = 0, 0, 0
    failures: list[dict] = []

    for path in files:
        slug = path.stem
        if slug in existing_map:
            skipped += 1
            continue

        ins = parse_insight(path)
        if not ins:
            print(f"   ⚠️  skip {slug}: 解析失敗")
            failed += 1
            failures.append({"slug": slug, "error": "parse failed"})
            continue

        try:
            page_id = sync_insight_v2(
                title=ins["title"],
                angle=ins["angle"],
                date_str=ins["date_str"],
                source=ins["source"],
                tags=ins["tags"],
                status=ins["status"],
            )
            if not page_id:
                raise RuntimeError("sync_insight_v2 回傳空 page_id")
            existing_map[slug] = page_id
            write_notion_id(path, page_id)
            print(f"   ✅ {slug} → {page_id[:12]}...")
            created += 1
            # 邊跑邊存，斷線也不丟
            save_map(existing_map)
            time.sleep(args.sleep)
        except Exception as e:
            print(f"   ❌ {slug}: {str(e)[:200]}")
            failed += 1
            failures.append({"slug": slug, "error": str(e)[:500]})

    if failures:
        FAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
        FAIL_FILE.write_text(json.dumps(failures, ensure_ascii=False, indent=2))

    print(f"\n📊 結果：建立 {created} / 跳過 {skipped} / 失敗 {failed}")
    print(f"📊 map file: {MAP_FILE} ({len(existing_map)} 筆)")
    if failures:
        print(f"📊 failures: {FAIL_FILE}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
