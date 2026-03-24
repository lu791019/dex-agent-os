# Reader → Google Sheets + Daily Digest 改版

## 目標
用 Google Sheet 取代本地 `000_Inbox/readings/` 作為閱讀內容的目錄層，Reader API 作為全文倉庫。

## 架構
```
reader-to-sheets（每週/手動）: Reader API → 過濾+去重 → Google Sheet
daily-digest（每日改版）:     Sheet 讀清單 → Reader API 拿全文 → LLM → digest
```

## 改動範圍

### Section A：Google Sheets 基礎設施
1. `google_api.py` — 加 Sheets scope + `get_sheets_service()` helper
2. `config.py` — 加 `GOOGLE_SHEET_ID` 環境變數
3. `.env.example` — 加 `GOOGLE_SHEET_ID` 說明

> 決策：用 `google-api-python-client` 的 Sheets API（已裝），不另裝 gspread。

### Section B：reader_to_sheets.py（新腳本）
1. 從 Reader API v3 拉 email（全部）+ podcast（全部）+ rss（白名單）
2. 去重：email 先寫，RSS skip 已存在的 title
3. Seeking Alpha 寫入獨立工作表
4. 排除清單過濾
5. 每篇一行：日期 / 來源分類 / 作者 / 標題 / 來源URL / 摘要
6. bin/agent 加 `reader-to-sheets` 子指令

### Section C：daily-digest.py 改版
1. 新增 `_collect_from_sheet()` — 從 Google Sheet 讀指定日期的行
2. 對需要全文的項目，用 Reader API 的 URL 查詢拿 content
3. 保留 `300_Learning/input/`、`youtube/`、`podcasts/` 的掃描（不在 Sheet 裡）
4. `_collect_readings()` 改為優先讀 Sheet，fallback 到本地（過渡期）

### Section D：收尾
1. 更新 CLAUDE.md CLI 速查表
2. 更新 .env.example
3. GCP 啟用 Sheets API + 刪 token 重新授權（加了 scope）

## 不做的事
- 不改 readwise-sync / rss-sync / gmail-sync（保留但不再是主要路徑）
- 不刪 000_Inbox/readings/（留著 fallback）
- 不改 daily-all 的串接（digest 內部改，外部介面不變）

## 風險
- Reader 已退訂，token 壽命不確定 → Section C 保留本地 fallback
- Google OAuth scope 變更需刪 token 重新授權
- Sheets API 有 60 req/min 限制 → 批次寫入（一次 append 多行）
