"""端對端測試內容管線 v3 的四個 DB：
  1. 在 Insight DB 建 1 筆測試 Insight
  2. 在 Topic DB 建 1 筆測試 Topic，relation 到那筆 Insight
  3. 在 Content DB 建 1 筆測試 Content，relation 到那筆 Topic
  4. 查 Insight 看 Topic 反向有沒有；查 Topic 看 Content 反向有沒有
  5. archive 所有測試頁面（清場）

全程自動化，輸出 pass/fail。
"""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from lib.notion_api import (
    add_page,
    archive_page,
    notion_request,
    prop_date,
    prop_multi_select,
    prop_relation,
    prop_rich_text,
    prop_select,
    prop_title,
)

TAG = "E2E-TEST-2026-04-22"


def main() -> int:
    insight_db = os.environ.get("NOTION_INSIGHT_DB", "")
    topic_db = os.environ.get("NOTION_TOPIC_DB", "")
    content_db = os.environ.get("NOTION_CONTENT_DB", "")

    if not all([insight_db, topic_db, content_db]):
        print("❌ 缺 env", file=sys.stderr)
        return 1

    today = date.today().isoformat()
    created_ids: list[str] = []
    failures: list[str] = []

    try:
        # ── 1. 建 Insight ───────────────────────────────
        print("▶ 1/5 建立測試 Insight...")
        insight_id = add_page(insight_db, properties={
            "Title": prop_title(f"[{TAG}] 測試 Insight"),
            "Angle": prop_rich_text("一句話觀點：schema 測試"),
            "Status": prop_select("raw"),
            "Source": prop_rich_text("e2e test"),
            "Source Date": prop_date(today),
            "Tags": prop_multi_select(["test"]),
        })
        created_ids.append(insight_id)
        print(f"   ✅ Insight page: {insight_id}")

        # ── 2. 建 Topic，relation → Insight ─────────────
        print("▶ 2/5 建立測試 Topic，relation → Insight...")
        topic_id = add_page(topic_db, properties={
            "Title": prop_title(f"[{TAG}] 測試 Topic"),
            "Core Message": prop_rich_text("測試 Topic 的核心訊息"),
            "Status": prop_select("draft"),
            "Created Date": prop_date(today),
            "Related Insights": prop_relation([insight_id]),
        })
        created_ids.append(topic_id)
        print(f"   ✅ Topic page: {topic_id}")

        # ── 3. 建 Content，relation → Topic + Channel ──
        print("▶ 3/5 建立測試 Content，relation → Topic + Channel=threads...")
        content_id = add_page(content_db, properties={
            "標題": prop_title(f"[{TAG}] 測試 Content"),
            "狀態": prop_select("seed"),
            "建立日期": prop_date(today),
            "Channel": prop_select("threads"),
            "Related Topic": prop_relation([topic_id]),
        })
        created_ids.append(content_id)
        print(f"   ✅ Content page: {content_id}")

        # ── 4. 驗證反向 relation ────────────────────────
        print("▶ 4/5 驗證雙向 relation...")

        # Insight 應該看到 Topic 反向
        insight_r = notion_request("GET", f"pages/{insight_id}")
        topic_rel = insight_r.get("properties", {}).get("Topic", {}).get("relation", [])
        if any(r.get("id") == topic_id for r in topic_rel):
            print(f"   ✅ Insight.Topic 反向連到 Topic: {[r['id'] for r in topic_rel]}")
        else:
            failures.append(f"Insight.Topic 沒有反向連到 Topic (got {topic_rel})")

        # Topic 應該看到 Content 反向
        topic_r = notion_request("GET", f"pages/{topic_id}")
        content_rel = topic_r.get("properties", {}).get("Related Content", {}).get("relation", [])
        if any(r.get("id") == content_id for r in content_rel):
            print(f"   ✅ Topic.Related Content 反向連到 Content: {[r['id'] for r in content_rel]}")
        else:
            failures.append(f"Topic.Related Content 沒有反向連到 Content (got {content_rel})")

        # Content.Related Topic 正向應包含 Topic
        content_r = notion_request("GET", f"pages/{content_id}")
        cr_rel = content_r.get("properties", {}).get("Related Topic", {}).get("relation", [])
        if any(r.get("id") == topic_id for r in cr_rel):
            print(f"   ✅ Content.Related Topic 正向連到 Topic")
        else:
            failures.append(f"Content.Related Topic 正向缺失 (got {cr_rel})")

    finally:
        # ── 5. 清場（archive 所有測試頁面）─────────────
        print("▶ 5/5 清場（archive 測試頁面）...")
        for pid in created_ids:
            try:
                archive_page(pid)
                print(f"   🧹 archived {pid}")
            except Exception as e:
                print(f"   ⚠️  archive 失敗 {pid}: {e}")

    # 結果
    print("\n" + "=" * 60)
    if failures:
        print(f"❌ 測試失敗：{len(failures)} 項")
        for f in failures:
            print(f"   - {f}")
        return 2
    print("✅ 全部測試通過 — schema 可正常寫入與雙向 relation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
