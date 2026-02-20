# Phase 6 P1 Tasks — 會議 / 諮詢 / 專案狀態 / Classroom / Fireflies

## Section A：基礎設施（Config + 模板 + 測試資料） ✅ `e51cd94`

- [x] 更新 `scripts/lib/config.py` 加入 MEETINGS_DIR / CONSULTATIONS_DIR / PROJECTS_SOFTWARE_DIR / PROJECTS_PRODUCTS_DIR + FIREFLIES_API_KEY
- [x] 建立 `800_System/templates/meeting-notes-template.md`
- [x] 建立 `800_System/templates/project-status-template.md`
- [x] 建立 `400_Projects/software/dex-agent-os/STATUS.md`（測試用）
- [x] 建立 `tests/fixtures/sample-transcript.txt`（測試用逐字稿）
- [x] 建立 `tests/fixtures/sample-consultation-notes.txt`（測試用諮詢筆記）
- [x] 驗證：`python3 -c "from scripts.lib.config import MEETINGS_DIR; print(MEETINGS_DIR)"`
- [x] Commit Section A

## Section B：Google Classroom Collector + Google Docs Reader ✅ `76f3c18`

- [x] 更新 `scripts/lib/google_api.py`：SCOPES 加老師用 classroom scope + `get_classroom_service()` + `read_google_doc(url)` helper
- [x] 建立 `scripts/collectors/classroom_sync.py`（--courses / --active-only / --student-name / --announcements / --coursework / --latest N）
- [x] 更新 `bin/agent` 加 `classroom-sync` 子命令
- [x] 驗證：`python3 -c "import scripts.collectors.classroom_sync"` 無錯誤
- [x] 驗證：`./bin/agent classroom-sync --courses` 可列出課程（需刪 token 重新授權）
- [x] Commit Section B

## Section C1：Fireflies.ai Collector（graceful fallback） ✅ `be5d648`

- [x] 建立 `scripts/lib/fireflies_api.py`（GraphQL API 封裝：list_transcripts / get_transcript，未設定 token 時優雅 fallback）
- [x] 建立 `scripts/collectors/fireflies_sync.py`（--list / --latest N → 200_Work/meetings/）
- [x] 更新 `bin/agent` 加 `fireflies-sync` 子命令
- [x] 更新 `config/.env.example` 加 FIREFLIES_API_KEY 說明
- [x] 驗證：`python3 -c "import scripts.collectors.fireflies_sync"` 無錯誤
- [x] 驗證：`./bin/agent fireflies-sync --list`（無 token 時顯示 setup 引導）
- [x] Commit Section C1

## Section C2：共用 Input Loader + Meeting Notes + Consultation Notes Generator ✅ `b97897b`

- [x] 建立 `scripts/lib/input_loader.py`（load_from_transcript / load_from_notes / load_from_google_doc / load_from_fireflies / load_input）
- [x] 建立 `scripts/generators/meeting_notes.py`（使用 input_loader，--transcript / --notes / --google-doc / --fireflies / --title / --date / --attendees）
- [x] 建立 `scripts/generators/consultation_notes.py`（使用 input_loader，--transcript / --notes / --google-doc / --fireflies / --title / --person / --direction / --date）
- [x] 更新 `bin/agent` 加 `meeting-notes` + `consultation-notes` 子命令
- [x] 驗證：`python3 -c "import scripts.lib.input_loader"` 無錯誤
- [x] 驗證：`python3 -c "import scripts.generators.meeting_notes"` 無錯誤
- [x] 驗證：`python3 -c "import scripts.generators.consultation_notes"` 無錯誤
- [x] 驗證：`./bin/agent meeting-notes --transcript tests/fixtures/sample-transcript.txt --title "Test"` 產出正確路徑
- [x] 驗證：`./bin/agent meeting-notes --notes "重點" --title "Test"` 產出正確路徑
- [x] 驗證：`./bin/agent consultation-notes --notes "問題" --title "Test" --person "Alice"` 產出正確路徑
- [x] Commit Section C2

## Section D：Project Status Generator ✅ `be2f7e7`

- [x] 建立 `scripts/generators/project_status.py`（讀 STATUS.md + DECISIONS.md + git log → LLM 更新）
- [x] 更新 `bin/agent` 加 `project-status` 子命令
- [x] 驗證：`python3 -c "import scripts.generators.project_status"` 無錯誤
- [x] 驗證：`./bin/agent project-status dex-agent-os` 用測試用 STATUS.md 產出更新
- [x] Commit Section D

## Section E：Workflows + Skills + 文件 + 收尾 ✅

- [x] 建立 `canonical/workflows/meeting-notes.md`
- [x] 建立 `canonical/workflows/consultation-notes.md`
- [x] 建立 `canonical/workflows/project-status.md`
- [x] 建立 `canonical/workflows/classroom-sync.md`
- [x] 建立 `canonical/workflows/fireflies-sync.md`
- [x] 建立 `.claude/commands/meeting-notes.md`（IDE skill）
- [x] 建立 `.claude/commands/consultation-notes.md`（IDE skill）
- [x] 建立 `.claude/commands/project-status.md`（IDE skill）
- [x] 建立 `.claude/commands/classroom-sync.md`（IDE skill）
- [x] 建立 `.claude/commands/fireflies-sync.md`（IDE skill）
- [x] 執行 `bin/sync` 同步到 .agent/ + .cursor/
- [x] 更新 `CLAUDE.md` CLI 速查表
- [x] 更新 `GUIDE.md` 加 Phase 6 使用說明（含轉錄工具整合對照表）
- [x] 更新 `PLAN.md` Phase 6 任務狀態
- [x] 更新 `MEMORY.md`
- [x] 驗證：`./bin/agent help` 顯示所有新指令
- [x] 驗證：`bin/sync` 無錯誤
- [x] Commit Section E（`fa430cf`）
- [x] 產出 `walkthrough.md`

## Section F：Work-log 整合 ✅

- [x] 建立 `work-log/scripts/scan-work-outputs.py`（掃描 meetings/consultations/projects，輸出 markdown 參考清單）
- [x] 修改 `~/.claude/commands/work-log.md`（加 Step 3.9 + 工作紀錄產出 section）
- [x] 修改 `work-log/templates/daily-template.md`（加「工作紀錄產出」section）
- [x] 驗證：`scan-work-outputs.py --date 2026-02-20` 正確掃描三種資料
- [x] 驗證：空日期回傳「該日無」訊息
- [x] 更新 `PLAN.md` + `GUIDE.md`
