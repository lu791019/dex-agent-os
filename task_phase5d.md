# Phase 5d — 任務追蹤

> 對應計畫：`implementation_plan_phase5d.md`

---

## Section A：資料夾建立 + 檔案搬遷

- [ ] A1. 建立 `510_Insights/`、`520_Topics/`、`530_Channels/` 及子目錄
- [ ] A2. 搬遷 `500_Content/insights/*.md` → `510_Insights/`（~30 篇，用 `git mv`）
- [ ] A3. 搬遷 `500_Content/topics/<slug>/TOPIC.md` → `520_Topics/<slug>/TOPIC.md`（4 個）
- [ ] A4. 搬遷 topic 內的 threads-draft.md → `530_Channels/threads/YYYY-MM-DD/<slug>.md`（4 篇）
- [ ] A5. 搬遷 `/daily-content` 產出的散檔 → `530_Channels/threads/YYYY-MM-DD/<slug>.md`（~24 篇）
- [ ] A6. 搬遷其他頻道內容（newsletter/podcast/presentations 等，有內容就搬）
- [ ] A7. 刪除空的 `500_Content/` 目錄
- [ ] A8. Commit：`refactor: restructure 500_Content → 510/520/530`

---

## Section B：config.py + 腳本路徑更新

- [ ] B1. 更新 `scripts/lib/config.py` 路徑常數（INSIGHTS_DIR / TOPICS_DIR / CHANNELS_DIR / 各頻道 DIR）
- [ ] B2. 更新 `topic_create.py` 輸出路徑 → `520_Topics/`
- [ ] B3. 更新 `topic_to_thread.py` 輸出路徑 → `530_Channels/threads/YYYY-MM-DD/`
- [ ] B4. 更新 `topic_to_fb.py` 輸出路徑 → `530_Channels/facebook/YYYY-MM-DD/`
- [ ] B5. 更新 `topic_to_blog.py` 輸出路徑 → `530_Channels/blog/YYYY-MM-DD/`
- [ ] B6. 更新 `topic_to_short_video.py` 輸出路徑 → `530_Channels/short-video/YYYY-MM-DD/`
- [ ] B7. 更新 `film_review.py` 輸出路徑 → `530_Channels/film-reviews/YYYY-MM-DD/`
- [ ] B8. 更新 `journal_knowledge_extract.py` insights 輸出路徑 → `510_Insights/`
- [ ] B9. 更新 `weekly_newsletter.py` 輸出路徑 → `530_Channels/newsletter/`
- [ ] B10. 更新 `podcast_digest.py` 簡報輸出路徑 → `530_Channels/presentations/`
- [ ] B11. 逐一測試每個 generator（乾跑或實跑確認路徑正確）
- [ ] B12. Commit：`refactor: update all generator output paths to 510/520/530`

---

## Section C：sync-all 指令

- [ ] C1. `bin/agent` 加入 `sync-all` 子命令（readwise + rss + anybox + gmail）
- [ ] C2. 加入 help text
- [ ] C3. 測試 `./bin/agent sync-all`（確認各 sync 正常跑或顯示引導）
- [ ] C4. Commit：`feat: add sync-all command for batch import`

---

## Section D：`/daily-content` 改造

- [ ] D1. 重寫 `.claude/commands/daily-content.md`，改走 extract → topic-create → topic-to-thread 流程
- [ ] D2. 確認 extract / topic-create / topic-to-thread 各自可獨立使用
- [ ] D3. 端到端測試 `/daily-content`（或用過去日期測試）
- [ ] D4. Commit：`refactor: daily-content walks full insight→topic→draft pipeline`

---

## Section E：文件更新 + 收尾

- [ ] E1. 更新 `CLAUDE.md`（專案結構表 + CLI 速查表加 sync-all）
- [ ] E2. 更新 `GUIDE.md`（目錄結構 + 管線流程圖 + sync-all 用法 + /daily-content 新流程）
- [ ] E3. 更新 `PLAN.md`（加入 Phase 5d 區段）
- [ ] E4. 更新 `canonical/rules/00-core.md`（檔案位置規則）
- [ ] E5. 更新涉及路徑的 `canonical/workflows/*.md`
- [ ] E6. 跑 `bin/sync` 同步到 IDE
- [ ] E7. 更新 `MEMORY.md`
- [ ] E8. Commit：`docs: update all documentation for Phase 5d restructure`
- [ ] E9. Merge to master
