---
description: Fireflies Sync — Fireflies.ai 會議逐字稿同步，匯入或列出會議記錄
alwaysApply: false
---

# Fireflies Sync — Fireflies.ai 會議逐字稿同步

從 Fireflies.ai 同步會議逐字稿，供 meeting-notes 或 consultation-notes 使用。

## 觸發方式

- 指令：`./bin/agent fireflies-sync`
- 指令：`./bin/agent fireflies-sync --latest 5 --force`
- IDE 內：`/fireflies-sync`

## 輸入來源

1. **Fireflies GraphQL API**：透過 `fireflies_collector.py`
2. **篩選參數**：
   - `--latest N` — 最新 N 場會議（預設：列出最近 10 場）
   - `--days N` — 最近 N 天的會議（預設：7）
   - `--meeting-id <id>` — 指定會議 ID
   - `--search "關鍵字"` — 搜尋會議標題

## 處理邏輯

1. 呼叫 Fireflies GraphQL API 列出會議
2. 根據篩選條件取得會議清單
3. 對每場會議擷取：
   - 會議標題、日期、時長、參與者
   - 逐字稿全文
   - AI 摘要（如 Fireflies 有提供）
4. 轉換為 Markdown 格式
5. 無 LLM，純 API 擷取

## 輸出

- 路徑：`000_Inbox/transcripts/YYYY-MM-DD-fireflies-<title-slug>.md`
- frontmatter：title / date / duration / attendees / source:fireflies / type:transcript
- 列表模式（無 `--force`）只顯示會議清單不寫檔

## Graceful Fallback

- API key 未設定 → 提示設定方式，不報錯
- API 回傳錯誤 → 顯示錯誤訊息，繼續處理其他會議
- 逐字稿為空 → 跳過該會議，記錄 warning

## 前置需求

- `.env` 中設定 `FIREFLIES_API_KEY`（從 Fireflies.ai Settings → API 取得）
- 免費方案有 API 限制，建議使用付費方案

## 搭配使用

匯入後可接：
- `meeting-notes --fireflies <id>` — 從逐字稿產出會議筆記
- `consultation-notes --fireflies <id>` — 從逐字稿產出諮詢紀錄
