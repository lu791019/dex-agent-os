"""端對端測試 sync_insight_v2 / sync_topic_v2 / sync_draft_v2。

流程：
  1. 查 Template DB 拿 #1「不是錯覺框架」的 page_id 當 template_id
  2. sync_insight_v2 建 1 筆測試 Insight → insight_id
  3. sync_topic_v2 建 Topic，relation insight_ids + template_id
  4. sync_draft_v2 建 Draft，channel=threads + topic_id
  5. 驗證 4 個雙向 relation
  6. archive 清場
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

from lib.notion_api import archive_page, notion_request, query_database
from lib.notion_sync import sync_draft_v2, sync_insight_v2, sync_topic_v2

TAG = "E2E-V2-2026-04-22"


def main() -> int:
    template_db = os.environ.get("NOTION_TEMPLATE_DB", "")
    if not template_db:
        print("❌ NOTION_TEMPLATE_DB 未設定", file=sys.stderr)
        return 1

    today = date.today().isoformat()
    created: list[str] = []
    failures: list[str] = []

    try:
        # ── 0. 拿 #1 框架 page_id ──────────────────────
        print("▶ 0/5 查 Template DB 取得 #1「不是錯覺框架」...")
        tmpl = query_database(template_db, filter_obj={
            "property": "Number",
            "number": {"equals": 1},
        }, page_size=1)
        if not tmpl:
            failures.append("找不到 #1 框架")
            return 2
        template_id = tmpl[0]["id"]
        print(f"   ✅ template_id = {template_id}")

        # ── 1. sync_insight_v2 ─────────────────────────
        print("▶ 1/5 sync_insight_v2...")
        insight_id = sync_insight_v2(
            title=f"[{TAG}] 測試 Insight",
            angle="schema v2 測試：raw → curated 流程",
            date_str=today,
            source="sync_v2 end-to-end test",
            tags=["test", "schema-v2"],
            status="raw",
        )
        if not insight_id:
            failures.append("sync_insight_v2 回傳空 page_id")
            return 2
        created.append(insight_id)
        print(f"   ✅ insight_id = {insight_id}")

        # ── 2. sync_topic_v2（含 relations）────────────
        print("▶ 2/5 sync_topic_v2 with insight_ids + template_id...")
        topic_id = sync_topic_v2(
            title=f"[{TAG}] 測試 Topic",
            core_message="端對端驗證 Topic 可 relation Insight+Template",
            date_str=today,
            status="draft",
            outline="段落 1 / 段落 2 / 段落 3",
            insight_ids=[insight_id],
            template_id=template_id,
        )
        if not topic_id:
            failures.append("sync_topic_v2 回傳空 page_id")
            return 2
        created.append(topic_id)
        print(f"   ✅ topic_id = {topic_id}")

        # ── 3. sync_draft_v2（Channel=threads）────────
        print("▶ 3/5 sync_draft_v2 channel=threads, topic_id...")
        draft_id = sync_draft_v2(
            title=f"[{TAG}] 測試 Draft",
            channel="threads",
            draft_content="這是一段測試草稿內容。\n用來驗證 Channel + Related Topic 運作。",
            date_str=today,
            topic_id=topic_id,
            core_message="測試草稿核心觀點",
            tags=["test"],
        )
        if not draft_id:
            failures.append("sync_draft_v2 回傳空 page_id")
            return 2
        created.append(draft_id)
        print(f"   ✅ draft_id = {draft_id}")

        # ── 4. 驗證 4 組 relations ─────────────────────
        print("▶ 4/5 驗證雙向 relations...")

        # Topic.Related Insights 正向
        topic_r = notion_request("GET", f"pages/{topic_id}")
        tp = topic_r.get("properties", {})

        ri = [r["id"] for r in tp.get("Related Insights", {}).get("relation", [])]
        if insight_id in ri:
            print(f"   ✅ Topic.Related Insights 連到 Insight")
        else:
            failures.append(f"Topic.Related Insights 缺 Insight (got {ri})")

        tmpl_r = [r["id"] for r in tp.get("Template", {}).get("relation", [])]
        if template_id in tmpl_r:
            print(f"   ✅ Topic.Template 連到 Template #1")
        else:
            failures.append(f"Topic.Template 缺 Template (got {tmpl_r})")

        rc = [r["id"] for r in tp.get("Related Content", {}).get("relation", [])]
        if draft_id in rc:
            print(f"   ✅ Topic.Related Content 反向連到 Draft")
        else:
            failures.append(f"Topic.Related Content 缺 Draft (got {rc})")

        # Insight.Topic 反向
        insight_r = notion_request("GET", f"pages/{insight_id}")
        ip_topic = [r["id"] for r in insight_r.get("properties", {}).get("Topic", {}).get("relation", [])]
        if topic_id in ip_topic:
            print(f"   ✅ Insight.Topic 反向連到 Topic")
        else:
            failures.append(f"Insight.Topic 缺 Topic (got {ip_topic})")

        # Template.Topics Using 反向
        tmpl_full = notion_request("GET", f"pages/{template_id}")
        tu = [r["id"] for r in tmpl_full.get("properties", {}).get("Topics Using", {}).get("relation", [])]
        if topic_id in tu:
            print(f"   ✅ Template.Topics Using 反向連到 Topic")
        else:
            failures.append(f"Template.Topics Using 缺 Topic (got {tu})")

        # Draft.Related Topic + Channel
        draft_r = notion_request("GET", f"pages/{draft_id}")
        dp = draft_r.get("properties", {})
        rt = [r["id"] for r in dp.get("Related Topic", {}).get("relation", [])]
        if topic_id in rt:
            print(f"   ✅ Draft.Related Topic 連到 Topic")
        else:
            failures.append(f"Draft.Related Topic 缺 Topic (got {rt})")

        ch = dp.get("Channel", {}).get("select", {}).get("name") if dp.get("Channel", {}).get("select") else None
        if ch == "threads":
            print(f"   ✅ Draft.Channel = threads")
        else:
            failures.append(f"Draft.Channel 非 threads (got {ch!r})")

    finally:
        # ── 5. 清場 ────────────────────────────────────
        print("▶ 5/5 清場...")
        for pid in created:
            try:
                archive_page(pid)
                print(f"   🧹 archived {pid[:12]}...")
            except Exception as e:
                print(f"   ⚠️  archive 失敗 {pid}: {e}")

    print("\n" + "=" * 60)
    if failures:
        print(f"❌ 測試失敗：{len(failures)} 項")
        for f in failures:
            print(f"   - {f}")
        return 2
    print("✅ 全部測試通過 — sync v2 三個函式全部正確寫入 + 雙向 relation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
