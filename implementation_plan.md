# Sync 架構改版 — Sheet + Notion 雙軌寫入

## 目標

所有 sync 統一寫入 Google Sheet（摘要）+ Notion（全文），停止寫本地 `000_Inbox/readings/`。

## 架構（Before → After）

```
Before:
  readwise-sync → 000_Inbox/readings/ (本地)
  rss-sync      → 000_Inbox/readings/ (本地，需手動 --feed)
  anybox-sync   → 000_Inbox/readings/ (本地，需 app 開啟)
  gmail-sync    → 000_Inbox/readings/ (本地，含垃圾信)
  reader-to-sheets → Google Sheet (獨立)

After:
  reader-to-sheets → ┬→ Google Sheet (摘要+分類)
  rss-to-sheets    → ┤→ Notion (全文+筆記)
  gmail-to-sheets  → ┤
  anybox-to-sheets → ┘

  readwise-sync    → 退役留存
  舊 rss-sync      → 退役留存（改用 rss-to-sheets）
  舊 gmail-sync    → 退役留存（改用 gmail-to-sheets）
  舊 anybox-sync   → 退役留存（改用 anybox-to-sheets）
  本地 readings/   → 不再寫入，保留既有檔案做 fallback
```

## 雙軌儲存策略

| | Google Sheet | Notion |
|---|---|---|
| 存什麼 | 日期/分類/作者/標題/URL/中文摘要/主題 | 同上 + **全文** |
| 用途 | 快速瀏覽、篩選、自動化入口 | 深度閱讀、跨裝置、個人筆記 |
| 讀取者 | daily-digest、/轉譯 | Dex 手動閱讀 |

## 全文策略

- Sheet 只存摘要（100-150 字中文）— 瀏覽、篩選、分類
- Notion 存全文 — 深度閱讀、標註
- /轉譯 寫文時用 source_url 即時抓全文（已實作）
- 不預存全文到本地

## 改動範圍

### Phase 1：四管寫 Sheet + Notion

#### A. rss-to-sheets — RSS 一鍵自動化
1. 建立 `config/rss-feeds.txt`（預設 feed URL 清單，一行一個）
2. 新建 `scripts/collectors/rss_to_sheets.py`
3. 讀 feeds.txt → 抓每個 feed → 過濾 → 寫入 Sheet「Readings」
4. LLM 中文摘要 + 主題分類（複用 `_enrich_rows_with_llm`）
5. 同時寫 Notion（全文）
6. `bin/agent rss-to-sheets [--no-llm] [--dry-run]`

#### B. gmail-to-sheets — 電子報過濾寫 Sheet
1. 新建 `scripts/collectors/gmail_to_sheets.py`
2. Gmail 過濾：排除促銷寄件者 + subject 關鍵字排除
3. 寫入 Sheet「Readings」+ Notion（全文）
4. LLM 中文摘要 + 主題分類
5. `bin/agent gmail-to-sheets [--days N] [--no-llm] [--dry-run]`

#### C. anybox-to-sheets — Anybox 書籤寫 Sheet
1. 新建 `scripts/collectors/anybox_to_sheets.py`
2. 讀 Anybox API（需 app 開啟）→ 寫 Sheet「Readings」+ Notion
3. LLM 中文摘要 + 主題分類
4. `bin/agent anybox-to-sheets [--no-llm] [--dry-run]`
5. Anybox 未開啟 → graceful skip

#### D. reader-to-sheets 加 Notion 寫入
1. 既有 reader-to-sheets 加 Notion 同步（寫全文）
2. 複用共用 Notion 寫入模組

#### E. 共用模組：Notion 寫入層
1. 新建 `scripts/lib/notion_api.py`（或擴充既有）
2. `write_to_notion(items)` — 批次寫入 Notion database
3. Notion DB 結構：日期 / 分類 / 作者 / 標題 / URL / 中文摘要 / 主題 / 全文
4. `.env` 加 `NOTION_DATABASE_ID`
5. 去重：Notion 內 title 比對

#### F. sync-all 瘦身 + daily-all 更新
1. `sync-all` 改為：
   - `reader-to-sheets --days 2 --no-llm`
   - `rss-to-sheets --no-llm`
   - `gmail-to-sheets --days 2 --no-llm`
   - `anybox-to-sheets --no-llm`
2. daily-all 更新（用新版 sync-all）

#### G. 退役舊 sync
1. readwise-sync / 舊 rss-sync / 舊 gmail-sync / 舊 anybox-sync 加 deprecation 提示
2. 程式碼保留不刪

#### H. 收尾
1. CLAUDE.md / GUIDE.md / PLAN.md 更新
2. 本地 readings/ 停止寫入（fallback 保留）
3. 測試完整 daily-all 流程

## 不做的事

- 不改 youtube-add / podcast-add / learning-note（寫 300_Learning/）
- 不改 fireflies-sync / classroom-sync（寫 200_Work/）
- 不刪既有程式碼和本地檔案

## 風險

- Reader token 失效 → rss-to-sheets + gmail-to-sheets 雙保險
- Anybox app 未開啟 → graceful skip，不影響其他 sync
- Notion API rate limit（3 req/sec）→ 批次寫入 + sleep
- RSS feed URL 需維護 → config/rss-feeds.txt 方便增減
