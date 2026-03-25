# Sync 架構改版 Tasks — Sheet + Notion 雙軌

## Section A：rss-to-sheets（RSS 一鍵自動化）
- [x] A1. 建立 config/rss-feeds.txt（15 個 feed）
- [x] A2. 新建 scripts/collectors/rss_to_sheets.py
- [x] A3. 抓 feed → 過濾 → 寫入 Sheet（Notion 待 Section E）
- [x] A4. LLM 中文摘要 + 主題分類（內建，--no-llm 可跳過）
- [x] A5. bin/agent 加 rss-to-sheets 子指令
- [x] A6. dry-run 29 篇 + 真實寫入 27 篇 ✅

## Section B：gmail-to-sheets（電子報過濾）
- [x] B1. 新建 scripts/collectors/gmail_to_sheets.py
- [x] B2. Gmail 過濾：排除 16 寄件者 + 1 主旨（可微調）
- [x] B3. 寫入 Sheet（Notion 待 Section E）
- [x] B4. LLM 中文摘要 + 主題分類（內建，--no-llm 可跳過）
- [x] B5. bin/agent 加 gmail-to-sheets 子指令
- [x] B6. dry-run 83 封 + 真實寫入 81 封 ✅

## Section C：anybox-to-sheets（書籤同步）
- [x] C1. 新建 scripts/collectors/anybox_to_sheets.py
- [x] C2. Anybox API → Sheet（Notion 待 Section E）+ graceful skip ✅
- [x] C3. LLM 中文摘要 + 主題分類（內建）
- [x] C4. bin/agent 加 anybox-to-sheets 子指令
- [x] C5. 測試：app 未開 → graceful skip ✅

## Section D：reader-to-sheets 加 Notion
- [ ] D1. 既有 reader-to-sheets 加 Notion 同步寫入

## Section E：共用模組 — Notion 寫入層
- [ ] E1. 新建 scripts/lib/notion_api.py（write_to_notion）
- [ ] E2. Notion DB 結構設計 + .env 加 NOTION_DATABASE_ID
- [ ] E3. 去重邏輯（title 比對）

## Section F：sync-all + daily-all 更新
- [ ] F1. sync-all 改為 reader-to-sheets + rss-to-sheets + gmail-to-sheets + anybox-to-sheets
- [ ] F2. daily-all 更新

## Section G：退役舊 sync
- [ ] G1. readwise-sync / 舊 rss-sync / 舊 gmail-sync / 舊 anybox-sync 加 deprecation
- [ ] G2. 本地 readings/ 停止寫入

## Section H：收尾
- [ ] H1. CLAUDE.md / GUIDE.md / PLAN.md 更新
- [ ] H2. 測試完整 daily-all
- [ ] H3. Git commit
