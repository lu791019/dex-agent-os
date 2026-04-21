"""修正 create_content_databases.py 造成的 relation 重複與命名問題。

問題：
  1. Content ↔ Topic 有兩組獨立的 dual relation（Content 的 Related Topic + Topic 的 Related Content）
  2. 自動反向欄位名稱醜（Related to Topic DB (Template) 等）

修正：
  1. 刪除 Content DB 的 Related Topic → 連動刪除 Topic DB 的「Related to 內容 (Related Topic)」
  2. 把 Content DB 的「Related to Topic DB (Related Content)」rename 為 Related Topic
  3. 把 Template DB 的「Related to Topic DB (Template)」rename 為 Topics Using
  4. 把 Insight DB 的「Related to Topic DB (Related Insights)」rename 為 Topic
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from lib.notion_api import update_database, notion_request


def rename_or_delete(db_id: str, changes: dict) -> None:
    """對 DB 套用 property 異動（改名或刪除）。"""
    notion_request("PATCH", f"databases/{db_id}", data={"properties": changes})


def main() -> int:
    content_db = os.environ.get("NOTION_CONTENT_DB", "")
    template_db = os.environ.get("NOTION_TEMPLATE_DB", "")
    insight_db = os.environ.get("NOTION_INSIGHT_DB", "")
    topic_db = os.environ.get("NOTION_TOPIC_DB", "")

    if not all([content_db, template_db, insight_db, topic_db]):
        print("❌ 缺 env", file=sys.stderr)
        return 1

    # Step 1: 刪除 Content DB 的 Related Topic（會連動刪除 Topic DB 的反向）
    print("▶ 1/4 刪除 Content DB 重複的 Related Topic...")
    rename_or_delete(content_db, {"Related Topic": None})
    print("   ✅")

    # Step 2: 把 Content DB 的自動反向欄位 rename 為 Related Topic
    print("▶ 2/4 Content DB：'Related to Topic DB (Related Content)' → 'Related Topic'...")
    rename_or_delete(content_db, {
        "Related to Topic DB (Related Content)": {"name": "Related Topic"},
    })
    print("   ✅")

    # Step 3: Template DB rename
    print("▶ 3/4 Template DB：'Related to Topic DB (Template)' → 'Topics Using'...")
    rename_or_delete(template_db, {
        "Related to Topic DB (Template)": {"name": "Topics Using"},
    })
    print("   ✅")

    # Step 4: Insight DB rename
    print("▶ 4/4 Insight DB：'Related to Topic DB (Related Insights)' → 'Topic'...")
    rename_or_delete(insight_db, {
        "Related to Topic DB (Related Insights)": {"name": "Topic"},
    })
    print("   ✅")

    # Verification
    print("\n🔍 驗證最終 schema...")
    dbs = {
        "Template": template_db,
        "Insight":  insight_db,
        "Topic":    topic_db,
        "Content":  content_db,
    }
    for name, db_id in dbs.items():
        r = notion_request("GET", f"databases/{db_id}")
        rels = [k for k, v in r.get("properties", {}).items() if v.get("type") == "relation"]
        print(f"  {name}: relations = {rels}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
