# Reader → Google Sheets Tasks

## Section A：Google Sheets 基礎設施
- [x] A1. google_api.py 加 Sheets scope + get_sheets_service()
- [x] A2. config.py 加 GOOGLE_SHEET_ID
- [x] A3. .env.example 加 GOOGLE_SHEET_ID 說明
- [x] A4. GCP 啟用 Sheets API + 刪 token 重新授權

## Section B：reader_to_sheets.py
- [x] B1. 建立 scripts/collectors/reader_to_sheets.py — 主邏輯
- [x] B2. 排除清單 + RSS 白名單 config
- [x] B3. 去重邏輯（email 先寫，RSS skip 已存在 title）
- [x] B4. Seeking Alpha 獨立工作表
- [x] B5. bin/agent 加 reader-to-sheets 子指令
- [x] B6. dry-run 測試通過（986 主 + 281 SA + 963 排除 + 68 非白名單 + 34 去重）
- [x] B7. 真實寫入測試（978 主 + 281 SA 已寫入）

## Section B+：reader_to_sheets 增強
- [x] B+1. LLM 中文摘要（取代 Reader 的英文 summary）
- [x] B+2. LLM 主題分類（技術/生產力/職涯/創作/投資/產業/生活/其他）
- [x] B+3. email 的 source_url 為空（已處理 mailto: 清除）
- [x] B+4. Sheet 欄位更新：加「主題」欄 + 既有 Sheet 自動 migration

## Section C：daily-digest.py 改版
- [ ] C1. 新增 _collect_from_sheet() 讀 Sheet 指定日期的行
- [ ] C2. 用 Reader API 拿全文（by URL）
- [ ] C3. _collect_readings() 改為 Sheet 優先 + 本地 fallback
- [ ] C4. 測試：跑一次 daily-digest，確認產出正常

## Section D：收尾
- [ ] D1. 更新 CLAUDE.md CLI 速查表
- [ ] D2. launchd 排程（每日自動跑 reader-to-sheets）
- [ ] D3. Git commit
