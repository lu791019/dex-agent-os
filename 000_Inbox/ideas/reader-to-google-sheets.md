---
date: 2026-03-22
status: planned
---

# Reader → Google Sheets 週報

## 目標

每 7 天從 Readwise Reader API 抓取閱讀內容，過濾後寫入 Google Sheet，作為雲端備份 + 瀏覽入口。

## 過濾策略

| 分類 | 規則 | 預估量/週 |
|------|------|-----------|
| email | 全部 | ~150 篇 |
| podcast | 全部 | ~140 篇 |
| rss | 白名單作者 | ~50 篇 |

### RSS 白名單（待確認）

- ByteByteGo
- Ben Thompson
- Pragmatic Engineer
- 瓦基
- freeCodeCamp
- Neo Kim
- （Dex 補充）

## API 觀察（2026-03-22）

過去 7 天 Reader API v3 回傳 2,331 篇：
- rss: 2,035（高噪音：Reddit bot 100、Seeking Alpha 183、GCP release notes 29）
- email: 153（Substack 電子報為主）
- podcast: 143（TED 29、報導者 8、How I Built This 8）

## Google Sheet 欄位

| 欄位 | 來源 |
|------|------|
| 日期 | `saved_at` 或 `updated_at` |
| 分類 | `category`（email/podcast/rss） |
| 作者 | `author` |
| 標題 | `title` |
| 來源 URL | `source_url` |
| 摘要 | `summary` 前 200 字 |
| 站名 | `site_name` |

## 技術依賴

- `READWISE_TOKEN`：已有（50 字元）
- `google_api.py`：需加 Google Sheets scope
- Python 套件：`gspread`（或直接 Google Sheets API）
- OAuth：已有 GCP 專案，需在 API Library 啟用 Sheets API

## 實作清單

1. `google_api.py` 加 Sheets scope
2. 新建 `scripts/collectors/reader_to_sheets.py`（~80 行）
3. `bin/agent` 加 `reader-weekly` 子指令
4. `config/.env.example` 加 `GOOGLE_SHEET_ID`
5. 測試：跑一次確認 Sheet 產出
6. 可選：加入 `/daily-all` 或獨立排程

## 不做的事

- 不存全文到 Sheet（太長，只存摘要）
- 不取代本地 `000_Inbox/readings/`（那是 sync-all 的產出，獨立運作）
- 不做即時同步（週批次就好）
