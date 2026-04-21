"""一次性建立內容管線 v3 的三個新 Notion DB，並擴充現有 Content DB。

執行順序（relation 依賴）：
  1. Template DB（無依賴）
  2. Insight DB（暫不含 Topic relation）
  3. Topic DB（含 Insight/Content/Template relation — 會自動在 Insight/Content 建反向）
  4. 擴充 Content DB 加 Channel(select) + Related Topic(relation → Topic)

最後印出所有 DB ID，請手動加入 .env。
可用 --dry-run 只檢查不建。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from lib.notion_api import (
    create_database,
    notion_request,
    schema_relation,
    update_database,
)

PARENT_PAGE_ID = "34952f3feb9180bda604d03f25ce56c2"  # 「內容管線」page


def _title_schema() -> dict:
    return {"title": {}}


def _rich_text_schema() -> dict:
    return {"rich_text": {}}


def _select_schema(options: list[str]) -> dict:
    return {"select": {"options": [{"name": n} for n in options]}}


def _multi_select_schema() -> dict:
    return {"multi_select": {"options": []}}


def _date_schema() -> dict:
    return {"date": {}}


def _number_schema() -> dict:
    return {"number": {"format": "number"}}


def _url_schema() -> dict:
    return {"url": {}}


def build_template_schema() -> dict:
    return {
        "Name": _title_schema(),
        "Number": _number_schema(),
        "Structure": _rich_text_schema(),
        "Logic": _rich_text_schema(),
        "Use Cases": _multi_select_schema(),
        "Example": _rich_text_schema(),
        "Variants": _rich_text_schema(),
        "Source File": _url_schema(),
    }


def build_insight_schema(knowledge_db_id: str | None) -> dict:
    props = {
        "Title": _title_schema(),
        "Angle": _rich_text_schema(),
        "Status": _select_schema(["raw", "curated", "topicized", "archived"]),
        "Source": _rich_text_schema(),
        "Source Date": _date_schema(),
        "Tags": _multi_select_schema(),
    }
    if knowledge_db_id:
        props["Related Knowledge"] = schema_relation(knowledge_db_id, dual=True)
    return props


def build_topic_schema(
    insight_db_id: str,
    content_db_id: str,
    template_db_id: str,
) -> dict:
    return {
        "Title": _title_schema(),
        "Core Message": _rich_text_schema(),
        "Status": _select_schema(["draft", "writing", "published", "dropped"]),
        "Outline": _rich_text_schema(),
        "Created Date": _date_schema(),
        "Related Insights": schema_relation(insight_db_id, dual=True),
        "Related Content": schema_relation(content_db_id, dual=True),
        "Template": schema_relation(template_db_id, dual=True),
    }


def verify_db_schema(db_id: str, expected_fields: list[str]) -> tuple[bool, list[str]]:
    """驗證 DB 的欄位符合預期。回傳 (ok, missing_fields)。"""
    r = notion_request("GET", f"databases/{db_id}")
    actual = set(r.get("properties", {}).keys())
    missing = [f for f in expected_fields if f not in actual]
    return (len(missing) == 0, missing)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只印計畫不實際建立")
    args = parser.parse_args()

    token = os.environ.get("NOTION_TOKEN", "")
    if not token:
        print("❌ NOTION_TOKEN 未設定", file=sys.stderr)
        return 1

    content_db_id = os.environ.get("NOTION_CONTENT_DB", "")
    knowledge_db_id = os.environ.get("NOTION_LEARNING_DB", "")
    if not content_db_id:
        print("❌ NOTION_CONTENT_DB 未設定", file=sys.stderr)
        return 1

    print(f"📍 Parent page: {PARENT_PAGE_ID}")
    print(f"📍 Content DB (擴充): {content_db_id}")
    print(f"📍 Knowledge DB (relation target): {knowledge_db_id or '(未設定，跳過 Insight→Knowledge relation)'}")
    print()

    if args.dry_run:
        print("[dry-run] 不實際建立，只列計畫：")
        print("  1. 建 Template DB")
        print("  2. 建 Insight DB (含 Related Knowledge)")
        print("  3. 建 Topic DB (含 3 個 relation)")
        print("  4. 擴充 Content DB 加 Channel + Related Topic")
        return 0

    # ── 1. Template DB ──────────────────────────────────
    print("▶ 1/4 建立 Template DB...")
    template_db_id = create_database(
        parent_page_id=PARENT_PAGE_ID,
        title="Template DB",
        properties=build_template_schema(),
        icon_emoji="📐",
    )
    print(f"   ✅ Template DB: {template_db_id}")

    # ── 2. Insight DB ───────────────────────────────────
    print("▶ 2/4 建立 Insight DB...")
    insight_db_id = create_database(
        parent_page_id=PARENT_PAGE_ID,
        title="Insight DB",
        properties=build_insight_schema(knowledge_db_id or None),
        icon_emoji="💡",
    )
    print(f"   ✅ Insight DB: {insight_db_id}")

    # ── 3. Topic DB（含 3 relation — 會自動在 Insight/Content 建反向） ──
    print("▶ 3/4 建立 Topic DB (含 relations to Insight/Content/Template)...")
    topic_db_id = create_database(
        parent_page_id=PARENT_PAGE_ID,
        title="Topic DB",
        properties=build_topic_schema(insight_db_id, content_db_id, template_db_id),
        icon_emoji="🎯",
    )
    print(f"   ✅ Topic DB: {topic_db_id}")

    # ── 4. 擴充 Content DB ──────────────────────────────
    print("▶ 4/4 擴充 Content DB 加 Channel + Related Topic...")
    update_database(
        content_db_id,
        properties={
            "Channel": _select_schema(["threads", "facebook", "blog", "newsletter", "shortvideo"]),
            "Related Topic": schema_relation(topic_db_id, dual=True),
        },
    )
    print(f"   ✅ Content DB 擴充完成")

    # ── Verification ─────────────────────────────────────
    print("\n🔍 驗證 schema...")
    checks = [
        ("Template", template_db_id, ["Name", "Number", "Structure", "Logic", "Use Cases", "Example", "Variants", "Source File"]),
        ("Insight", insight_db_id, ["Title", "Angle", "Status", "Source", "Source Date", "Tags"]),
        ("Topic", topic_db_id, ["Title", "Core Message", "Status", "Outline", "Created Date", "Related Insights", "Related Content", "Template"]),
        ("Content (擴充欄位)", content_db_id, ["Channel", "Related Topic"]),
    ]
    all_ok = True
    for name, db_id, expected in checks:
        ok, missing = verify_db_schema(db_id, expected)
        if ok:
            print(f"   ✅ {name}: 全部欄位就緒")
        else:
            all_ok = False
            print(f"   ❌ {name}: 缺欄位 {missing}")

    print("\n" + "=" * 60)
    print("請把以下三行加入 .env：")
    print("=" * 60)
    print(f"NOTION_TEMPLATE_DB={template_db_id.replace('-', '')}")
    print(f"NOTION_INSIGHT_DB={insight_db_id.replace('-', '')}")
    print(f"NOTION_TOPIC_DB={topic_db_id.replace('-', '')}")
    print("=" * 60)

    return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(main())
