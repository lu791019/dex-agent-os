# Dex Agent OS — 使用說明書

> 版本：Phase 2 完成
> 最後更新：2026-02-08

---

## 目錄

- [1. 快速開始](#1-快速開始)
- [2. 指令總覽](#2-指令總覽)
- [3. 日記系統完整流程](#3-日記系統完整流程)
- [4. 檔案架構與分類](#4-檔案架構與分類)
- [5. 跨平台同步](#5-跨平台同步)
- [6. 模板系統](#6-模板系統)
- [7. 規則系統](#7-規則系統)
- [8. 常見操作範例](#8-常見操作範例)
- [9. 目前功能狀態](#9-目前功能狀態)
- [10. 疑難排解](#10-疑難排解)

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
```

---

## 2. 指令總覽

### CLI 指令（`bin/agent`）

在終端機或 IDE 的 Terminal 中使用：

| 指令 | 用途 | 輸出位置 |
|------|------|----------|
| `./bin/agent journal [日期] [--force]` | 從 L1 工作日誌產出 L2 精煉日記 | `100_Journal/daily/YYYY-MM-DD.md` |
| `./bin/agent dayflow [日期] [--force]` | 從 Dayflow 螢幕記錄產出活動摘要 | `100_Journal/daily/YYYY-MM-DD-dayflow.md` |
| `./bin/agent sync` | 將 canonical/ 規則同步到所有 IDE | `.agent/` `.cursor/` `.claude/` |
| `./bin/agent help` | 顯示使用說明 | 終端機輸出 |

**參數說明：**
- `[日期]`：YYYY-MM-DD 格式，省略則使用今天
- `[--force]`：強制覆蓋已存在的檔案（不詢問確認）

### IDE 內指令（Claude Code `/` 指令）

在 Claude Code 對話中輸入：

| 指令 | 用途 | 前置條件 |
|------|------|----------|
| `/work-log` | 產出今天的 L1 完整工作日誌 | 當天有 Claude Code 對話 |
| `/work-log 2026-02-06` | 產出指定日期的 L1 工作日誌 | 該日有 Claude Code 對話記錄 |
| `/daily-journal` | 觸發 daily-journal workflow | 已有 L1 日誌 |
| `/daily-review` | 互動式每日回顧 | 已有 L1 或 L2 日記 |
| `/daily-dayflow-digest` | 觸發 Dayflow 活動摘要 | Dayflow 有記錄 |

### 跨 IDE 共用指令

以下指令在三個 IDE 中都可使用（透過 `bin/sync` 同步）：

| IDE | 觸發方式 |
|-----|----------|
| Claude Code | `/daily-journal`、`/daily-review`、`/daily-dayflow-digest` |
| Antigravity | `/daily-journal`、`/daily-review`、`/daily-dayflow-digest` |
| Cursor | `/daily-journal`、`/daily-review`、`/daily-dayflow-digest` |

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

從 L1 工作日誌提煉出精華，壓縮到 1/3 ~ 1/5 長度。

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
下班前 / 睡前：
  1. /work-log                         → 產出 L1 完整工作日誌
  2. ./bin/agent dayflow                → 產出 Dayflow 活動摘要
  3. ./bin/agent journal                → 從 L1 產出 L2 精煉日記
  4. /daily-review（選用）              → 互動回顧，補充洞察
```

---

## 4. 檔案架構與分類

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
│   └── weekly/             每週學習摘要
│
├── 400_Projects/       ← 專案 & 產品管理
│   ├── software/           軟體專案（STATUS.md / DECISIONS.md）
│   └── products/           產品（overview / roadmap / features / metrics）
│
├── 500_Content/        ← 內容生產管線
│   ├── topics/             主題庫（TOPIC.md → 多頻道草稿）
│   ├── newsletter/         電子報（drafts / archive）
│   ├── threads/            Threads（queue / posted）
│   ├── facebook/           Facebook
│   ├── blog/               WordPress 長文
│   ├── podcast/            Podcast
│   └── short-video/        短影音
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
│   ├── generators/         daily_journal.py / daily_dayflow_digest.py
│   ├── analyzers/          extract_style.py（Phase 3）
│   ├── collectors/         discord_collector.py（future）
│   ├── publishers/         wp_draft.py（Phase 5）
│   └── lib/                共用模組（llm.py / config.py / file_utils.py）
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
| 發展一個主題 | `500_Content/topics/topic-slug/TOPIC.md` |
| 寫 Threads 草稿 | `500_Content/topics/topic-slug/threads-draft.md` |
| 寫電子報 | `500_Content/newsletter/drafts/` |
| 存已發布的內容 | `700_Archive/<channel>/` |
| 改寫作風格規則 | `canonical/rules/10-writing-style.md` → `bin/sync` |
| 加新模板 | `800_System/templates/` |
| 放範例文章 | `800_System/references/examples/<channel>/` |

---

## 5. 跨平台同步

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

## 6. 模板系統

所有模板位於 `800_System/templates/`。

### 目前可用模板

| 模板 | 用途 | 使用者 |
|------|------|--------|
| `journal-template.md` | L2 精煉日記格式 | `daily_journal.py` |
| `dayflow-digest-template.md` | Dayflow 活動摘要格式 | `daily_dayflow_digest.py` |
| `consultation-notes-template.md` | 諮詢紀錄格式 | 手動填寫（Phase 6 完善） |

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

## 7. 規則系統

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
| 主題草稿 | `500_Content/topics/<slug>/` |
| 電子報草稿 | `500_Content/newsletter/drafts/` |
| 各頻道草稿 | `500_Content/<channel>/queue/` |
| 會議紀錄 | `200_Work/meetings/YYYY-MM-DD-title/` |
| 諮詢紀錄 | `200_Work/consultations/YYYY-MM-DD-person-topic/` |
| 專案狀態 | `400_Projects/` |

---

## 8. 常見操作範例

### 場景一：下班前產出完整日記

```bash
# 1. 在 Claude Code 中產出 L1 工作日誌
# （在 Claude Code 對話中輸入）
/work-log

# 2. 在終端機產出 Dayflow 活動摘要
cd ~/dex-agent-os
./bin/agent dayflow

# 3. 在終端機產出 L2 精煉日記
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

---

## 9. 目前功能狀態

### 已完成（可使用）

| 功能 | 觸發方式 | Phase |
|------|----------|-------|
| 目錄骨架（000-800） | — | 1 |
| 規則系統（core / writing-style / safety） | `canonical/rules/` | 1 |
| 跨平台同步 | `./bin/sync` | 1 |
| L1 工作日誌（支援指定日期） | `/work-log [日期]` | 2 |
| L2 精煉日記 | `./bin/agent journal [日期]` | 2 |
| Dayflow 活動摘要日記 | `./bin/agent dayflow [日期]` | 2 |
| 每日回顧（互動式） | `/daily-review` | 2 |
| 諮詢紀錄模板 | 手動使用模板 | 2（前置） |
| 全域 skills 同步（41 個） | `./bin/sync` | 1 |
| 全域 commands 同步（11 個） | `./bin/sync` | 1 |

### 尚未實作（計畫中）

| 功能 | 計畫 Phase |
|------|------------|
| 主題建立 / topic-to-thread | Phase 3 |
| 風格 DNA 提取 | Phase 3 |
| 週報 / 電子報自動產出 | Phase 4 |
| 其餘頻道（FB / Blog / Podcast / 短影音 / 影評） | Phase 5 |
| 會議筆記 / 諮詢紀錄 workflow | Phase 6 |
| 專案管理 / 訂閱管理 | Phase 6 |
| launchd 自動排程 | Phase 7 |

---

## 10. 疑難排解

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

### `bin/sync` 的 awk 誤判 YAML frontmatter

**原因：** 如果 Markdown 內容中包含 `---` 分隔線，awk 可能誤認為 frontmatter 結束。
**解法：** 目前為已知限制。避免在 workflow markdown 中使用 `---` 作為分隔線，改用 `***` 或空行。
