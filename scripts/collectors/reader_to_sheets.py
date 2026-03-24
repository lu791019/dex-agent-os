#!/usr/bin/env python3
"""Reader → Google Sheets — Readwise Reader 內容同步到 Google Sheet

使用方式：
  ./bin/agent reader-to-sheets                    # 同步過去 7 天
  ./bin/agent reader-to-sheets --days 14          # 同步過去 14 天
  ./bin/agent reader-to-sheets --since 2026-03-15 # 同步指定日期後
  ./bin/agent reader-to-sheets --dry-run          # 預覽不寫入

結構：
  主工作表「Readings」：email（全部）+ podcast（全部）+ RSS（白名單）
  獨立工作表「Seeking Alpha」：Seeking Alpha 文章

去重：email 先寫，RSS 寫入時 skip 已存在的 title
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import GOOGLE_SHEET_ID
from lib.google_api import get_sheets_service
from lib.readwise_api import check_readwise_setup, reader_list

# ── 排除清單（site_name 模糊匹配）──────────────────────

EXCLUDE_SITES = {
    "reddit.com",
    "google cloud documentation",
    "idealist.org",
    "betweengos",
    "thecaringtechie.com",
    "kill-the-newsletter.com",
    "tom's hardware",
    "bbc news afrique",
    "claude.com",
    "mistral.ai",
    "kagi.com",
    "notimenocode.com",
    "manager-tools.com",
    "karpathy.ai",
    "x (formerly twitter)",
    "financial times",
    "apple newsroom",
    "chiukaun.com",
}

SEEKING_ALPHA_KEY = "seeking alpha"

TOPIC_CATEGORIES = ["技術", "生產力", "職涯", "創作", "投資", "產業", "生活", "其他"]

# RSS 白名單（site_name 模糊匹配，只有這些 RSS 來源會進主工作表）
RSS_WHITELIST = {
    "medium",
    "techcrunch",
    "the verge",
    "youtube",
    "systemdesign.one",
    "pragmaticengineer.com",
    "substack.com",
    "dataengineeringweekly.com",
    "strategizeyourcareer.com",
    "bytebytego.com",
    "閱讀前哨站",
    "stratechery",
    "the github blog",
    "the pragmatic engineer",
    "datagibberish.com",
    "churchtechtod",
    "github",
    "雷蒙三十",
    "dataexpert.io",
    "創作者經濟",
    "engineering at meta",
    "notboring.co",
    "uber blog",
    "領先時代",
    "informalwriting.cc",
    "design.systems",
    "techchange",
    "algomaster.io",
    "workplace insights",
}

HEADER_ROW = ["日期", "分類", "作者", "標題", "來源URL", "摘要", "主題"]


# ── 工具函式 ──────────────────────────────────────────


def _strip_html(text: str) -> str:
    """去除 HTML 標籤並壓縮空白，優先擷取 article 區塊。"""
    m = re.search(r"<article[^>]*>(.*?)</article>", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    text = re.sub(r"<(style|script|noscript)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _is_excluded(site_name: str) -> bool:
    """檢查 site_name 是否在排除清單中。"""
    lower = (site_name or "").lower().strip()
    return any(exc in lower for exc in EXCLUDE_SITES)


def _is_seeking_alpha(site_name: str) -> bool:
    return SEEKING_ALPHA_KEY in (site_name or "").lower()


def _is_rss_whitelisted(site_name: str) -> bool:
    """RSS 來源是否在白名單中。"""
    lower = (site_name or "").lower().strip()
    return any(w in lower for w in RSS_WHITELIST)


def _doc_to_row(doc: dict) -> list[str]:
    """將 Reader 文件轉為 Sheet 行。"""
    updated = (doc.get("updated_at", "") or "")[:10]
    category = doc.get("category", "unknown")
    author = doc.get("author", "") or ""
    title = doc.get("title", "") or "Untitled"
    source_url = doc.get("source_url", "") or ""
    if source_url.startswith("mailto:"):
        source_url = ""
    summary = (doc.get("summary", "") or "").replace("\n", " ").strip()
    if len(summary) > 500:
        summary = summary[:497] + "..."
    return [updated, category, author, title, source_url, summary, ""]


def _ensure_sheet_exists(service, spreadsheet_id: str, sheet_name: str):
    """確保工作表存在，不存在則建立。"""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = [s["properties"]["title"] for s in meta.get("sheets", [])]
    if sheet_name not in existing:
        body = {
            "requests": [
                {"addSheet": {"properties": {"title": sheet_name}}}
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()
        # 寫 header
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption="RAW",
            body={"values": [HEADER_ROW]},
        ).execute()
        print(f"[reader-to-sheets] 建立工作表：{sheet_name}")


def _get_existing_titles(service, spreadsheet_id: str, sheet_name: str) -> set[str]:
    """讀取工作表中已存在的標題（D 欄）。"""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!D:D",
    ).execute()
    values = result.get("values", [])
    return {row[0].strip().lower() for row in values if row}


def _append_rows(service, spreadsheet_id: str, sheet_name: str, rows: list[list[str]]):
    """批次 append 行到工作表。"""
    if not rows:
        return
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


# ── LLM 摘要 + 分類 ─────────────────────────────────────


def _parse_llm_enrichment(response: str, expected_count: int) -> list[tuple[str, str]]:
    """解析 LLM 回應，提取中文摘要和主題分類。"""
    results = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("<"):
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            summary_zh = "|".join(parts[1:-1]).strip()
            topic = parts[-1].strip()
            if topic not in TOPIC_CATEGORIES:
                topic = "其他"
            results.append((summary_zh, topic))
    while len(results) < expected_count:
        results.append(("", "其他"))
    return results[:expected_count]


def _fetch_url_content(url: str, max_chars: int = 1500) -> str:
    """嘗試抓取 URL 網頁內容，去 HTML 後截斷。"""
    if not url or not url.startswith("http"):
        return ""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        return _strip_html(raw)[:max_chars]
    except Exception:
        return ""


def _enrich_rows_with_llm(rows: list[list[str]], batch_size: int = 5) -> list[list[str]]:
    """用 LLM 為每篇文章產生中文摘要和主題分類（盡量抓全文）。"""
    from lib.llm import ask_claude

    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"[reader-to-sheets] LLM batch {batch_num}/{total_batches}（{len(batch)} 篇）...")

        # 嘗試用 source_url 抓原文
        articles = []
        fetched = 0
        for j, row in enumerate(batch):
            source_url = row[4]
            content = _fetch_url_content(source_url)
            if content:
                fetched += 1

            entry = f"{j+1}. 標題: {row[3]} / 作者: {row[2]}"
            if content:
                entry += f"\n   內容摘錄: {content}"
            elif row[5]:
                entry += f" / 原摘要: {row[5]}"
            articles.append(entry)

        if fetched:
            print(f"[reader-to-sheets]   抓到 {fetched}/{len(batch)} 篇全文")

        prompt = (
            f"以下是 {len(batch)} 篇文章，請為每篇提供繁體中文摘要和主題分類。\n\n"
            "摘要要求：2-3 句，約 100-150 字，包含核心論點和為什麼值得看。\n"
            "主題分類只能從以下選擇：技術、生產力、職涯、創作、投資、產業、生活、其他\n\n"
            "回覆格式（嚴格遵守，每篇一行，不要加任何其他文字）：\n"
            "編號|中文摘要|主題分類\n\n"
            "範例：\n"
            "1|這篇探討 AI 輔助開發的實戰經驗，作者分享三個月內將程式碼審查時間縮短 40% 的具體做法，特別值得注意的是 prompt engineering 在 code review 場景的應用思路。|技術\n"
            "2|作者從遠端工作五年的經驗出發，歸納時間管理五大法則，其中「異步溝通優先」和「深度工作時段保護」對知識工作者特別有參考價值。|生產力\n\n"
            "文章列表：\n" + "\n".join(articles)
        )

        try:
            response = ask_claude(prompt)
            results = _parse_llm_enrichment(response, len(batch))
            for j, row in enumerate(batch):
                if j < len(results):
                    summary_zh, topic = results[j]
                    if summary_zh:
                        row[5] = summary_zh
                    row[6] = topic
        except Exception as e:
            print(f"[reader-to-sheets] LLM batch {batch_num} 失敗: {e}，保留原摘要")

    return rows


def _update_header_if_needed(service, spreadsheet_id: str, sheet_name: str):
    """如果既有工作表缺少「主題」欄，補上 header。"""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!1:1",
    ).execute()
    header = result.get("values", [[]])[0]
    if "主題" not in header:
        col_letter = chr(ord("A") + len(header))
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!{col_letter}1",
            valueInputOption="RAW",
            body={"values": [["主題"]]},
        ).execute()
        print(f"[reader-to-sheets] 更新 {sheet_name} header：加入「主題」欄")


# ── 主邏輯 ────────────────────────────────────────────


def sync_to_sheets(days: int = 7, since: str | None = None, dry_run: bool = False, use_llm: bool = True):
    """從 Reader API 拉資料並寫入 Google Sheet。"""

    if not GOOGLE_SHEET_ID:
        print("[reader-to-sheets] GOOGLE_SHEET_ID 未設定。請在 .env 中加入。", file=sys.stderr)
        sys.exit(1)

    if not check_readwise_setup():
        sys.exit(1)

    # 計算日期範圍（Reader API 需要完整 ISO 8601）
    if since:
        updated_after = f"{since}T00:00:00"
    else:
        updated_after = (datetime.now() - timedelta(days=days)).isoformat()

    print(f"[reader-to-sheets] 拉取 {updated_after} 之後的內容...")

    # 拉 email + podcast + rss
    all_docs = []
    for cat in ("email", "podcast", "rss"):
        print(f"[reader-to-sheets] 拉取 {cat}...")
        docs = reader_list(category=cat, updated_after=updated_after, fetch_all=True)
        print(f"[reader-to-sheets]   {cat}: {len(docs)} 篇")
        for doc in docs:
            doc["_category"] = cat
        all_docs.extend(docs)

    # 分類
    main_rows = []
    sa_rows = []
    skipped_exclude = 0
    skipped_dup = 0

    # email 先處理（去重用）
    email_docs = [d for d in all_docs if d["_category"] == "email"]
    other_docs = [d for d in all_docs if d["_category"] != "email"]

    seen_titles: set[str] = set()

    for doc in email_docs:
        site = doc.get("site_name", "") or ""
        if _is_excluded(site):
            skipped_exclude += 1
            continue
        title_lower = (doc.get("title", "") or "").strip().lower()
        seen_titles.add(title_lower)
        row = _doc_to_row(doc)
        if _is_seeking_alpha(site):
            sa_rows.append(row)
        else:
            main_rows.append(row)

    skipped_rss_nowhitelist = 0

    for doc in other_docs:
        site = doc.get("site_name", "") or ""
        if _is_excluded(site):
            skipped_exclude += 1
            continue
        # RSS 走白名單（podcast 全收）
        if doc["_category"] == "rss" and not _is_seeking_alpha(site) and not _is_rss_whitelisted(site):
            skipped_rss_nowhitelist += 1
            continue
        title_lower = (doc.get("title", "") or "").strip().lower()
        if title_lower in seen_titles:
            skipped_dup += 1
            continue
        seen_titles.add(title_lower)
        row = _doc_to_row(doc)
        if _is_seeking_alpha(site):
            sa_rows.append(row)
        else:
            main_rows.append(row)

    print(f"\n[reader-to-sheets] 結果：")
    print(f"  主工作表：{len(main_rows)} 篇")
    print(f"  Seeking Alpha：{len(sa_rows)} 篇")
    print(f"  排除（黑名單）：{skipped_exclude} 篇")
    print(f"  排除（RSS 非白名單）：{skipped_rss_nowhitelist} 篇")
    print(f"  去重：{skipped_dup} 篇")

    if dry_run:
        print("\n[reader-to-sheets] --dry-run 模式，不寫入 Sheet")
        return

    # 寫入 Google Sheet
    service = get_sheets_service()
    if not service:
        sys.exit(1)

    sheet_id = GOOGLE_SHEET_ID

    # 確保工作表存在 + header 更新
    _ensure_sheet_exists(service, sheet_id, "Readings")
    _ensure_sheet_exists(service, sheet_id, "Seeking Alpha")
    _update_header_if_needed(service, sheet_id, "Readings")
    _update_header_if_needed(service, sheet_id, "Seeking Alpha")

    # 讀取已存在的標題避免重複寫入
    existing_main = _get_existing_titles(service, sheet_id, "Readings")
    existing_sa = _get_existing_titles(service, sheet_id, "Seeking Alpha")

    new_main = [r for r in main_rows if r[3].strip().lower() not in existing_main]
    new_sa = [r for r in sa_rows if r[3].strip().lower() not in existing_sa]

    print(f"\n[reader-to-sheets] 新增（去除 Sheet 已存在）：")
    print(f"  主工作表：{len(new_main)} 篇")
    print(f"  Seeking Alpha：{len(new_sa)} 篇")

    # LLM 摘要 + 分類（只處理新增的）
    if use_llm and (new_main or new_sa):
        print("\n[reader-to-sheets] 開始 LLM 中文摘要 + 主題分類...")
        if new_main:
            new_main = _enrich_rows_with_llm(new_main)
        if new_sa:
            new_sa = _enrich_rows_with_llm(new_sa)

    _append_rows(service, sheet_id, "Readings", new_main)
    _append_rows(service, sheet_id, "Seeking Alpha", new_sa)

    print(f"\n[reader-to-sheets] 完成！")


# ── CLI ───────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Reader → Google Sheets 同步")
    parser.add_argument("--days", type=int, default=7, help="拉取過去 N 天（預設 7）")
    parser.add_argument("--since", type=str, default=None, help="拉取指定日期後 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="預覽不寫入")
    parser.add_argument("--no-llm", action="store_true", help="跳過 LLM 摘要/分類")
    args = parser.parse_args()

    sync_to_sheets(days=args.days, since=args.since, dry_run=args.dry_run, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
