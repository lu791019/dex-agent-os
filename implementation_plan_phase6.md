# Phase 6 P1 Implementation Plan — 會議 / 諮詢 / 專案狀態 / Classroom

## Goal Description

補齊 Phase 6 核心工作面功能：會議筆記、諮詢紀錄、專案狀態追蹤、Google Classroom 同步。
每項功能包含：模板 + workflow + Python generator/collector + CLI 指令 + IDE skill。
訂閱管理和 product 類留後續 Phase。

### 追加：Work-log 整合（Section F）

將會議筆記、諮詢紀錄、專案狀態更新整合進 `/work-log` L1 工作日誌流程：
- 新增 `work-log/scripts/scan-work-outputs.py`：掃描 `200_Work/meetings/`、`200_Work/consultations/`、`400_Projects/*/STATUS.md`
- 修改 `/work-log` skill（Step 3.9）呼叫掃描腳本，將參考清單（標題+路徑）加入 L1
- L2 精煉日記自然涵蓋「今天開了什麼會、諮詢了誰」

## User Review Required

> **NOTE**
> 1. Google Classroom API 需在 GCP 啟用 + 加 scope，首次執行須刪 `config/google-token.json` 重新授權（跟 Gmail 當時一樣）
> 2. Meeting notes 和 consultation notes 共用 `_load_input()` helper（抽到 `scripts/lib/input_loader.py`），差異只在 system prompt 和模板
> 3. Classroom 角色為**老師**：scope 用 `.students` 版本，支援 `--active-only` / `--student-name` 篩選
> 4. Classroom 資料歸類：課程公告/討論 → meetings/、作業回饋 → consultations/
> 5. Project status 掃描 `400_Projects/` 下指定專案，讀 STATUS.md + DECISIONS.md + git log
> 6. `--google-doc URL` 模式覆蓋 Tactiq / Scribbl 等 Chrome 外掛自動存到 Google Docs 的場景（零新依賴）
> 7. `--fireflies` 模式透過 Fireflies.ai GraphQL API 拉取逐字稿（需 Business plan $19/月）——目前無訂閱，先寫好程式碼 + graceful fallback
> 8. Otter.ai 無可用 API（Enterprise only），透過手動匯出 TXT 走 `--transcript FILE` 即可
> 9. Read.ai 僅 webhook（付費），目前不支援，未來可加

## 會議轉錄工具整合對照表

| 工具 | 免費額度 | 付費 | 整合方式 | 備註 |
|------|---------|------|---------|------|
| **Tactiq** | 10 會議/月 | $12/月 | `--google-doc URL` | 免費即可用，自動存 Google Docs |
| **Scribbl** | 15 會議/月 | $13/月 | `--google-doc URL` | 免費即可用，自動存 Google Docs |
| **Fireflies.ai** | 3 credits | $19/月 Business | `--fireflies` | GraphQL API，目前無訂閱，graceful fallback |
| **Otter.ai** | 300 分鐘/月 | $8.33/月 | `--transcript FILE` | 手動匯出 TXT，免費可用 |
| **Read.ai** | 5-10/月 | $15/月 | 未支援 | 僅 webhook，30 天刪除，不建議 |
| **Mac 聽寫** | 無限 | 免費 | `--transcript FILE` | 系統內建，零成本 |
| **Google Classroom** | — | — | `classroom-sync` | 獨立 collector，老師角色 |

## Proposed Changes

### Project Structure

```
新增檔案（~23 個）：
  800_System/templates/
    meeting-notes-template.md          [NEW] 會議筆記模板
    project-status-template.md         [NEW] 專案狀態模板

  400_Projects/software/dex-agent-os/
    STATUS.md                          [NEW] 測試用專案狀態檔

  tests/fixtures/
    sample-transcript.txt              [NEW] 測試用會議逐字稿
    sample-consultation-notes.txt      [NEW] 測試用諮詢筆記

  canonical/workflows/
    meeting-notes.md                   [NEW] 會議筆記 workflow
    consultation-notes.md              [NEW] 諮詢紀錄 workflow
    project-status.md                  [NEW] 專案狀態 workflow
    classroom-sync.md                  [NEW] Classroom 同步 workflow
    fireflies-sync.md                  [NEW] Fireflies 同步 workflow

  scripts/lib/
    input_loader.py                    [NEW] 共用輸入載入 helper（_load_input）
    fireflies_api.py                   [NEW] Fireflies.ai GraphQL API 封裝

  scripts/collectors/
    classroom_sync.py                  [NEW] Google Classroom API collector
    fireflies_sync.py                  [NEW] Fireflies.ai GraphQL API collector

  scripts/generators/
    meeting_notes.py                   [NEW] 會議筆記 generator
    consultation_notes.py              [NEW] 諮詢紀錄 generator
    project_status.py                  [NEW] 專案狀態 generator

  .claude/commands/
    meeting-notes.md                   [NEW] IDE skill
    consultation-notes.md              [NEW] IDE skill
    project-status.md                  [NEW] IDE skill
    classroom-sync.md                  [NEW] IDE skill
    fireflies-sync.md                  [NEW] IDE skill

修改檔案（~6 個）：
  scripts/lib/config.py               [MODIFY] 加 MEETINGS_DIR / CONSULTATIONS_DIR / PROJECTS_SOFTWARE_DIR / PROJECTS_PRODUCTS_DIR
  scripts/lib/google_api.py           [MODIFY] SCOPES 加 classroom（老師 scope）+ get_classroom_service() + read_google_doc()
  bin/agent                           [MODIFY] +5 子命令
  CLAUDE.md                           [MODIFY] CLI 速查表
  GUIDE.md                            [MODIFY] 使用說明
  PLAN.md                             [MODIFY] Phase 6 任務更新
```

### Components

#### A. 基礎設施（Config + 模板 + 測試資料）

- `[MODIFY] scripts/lib/config.py`
  新增路徑常數：MEETINGS_DIR、CONSULTATIONS_DIR、PROJECTS_SOFTWARE_DIR、PROJECTS_PRODUCTS_DIR
  新增 env var：FIREFLIES_API_KEY

- `[NEW] 800_System/templates/meeting-notes-template.md`
  會議筆記結構：基本資訊 → 與會者 → 討論要點 → 決策 → 行動項 → 後續追蹤

- `[NEW] 800_System/templates/project-status-template.md`
  專案狀態結構：基本資訊 → 目前進度 → 近期完成 → 進行中 → 風險/卡關 → 下一步

- `[NEW] 400_Projects/software/dex-agent-os/STATUS.md`
  測試用專案狀態檔，供 Section D 端到端測試

- `[NEW] tests/fixtures/sample-transcript.txt`
  測試用會議逐字稿範例（~20 行對話）

- `[NEW] tests/fixtures/sample-consultation-notes.txt`
  測試用諮詢筆記範例

#### B. Google Classroom Collector + Google Docs Reader

- `[MODIFY] scripts/lib/google_api.py`
  SCOPES 加入（**老師角色**）：
  - `classroom.courses.readonly`
  - `classroom.announcements.readonly`
  - `classroom.coursework.students.readonly`
  - `classroom.student-submissions.students.readonly`
  新增 `get_classroom_service()` helper
  新增 `read_google_doc(url)` helper — 從 Google Doc URL 讀取純文字內容

- `[NEW] scripts/collectors/classroom_sync.py`
  - `--courses`：列出所有課程
  - `--active-only`：僅顯示活躍課程
  - `--student-name NAME`：按學生名稱篩選課程
  - `--course-id ID --announcements`：拉課程公告 → 200_Work/meetings/
  - `--course-id ID --coursework`：拉作業 + 學生提交 → 200_Work/consultations/
  - `--latest N`：每類最新 N 筆
  - 輸出格式：markdown，填入對應模板欄位

#### C1. Fireflies.ai Collector（graceful fallback — 目前無訂閱）

- `[NEW] scripts/lib/fireflies_api.py`
  Fireflies.ai GraphQL API 封裝
  - `FIREFLIES_API_KEY` 環境變數
  - `list_transcripts(limit)`：列出最近的會議逐字稿
  - `get_transcript(id)`：取得單場完整逐字稿（含 speaker labels）
  - 未設定 token 時優雅 fallback（印 setup 引導，不 crash）

- `[NEW] scripts/collectors/fireflies_sync.py`
  - `--latest N`：匯入最近 N 場會議逐字稿
  - `--list`：列出可用的會議
  - 輸出：`200_Work/meetings/YYYY-MM-DD-slug/transcript.md`（原始逐字稿）
  - 匯入後可接 `meeting-notes` 處理

#### C2. Meeting Notes + Consultation Notes Generator

- `[NEW] scripts/lib/input_loader.py`
  共用輸入載入 helper，抽出 4 種模式的載入邏輯：
  - `load_from_transcript(path)` → 讀取檔案內容
  - `load_from_notes(text)` → 直接傳回
  - `load_from_google_doc(url)` → 呼叫 google_api.read_google_doc()
  - `load_from_fireflies(fireflies_id=None)` → 呼叫 fireflies_api
  - `load_input(args)` → 統一入口，根據 argparse args 自動判斷模式

- `[NEW] scripts/generators/meeting_notes.py`
  使用 `input_loader.load_input(args)` 取得輸入內容
  - `--transcript FILE` / `--notes "..."` / `--google-doc URL` / `--fireflies`
  - `--title "會議主題"` + `--date YYYY-MM-DD`
  - `--attendees "A, B, C"`（選用）
  - 輸出：`200_Work/meetings/YYYY-MM-DD-slug/notes.md`

- `[NEW] scripts/generators/consultation_notes.py`
  使用 `input_loader.load_input(args)` 取得輸入內容
  - `--transcript FILE` / `--notes "..."` / `--google-doc URL` / `--fireflies`
  - `--title "主題"` + `--person "對象"` + `--date YYYY-MM-DD`
  - `--direction giving|receiving`（預設 giving）
  - 輸出：`200_Work/consultations/YYYY-MM-DD-person-slug/notes.md`
  - 使用已有的 `consultation-notes-template.md`

#### D. Project Status Generator

- `[NEW] scripts/generators/project_status.py`
  - `<project-name>`：指定專案名稱（在 400_Projects/ 下搜尋）
  - `--type software|products`（選用，指定搜尋範圍）
  - 讀取：STATUS.md、DECISIONS.md、README.md、近 30 天 git log
  - LLM 產出更新版 STATUS.md
  - 輸出：`400_Projects/{software|products}/<name>/STATUS.md`

#### E. CLI + Workflows + Skills + 文件

- `[MODIFY] bin/agent`
  新增子命令：meeting-notes / consultation-notes / project-status / classroom-sync / fireflies-sync

- `[NEW] canonical/workflows/{meeting-notes,consultation-notes,project-status,classroom-sync,fireflies-sync}.md`
  各 workflow 文件，描述觸發方式、輸入來源、處理邏輯、輸出

- `[NEW] .claude/commands/{meeting-notes,consultation-notes,project-status,classroom-sync,fireflies-sync}.md`
  IDE skill，可在 Claude Code 內用 `/meeting-notes` 等觸發

- `[MODIFY] CLAUDE.md` — CLI 速查表加新指令
- `[MODIFY] GUIDE.md` — 加 Phase 6 使用說明章節（含轉錄工具整合對照表）
- `[MODIFY] PLAN.md` — Phase 6 任務狀態更新

## Verification Plan

### Manual Verification

每個 Section 完成後逐一驗證：

1. **Section A**：`python3 -c "from scripts.lib.config import MEETINGS_DIR; print(MEETINGS_DIR)"` 確認路徑正確
2. **Section B**：
   - `./bin/agent classroom-sync --courses` — 列出課程（需已設定 Google API + 重新授權）
   - `./bin/agent classroom-sync --courses --active-only` — 僅活躍課程
   - `./bin/agent classroom-sync --courses --student-name "XXX"` — 按學生篩選
   - `./bin/agent classroom-sync --course-id ID --announcements --latest 3` — 拉公告
   - `./bin/agent classroom-sync --course-id ID --coursework --latest 3` — 拉作業
3. **Section C1**：
   - `./bin/agent fireflies-sync --list`（無 token 時顯示 setup 引導）
4. **Section C2**：
   - `./bin/agent meeting-notes --transcript tests/fixtures/sample-transcript.txt --title "Test"` — 逐字稿模式
   - `./bin/agent meeting-notes --notes "重點1, 重點2" --title "Test"` — 手動筆記模式
   - `./bin/agent consultation-notes --notes "問題描述" --title "Test" --person "Alice"` — 諮詢模式
5. **Section D**：
   - `./bin/agent project-status dex-agent-os` — 用測試用 STATUS.md
6. **Section E**：
   - `./bin/agent help` — 確認新指令出現
   - `bin/sync` — 確認 workflow/skill 同步到三個 IDE

### Automated Tests

- `python3 -c "import scripts.lib.input_loader"` — import 無錯誤
- `python3 -c "import scripts.generators.meeting_notes"` — import 無錯誤
- `python3 -c "import scripts.generators.consultation_notes"` — import 無錯誤
- `python3 -c "import scripts.generators.project_status"` — import 無錯誤
- `python3 -c "import scripts.collectors.classroom_sync"` — import 無錯誤
- `python3 -c "import scripts.collectors.fireflies_sync"` — import 無錯誤
- `python3 -c "import scripts.lib.fireflies_api"` — import 無錯誤
