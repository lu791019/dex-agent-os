"""Backfill 520_Topics/*/TOPIC.md → Notion Topic DB（v3 架構）。

解析每個 TOPIC.md：
  - YAML frontmatter: title / status / created / source（wikilink → insight slug）
  - 「## 核心論點」段落 → core_message
  - 整份內容（去 frontmatter）→ outline（截斷至 2000 char 內，避免 Notion rich_text 上限）
  - source wikilink → 查 insight_notion_map.json → 建 Related Insights relation

防呆：
  - --dry-run / --limit N
  - data/topic_notion_map.json 紀錄已 backfill
  - 寫回 notion_id 到 TOPIC.md frontmatter
  - 失敗紀錄到 data/topic_backfill_failed.json
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
from lib.notion_sync import sync_topic_v2

TOPICS_DIR = ROOT / "520_Topics"
TOPIC_MAP_FILE = ROOT / "data" / "topic_notion_map.json"
INSIGHT_MAP_FILE = ROOT / "data" / "insight_notion_map.json"
FAIL_FILE = ROOT / "data" / "topic_backfill_failed.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# 找任意位置的 ---\n...title:...\n---\n 區塊（容忍 nested code fence 包覆）
ANY_FM_WITH_TITLE_RE = re.compile(
    r"---\s*\n([^\n]*\n)*?title:[^\n]*\n(?:[^\n]*\n)*?---\s*\n",
)
CORE_MSG_RE = re.compile(r"^## 核心論點\s*\n(.+?)(?=\n##\s|\Z)", re.DOTALL | re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

STATUS_MAP = {
    "drafting": "draft",
    "draft": "draft",
    "writing": "writing",
    "published": "published",
    "dropped": "dropped",
}

OUTLINE_MAX_CHARS = 2000


def parse_frontmatter(text: str) -> tuple[dict, str]:
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
            inner = val[1:-1].strip()
            if not inner:
                fm[key] = []
                continue
            fm[key] = [v.strip().strip('"').strip("'") for v in inner.split(",")]
            continue
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        fm[key] = val
    return fm, body


def _parse_yaml_block(fm_text: str) -> dict:
    fm: dict = {}
    for line in fm_text.split("\n"):
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                fm[key] = []
                continue
            fm[key] = [v.strip().strip('"').strip("'") for v in inner.split(",")]
            continue
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        fm[key] = val
    return fm


def parse_topic(topic_dir: Path) -> dict | None:
    md_path = topic_dir / "TOPIC.md"
    if not md_path.exists():
        return None
    text = md_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    # Fallback: 找任意位置含 title: 的 ---/--- 區塊（21 個包在 ```markdown fence 內的歷史檔案）
    if not fm or "title" not in fm:
        m = ANY_FM_WITH_TITLE_RE.search(text)
        if m:
            # 重抓內容：去掉首尾的 --- 行
            block = m.group(0)
            inner = re.sub(r"^---\s*\n|\n---\s*\n$", "", block)
            fm = _parse_yaml_block(inner)
            body = text[m.end():]

    title = fm.get("title", "").strip()
    if not title:
        # fallback: 用第一個 H1
        h1 = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if h1:
            title = h1.group(1).strip()
    if not title:
        return None

    core_match = CORE_MSG_RE.search(body)
    core_message = core_match.group(1).strip() if core_match else ""

    # outline: 整個 body 截斷
    outline = body.strip()
    if len(outline) > OUTLINE_MAX_CHARS:
        outline = outline[:OUTLINE_MAX_CHARS] + "\n... (截斷)"

    # source → insight slug（支援 wikilink 和 path 兩種格式）
    insight_slugs: list[str] = []
    source = fm.get("source", "")
    if source:
        for m in WIKILINK_RE.finditer(source):
            insight_slugs.append(m.group(1))
        # path 格式 fallback: 000_Inbox/ideas/{slug}.md or similar
        if not insight_slugs and source.endswith(".md"):
            path_stem = Path(source).stem
            if path_stem:
                insight_slugs.append(path_stem)

    status_raw = fm.get("status", "drafting").strip()
    status = STATUS_MAP.get(status_raw, "draft")

    return {
        "slug": topic_dir.name,
        "title": title,
        "core_message": core_message,
        "outline": outline,
        "date_str": fm.get("created", ""),
        "status": status,
        "insight_slugs": insight_slugs,
        "notion_id": fm.get("notion_id", ""),
        "md_path": md_path,
    }


def load_map(path: Path) -> dict[str, str]:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_map(path: Path, m: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m, ensure_ascii=False, indent=2))


def write_notion_id(md_path: Path, page_id: str) -> None:
    text = md_path.read_text(encoding="utf-8")
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
    md_path.write_text(new_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=0.35)
    args = parser.parse_args()

    if not os.environ.get("NOTION_TOPIC_DB"):
        print("❌ NOTION_TOPIC_DB 未設定", file=sys.stderr)
        return 1

    insight_map = load_map(INSIGHT_MAP_FILE)
    print(f"📚 Insight map: {len(insight_map)} 筆")

    dirs = sorted([d for d in TOPICS_DIR.iterdir() if d.is_dir()])
    if args.limit > 0:
        dirs = dirs[: args.limit]
    print(f"📖 找到 {len(dirs)} 個 Topic 目錄")

    topic_map = load_map(TOPIC_MAP_FILE)

    parsed: list[dict] = []
    skipped_broken: list[str] = []
    for d in dirs:
        t = parse_topic(d)
        if t is None or not t["core_message"]:
            skipped_broken.append(d.name)
            continue
        parsed.append(t)

    if skipped_broken:
        print(f"⚠️  跳過 {len(skipped_broken)} 個解析失敗（無 title 或缺核心論點）:")
        for s in skipped_broken:
            print(f"   - {s}")

    if args.dry_run:
        print(f"\n[dry-run] 前 3 個 Topic 解析結果：")
        for t in parsed[:3]:
            related_ids = [insight_map[s] for s in t["insight_slugs"] if s in insight_map]
            missing = [s for s in t["insight_slugs"] if s not in insight_map]
            print(f"\n  --- {t['slug']} ---")
            print(f"  title:        {t['title']}")
            print(f"  date:         {t['date_str']}")
            print(f"  status:       {t['status']}")
            print(f"  core[:120]:   {t['core_message'][:120]!r}")
            print(f"  outline len:  {len(t['outline'])}")
            print(f"  related ins:  {len(related_ids)} matched, {len(missing)} missing")
            if missing:
                print(f"    missing slugs: {missing}")
        return 0

    created, skipped, failed = 0, 0, 0
    failures: list[dict] = []

    for t in parsed:
        if t["slug"] in topic_map:
            skipped += 1
            continue

        related_ids = [insight_map[s] for s in t["insight_slugs"] if s in insight_map]

        try:
            page_id = sync_topic_v2(
                title=t["title"],
                core_message=t["core_message"],
                date_str=t["date_str"],
                status=t["status"],
                outline=t["outline"],
                insight_ids=related_ids if related_ids else None,
            )
            if not page_id:
                raise RuntimeError("sync_topic_v2 回傳空 page_id")
            topic_map[t["slug"]] = page_id
            write_notion_id(t["md_path"], page_id)
            print(f"   ✅ {t['slug']} → {page_id[:12]}... (rel: {len(related_ids)})")
            created += 1
            save_map(TOPIC_MAP_FILE, topic_map)
            time.sleep(args.sleep)
        except Exception as e:
            print(f"   ❌ {t['slug']}: {str(e)[:200]}")
            failed += 1
            failures.append({"slug": t["slug"], "error": str(e)[:500]})

    if failures:
        FAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
        FAIL_FILE.write_text(json.dumps(failures, ensure_ascii=False, indent=2))

    print(f"\n📊 結果：建立 {created} / 跳過(已存在) {skipped} / 解析失敗 {len(skipped_broken)} / 寫入失敗 {failed}")
    if failures:
        print(f"📊 failures: {FAIL_FILE}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
