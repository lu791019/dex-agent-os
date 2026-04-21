"""把 800_System/references/writing-frameworks.md 的 19 個框架匯入 Template DB。

解析邏輯：
  - 以 `## N. 框架名` 切 section
  - 每個 section 內用 `**XXX**` 切子區塊
  - 對應欄位：結構→Structure / 邏輯→Logic / 適用場景→Use Cases(multi_select) /
             範例*→Example / 變體|關鍵原則→Variants

重跑安全：
  --skip-existing 會先查 DB，跳過同名 Name 的紀錄
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from lib.notion_api import (
    add_page,
    notion_request,
    prop_multi_select,
    prop_number,
    prop_rich_text,
    prop_title,
    prop_url,
    query_database,
)

FRAMEWORKS_MD = ROOT / "800_System" / "references" / "writing-frameworks.md"
SOURCE_URL = "https://github.com/lu791019/dex-agent-os/blob/master/800_System/references/writing-frameworks.md"


def parse_sections(text: str) -> list[dict]:
    """把 md 切成每個框架一個 dict。"""
    section_pattern = re.compile(r"^## (\d+)\.\s+(.+?)$", re.MULTILINE)
    matches = list(section_pattern.finditer(text))
    results = []
    for i, m in enumerate(matches):
        number = int(m.group(1))
        name = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        results.append({"number": number, "name": name, "body": body})
    return results


def parse_fields(body: str) -> dict[str, str]:
    """從 section body 抽出 **XXX** 對應的內容。"""
    parts = re.split(r"^\*\*(.+?)\*\*", body, flags=re.MULTILINE)
    fields: dict[str, str] = {}
    for i in range(1, len(parts), 2):
        key = parts[i].strip()
        val = parts[i + 1] if i + 1 < len(parts) else ""
        val = val.lstrip("：:").strip()
        # 去除尾端的 --- 分隔線
        val = re.sub(r"\n---\s*$", "", val).strip()
        fields[key] = val
    return fields


def extract_use_cases(raw: str) -> list[str]:
    """從 '適用場景' 值抽出 bullet list → tag 列表。"""
    tags = []
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            tag = line[2:].strip()
            # Notion multi_select name 不能含逗號；截短到 100 char
            tag = tag.replace(",", "、")[:100]
            if tag:
                tags.append(tag)
    return tags


def build_record(item: dict) -> dict:
    """把解析結果轉成 Notion properties dict。"""
    fields = parse_fields(item["body"])

    # 範例欄位有多種名稱變體
    example = ""
    for k in ("範例", "範例收尾", "範例結構示範"):
        if k in fields:
            example = fields[k]
            break

    # 變體欄位也有變體
    variants = ""
    for k in ("變體", "關鍵原則"):
        if k in fields:
            variants = fields[k]
            break

    use_cases = extract_use_cases(fields.get("適用場景", ""))

    return {
        "Name": prop_title(item["name"]),
        "Number": prop_number(item["number"]),
        "Structure": prop_rich_text(fields.get("結構", "")),
        "Logic": prop_rich_text(fields.get("邏輯", "")),
        "Use Cases": prop_multi_select(use_cases),
        "Example": prop_rich_text(example),
        "Variants": prop_rich_text(variants),
        "Source File": prop_url(SOURCE_URL),
    }


def get_existing_names(db_id: str) -> set[str]:
    """查 Template DB 裡已有的 Name（去重用）。"""
    results = query_database(db_id, page_size=100)
    names = set()
    for r in results:
        title_prop = r.get("properties", {}).get("Name", {}).get("title", [])
        if title_prop:
            names.add(title_prop[0].get("plain_text", ""))
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db_id = os.environ.get("NOTION_TEMPLATE_DB", "")
    if not db_id:
        print("❌ NOTION_TEMPLATE_DB 未設定", file=sys.stderr)
        return 1

    if not FRAMEWORKS_MD.exists():
        print(f"❌ 找不到 {FRAMEWORKS_MD}", file=sys.stderr)
        return 1

    text = FRAMEWORKS_MD.read_text()
    sections = parse_sections(text)
    print(f"📖 解析到 {len(sections)} 個框架")

    if args.dry_run:
        print("\n[dry-run] 前 3 個框架的欄位摘要：")
        for item in sections[:3]:
            fields = parse_fields(item["body"])
            print(f"\n--- #{item['number']} {item['name']} ---")
            print(f"  keys: {list(fields.keys())}")
            print(f"  use_cases: {extract_use_cases(fields.get('適用場景', ''))[:3]}")
            print(f"  structure[:100]: {fields.get('結構', '')[:100]!r}")
        return 0

    existing = get_existing_names(db_id) if args.skip_existing else set()
    if existing:
        print(f"⚠️  Template DB 已有 {len(existing)} 筆，重複的會跳過")

    created, skipped, failed = 0, 0, 0
    for item in sections:
        if item["name"] in existing:
            print(f"   ⏭  skip #{item['number']} {item['name']}")
            skipped += 1
            continue
        try:
            props = build_record(item)
            page_id = add_page(db_id, properties=props)
            print(f"   ✅ #{item['number']} {item['name']} → {page_id[:12]}...")
            created += 1
        except Exception as e:
            print(f"   ❌ #{item['number']} {item['name']}: {str(e)[:200]}")
            failed += 1

    # Verification
    print(f"\n📊 結果：建立 {created} / 跳過 {skipped} / 失敗 {failed}")
    final_count = len(get_existing_names(db_id))
    print(f"📊 Template DB 現有紀錄總數：{final_count}")
    if final_count != 19:
        print(f"⚠️  預期 19 筆，實際 {final_count}")
        return 2
    print("✅ 全部 19 個框架就緒")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
