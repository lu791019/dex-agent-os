# Dex Agent OS — 使用說明書

> 版本：Phase 6 P1 — 會議 / 諮詢 / 專案狀態 / Classroom / Fireflies
> 最後更新：2026-02-20

---

## 目錄

- [1. 快速開始](#1-快速開始)
- [2. 指令總覽](#2-指令總覽)
- [3. 日記系統完整流程](#3-日記系統完整流程)
- [4. 知識萃取系統](#4-知識萃取系統)
- [5. 內容生產管線](#5-內容生產管線)
- [6. 週回顧與電子報系統](#6-週回顧與電子報系統)
- [6.5 Podcast & YouTube 消化系統](#65-podcast--youtube-消化系統)
- [6.7 學習輸入管線 + 每日消化](#67-學習輸入管線--每日消化)
- [6.8 工作管理系統](#68-工作管理系統)
- [7. 檔案架構與分類](#7-檔案架構與分類)
- [8. 跨平台同步](#8-跨平台同步)
- [9. 模板系統](#9-模板系統)
- [10. 規則系統](#10-規則系統)
- [11. 常見操作範例](#11-常見操作範例)
- [12. 目前功能狀態](#12-目前功能狀態)
- [13. 疑難排解](#13-疑難排解)

---

## 1. 快速開始

### 環境需求

| 需求 | 說明 |
|------|------|
| macOS | 目前僅支援 macOS（Dayflow、launchd） |
| Python 3 | 腳本執行 |
| Claude Code CLI | `claude --print` 用於 LLM 呼叫 |
| Claude Pro 訂閱 | 所有 LLM 呼叫走 Pro 額度，不花 API 費用 |
| Dayflow app | 螢幕活動追蹤（選用，沒有也能跑 journal） |
| Threads API Token | 內容生產管線需要（選用，見下方設定） |

### 第一次使用

```bash
# 1. 進入專案目錄
cd ~/dex-agent-os

# 2. 同步規則到所有 IDE
./bin/sync

# 3. 查看可用指令
./bin/agent help

# 4. 產出你的第一份精煉日記（需先有 L1 工作日誌）
./bin/agent journal 2026-02-07

# 5. 產出 Dayflow 活動摘要（需 Dayflow 有記錄）
./bin/agent dayflow 2026-02-07

# 6. （選用）設定 Threads API Token — 內容生產管線需要
#    到 developers.facebook.com → 建立 Meta App → Threads API
#    用 App Dashboard 的「用戶權杖產生器」取得 Access Token
echo "THREADS_ACCESS_TOKEN=你的token" >> .env
```

---

## 2. 指令總覽

### 按情境分組的完整指令清單

以下按**典型使用順序**排列，同一情境內的指令建議依序執行。

#### A. 每日記錄（下班前 / 睡前）

| 順序 | 指令 | 類型 | 說明 | 輸出位置 |
|:----:|------|:----:|------|----------|
| 1 | `/work-log [日期]` | IDE | 收集 Claude Code 對話、git commits、Dayflow 資料，產出 L1 完整工作日誌 | `~/work-logs/YYYY/MM/YYYY-MM-DD.md` |
| 2 | `./bin/agent dayflow [日期]` | CLI | 從 Dayflow SQLite 讀取螢幕活動，產出行為分析摘要 | `100_Journal/daily/YYYY-MM-DD-dayflow.md` |
| 3 | `./bin/agent journal [日期]` | CLI | 從 L1 工作日誌 + Dayflow 摘要（如存在）提煉精華，壓縮為 L2 精煉日記 | `100_Journal/daily/YYYY-MM-DD.md` |
| 4 | `./bin/agent extract [日期\|all]` | CLI | 從 L2 日記萃取知識（學習/反思/靈感）到記憶庫 | `~/.claude/projects/-Users-dex-dex-agent-os/memory/` + `800_System/knowledge/` + `510_Insights/` |
| 5 | `/daily-review` | IDE | 互動式每日回顧：AI 呈現摘要 → 問你 3 個問題 → 更新 L2 日記洞察 | 更新既有 L2 日記 |

> **一鍵替代 1-3：** `/daily-content [日期]` 會自動執行 L1 → Dayflow → L2 → extract → topic-create → topic-to-thread 完整流水線（L2 會自動讀取 Dayflow 摘要），並產出 Threads 草稿。
>
> **一鍵全流程：** `/daily-all [日期]` 整合所有管線（sync-all → 工作管理 → 日記 → digest → 互動學習/回顧 → extract → topic-create → thread + fb），`--skip-interactive` 跳過互動步驟。詳見第 5 節「一鍵每日全流程」。

#### B. 每日內容生產（有素材想發文時）

| 順序 | 指令 | 類型 | 說明 | 輸出位置 |
|:----:|------|:----:|------|----------|
| 1 | `/daily-content [日期]` | IDE | 一鍵完整管線：L1 → L2 + Dayflow → extract → topic-create → topic-to-thread | `530_Channels/threads/YYYY-MM-DD/` |
| 2 | `./bin/agent topic-create <insight-file>` | CLI | 從 insight 卡片建立結構化主題（含核心論點、頻道適合度） | `520_Topics/<slug>/TOPIC.md` |
| 3 | `./bin/agent topic-to-thread <topic-slug>` | CLI | 從 TOPIC.md 產出 Threads 草稿，自動套用 Style DNA | `530_Channels/threads/<created-date>/<slug>.md` |
| 3' | `./bin/agent topic-to-fb <topic-slug>` | CLI | 從 TOPIC.md 產出 Facebook 貼文草稿 | `530_Channels/facebook/<created-date>/<slug>.md` |
| 3'' | `./bin/agent topic-to-blog <topic-slug>` | CLI | 從 TOPIC.md 產出部落格文章草稿 | `530_Channels/blog/<created-date>/<slug>.md` |
| 3''' | `./bin/agent topic-to-short-video <topic-slug>` | CLI | 從 TOPIC.md 產出短影音腳本 | `530_Channels/short-video/<created-date>/<slug>.md` |
| 4 | `./bin/agent film-review --title "..."` | CLI | 從電影資訊產出影評 | `600_Life/film/reviews/YYYY-MM-DD-slug.md` |

#### C. 學習輸入 + 每日消化（持續 / 每天）

| 順序 | 指令 | 類型 | 說明 | 輸出位置 |
|:----:|------|:----:|------|----------|
| 1 | `./bin/agent readwise-sync --reader --latest N` | CLI | Readwise Reader 文章批次匯入 | `000_Inbox/readings/YYYY-MM-DD-slug.md` |
| 1' | `./bin/agent rss-sync --feed URL --latest N` | CLI | RSS feed 批次匯入 | 同上 |
| 1'' | `./bin/agent anybox-sync --starred --latest N` | CLI | Anybox 星號書籤批次匯入 | 同上 |
| 2 | `./bin/agent learning-note --url URL` | CLI | 單篇 URL → LLM 學習筆記 | `300_Learning/input/articles/YYYY-MM-DD-slug.md` |
| 2' | `./bin/agent learning-note --readwise --reader --latest N` | CLI | Reader 文章 → LLM 學習筆記 | 同上 |
| 2'' | `./bin/agent learning-note --rss FEED --latest N` | CLI | RSS 文章 → LLM 學習筆記 | 同上 |
| 3 | `./bin/agent daily-digest [--today]` | CLI | 掃描當日所有學習內容 → LLM 消化摘要 | `100_Journal/digest/YYYY-MM-DD-digest.md` |
| 3' | `./bin/agent daily-digest --send` | CLI | 同上 + 建立 Google Doc + 寄 Gmail | Google Docs + Gmail |
| 4 | `/daily-learning` | IDE | 互動學習對話：逐篇提問 → 歸納洞察 | `510_Insights/` + `300_Learning/input/` |

> **流程建議：** 每天先用 sync 指令匯入新內容 → 選感興趣的跑 learning-note → 跑 daily-digest → 用 /daily-learning 深度消化。

#### D. 每週彙總（週日或週一）

| 順序 | 指令 | 類型 | 說明 | 輸出位置 |
|:----:|------|:----:|------|----------|
| 1 | `./bin/agent youtube-add "URL"` | CLI | YouTube 字幕 → 結構化學習筆記 | `300_Learning/youtube/YYYY-MM-DD-slug.md` |
| 2 | `./bin/agent podcast-add --transcript FILE --title "..."` | CLI | 手動逐字稿 → episode 筆記 | `300_Learning/podcasts/episodes/YYYY-MM-DD-slug.md` |
| 2' | `./bin/agent podcast-add --apple` | CLI | Apple Podcast 快取匯入 | 同上 |
| 2'' | `./bin/agent podcast-add --notion [--latest N]` | CLI | Notion Podwise 匯入 | 同上 |
| 2''' | `./bin/agent podcast-add --readwise [--latest N]` | CLI | Readwise Podwise 匯入 | 同上 |
| 3 | `./bin/agent podcast-digest [日期]` | CLI | 週度消化報告（合併 YouTube + Podcast） | `300_Learning/podcasts/weekly/YYYY-Wxx-podcast-digest.md` |
| 4 | `./bin/agent weekly-review [日期]` | CLI | 從 7 天 L2 日記 + Dayflow 彙整為結構化週回顧 | `100_Journal/weekly/YYYY-Wxx.md` |
| 5 | `./bin/agent weekly-newsletter [日期]` | CLI | 從 L2 + Topics + Insights 產出電子報草稿（月度輪替 4 種類型） | `530_Channels/newsletter/YYYY-Wxx-{type}.md` |

> **一鍵替代 3：** `/podcast-weekly [日期]` 一鍵產出 digest + 可選簡報。
> **一鍵替代 4-5：** `/weekly-content [日期]` 會自動依序產出週回顧 + 電子報草稿。

#### H. 工作管理（會議後 / 諮詢後 / 專案追蹤）

| 順序 | 指令 | 類型 | 說明 | 輸出位置 |
|:----:|------|:----:|------|----------|
| 1 | `./bin/agent meeting-notes --title "..." [輸入來源]` | CLI | 逐字稿/筆記/Google Doc/Fireflies → 結構化會議筆記 | `200_Work/meetings/YYYY-MM-DD-slug/notes.md` |
| 2 | `./bin/agent consultation-notes --title "..." --person "..." [輸入來源]` | CLI | 多來源 → 諮詢紀錄（支援 giving/receiving 方向） | `200_Work/consultations/YYYY-MM-DD-slug/notes.md` |
| 3 | `./bin/agent project-status [專案名]` | CLI | 讀 STATUS.md + git log → LLM 更新專案狀態 | `400_Projects/{software|products}/<name>/STATUS.md` |
| 4 | `./bin/agent classroom-sync --courses` | CLI | 列出 Google Classroom 課程（老師角色） | 終端輸出 |
| 4' | `./bin/agent classroom-sync --course-id ID --announcements` | CLI | 拉課程公告 → 會議筆記格式 | `200_Work/meetings/` |
| 5 | `./bin/agent fireflies-sync --list` | CLI | 列出 Fireflies.ai 可用逐字稿 | 終端輸出 |
| 5' | `./bin/agent fireflies-sync --latest N` | CLI | 匯入最近 N 場會議逐字稿 | `200_Work/meetings/YYYY-MM-DD-slug/transcript.md` |

> **輸入來源參數（4 種擇一）：** `--transcript FILE`（檔案逐字稿）、`--notes "..."`（手動筆記）、`--google-doc URL`（Tactiq/Scribbl 存的 Google Doc）、`--fireflies`（Fireflies.ai 最新逐字稿）

> **會議轉錄工具整合：** Tactiq（免費 10 會/月）→ `--google-doc`、Scribbl（免費 15 會/月）→ `--google-doc`、Otter.ai（免費 300 分/月）→ 手動匯出走 `--transcript`、Fireflies.ai（需訂閱）→ `--fireflies`、Mac 聽寫 → `--transcript`

#### E. 知識管理（每週一次或累積足夠時）

| 順序 | 指令 | 類型 | 說明 | 輸出位置 |
|:----:|------|:----:|------|----------|
| 1 | `./bin/agent extract` | CLI | 萃取所有未處理日記的知識到記憶庫 | `~/.claude/projects/-Users-dex-dex-agent-os/memory/` + `800_System/knowledge/` |
| 2 | `./bin/agent extract --global` | CLI | 萃取後額外更新全域 `~/CLAUDE.md` 的「累積學習」速查表 | `~/CLAUDE.md` 末尾 |

#### F. 風格系統（初次設定 + 定期更新）

| 順序 | 指令 | 類型 | 說明 | 輸出位置 |
|:----:|------|:----:|------|----------|
| 1 | `./bin/agent collect-threads` | CLI | 從 Threads API 抓取歷史貼文（建議 ≥50 篇），需 `.env` 中有 token | `800_System/references/examples/threads/` |
| 2 | `./bin/agent extract-style <channel>` | CLI | 從範例中萃取 7 維度風格指紋（threads / newsletter） | `800_System/references/style-dna/<channel>-dna.md` |

#### F. 系統維護

| 指令 | 類型 | 說明 |
|------|:----:|------|
| `./bin/agent sync` 或 `./bin/sync` | CLI | 將 `canonical/` 規則同步到 `.agent/` `.cursor/` `.claude/` 三個 IDE |
| `./bin/agent sync-all` | CLI | 一鍵批次匯入所有來源（Readwise Reader + RSS + Anybox + Gmail） |
| `./bin/agent help` | CLI | 顯示 CLI 使用說明與範例 |

#### G. 規格驅動開發（OpenSpec / OPSX）

用於**規劃新功能、架構變更**時的結構化工作流，非日常內容操作。

| 順序 | 指令 | 類型 | 說明 |
|:----:|------|:----:|------|
| — | `/opsx:explore` | IDE | 探索模式：釐清需求、調查問題、brainstorm 方案 |
| 1 | `/opsx:new` | IDE | 建立新 change：產出提案 + delta spec |
| 2 | `/opsx:continue` | IDE | 繼續推進 change：產出下一個 artifact |
| 3 | `/opsx:ff` | IDE | 快轉模式：一口氣產出所有 artifact |
| 4 | `/opsx:apply` | IDE | 根據 change artifact 執行實作 |
| 5 | `/opsx:verify` | IDE | 驗證實作是否符合 artifact |
| 6 | `/opsx:sync` | IDE | 將 delta spec 同步回 main spec |
| 7 | `/opsx:archive` | IDE | 歸檔已完成的 change |
| — | `/opsx:bulk-archive` | IDE | 批次歸檔多個已完成的 change |
| — | `/opsx:onboard` | IDE | 引導式教學：走完一次完整 OPSX 流程 |

---

### 參數速查

| 參數 | 適用指令 | 說明 |
|------|---------|------|
| `[日期]` | journal, dayflow, extract, weekly-review, weekly-newsletter | YYYY-MM-DD 格式，省略則今天（extract 預設 `all`） |
| `--force` | journal, dayflow, extract, collect-threads, extract-style, topic-to-thread, weekly-review, weekly-newsletter | 強制覆蓋已存在檔案或重新處理 |
| `--dry-run` | extract | 只顯示將處理什麼，不寫入 |
| `--type TYPE` | extract, weekly-newsletter | extract: learnings/blockers/insights/all；newsletter: curated/deep-dive/mixed/monthly-reflection |
| `--global` | extract | 額外更新全域 `~/CLAUDE.md` 速查表 |
| `--limit N` | collect-threads | 抓取筆數上限（預設 50） |
| `--token TOKEN` | collect-threads | 直接傳入 Threads API token（預設讀 .env） |
| `--skip-worklog` | /daily-content | 跳過 L1 產出步驟（已有工作日誌時） |
| `--title "..."` | topic-create, podcast-add | 手動指定標題 |
| `--pptx` | podcast-digest | 同時產出簡報結構化 markdown |
| `--apple` | podcast-add | 使用 Apple Podcast TTML 快取 |
| `--notion` | podcast-add | 從 Notion Podwise DB 匯入 |
| `--readwise` | podcast-add | 從 Readwise 匯入 podcast highlights |
| `--transcript FILE` | podcast-add | 指定手動逐字稿檔案路徑 |
| `--latest N` | podcast-add (--apple/--notion/--readwise) | 自動匯入最新 N 集 |
| `--all` | podcast-add (--notion/--readwise) | 匯入全部（不限日期） |
| `--notes "..."` | film-review | 觀影筆記（選用） |
| `--rating N` | film-review | 評分 1-10（選用） |
| `--transcript FILE` | meeting-notes, consultation-notes | 逐字稿檔案路徑 |
| `--notes "..."` | meeting-notes, consultation-notes | 手動筆記文字 |
| `--google-doc URL` | meeting-notes, consultation-notes | Google Doc URL（Tactiq/Scribbl） |
| `--fireflies` | meeting-notes, consultation-notes | 使用 Fireflies.ai 最新逐字稿 |
| `--person "..."` | consultation-notes | 諮詢對象 |
| `--direction giving\|receiving` | consultation-notes | 諮詢方向（預設 giving） |
| `--attendees "..."` | meeting-notes | 與會者（逗號分隔） |
| `--courses` | classroom-sync | 列出所有課程 |
| `--active-only` | classroom-sync | 僅顯示活躍課程 |
| `--student-name NAME` | classroom-sync | 按學生名稱篩選課程 |
| `--course-id ID` | classroom-sync | 指定課程 ID |
| `--announcements` | classroom-sync | 拉課程公告 |
| `--coursework` | classroom-sync | 拉作業 + 學生提交 |
| `--list` | fireflies-sync | 列出可用逐字稿 |

### 跨 IDE 共用指令

以下 workflow 指令透過 `bin/sync` 同步，在三個 IDE 中都可使用：

| 指令 | Claude Code | Antigravity | Cursor |
|------|:-----------:|:-----------:|:------:|
| `/daily-journal` | ✓ | ✓ | ✓ |
| `/daily-review` | ✓ | ✓ | ✓ |
| `/daily-dayflow-digest` | ✓ | ✓ | ✓ |
| `/extract-style` | ✓ | ✓ | ✓ |
| `/topic-create` | ✓ | ✓ | ✓ |
| `/topic-to-thread` | ✓ | ✓ | ✓ |
| `/weekly-review` | ✓ | ✓ | ✓ |
| `/weekly-newsletter` | ✓ | ✓ | ✓ |
| `/podcast-weekly` | ✓ | ✓ | ✓ |
| `/meeting-notes` | ✓ | ✓ | ✓ |
| `/consultation-notes` | ✓ | ✓ | ✓ |
| `/project-status` | ✓ | ✓ | ✓ |
| `/classroom-sync` | ✓ | ✓ | ✓ |
| `/fireflies-sync` | ✓ | ✓ | ✓ |

以下為 Claude Code 專屬指令（`.claude/commands/` 中定義）：

| 指令 | 說明 |
|------|------|
| `/work-log` | L1 工作日誌（需 Claude Code 對話歷史） |
| `/daily-content` | 一鍵每日內容管線 |
| `/weekly-content` | 一鍵每週內容管線 |
| `/youtube-add` | YouTube 字幕 → 結構化學習筆記 |
| `/podcast-add` | Podcast 逐字稿 → episode 筆記 |
| `/podcast-weekly` | 一鍵 Podcast 週度消化 + 簡報 |
| `/opsx:*` | OpenSpec 規格驅動開發系列 |

---

## 3. 日記系統完整流程

### 概覽

日記系統有 **三條管線**，各自獨立：

```
管線 A：L0 → L1 → L2（工作日誌 → 精煉日記）
管線 B：Dayflow SQLite → 活動摘要（螢幕行為分析）
管線 C：L1 + L2 + Dayflow → 互動回顧（即時對話）
```

### 管線 A：工作日誌 → 精煉日記

#### Step 1：L0 自動記錄

每次 `git commit` 時，`post-commit-log.sh`（git hook）自動在工作日誌中追加一行：

```
> **自動記錄** [10:57] `22e1912` 初始化專案結構
```

- 觸發：自動（git hook）
- 輸出：`~/work-logs/YYYY/MM/YYYY-MM-DD.md`（追加模式）

#### Step 2：L1 完整工作日誌

在 Claude Code 中執行 `/work-log` 或 `/work-log YYYY-MM-DD`，收集所有資料源並整合為完整日誌。

**資料來源：**

| 來源 | 收集方式 |
|------|----------|
| Claude Code 對話 | `extract-sessions.py --date YYYY-MM-DD` |
| Git commits | `git log --oneline --after/--before` |
| Dayflow 螢幕活動 | SQLite 查詢 timeline_cards |
| Dayflow AI 觀察 | SQLite 查詢 observations |
| 當前對話視窗 | 直接從上下文分析 |

**日誌包含區塊：**
- 基本資訊 / 今日摘要 / 優化目標
- 討論過程與思路（每個議題的背景 → 方案比較 → 決策）
- 程式碼變更 / 相關 Commits / 相關 PR
- 遇到的問題與解決方式
- 反思與思考（做得好 / 可改進 / 學到 / 技術債）
- 結論 / 待辦
- Dayflow 活動紀錄

**指令用法：**

```
/work-log                              → 今天的日誌
/work-log 2026-02-06                   → 指定日期
/work-log 2026-02-06 專案名稱          → 指定日期 + 專案名稱
```

- 觸發：手動（`/work-log`）
- 輸出：`~/work-logs/YYYY/MM/YYYY-MM-DD.md`（覆蓋模式）
- 長度：約 5,000 ~ 8,000 字元

#### Step 3：L2 精煉日記

從 L1 工作日誌 + Dayflow 活動摘要（如存在）提煉出精華，壓縮到 1/3 ~ 1/5 長度。Dayflow 的行為模式洞察會自動融入「卡在哪裡」和「洞察 & 靈感」區段。

```bash
./bin/agent journal                    # 今天
./bin/agent journal 2026-02-07         # 指定日期
./bin/agent journal 2026-02-07 --force # 強制覆蓋
```

**產出格式：**
- 今日一句話（一句精煉概括）
- 做了什麼（條列重點）
- 學到什麼（知識萃取）
- 洞察 & 靈感（每條標註適合頻道：→ Threads / Newsletter / Blog）
- 卡在哪裡
- 明天優先（最多 3 項）
- 能量 & 狀態（1-5 分）

- 觸發：手動（`./bin/agent journal`）
- 輸入：L1 工作日誌（**必須先有 L1**）
- 輸出：`100_Journal/daily/YYYY-MM-DD.md`
- 長度：約 1,000 ~ 2,000 字元

### 管線 B：Dayflow 活動摘要

直接從 Dayflow SQLite 資料庫讀取螢幕活動記錄，分析你一天的行為模式。

```bash
./bin/agent dayflow                    # 今天
./bin/agent dayflow 2026-02-07         # 指定日期
./bin/agent dayflow 2026-02-07 --force # 強制覆蓋
```

**資料來源（直接讀取，不依賴 L1）：**

| 資料表 | 內容 |
|--------|------|
| `timeline_cards` | 螢幕活動時間軸（應用程式、網頁、時間區段） |
| `observations` | Dayflow AI 自動產生的行為觀察 |

**產出格式：**
- 今日節奏（一句話概括整天節奏）
- 時間分布（按類別統計百分比）
- 活動時間軸（合併碎片、簡化呈現）
- AI 觀察摘要（去重、合併相似觀察）
- 行為模式 & 洞察（跨活動分析）
- 值得注意的事（異常行為、可改進習慣）

- 觸發：手動（`./bin/agent dayflow`）
- 輸入：Dayflow SQLite（`~/Library/Application Support/Dayflow/chunks.sqlite`）
- 輸出：`100_Journal/daily/YYYY-MM-DD-dayflow.md`
- 長度：約 3,000 ~ 5,000 字元

### 管線 C：每日回顧（互動式）

在 IDE 中觸發 `/daily-review`，AI 會：

1. 讀取 L1 + L2 + Dayflow 資料
2. 呈現回顧摘要（完成了什麼、花最多時間在、值得深入的點、未完成）
3. 問你 3 個問題：
   - 「今天有什麼你覺得特別值得記下來的想法嗎？」
   - 「有哪個洞察你想發展成內容？」
   - 「明天最重要的一件事是什麼？」
4. 根據你的回答，更新 L2 日記的洞察區塊

- 觸發：手動（IDE 內 `/daily-review`）
- 不產出新檔案，而是更新既有的 L2 日記

### 每日建議操作順序

```
下班前 / 睡前（方式 A — 一鍵完成）：
  1. /daily-content                     → L1 + L2 + Dayflow + extract → topic-create → Threads 草稿
  2. ./bin/agent extract                → 萃取知識到記憶庫
  3. /daily-review（選用）              → 互動回顧，補充洞察

下班前 / 睡前（方式 B — 分步執行）：
  1. /work-log                         → 產出 L1 完整工作日誌
  2. ./bin/agent dayflow                → 產出 Dayflow 活動摘要
  3. ./bin/agent journal                → 從 L1 + Dayflow 摘要產出 L2 精煉日記（需先跑完 step 2）
  4. ./bin/agent extract                → 萃取知識到記憶庫
  5. /daily-review（選用）              → 互動回顧，補充洞察

每週一次（或累積足夠新知識時）：
  6. ./bin/agent extract --global       → 更新全域速查表
  7. ./bin/agent collect-threads        → 更新 Threads 範例
  8. ./bin/agent extract-style threads  → 重新萃取 Style DNA

每週日 / 週一（方式 A — 一鍵完成）：
  9. /weekly-content                    → 週回顧 + 電子報草稿

每週日 / 週一（方式 B — 分步執行）：
  9. ./bin/agent weekly-review          → 個人週回顧
  10. ./bin/agent weekly-newsletter     → 電子報草稿
```

---

## 4. 知識萃取系統

### 概覽

每日 L2 精煉日記中有三個高價值區段，知識萃取系統自動將它們歸檔到正確位置：

```
100_Journal/daily/YYYY-MM-DD.md
    │
    ├─ 「學到什麼」 → learnings.md（Claude 自動載入）+ archive
    ├─ 「卡在哪裡」 → reflections.md（Claude 自動載入）+ archive
    └─ 「洞察 & 靈感」→ 510_Insights/ 或 000_Inbox/ideas/ 或 600_Life/personal/
```

### 為什麼寫到 memory/ 就能「記住」？

這是 Claude Code 的內建機制。當你在 `~/dex-agent-os/` 開啟 Claude Code 時，它會自動找到對應的 `~/.claude/projects/-Users-dex-dex-agent-os/` 目錄，並將 `memory/` 資料夾裡的所有 `.md` 檔案**注入到每次對話的 system prompt**。

路徑命名規則：專案絕對路徑 `/Users/dex/dex-agent-os` 的 `/` 替換成 `-`，得到 `-Users-dex-dex-agent-os`。

所以 `extract` 指令寫入到這個目錄的 `learnings.md`、`reflections.md`、`MEMORY.md`，每次開新對話就自動帶進來，不需要手動指定。

### 三層分級記憶架構

| 層級 | 位置 | 載入時機 | 行數限制 | 用途 |
|------|------|---------|---------|------|
| 全域速查表 | `~/CLAUDE.md` 末尾 | **所有專案每個 session** | ≤40 行 | 跨專案通用教訓 |
| 專案記憶 | `~/.claude/projects/-Users-dex-dex-agent-os/memory/` | **dex-agent-os 每個 session** | learnings ≤120 行、reflections ≤80 行 | 專案內詳細學習 |
| 歸檔 | `800_System/knowledge/` | 不載入（版控查閱用） | 無限制 | 完整歷史記錄 |

### 指標觸發機制

全域速查表（`~/CLAUDE.md`）末尾有 P1/P2 觸發條件，指導 Claude 何時主動讀取專案記憶的詳細檔案：

| 觸發等級 | 條件 | 動作 |
|---------|------|------|
| **P1 必讀** | 進入 Plan Mode 或撰寫 implementation_plan.md 前 | 讀取 `memory/learnings.md` + `memory/reflections.md` |
| **P2 選讀** | 同一問題連續失敗 2 次以上 | 讀取 `memory/reflections.md` |
| **不讀** | 一般 coding、內容撰寫、git 操作 | 使用 ~/CLAUDE.md 的速查表即可 |

### 指令用法

```bash
# 基本用法 — 萃取所有日記的全部類型
./bin/agent extract

# 萃取指定日期
./bin/agent extract 2026-02-07

# 預覽模式（不寫入）
./bin/agent extract --dry-run

# 只萃取學習記錄
./bin/agent extract --type learnings

# 強制重新處理（忽略冪等性記錄）
./bin/agent extract --force

# 萃取 + 更新全域 ~/CLAUDE.md
./bin/agent extract --global

# 組合使用
./bin/agent extract --force --type learnings --global
```

### 萃取類型

| 類型 | 日記區段 | 輸出位置 | 處理方式 |
|------|---------|---------|---------|
| `learnings` | 「學到什麼」 | `~/.claude/projects/.../memory/learnings.md` + `800_System/knowledge/learnings-archive.md` | LLM 合併去重，四分類：技術/工具/方法論/認知 |
| `blockers` | 「卡在哪裡」 | `~/.claude/projects/.../memory/reflections.md` + `800_System/knowledge/reflections-archive.md` | LLM 轉化為反思教訓，五分組：資源管理/技術債/決策品質/流程效率/其他 |
| `insights` | 「洞察 & 靈感」 | 依分類分流（見下方） | LLM 分類 + 自動產生個別檔案 |

### Insight 分流

每條洞察由 LLM 判斷分類，自動寫入對應目錄：

| 分類 | 目的地 | 條件 |
|------|--------|------|
| `content` | `510_Insights/` | 有明確頻道標記（→ Threads / Blog / Newsletter 等） |
| `idea` | `000_Inbox/ideas/` | 沒有明確頻道但有潛力的想法 |
| `personal` | `600_Life/personal/reflections/` | 關於個人成長、職涯、生活的反思 |

**Insight 檔案格式：**

```markdown
---
date: 2026-02-07
source: 100_Journal/daily/2026-02-07.md
classification: content
channel_tags: ["Threads", "Blog"]
status: raw
---

# 多 AI IDE 協作的最佳實踐

canonical 單一真實來源 + sync 腳本...

## 潛在切入角度
可以寫成教學文...
```

### 冪等性

- 系統用 `800_System/knowledge/.processed`（JSON）追蹤每篇日記的 SHA-256 hash
- 相同 hash + 相同 types → 自動跳過
- 日記內容變更（hash 改變）→ 重新處理
- `--force` → 忽略記錄，強制全部重處理

### 全域更新（--global）

`--global` flag 會額外執行一次 LLM 呼叫，將 memory 版精煉為全域速查表：

1. 讀取 `memory/learnings.md` + `memory/reflections.md`
2. LLM 精煉為 ≤40 行的全域速查表
3. 原地替換 `~/CLAUDE.md` 的「## 累積學習」區段到檔案結尾
4. 原有的開發流程等內容不受影響

**速查表四大分類：**
- **工具與環境** — Claude Code、Cursor、Antigravity 等工具的用法與避坑
- **跨平台** — 跨 IDE 協作的注意事項
- **工程原則** — 通用的開發方法論與設計原則
- **反思教訓** — 從失敗和卡關中總結的策略

### 建議操作流程

```
每日下班前 / 睡前：
  1. /work-log                         → L1 工作日誌
  2. ./bin/agent dayflow                → Dayflow 活動摘要
  3. ./bin/agent journal                → L2 精煉日記（自動讀取 Dayflow 摘要，需先跑完 step 2）
  4. ./bin/agent extract                → 萃取知識到記憶庫

每週一次（或累積足夠新知識時）：
  5. ./bin/agent extract --global       → 更新全域速查表
```

### LLM 呼叫策略

- 每次 extract 固定 **3 次 LLM 呼叫**（learnings / blockers / insights 各一次），不管處理多少篇日記
- `--global` 時多 1 次呼叫（精煉全域速查表）
- 所有呼叫使用 `claude --print`，走 Pro 訂閱額度，不花 API 費用

---

## 5. 內容生產管線

### 概覽

Phase 3 建立了從素材到 Threads 草稿的完整管線，並透過 Style DNA 系統讓 AI 產出「像你寫的」內容。

```
素材來源                          內容產出
─────────                        ─────────
Insight 卡片 ──→ topic-create ──→ TOPIC.md ──→ topic-to-thread ──→ Threads 草稿
L1/L2 日記   ──→ /daily-content ──→ extract → topic-create → topic-to-thread
                                      ↑
                              Style DNA（風格指紋）

輸出位置：
  510_Insights/                         ← 洞察素材
  520_Topics/<slug>/TOPIC.md            ← 結構化主題
  530_Channels/threads/<date>/<slug>.md ← 頻道草稿
```

### Threads 範例收集

從 Threads API 自動抓取你的歷史貼文 + 互動數據，作為風格分析的素材：

```bash
# 首次抓取（建議 ≥50 篇以獲得足夠風格樣本）
./bin/agent collect-threads --limit 100

# 強制覆蓋已存在的範例
./bin/agent collect-threads --limit 100 --force
```

**前置需求：**
1. 在 [developers.facebook.com](https://developers.facebook.com) 建立 Meta App（選 Threads API）
2. 在 App Dashboard 使用「用戶權杖產生器」產生 Access Token
3. 將 token 存入 `.env`：`THREADS_ACCESS_TOKEN=你的token`

**輸出格式：** `800_System/references/examples/threads/NNN-slug.md`

每篇包含：
- 元資料（發布日期、互動數據、媒體類型）
- 原文全文
- 永久連結

> **注意：** 用戶權杖有效期 60 天，過期後需到 Dashboard 重新產生。

### Style DNA 萃取

從範例中提取 7 個維度的抽象風格指紋：

```bash
./bin/agent extract-style threads          # 分析 Threads 範例
./bin/agent extract-style threads --force  # 強制覆蓋
```

**分析維度：**

| 維度 | 說明 |
|------|------|
| 結構模式 | 常見段落結構（Hook → 條列 → 金句） |
| 開場 Hook 模式 | 反差型、提問型、宣告型等 |
| 語氣特徵 | 精準度、口語比例、用字習慣 |
| CTA / 收尾模式 | 金句收尾、開放提問、行動呼籲 |
| 長度 / 格式 | 典型字數、段落數、標點習慣 |
| 高互動特徵 | 從互動數據回推的成功模式 |
| 禁忌 | 應避免的模式 |

**輸出：** `800_System/references/style-dna/threads-dna.md`

**範例越多 DNA 越精準** — 建議至少 50 篇以上。DNA 會隨著你持續發文而演化（定期重抓 + 重萃取）。

### 主題建立（topic-create）

從 insight 卡片或手動描述建立結構化主題：

```bash
# 從 insight 建立
./bin/agent topic-create 510_Insights/2026-02-07-xxx.md

# 手動建立
./bin/agent topic-create --title "用 Claude Code 打造個人 Agent OS"

# 列出可用 insights
./bin/agent topic-create
```

**輸出：** `520_Topics/<slug>/TOPIC.md`（含核心論點、關鍵素材、頻道適合度、已產出 checklist）

### 主題轉 Threads（topic-to-thread）

從 TOPIC.md 產出 Threads 草稿，自動套用 Style DNA：

```bash
./bin/agent topic-to-thread <topic-slug>          # 產出草稿
./bin/agent topic-to-thread <topic-slug> --force  # 覆蓋既有
```

**輸出：** `530_Channels/threads/<created-date>/<slug>.md`（自動更新 TOPIC.md 的 checklist）

### 每日內容管線（/daily-content）

一鍵從工作紀錄走完 extract → topic-create → topic-to-thread 完整流水線：

```
/daily-content                    → 今天
/daily-content 2026-02-09         → 指定日期
/daily-content --skip-worklog     → 跳過 L1（已有工作日誌時）
```

**完整流程：**

```
Step 1: L1 工作日誌（/work-log，如不存在自動觸發）
Step 2: Dayflow 活動摘要 → L2 精煉日記（依序執行，L2 會讀取 Dayflow）
Step 3: extract — 從 L2 萃取 insights
Step 4: topic-create — 從 insights 建立 TOPIC.md
Step 5: topic-to-thread — 從 TOPIC.md 產出 Threads 草稿（套用 Style DNA）
Step 6: 寫入檔案 + 產出摘要
```

**輸出目錄：**
- `530_Channels/threads/YYYY-MM-DD/`（按日期資料夾）

> **提醒：** 同一天的 insights 可能產出類似主題，發布前請檢查去重。

### 主題轉 Facebook（topic-to-fb）

從 TOPIC.md 產出 Facebook 貼文草稿：

```bash
./bin/agent topic-to-fb <topic-slug>          # 產出草稿
./bin/agent topic-to-fb <topic-slug> --force  # 覆蓋既有
```

**輸出：** `530_Channels/facebook/<created-date>/<slug>.md`（自動更新 TOPIC.md 的 checklist）

### 主題轉部落格（topic-to-blog）

從 TOPIC.md 產出部落格文章草稿（長篇、含 SEO 結構）：

```bash
./bin/agent topic-to-blog <topic-slug>          # 產出草稿
./bin/agent topic-to-blog <topic-slug> --force  # 覆蓋既有
```

**輸出：** `530_Channels/blog/<created-date>/<slug>.md`

### 主題轉短影音（topic-to-short-video）

從 TOPIC.md 產出短影音腳本（含 Hook、分鏡、CTA）：

```bash
./bin/agent topic-to-short-video <topic-slug>          # 產出草稿
./bin/agent topic-to-short-video <topic-slug> --force  # 覆蓋既有
```

**輸出：** `530_Channels/short-video/<created-date>/<slug>.md`

### 影評產出（film-review）

從電影資訊產出結構化影評：

```bash
./bin/agent film-review --title "電影名"                          # 基本用法
./bin/agent film-review --title "電影名" --notes "觀影筆記"       # 附帶筆記
./bin/agent film-review --title "電影名" --rating 8               # 指定評分
./bin/agent film-review --title "電影名" --notes "..." --rating 8 --force  # 完整參數
```

**輸出：** `600_Life/film/reviews/YYYY-MM-DD-slug.md`

### 一個主題 → 多頻道

Phase 5b 實現了「一次建立主題，多頻道產出」的流程：

```
insight / 手動 → topic-create → TOPIC.md
                                   ├→ topic-to-thread     → Threads 草稿
                                   ├→ topic-to-fb         → Facebook 貼文
                                   ├→ topic-to-blog       → 部落格文章
                                   └→ topic-to-short-video → 短影音腳本

電影觀影 → film-review → 影評
```

每個 TOPIC.md 中都有 checklist 追蹤各頻道產出狀態。

### DNA 的有機生長

```
初始 → collect-threads 抓 50+ 篇 → extract-style → v1 DNA
用了一個月 → 重新 collect-threads → 重跑 extract-style → v2 DNA
持續 → DNA 隨你的風格演化而演化
```

---

## 6. 週回顧與電子報系統

### 概覽

Phase 4 建立了週級別的彙總系統：個人週回顧 + 對外電子報，月度輪替 4 種類型。

```
7 天 L2 日記 + Dayflow ──→ 週回顧（100_Journal/weekly/）
7 天 L2 日記 + Topics + Insights ──→ 電子報草稿（530_Channels/newsletter/）
                                         ↑ Newsletter DNA（如有）
```

### 個人週回顧

從 7 天的 L2 日記 + Dayflow 摘要中提煉結構化週回顧：

```bash
./bin/agent weekly-review                    # 本週
./bin/agent weekly-review 2026-02-10         # 指定日期所在週
./bin/agent weekly-review --force            # 強制覆蓋
```

**產出包含：**
- 本週一句話總結
- 完成了什麼（具體事項）
- 學到什麼（知識萃取）
- 本週數據（量化指標）
- 模式與趨勢（跨天觀察）
- 卡住的地方
- 下週重點
- 能量曲線

**輸出：** `100_Journal/weekly/YYYY-Wxx.md`

### 電子報（月度輪替 4 種類型）

根據月內週數自動選擇電子報類型：

| 月內週數 | 類型 | 說明 |
|---------|------|------|
| Week 1 | `curated` | 主題策展：3-5 精選主題，每個展開 1-2 段 |
| Week 2 | `deep-dive` | 長篇深度：1 個深度主題 + 2-3 個短 highlight |
| Week 3 | `mixed` | 混合：1 個深度主題 + 3-4 個短洞察條列 + 推薦資源 |
| Week 4+ | `monthly-reflection` | 月度心得反思：整月回顧 + 個人成長 |

```bash
./bin/agent weekly-newsletter                          # 本週（自動選類型）
./bin/agent weekly-newsletter 2026-02-10               # 指定日期所在週
./bin/agent weekly-newsletter --type deep-dive         # 指定類型（override 輪替）
./bin/agent weekly-newsletter --force                  # 強制覆蓋
```

**輸出：** `530_Channels/newsletter/YYYY-Wxx-{type}.md`

### Newsletter DNA（提升品質的關鍵）

與 Threads Style DNA 同理，放入電子報範例後萃取風格指紋：

```bash
# 1. 手動放入過去的電子報範例
#    → 800_System/references/examples/newsletter/*.md

# 2. 萃取風格 DNA
./bin/agent extract-style newsletter

# 3. 之後的電子報會自動套用 DNA
./bin/agent weekly-newsletter
```

### 一鍵週報（/weekly-content）

在 Claude Code 中執行 `/weekly-content`，一次產出週回顧 + 電子報草稿。

```
/weekly-content                    → 本週
/weekly-content 2026-02-10         → 指定日期所在週
/weekly-content --type deep-dive   → 指定電子報類型
```

### 一鍵每日全流程（/daily-all）— 設計中，尚未實作

在 Claude Code 中執行 `/daily-all`，整合四大管線一次完成。

```
/daily-all                         → 今天，含互動
/daily-all 2026-02-21              → 指定日期
/daily-all --skip-interactive      → 跳過互動步驟（/daily-learning + /daily-review）
```

**15 步流程：**

| 區段 | Step | 指令 | 說明 |
|------|------|------|------|
| 自動同步 | 1 | `sync-all` | Readwise+RSS+Anybox+Gmail（無 token 自動 skip） |
| | 2 | `fireflies-sync --latest 5` | 無 API key → skip |
| | 3 | `classroom-sync --courses` | 無 token → skip |
| | 4 | `project-status` (全部) | 無專案 → skip |
| 日記 | 5 | `/work-log DATE` | L1（含 scan-work-outputs） |
| | 6 | `dayflow DATE` | Dayflow 活動摘要 |
| | 7 | `journal DATE` | L2（依賴 5+6） |
| 每日消化 | 8 | `daily-digest DATE` | 閱讀消化報告（依賴 1） |
| | 9 | skill LLM 萃取 | 從 digest「今日洞察」→ 510_Insights/ |
| 互動（可跳） | 10 | `/daily-learning` | 挑 3-5 篇深聊，每篇 1 件事 |
| | 11 | `/daily-review` | 反思工作，更新 L2 |
| 收斂產出 | 12 | `extract --type all` | 從 L2 萃取 insights+learnings+reflections |
| | 13 | `topic-create --force` | 所有新 insight（step 9+10+12） |
| | 14a/b | `topic-to-thread` + `topic-to-fb` | 一次性產出草稿 |
| | 15 | 最終摘要 | 顯示所有產出總覽 |

> **與 /daily-content 的關係：** `/daily-content` 只涵蓋日記 + 內容生產（step 5-7, 12-14），`/daily-all` 是超集，額外包含 sync、工作管理、digest、互動學習/回顧。

**各步驟 I/O 對照表：**

| Step | 名稱 | 輸入 | 產出位置 |
|------|------|------|----------|
| 1 | sync-all | 外部 API | `000_Inbox/readings/DATE-*.md` |
| 2 | Fireflies | Fireflies API | `200_Work/meetings/DATE-*.md` |
| 3 | Classroom | Google Classroom API | 僅列出課程（不產檔案） |
| 4 | project-status | `400_Projects/*/STATUS.md` + git log | `400_Projects/*/STATUS.md`（原地更新） |
| 5 | L1 工作日誌 | git log + scan-work-outputs | `~/work-logs/YYYY/MM/DATE.md` |
| 6 | Dayflow | Dayflow SQLite DB | `100_Journal/daily/DATE-dayflow.md` |
| 7 | L2 精煉日記 | Step 5 L1 + Step 6 dayflow | `100_Journal/daily/DATE.md` |
| 8 | Digest | Step 1 readings | `100_Journal/digest/DATE-digest.md` |
| 9 | Digest→Insight | Step 8 digest「今日洞察」 | `510_Insights/DATE-*.md` |
| 10 | 互動學習 | Step 8 digest + Step 9 insights | `510_Insights/DATE-*.md`（新增） |
| 11 | 每日回顧 | Step 5 L1 + Step 7 L2 | `100_Journal/daily/DATE.md`（更新洞察區塊） |
| 12 | Extract | Step 7/11 L2（含更新） | `510_Insights/` + `memory/learnings.md` + `memory/reflections.md` |
| 13 | Topic | 全部 `510_Insights/DATE-*.md` | `520_Topics/slug/TOPIC.md` |
| 14 | Drafts | Step 13 TOPIC.md | `530_Channels/threads/DATE/*.md` + `530_Channels/facebook/DATE/*.md` |

**已知問題與解法：**

| 問題 | 狀態 | 解法 |
|------|------|------|
| Step 5 `/work-log` 巢狀 skill 無法執行 | 暫行方案 C | daily-all 內聯：用 git log + scan-work-outputs 由當前 LLM 產生 L1。方案 A（Python 腳本）留待 Phase 7 |
| Google OAuth scope 不匹配 | 已修復 | `google_api.py` 加 `OAUTHLIB_RELAX_TOKEN_SCOPE=1` |
| GCP Classroom API 未啟用 | 已解決 | 需在 GCP Console 手動啟用 |

### 建議每週操作流程

```
每週日 / 週一：
  1. /weekly-content（或分步）     → 週回顧 + 電子報草稿
  2. 審閱週回顧                    → 可直接發布或作為個人參考
  3. 審閱電子報草稿                → 修改後發送
  4. 發送後歸檔到 700_Archive/newsletter/
```

---

## 6.5 Podcast & YouTube 消化系統

### 概覽

Phase 5a 建立了兩條獨立的學習素材收集管線，以及一個合併消化報告系統：

```
YouTube 線：YouTube URL → 字幕 → LLM 結構化 → 學習筆記
Podcast 線：逐字稿（手動/Apple 快取）→ LLM 結構化 → episode 筆記
Podwise 線：Notion DB / Readwise → API 取得 → LLM 結構化 → episode 筆記
                        ↓                    ↓
                  podcast-digest（合併 YouTube + Podcast）
                         ↓            ↓
                   Markdown 週摘要   .pptx 簡報（可選）
```

### YouTube 筆記

從 YouTube 影片取得字幕，自動產出結構化學習筆記：

```bash
./bin/agent youtube-add "https://youtube.com/watch?v=xxx"         # 基本用法
./bin/agent youtube-add "https://youtube.com/watch?v=xxx" --force # 覆蓋已存在
./bin/agent youtube-add "URL" --date 2026-02-10                   # 指定日期
```

**前置需求：** `pip3 install youtube-transcript-api`

**輸出：** `300_Learning/youtube/YYYY-MM-DD-slug.md`，包含：
- 一句話摘要、核心觀點（3-5 個）、關鍵引述
- 市場趨勢相關、可轉化為內容的素材
- 「我的想法」區塊留空供手動補充

### Podcast Episode 筆記

支援四種輸入模式：

```bash
# P4: 手動文字稿（零依賴）
./bin/agent podcast-add --transcript ~/transcript.txt --title "Hard Fork: AI Agents"

# P3: Apple Podcast TTML 快取
./bin/agent podcast-add --apple              # 列出可用快取
./bin/agent podcast-add --apple --latest 3   # 自動匯入最新 3 集

# P5: Notion（Podwise 匯出）— 需先設定，見下方
./bin/agent podcast-add --notion             # 列出最近 7 天 episodes
./bin/agent podcast-add --notion --latest 5  # 匯入最新 5 集
./bin/agent podcast-add --notion --all       # 匯入全部（首次同步）

# P6: Readwise（Podwise 匯出）— 需先設定，見下方
./bin/agent podcast-add --readwise           # 列出最近 7 天 highlights
./bin/agent podcast-add --readwise --latest 5
./bin/agent podcast-add --readwise --all
```

**輸出：** `300_Learning/podcasts/episodes/YYYY-MM-DD-slug.md`（結構同 YouTube 筆記）

### Podwise 串接設定（Notion + Readwise）

[Podwise](https://podwise.ai/) 是 podcast AI 摘要工具，可將摘要匯出到 Notion 或 Readwise。設定完成後，只需跑 `podcast-add --notion` 或 `--readwise` 就能自動匯入。

> **目前狀態：** 程式碼已就緒，等訂閱 Podwise 後設定 env vars 即可使用。

#### Notion Integration 設定

1. 到 [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations) → 建立新 Integration
2. 複製 **Internal Integration Secret** → 存入 `.env`：
   ```
   NOTION_TOKEN=secret_xxxxxxxxxxxx
   ```
3. 在 Podwise 匯出的 Notion database 頁面 → 點 `...` → `Connect to` → 選擇剛建立的 Integration
4. 複製 database URL 中的 ID（32 碼字串，在 `.so/` 和 `?` 之間）→ 存入 `.env`：
   ```
   NOTION_PODWISE_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

#### Readwise Token 設定

1. 到 [https://readwise.io/access_token](https://readwise.io/access_token) → 複製 token
2. 存入 `.env`：
   ```
   READWISE_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

#### 驗證設定

```bash
# Token 未設定時會顯示引導訊息（不會 crash）
./bin/agent podcast-add --notion
./bin/agent podcast-add --readwise

# 設定完成後測試
./bin/agent podcast-add --notion --latest 1
./bin/agent podcast-add --readwise --latest 1
```

### 週度消化報告

合併一週內所有 YouTube + Podcast 筆記，產出市場趨勢消化報告：

```bash
./bin/agent podcast-digest                    # 本週
./bin/agent podcast-digest 2026-02-10         # 指定日期所在週
./bin/agent podcast-digest --pptx             # 同時產出簡報
./bin/agent podcast-digest --force            # 強制覆蓋
```

**消化報告包含：**
- 本週一句話、本週聽了/看了什麼
- 市場趨勢觀察（跨集歸納 2-3 個趨勢）
- 核心學習、內容種子、推薦片段、下週想深入

**簡報產出：** `--pptx` 會產出 `530_Channels/presentations/YYYY-Wxx-market-trends.md`，可用 `/pptx` skill 轉為 .pptx 檔案。

### 建議每週操作流程

```
聽完 Podcast / 看完 YouTube 後：
  1. ./bin/agent youtube-add "URL"                → YouTube 筆記
  2. ./bin/agent podcast-add --transcript ...      → Podcast 筆記（手動）
  2'. ./bin/agent podcast-add --notion --latest 5  → 從 Podwise/Notion 匯入
  2'. ./bin/agent podcast-add --readwise --latest 5 → 從 Podwise/Readwise 匯入

每週日 / 週一：
  3. /podcast-weekly（或 ./bin/agent podcast-digest）→ 週度消化
  4. （可選）./bin/agent podcast-digest --pptx      → 簡報
  5. /weekly-content                               → 週回顧 + 電子報
```

---

## 6.7 學習輸入管線 + 每日消化

### 完整流程

```
多來源匯入 ─────────────────────────────────────────
  Readwise Reader   → readwise-sync --reader
  RSS feeds         → rss-sync --feed URL
  Anybox 書籤       → anybox-sync --starred
  Gmail 電子報      → gmail-sync --from / --label
  URL / 本地檔案    → learning-note --url / --file
  YouTube           → youtube-add（既有）
  Podcast           → podcast-add（既有）
      │
      ▼
原文存檔：000_Inbox/readings/     ← sync 指令存這裡（純原文）
學習筆記：300_Learning/input/     ← learning-note 存這裡（LLM 消化）
      │
      ▼
每日消化報告 ─── daily-digest ────────────────────
  掃描當日 readings/ + input/ + youtube/ + podcasts/
  去重（同篇優先取 input/ 版本）
  LLM 產出摘要 + takeaway + 今日洞察
  存檔：100_Journal/digest/YYYY-MM-DD-digest.md
  可選：--send → Google Doc + Gmail
      │
      ▼
互動學習對話 ─── /daily-learning ─────────────────
  讀取 digest → 逐篇提問（蘇格拉底 / 考試 / 深聊）
  歸納洞察 → 510_Insights/
  補充想法 → 更新 300_Learning/input/ 的「我的想法」
```

### 學習輸入指令

#### Sync 指令（批次匯入原文，不用 LLM）

```bash
# Readwise Reader（v3 API，推薦）
./bin/agent readwise-sync --reader                    # 列出最近文章
./bin/agent readwise-sync --reader --latest 5 --force # 匯入最新 5 篇

# Readwise v2 Highlights
./bin/agent readwise-sync                             # 列出最近 7 天 highlights
./bin/agent readwise-sync --category articles --latest 3

# RSS
./bin/agent rss-sync                                  # 列出 OPML 中所有 feeds
./bin/agent rss-sync --feed "https://jvns.ca/atom.xml" --latest 3
./bin/agent rss-sync --opml config/subscriptions.opml --latest 5

# Anybox（需開啟 Anybox app）
./bin/agent anybox-sync --starred                     # 列出星號書籤
./bin/agent anybox-sync --starred --latest 3 --force  # 匯入最新 3 筆
./bin/agent anybox-sync --tag "to-read" --latest 5

# Gmail 電子報（需 Google API 設定）
./bin/agent gmail-sync                                    # 列出最近 7 天電子報
./bin/agent gmail-sync --latest 5 --force                 # 匯入最新 5 封
./bin/agent gmail-sync --from "newsletter@substack.com" --latest 3 --force
./bin/agent gmail-sync --label "newsletters" --latest 5 --force
./bin/agent gmail-sync --query "from:substack.com" --days 30 --latest 10 --force
```

#### Learning Note（單篇 / 批次 → LLM 學習筆記）

```bash
# 單篇 URL
./bin/agent learning-note --url "https://..." --type articles

# 本地檔案
./bin/agent learning-note --file path/to/doc.md --title "..." --type tech

# 從 Readwise Reader 批次
./bin/agent learning-note --readwise --reader --latest 3

# 從 RSS 批次
./bin/agent learning-note --rss "https://jvns.ca/atom.xml" --latest 2

# 從 Anybox 批次
./bin/agent learning-note --anybox --starred --latest 2

# --type 可選：articles（預設）/ books / courses / tech
```

### 每日消化報告

```bash
./bin/agent daily-digest                # 掃描昨天的內容
./bin/agent daily-digest --today        # 掃描今天的內容
./bin/agent daily-digest 2026-02-18     # 指定日期
./bin/agent daily-digest --today --send # 同時建立 Google Doc + 寄 Gmail
./bin/agent daily-digest --force        # 覆蓋已存在的 digest
```

### Gmail 電子報匯入

```bash
./bin/agent gmail-sync                                    # 列出最近 7 天電子報
./bin/agent gmail-sync --latest 5 --force                 # 匯入最新 5 封
./bin/agent gmail-sync --from "newsletter@substack.com" --latest 3 --force  # 篩選寄件者
./bin/agent gmail-sync --label "newsletters" --latest 5 --force             # 篩選 label
./bin/agent gmail-sync --query "from:substack.com" --days 30 --latest 10 --force  # 自訂搜尋
```

- 預設搜尋 Gmail 的 Promotions + Updates 分類（電子報常見位置）
- `--from` 可填任何 email 或 domain（如 `substack.com`）
- `--label` 可填任何 Gmail 標籤
- `--query` 可寫完整 Gmail 搜尋語法
- 輸出：`000_Inbox/readings/YYYY-MM-DD-gmail-<slug>.md`
- 需要 Google API 設定（見下方）

#### Google API 設定（daily-digest --send + gmail-sync 共用）

1. GCP Console → 建專案 → 啟用 **Google Docs API** + **Gmail API**
2. OAuth 同意畫面 → External → 加自己的 Gmail 為測試者
3. 建立 OAuth 桌面應用程式憑證 → 下載 JSON
4. 存為 `config/google-credentials.json`
5. `.env` 加 `DIGEST_EMAIL=you@gmail.com`（daily-digest --send 用）
6. 首次執行會開瀏覽器授權，token 自動存在 `config/google-token.json`
7. 若新增 scope（如 gmail.readonly），需刪除 `config/google-token.json` 重新授權

### 互動學習對話

在 Claude Code 中啟動：
```
/daily-learning
```

流程：讀取 digest → 對每篇內容互動提問 → 歸納洞察 → 自動產出 insights

### 環境變數

| 變數 | 用途 | 必要性 |
|------|------|--------|
| `READWISE_TOKEN` | Readwise v2 + v3 API | readwise-sync / learning-note --readwise |
| `ANYBOX_API_KEY` | Anybox 本地 API | anybox-sync / learning-note --anybox |
| `DIGEST_EMAIL` | Gmail 寄信收件者 | daily-digest --send |
| Google credentials | OAuth 憑證檔 | daily-digest --send / gmail-sync |

### MCP Server（Claude Code 互動式存取）

除了 CLI 批次指令，也可在 Claude Code session 內直接查詢：

| MCP Server | 套件 | 用途 |
|---|---|---|
| Readwise-MCP | `@readwise/readwise-mcp` | 對話中查 highlights、搜尋 Reader 文章 |
| rss-reader | `rss-reader-mcp` | 對話中讀 RSS feed、取得文章全文 |

設定檔：`.mcp.json`（已加入 `.gitignore`，含 API token）

新增 MCP server：
```bash
claude mcp add <name> --scope project -- npx -y <package>
```

### 檔案位置

| 目錄 | 內容 |
|------|------|
| `000_Inbox/readings/` | sync 指令匯入的原文 |
| `300_Learning/input/articles/` | learning-note 產出的學習筆記 |
| `300_Learning/input/books/` | 書籍類筆記 |
| `300_Learning/input/courses/` | 課程類筆記 |
| `300_Learning/input/tech/` | 技術類筆記 |
| `100_Journal/digest/` | daily-digest 產出 |
| `config/subscriptions.opml` | RSS 訂閱清單 |

---

## 6.8 工作管理系統

### 概覽

工作管理系統涵蓋三個場景：**會議紀錄**、**諮詢紀錄**、**專案狀態追蹤**，外加兩個外部資料來源整合（Google Classroom、Fireflies.ai）。

### 會議筆記流程

```
逐字稿/筆記/Google Doc/Fireflies
           │
           ▼
    input_loader（四選一）
           │
           ▼
    meeting_notes.py（LLM）
           │
           ▼
  200_Work/meetings/YYYY-MM-DD-slug/notes.md
```

**四種輸入來源：**

| 來源 | 參數 | 說明 |
|------|------|------|
| 檔案逐字稿 | `--transcript FILE` | Otter.ai 匯出、Mac 聽寫等 |
| 手動筆記 | `--notes "..."` | 快速會議摘要 |
| Google Doc | `--google-doc URL` | Tactiq / Scribbl 自動存檔 |
| Fireflies.ai | `--fireflies` | GraphQL API 拉取（需訂閱） |

**範例：**
```bash
# 從 Otter.ai 匯出的逐字稿
./bin/agent meeting-notes --transcript ~/Downloads/meeting.txt --title "週會" --attendees "Alice, Bob"

# 從 Tactiq 存的 Google Doc
./bin/agent meeting-notes --google-doc "https://docs.google.com/document/d/xxx" --title "客戶會議"

# 快速手動筆記
./bin/agent meeting-notes --notes "討論了 A 方案和 B 方案，決定用 A" --title "技術決策"
```

### 諮詢紀錄流程

與會議筆記共用 `input_loader`，但多了 `--person` 和 `--direction` 參數：

```bash
# 提供諮詢（giving）
./bin/agent consultation-notes --transcript record.txt --title "職涯諮詢" --person "Alice" --direction giving

# 接受諮詢（receiving）
./bin/agent consultation-notes --notes "問了 X 問題，得到 Y 建議" --title "技術顧問" --person "Bob" --direction receiving
```

### 專案狀態追蹤

```bash
# 列出所有專案
./bin/agent project-status

# 更新指定專案的 STATUS.md
./bin/agent project-status dex-agent-os --force
```

讀取 `STATUS.md` + `DECISIONS.md` + `README.md` + 近 30 天 git log，由 LLM 產出更新版 STATUS.md。

### Google Classroom 同步

以**老師角色**存取 Google Classroom API，支援篩選：

```bash
# 列出所有課程
./bin/agent classroom-sync --courses

# 僅活躍課程
./bin/agent classroom-sync --courses --active-only

# 按學生名稱篩選
./bin/agent classroom-sync --courses --student-name "王小明"

# 拉指定課程的公告
./bin/agent classroom-sync --course-id 12345 --announcements --latest 5

# 拉指定課程的作業 + 學生提交
./bin/agent classroom-sync --course-id 12345 --coursework --latest 5
```

> **注意：** 首次使用需在 GCP 啟用 Classroom API + 刪除 `config/google-token.json` 重新授權。

### Fireflies.ai 同步

```bash
# 列出可用逐字稿（無 token 時顯示設定引導）
./bin/agent fireflies-sync --list

# 匯入最近 3 場
./bin/agent fireflies-sync --latest 3 --force
```

匯入後的逐字稿可接 `meeting-notes` 處理：
```bash
./bin/agent meeting-notes --transcript 200_Work/meetings/2026-02-20-slug/transcript.md --title "會議標題"
```

### work-log 工作紀錄整合

`/work-log [日期]` 產出 L1 工作日誌時，會自動掃描當日的會議筆記、諮詢紀錄、專案狀態更新，將參考清單（標題 + 路徑）加入日誌。

**掃描範圍：**

- `200_Work/meetings/{date}-*/notes.md` → 會議筆記
- `200_Work/consultations/{date}-*/notes.md` → 諮詢紀錄
- `400_Projects/*/STATUS.md`（當日修改的）→ 專案狀態

**範例：**

如果 2026-02-20 有以下內容：
```
200_Work/meetings/2026-02-20-weekly/notes.md
200_Work/consultations/2026-02-20-alice/notes.md
400_Projects/dex-agent-os/STATUS.md (2026-02-20 修改)
```

那麼產出的 L1 工作日誌會自動包含：
```markdown
### 今日工作項目參考

**會議**
- 2026-02-20 週會 → `200_Work/meetings/2026-02-20-weekly/notes.md`

**諮詢**
- 2026-02-20 與 Alice 的諮詢 → `200_Work/consultations/2026-02-20-alice/notes.md`

**專案更新**
- dex-agent-os → `400_Projects/dex-agent-os/STATUS.md`
```

這讓 L2 精煉日記自然涵蓋「今天開了什麼會、諮詢了誰、哪些專案有更新」，無需手動複製內容，只保留參考連結。

### 會議轉錄工具整合對照表

| 工具 | 免費額度 | 整合方式 | 備註 |
|------|---------|---------|------|
| **Tactiq** | 10 會議/月 | `--google-doc URL` | 自動存 Google Docs |
| **Scribbl** | 15 會議/月 | `--google-doc URL` | 自動存 Google Docs |
| **Fireflies.ai** | 3 credits | `--fireflies` | 需 Business plan |
| **Otter.ai** | 300 分鐘/月 | `--transcript FILE` | 手動匯出 TXT |
| **Mac 聽寫** | 無限 | `--transcript FILE` | 系統內建 |

---

## 7. 檔案架構與分類

### 編號目錄系統

按「從輸入到輸出」的流向排列：

```
dex-agent-os/
│
├── 000_Inbox/          ← 所有東西的入口
│   ├── ideas/              隨手記的靈感 & 閃念
│   ├── readings/           閱讀摘要 & 筆記
│   └── bookmarks/          待讀 / 待看 / 待聽
│
├── 100_Journal/        ← 每日紀錄
│   ├── daily/
│   │   ├── YYYY-MM-DD.md          L2 精煉日記
│   │   └── YYYY-MM-DD-dayflow.md  Dayflow 活動摘要
│   └── weekly/
│       └── YYYY-Wxx.md            每週回顧（Phase 4）
│
├── 200_Work/           ← 工作
│   ├── meetings/           會議紀錄
│   ├── consultations/      諮詢紀錄（給予 & 接受）
│   ├── code-lab/           程式實驗
│   ├── marketing/          行銷（靈感池 / campaigns / 競品）
│   └── subscriptions/      訂閱 & 工具管理
│
├── 300_Learning/       ← 學習
│   ├── input/              課程 / 書籍 / 技術筆記
│   ├── output/             TIL / 教學文草稿
│   ├── weekly/             每週學習摘要
│   ├── youtube/            YouTube 影片學習筆記（Phase 5a）
│   └── podcasts/           Podcast 消化系統（Phase 5a）
│       ├── episodes/           結構化 episode 筆記
│       ├── weekly/             週度消化報告
│       └── transcripts/        原始逐字稿（gitignore）
│
├── 400_Projects/       ← 專案 & 產品管理
│   ├── software/           軟體專案（STATUS.md / DECISIONS.md）
│   └── products/           產品（overview / roadmap / features / metrics）
│
├── 510_Insights/       ← 洞察素材庫（extract 產出）
│
├── 520_Topics/         ← 主題庫（TOPIC.md → 多頻道草稿）
│   └── <slug>/TOPIC.md
│
├── 530_Channels/       ← 各頻道草稿（按日期資料夾）
│   ├── threads/            Threads（YYYY-MM-DD/<slug>.md）
│   ├── facebook/           Facebook（YYYY-MM-DD/<slug>.md）
│   ├── blog/               WordPress 長文（YYYY-MM-DD/<slug>.md）
│   ├── short-video/        短影音（YYYY-MM-DD/<slug>.md）
│   ├── newsletter/         電子報（YYYY-Wxx-{type}.md）
│   ├── presentations/      簡報
│   └── podcast/            Podcast
│
├── 600_Life/           ← 個人
│   ├── career/             職涯（反思 / 目標 / 機會評估）
│   ├── film/               影評（reviews / analysis / watchlist）
│   └── personal/           個人想法
│
├── 700_Archive/        ← 已發布存檔
│   └── newsletter/ blog/ threads/ facebook/ podcast/ film-reviews/
│
└── 800_System/         ← 系統設定
    ├── templates/          輸出模板（journal / dayflow / consultation...）
    ├── knowledge/          知識萃取歸檔（learnings-archive / reflections-archive / .processed）
    └── references/
        ├── examples/       過去的真實範例（按頻道分）
        └── style-dna/      從範例提取的抽象風格文件
```

### 系統檔案

```
dex-agent-os/
│
├── canonical/          ← 規則的唯一真實來源
│   ├── rules/              00-core / 10-writing-style / 20-safety
│   ├── workflows/          所有 workflow 的 canonical 版本
│   └── skills/             skill 定義
│
├── scripts/            ← Python 腳本
│   ├── generators/         daily_journal.py / daily_dayflow_digest.py / topic_create.py / topic_to_thread.py / topic_to_fb.py / topic_to_blog.py / topic_to_short_video.py / film_review.py / weekly_review.py / weekly_newsletter.py
│   ├── extractors/         journal_knowledge_extract.py（知識萃取）
│   ├── analyzers/          extract_style.py（風格 DNA 萃取）
│   ├── collectors/         threads_collector.py / youtube_transcript.py / podcast_transcript.py
│   ├── publishers/         wp_draft.py（Phase 5）
│   └── lib/                共用模組（llm.py / config.py / file_utils.py / journal_parser.py）
│
├── bin/                ← 可執行腳本
│   ├── agent               CLI 入口
│   └── sync                跨平台同步
│
├── work-log/           ← 從 ~/work-logs/ 合併進來的工具
│   ├── scripts/            extract-sessions.py / post-commit-log.sh
│   └── templates/          daily-template.md
│
├── config/             ← 設定
│   ├── schedules/          launchd plist（Phase 7）
│   └── .env.example        環境變數範本
│
├── context/            ← 系統記憶（有機生長）
│   └── preferences.md / feedback-log.md / topic-registry.md / ...
│
├── data/               ← 原始資料（gitignore）
│   ├── raw/                每日原始收集
│   └── processed/          AI 整理後的中間產物
│
├── .agent/             ← Antigravity 用（bin/sync 產生，勿手改）
├── .cursor/            ← Cursor 用（bin/sync 產生，勿手改）
├── .claude/            ← Claude Code 用（bin/sync 產生，勿手改）
│
├── AGENTS.md           ← 跨平台核心人格（三個 IDE 都讀）
├── CLAUDE.md           ← Claude Code 專案指令
├── PLAN.md             ← 完整專案規劃
└── GUIDE.md            ← 本文件
```

### 檔案分類速查

| 我想要... | 放在 / 找在 |
|-----------|-------------|
| 記一個靈感 | `000_Inbox/ideas/` |
| 看今天的日記 | `100_Journal/daily/YYYY-MM-DD.md` |
| 看螢幕活動分析 | `100_Journal/daily/YYYY-MM-DD-dayflow.md` |
| 記一場會議 | `200_Work/meetings/YYYY-MM-DD-title/notes.md` |
| 記一次諮詢 | `200_Work/consultations/YYYY-MM-DD-person-topic/notes.md` |
| 寫學習筆記 | `300_Learning/input/tech/` 或 `courses/` |
| 追蹤專案進度 | `400_Projects/software/project-name/STATUS.md` |
| 發展一個主題 | `520_Topics/topic-slug/TOPIC.md` |
| 寫 Threads 草稿 | `530_Channels/threads/YYYY-MM-DD/<slug>.md` |
| 寫電子報 | `530_Channels/newsletter/` |
| 存已發布的內容 | `700_Archive/<channel>/` |
| 記 YouTube 學習筆記 | `300_Learning/youtube/` |
| 記 Podcast episode | `300_Learning/podcasts/episodes/` |
| 看本週消化報告 | `300_Learning/podcasts/weekly/` |
| 看累積學到什麼 | `~/.claude/projects/.../memory/learnings.md` |
| 看卡關反思教訓 | `~/.claude/projects/.../memory/reflections.md` |
| 看洞察素材庫 | `510_Insights/` |
| 看全域速查表 | `~/CLAUDE.md` 末尾「## 累積學習」 |
| 看完整學習歷史 | `800_System/knowledge/learnings-archive.md` |
| 改寫作風格規則 | `canonical/rules/10-writing-style.md` → `bin/sync` |
| 加新模板 | `800_System/templates/` |
| 放範例文章 | `800_System/references/examples/<channel>/` |

---

## 8. 跨平台同步

### 核心原則

**只改 `canonical/`，然後跑 `bin/sync`**。永遠不要直接修改 `.agent/`、`.cursor/`、`.claude/` 裡的檔案。

### 同步對照表

```
canonical/rules/*.md
    ├──→ .agent/rules/*.md            （直接複製）
    ├──→ .cursor/rules/*.mdc          （加 YAML frontmatter）
    └──→ CLAUDE.md                    （手動維護，不自動覆蓋）

canonical/workflows/*.md
    ├──→ .agent/workflows/*.md        （加 YAML frontmatter）
    ├──→ .cursor/commands/*.md        （去掉 frontmatter）
    └──→ .claude/commands/*.md        （去掉 frontmatter）

~/.claude/skills/*                    （全域 skills）
    ├──→ ~/.gemini/antigravity/skills/ （複製到 Antigravity 全域）
    └──→ .cursor/commands/            （轉成 Cursor command）

~/.claude/commands/*                  （全域 commands）
    └──→ ~/.gemini/antigravity/global_workflows/（加 YAML frontmatter）
```

### 操作步驟

```bash
# 1. 修改規則（例如寫作風格）
vim ~/dex-agent-os/canonical/rules/10-writing-style.md

# 2. 同步到所有平台
./bin/sync

# 3. 驗證（在各 IDE 中確認）
# Claude Code: 開啟專案 → 輸入 /
# Antigravity: 開啟專案 → 輸入 /
# Cursor: 開啟專案 → 輸入 /
```

### 各 IDE 載入機制

| 檔案 | Claude Code | Antigravity | Cursor |
|------|:-----------:|:-----------:|:------:|
| `AGENTS.md` | 啟動時自動載入 | 啟動時自動載入 | 啟動時自動載入 |
| `CLAUDE.md` | 啟動時自動載入 | — | — |
| Rules | — | 自動載入 | 自動載入（.mdc） |
| Workflows/Commands | 打 `/` 時載入 | 打 `/` 時載入 | 打 `/` 時載入 |
| Skills | 按需載入 | 按需載入 | — |

---

## 9. 模板系統

所有模板位於 `800_System/templates/`。

### 目前可用模板

| 模板 | 用途 | 使用者 |
|------|------|--------|
| `journal-template.md` | L2 精煉日記格式 | `daily_journal.py` |
| `dayflow-digest-template.md` | Dayflow 活動摘要格式 | `daily_dayflow_digest.py` |
| `consultation-notes-template.md` | 諮詢紀錄格式 | 手動填寫（Phase 6 完善） |
| `topic-template.md` | 主題檔案格式（TOPIC.md） | `topic_create.py` |
| `thread-template.md` | Threads 草稿格式 | `topic_to_thread.py` |
| `weekly-review-template.md` | 週回顧格式 | `weekly_review.py` |
| `newsletter-template.md` | 電子報格式（4 種類型） | `weekly_newsletter.py` |
| `podcast-episode-template.md` | Podcast episode 筆記格式 | `podcast_transcript.py` |
| `youtube-note-template.md` | YouTube 學習筆記格式 | `youtube_transcript.py` |
| `podcast-digest-template.md` | 週度消化報告格式 | `podcast_digest.py` |
| `podcast-pptx-template.md` | 簡報結構模板 | `podcast_digest.py --pptx` |
| `fb-post-template.md` | Facebook 貼文格式 | `topic_to_fb.py` |
| `blog-template.md` | 部落格文章格式 | `topic_to_blog.py` |
| `short-video-template.md` | 短影音腳本格式 | `topic_to_short_video.py` |
| `film-review-template.md` | 影評格式 | `film_review.py` |

### L1 工作日誌模板

位於 `work-log/templates/daily-template.md`，由 `/work-log` 指令使用。

### 模板佔位符格式

模板中使用 `{{PLACEHOLDER}}` 格式的佔位符，由 LLM 或腳本替換為實際內容：

```markdown
# {{DATE}}（{{WEEKDAY}}）— 每日精煉日記

## 今日一句話
{{ONE_LINER}}
```

---

## 10. 規則系統

### 三層規則

| 檔案 | 用途 | 適用 |
|------|------|------|
| `canonical/rules/00-core.md` | 身份、決策權限、檔案寫入位置 | 所有操作 |
| `canonical/rules/10-writing-style.md` | 各頻道寫作風格 | 內容產出 |
| `canonical/rules/20-safety.md` | 安全護欄 | 所有操作 |

### 決策權限（IPO 原則）

| 風險等級 | 行為 | 範例 |
|----------|------|------|
| 低風險 — 自動執行 | 整理、摘要、分類、產草稿 | 產出日記、整理筆記 |
| 高風險 — 必須問 Dex | 發布、刪除、金流、對外寄信 | 發 WordPress、刪檔案 |

### 檔案寫入位置規則

| 內容類型 | 輸出位置 |
|----------|----------|
| L2 精煉日記 | `100_Journal/daily/YYYY-MM-DD.md` |
| Dayflow 活動摘要 | `100_Journal/daily/YYYY-MM-DD-dayflow.md` |
| 每週回顧 | `100_Journal/weekly/YYYY-Wxx.md` |
| 靈感/想法 | `000_Inbox/ideas/` |
| 閱讀筆記 | `000_Inbox/readings/` |
| 學習筆記 | `300_Learning/input/` |
| 主題草稿 | `520_Topics/<slug>/` |
| 電子報草稿 | `530_Channels/newsletter/` |
| 各頻道草稿 | `530_Channels/<channel>/YYYY-MM-DD/` |
| 會議紀錄 | `200_Work/meetings/YYYY-MM-DD-title/` |
| 諮詢紀錄 | `200_Work/consultations/YYYY-MM-DD-person-topic/` |
| 專案狀態 | `400_Projects/` |

---

## 11. 常見操作範例

### 場景一：下班前產出完整日記

```bash
# 1. 在 Claude Code 中產出 L1 工作日誌
# （在 Claude Code 對話中輸入）
/work-log

# 2. 在終端機產出 Dayflow 活動摘要
cd ~/dex-agent-os
./bin/agent dayflow

# 3. 在終端機產出 L2 精煉日記（會自動讀取上一步的 Dayflow 摘要）
./bin/agent journal

# 完成！三份檔案已產出：
# ~/work-logs/2026/02/2026-02-08.md          ← L1
# 100_Journal/daily/2026-02-08-dayflow.md    ← Dayflow
# 100_Journal/daily/2026-02-08.md            ← L2
```

### 場景二：補產前幾天的日記

```bash
# 1. 在 Claude Code 中補產 L1（指定日期）
/work-log 2026-02-06

# 2. 補產 Dayflow 摘要
./bin/agent dayflow 2026-02-06

# 3. 補產 L2
./bin/agent journal 2026-02-06
```

### 場景三：修改寫作風格規則

```bash
# 1. 編輯 canonical 規則（唯一真實來源）
vim ~/dex-agent-os/canonical/rules/10-writing-style.md

# 2. 同步到所有 IDE
./bin/sync

# 3. 重開 IDE 或新開 session 即可生效
```

### 場景四：新增一個 workflow

```bash
# 1. 在 canonical 中建立 workflow
vim ~/dex-agent-os/canonical/workflows/my-new-workflow.md

# 2. 同步（自動分發到 .agent/.cursor/.claude）
./bin/sync

# 3. 在 IDE 中用 /my-new-workflow 觸發
```

### 場景五：記錄一次諮詢

```bash
# 1. 複製模板
cp ~/dex-agent-os/800_System/templates/consultation-notes-template.md \
   ~/dex-agent-os/200_Work/consultations/2026-02-08-alice-career/notes.md

# 2. 編輯填入內容
vim ~/dex-agent-os/200_Work/consultations/2026-02-08-alice-career/notes.md
```

### 場景六：從工作紀錄一鍵產出 Threads 草稿

```bash
# 在 Claude Code 中執行完整內容管線（extract → topic-create → topic-to-thread）
/daily-content

# 指定日期
/daily-content 2026-02-09

# 如果 L1 已存在，跳過 work-log 步驟
/daily-content --skip-worklog

# 完成！Threads 草稿已產出：
# 530_Channels/threads/2026-02-09/<slug>.md
```

### 場景七：建立 Style DNA 系統

```bash
# 1. 設定 Threads API token（.env）
# 2. 抓取歷史貼文
./bin/agent collect-threads --limit 100

# 3. 確認抓取結果
ls 800_System/references/examples/threads/

# 4. 萃取風格 DNA
./bin/agent extract-style threads

# 5. 檢查 DNA 內容
cat 800_System/references/style-dna/threads-dna.md
```

### 場景八：產出週回顧 + 電子報

```bash
# 方式 A — 一鍵完成（在 Claude Code 中）
/weekly-content

# 方式 B — 分步執行
./bin/agent weekly-review              # 產出週回顧
./bin/agent weekly-newsletter          # 產出電子報草稿（自動選類型）

# 指定電子報類型
./bin/agent weekly-newsletter --type deep-dive

# 查看產出
cat 100_Journal/weekly/2026-W07.md
cat 530_Channels/newsletter/2026-W07-deep-dive.md
```

### 場景九：萃取日記知識並更新全域記憶

```bash
# 1. 先確認有哪些日記需要處理
./bin/agent extract --dry-run

# 2. 萃取所有未處理的日記
./bin/agent extract

# 3. 檢查結果
cat ~/.claude/projects/-Users-dex-dex-agent-os/memory/learnings.md
cat ~/.claude/projects/-Users-dex-dex-agent-os/memory/reflections.md
ls 510_Insights/

# 4. 滿意後更新全域速查表
./bin/agent extract --global

# 5. 驗證 ~/CLAUDE.md 尾端的「累積學習」區段
tail -40 ~/CLAUDE.md
```

---

## 12. 目前功能狀態

### 已完成（可使用）

| 功能 | 觸發方式 | Phase |
|------|----------|-------|
| 目錄骨架（000-800） | — | 1 |
| 規則系統（core / writing-style / safety） | `canonical/rules/` | 1 |
| 跨平台同步 | `./bin/sync` | 1 |
| 全域 skills 同步（41 個） | `./bin/sync` | 1 |
| 全域 commands 同步（11 個） | `./bin/sync` | 1 |
| L1 工作日誌（支援指定日期） | `/work-log [日期]` | 2 |
| L2 精煉日記 | `./bin/agent journal [日期]` | 2 |
| Dayflow 活動摘要日記 | `./bin/agent dayflow [日期]` | 2 |
| 每日回顧（互動式） | `/daily-review` | 2 |
| 諮詢紀錄模板 | 手動使用模板 | 2（前置） |
| 知識萃取（learnings / blockers / insights） | `./bin/agent extract` | 2.5 |
| 全域速查表更新 | `./bin/agent extract --global` | 2.5 |
| Threads 貼文自動抓取 | `./bin/agent collect-threads` | 3 |
| 風格 DNA 萃取（Threads） | `./bin/agent extract-style threads` | 3 |
| 主題建立（從 insight） | `./bin/agent topic-create` | 3 |
| 主題 → Threads 草稿 | `./bin/agent topic-to-thread` | 3 |
| 每日內容管線（extract → topic → thread） | `/daily-content` | 3 |
| 個人週回顧 | `./bin/agent weekly-review` | 4 |
| 電子報草稿（4 種月度輪替類型） | `./bin/agent weekly-newsletter` | 4 |
| 一鍵週報管線 | `/weekly-content` | 4 |
| YouTube 字幕 → 學習筆記 | `./bin/agent youtube-add` / `/youtube-add` | 5a |
| Podcast 逐字稿 → episode 筆記 | `./bin/agent podcast-add` / `/podcast-add` | 5a |
| Podwise Notion/Readwise 匯入 | `./bin/agent podcast-add --notion/--readwise` | 5a-ext |
| 週度 Podcast & YouTube 消化報告 | `./bin/agent podcast-digest` / `/podcast-weekly` | 5a |
| 簡報結構化內容產出 | `./bin/agent podcast-digest --pptx` | 5a |
| 主題 → Facebook 貼文 | `./bin/agent topic-to-fb` | 5b |
| 主題 → 部落格文章 | `./bin/agent topic-to-blog` | 5b |
| 主題 → 短影音腳本 | `./bin/agent topic-to-short-video` | 5b |
| 影評產出 | `./bin/agent film-review` | 5b |
| 學習筆記（URL / 檔案 / Readwise / RSS / Anybox） | `./bin/agent learning-note` | 5c |
| Readwise 批次匯入（v2 + v3 Reader） | `./bin/agent readwise-sync` | 5c |
| RSS 批次匯入 | `./bin/agent rss-sync` | 5c |
| Anybox 書籤批次匯入 | `./bin/agent anybox-sync` | 5c |
| Gmail 電子報批次匯入 | `./bin/agent gmail-sync` | 5c+ |
| 每日學習消化報告 | `./bin/agent daily-digest` | 5c |
| Google Doc + Gmail 發送 | `./bin/agent daily-digest --send` | 5c |
| 互動學習對話 | `/daily-learning` | 5c |
| 會議筆記（4 種輸入來源） | `./bin/agent meeting-notes` / `/meeting-notes` | 6 |
| 諮詢紀錄（giving/receiving） | `./bin/agent consultation-notes` / `/consultation-notes` | 6 |
| 專案狀態追蹤 | `./bin/agent project-status` / `/project-status` | 6 |
| Google Classroom 同步（老師角色） | `./bin/agent classroom-sync` / `/classroom-sync` | 6 |
| Fireflies.ai 同步（graceful fallback） | `./bin/agent fireflies-sync` / `/fireflies-sync` | 6 |
| 共用輸入載入器（transcript/notes/google-doc/fireflies） | `scripts/lib/input_loader.py` | 6 |

### 尚未實作（計畫中）

| 功能 | 計畫 Phase |
|------|------------|
| 一鍵每日全流程（/daily-all） | 設計完成，待實作 |
| 主題 → LinkedIn 貼文 | 待辦 |
| 產品管理 / 訂閱管理 | Phase 6 P2 |
| launchd 自動排程 | Phase 7 |

---

## 13. 疑難排解

### `/work-log` 更新後沒生效

**原因：** Claude Code 在 session 啟動時快取指令內容，更新後需要開新 session。
**解法：** 關閉目前 Claude Code session，開新的。

### `./bin/agent journal` 提示找不到工作日誌

**原因：** 該日期的 L1 工作日誌不存在。
**解法：** 先執行 `/work-log YYYY-MM-DD` 產出 L1。

### `./bin/agent dayflow` 提示無記錄

**原因：** Dayflow app 在該日沒有運行或沒有記錄。
**解法：** 確認 Dayflow 是否在運行、是否有 `~/Library/Application Support/Dayflow/chunks.sqlite`。

### 互動式確認（y/N）在 Claude Code 中卡住

**原因：** Claude Code 的 Bash 工具不支援 stdin 互動輸入。
**解法：** 使用 `--force` 旗標跳過確認，例如 `./bin/agent journal --force`。

### LLM 產出的日記開頭有英文思考過程

**原因：** `claude --print` 偶爾會輸出思考過程殘留。
**解法：** `daily_dayflow_digest.py` 已內建清理邏輯（自動找到第一個 `#` 標題並去掉之前的內容）。如果 `daily_journal.py` 也遇到，可手動刪除。

### `./bin/agent extract` 顯示「所有日記已處理過」

**原因：** `.processed` JSON 已記錄這些日記的 hash，冪等性檢查判定無需重處理。
**解法：** 如果日記內容有更新，hash 會自動改變並重新處理。如果想強制重處理，加 `--force`。

### `./bin/agent extract --global` 後 `~/CLAUDE.md` 出現多餘文字

**原因：** LLM 偶爾會在速查表之後附加統計或說明文字。
**解法：** 腳本已內建清理邏輯（截斷到 `---` 之前）。如果仍有殘留，手動刪除「## 累積學習」區段之後不需要的內容。

### Insight 檔案全部分到同一個目錄

**原因：** LLM 的 classification 判斷可能偏向某一類。
**解法：** 這是正常的 — 大部分日記洞察確實是 content 類型（有頻道標記）。可以手動調整 classification，將檔案搬到正確目錄。

### `./bin/agent collect-threads` 提示找不到 token

**原因：** `.env` 中沒有 `THREADS_ACCESS_TOKEN`，或 token 已過期。
**解法：**
1. 到 [developers.facebook.com](https://developers.facebook.com) 的 App Dashboard
2. 使用「用戶權杖產生器」（User Token Generator）重新產生 Access Token
3. 更新 `.env` 中的 `THREADS_ACCESS_TOKEN=`

> **注意：** Meta OAuth 的 localhost redirect URI 被封殺，個人開發者請直接用 Dashboard 的用戶權杖產生器，不要走 OAuth 流程。

### `./bin/agent collect-threads` 抓取數量少於預期

**原因：** 部分 Threads 貼文可能是純圖片/影片（無文字），系統會自動跳過。
**解法：** 這是正常行為。例如 `--limit 100` 可能只產出 78 篇有文字的範例。

### `./bin/agent extract-style` 產出的 DNA 不夠精準

**原因：** 範例數量不足。
**解法：** 建議至少 50 篇以上的範例。用 `collect-threads --limit 100` 抓取更多，再重跑 `extract-style threads --force`。

### `./bin/agent podcast-add --notion` 提示 token 未設定

**原因：** `.env` 中沒有 `NOTION_TOKEN` 或 `NOTION_PODWISE_DB_ID`。
**解法：** 依照 GUIDE.md「Podwise 串接設定」完成 Notion Integration 設定。

### `./bin/agent podcast-add --readwise` 提示 token 未設定

**原因：** `.env` 中沒有 `READWISE_TOKEN`。
**解法：** 到 https://readwise.io/access_token 取得 token，存入 `.env`。

### `./bin/agent podcast-add --notion` 回傳 401 錯誤

**原因：** Token 無效，或 Integration 尚未連接到 Podwise 的 Notion database。
**解法：** 確認 Integration 已在 database 的 "Connect to" 中被選取。

### `bin/sync` 的 awk 誤判 YAML frontmatter

**原因：** 如果 Markdown 內容中包含 `---` 分隔線，awk 可能誤認為 frontmatter 結束。
**解法：** 目前為已知限制。避免在 workflow markdown 中使用 `---` 作為分隔線，改用 `***` 或空行。
