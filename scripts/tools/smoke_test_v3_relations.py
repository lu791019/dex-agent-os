"""A3 煙霧測試：用真實 backfill 的 Topic 建一筆測試 Draft，驗證三層 relation。

流程：
  1. 從 data/topic_notion_map.json 挑一個指定（或預設）Topic
  2. 呼叫 sync_draft_v2 建 Threads 草稿，topic_id=該 Topic
  3. 印出 Notion page URL，請使用者目視驗證：
       - Topic page → 看得到 Related Drafts 反向連結
       - Draft page → Channel=threads + Related Topic 指回 Topic
       - Topic page → Related Insights（從 backfill 帶過來）

清場：
  --cleanup 模式會把上次測試建的 Draft archive 掉（讀 .smoke_test_draft_id）
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lib.config  # noqa: F401
from lib.notion_api import archive_page
from lib.notion_sync import sync_draft_v2

TOPIC_MAP = ROOT / "data" / "topic_notion_map.json"
LAST_DRAFT_FILE = ROOT / "data" / ".smoke_test_draft_id"

DEFAULT_TOPIC_SLUG = "ai-persistent-consciousness-three-mechanisms"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic-slug", default=DEFAULT_TOPIC_SLUG)
    parser.add_argument("--cleanup", action="store_true", help="archive 上次測試建的 draft")
    args = parser.parse_args()

    if args.cleanup:
        if not LAST_DRAFT_FILE.exists():
            print("沒有上次測試的紀錄，無需 cleanup")
            return 0
        draft_id = LAST_DRAFT_FILE.read_text().strip()
        archive_page(draft_id)
        LAST_DRAFT_FILE.unlink()
        print(f"✅ archived draft {draft_id}")
        return 0

    topic_map = json.loads(TOPIC_MAP.read_text())
    if args.topic_slug not in topic_map:
        print(f"❌ Topic slug 不在 map 中：{args.topic_slug}")
        print(f"   可選範例：{list(topic_map.keys())[:5]}")
        return 1

    topic_id = topic_map[args.topic_slug]
    print(f"▶ 使用 Topic: {args.topic_slug}")
    print(f"  Topic page_id: {topic_id}")

    draft_content = (
        "## 第一稿（smoke test）\n\n"
        "這是 A3 端對端煙霧測試建立的草稿，用來驗證 v3 三層 relation。\n\n"
        "- 預期 Topic page 顯示 Related Drafts 反向連結\n"
        "- 預期此 Draft 頁面顯示 Channel=threads、Related Topic 指回 Topic\n"
        "- Topic 應仍保留 Related Insights（backfill 帶過來的）\n"
    )

    draft_id = sync_draft_v2(
        title=f"[SMOKE TEST] {args.topic_slug}",
        channel="threads",
        draft_content=draft_content,
        date_str=date.today().isoformat(),
        topic_id=topic_id,
        core_message="煙霧測試：驗證 Insight → Topic → Draft 三層 relation",
        tags=["smoke-test"],
        source="A3 自動測試",
    )

    if not draft_id:
        print("❌ sync_draft_v2 失敗")
        return 2

    LAST_DRAFT_FILE.write_text(draft_id)
    page_url = f"https://www.notion.so/{draft_id.replace('-', '')}"
    print()
    print("✅ Draft 建立完成")
    print(f"  Draft page_id: {draft_id}")
    print(f"  URL: {page_url}")
    print()
    print("👀 請到 Notion 目視驗證以下三件事：")
    print("  1. 打開上面 Draft URL → Channel 欄位是 threads / Related Topic 指回 Topic")
    print("  2. 打開 Topic page → Related Drafts 反向欄位裡有這筆 Draft")
    print("  3. 打開 Topic page → Related Insights 有 backfill 帶過來的 Insight")
    print()
    print("驗證完跑 `--cleanup` 清掉這筆測試 Draft")
    return 0


if __name__ == "__main__":
    sys.exit(main())
