# Phase 5d — 任務追蹤

> 對應計畫：`implementation_plan_phase5d.md`
> **狀態：已完成** — 2026-02-19 merged to master

---

## Section A：資料夾建立 + 檔案搬遷

- [x] A1. 建立 `510_Insights/`、`520_Topics/`、`530_Channels/` 及子目錄
- [x] A2. 搬遷 `500_Content/insights/*.md` → `510_Insights/`（~30 篇，用 `git mv`）
- [x] A3. 搬遷 `500_Content/topics/<slug>/TOPIC.md` → `520_Topics/<slug>/TOPIC.md`（4 個）
- [x] A4. 搬遷 topic 內的 threads-draft.md → `530_Channels/threads/YYYY-MM-DD/<slug>.md`（4 篇）
- [x] A5. 搬遷 `/daily-content` 產出的散檔 → `530_Channels/threads/YYYY-MM-DD/<slug>.md`（~24 篇）
- [x] A6. 搬遷其他頻道內容（newsletter/podcast/presentations 等，有內容就搬）
- [x] A7. 刪除空的 `500_Content/` 目錄
- [x] A8. Commit：`971a438` refactor: restructure 500_Content → 510/520/530

---

## Section B：config.py + 腳本路徑更新

- [x] B1. 更新 `scripts/lib/config.py` 路徑常數（INSIGHTS_DIR / TOPICS_DIR / CHANNELS_DIR / 各頻道 DIR）
- [x] B2. 更新 `topic_create.py` 輸出路徑 → `520_Topics/`
- [x] B3. 更新 `topic_to_thread.py` 輸出路徑 → `530_Channels/threads/YYYY-MM-DD/`
- [x] B4. 更新 `topic_to_fb.py` 輸出路徑 → `530_Channels/facebook/YYYY-MM-DD/`
- [x] B5. 更新 `topic_to_blog.py` 輸出路徑 → `530_Channels/blog/YYYY-MM-DD/`
- [x] B6. 更新 `topic_to_short_video.py` 輸出路徑 → `530_Channels/short-video/YYYY-MM-DD/`
- [x] B7. 更新 `film_review.py` 輸出路徑 → `530_Channels/film-reviews/YYYY-MM-DD/`
- [x] B8. 更新 `journal_knowledge_extract.py` insights 輸出路徑 → `510_Insights/`
- [x] B9. 更新 `weekly_newsletter.py` 輸出路徑 → `530_Channels/newsletter/`
- [x] B10. 更新 `podcast_digest.py` 簡報輸出路徑 → `530_Channels/presentations/`（config 自動解析，無需改動）
- [x] B11. 逐一測試每個 generator（9/9 import 驗證通過）
- [x] B12. Commit：`1da19ff` refactor: update all generator output paths to 510/520/530

---

## Section C：sync-all 指令

- [x] C1. `bin/agent` 加入 `sync-all` 子命令（readwise + rss + anybox + gmail）
- [x] C2. 加入 help text
- [x] C3. 測試 `./bin/agent sync-all`（help 確認指令存在）
- [x] C4. Commit：`9fa4945` feat: add sync-all command for batch import

---

## Section D：`/daily-content` 改造

- [x] D1. 重寫 `.claude/commands/daily-content.md`，改走 extract → topic-create → topic-to-thread 流程
- [x] D2. 確認 extract / topic-create / topic-to-thread 各自可獨立使用
- [x] D3. 端到端測試 `/daily-content 2026-02-19`（L2 → 3 insights → 3 topics → 3 threads 全部成功）
- [x] D4. Commit：`cbb6ffd` refactor: daily-content walks full insight→topic→draft pipeline

---

## Section E：文件更新 + 收尾

- [x] E1. 更新 `CLAUDE.md`（專案結構表 + CLI 速查表加 sync-all）
- [x] E2. 更新 `GUIDE.md`（30+ 處路徑替換 + 目錄樹 + sync-all + daily-content 新流程）
- [x] E3. 更新 `PLAN.md`（8 個區塊更新 + Phase 5d 標記完成）
- [x] E4. 更新 `canonical/rules/00-core.md`（檔案位置規則）
- [x] E5. 更新涉及路徑的 `canonical/workflows/*.md`（7 檔）+ `.claude/commands/*.md`（9 檔）
- [x] E6. 跑 `bin/sync` 同步到 IDE（.agent/ + .cursor/ 已更新）
- [x] E7. 更新 `MEMORY.md`
- [x] E8. Commit：`78934d6` docs: update all documentation for Phase 5d restructure
- [x] E9. Merge to master ✓
