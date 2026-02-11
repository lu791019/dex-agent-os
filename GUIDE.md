# Dex Agent OS — 使用說明書

> 版本：Phase 4 完成 — 週回顧 + 電子報系統
> 最後更新：2026-02-11

---

## 目錄

- [1. 快速開始](#1-快速開始)
- [2. 指令總覽](#2-指令總覽)
- [3. 日記系統完整流程](#3-日記系統完整流程)
- [4. 知識萃取系統](#4-知識萃取系統)
- [5. 內容生產管線](#5-內容生產管線)
- [6. 週回顧與電子報系統](#6-週回顧與電子報系統)
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

### CLI 指令（`bin/agent`）

在終端機或 IDE 的 Terminal 中使用：

| 指令 | 用途 | 輸出位置 |
|------|------|----------|
| `./bin/agent journal [日期] [--force]` | 從 L1 工作日誌產出 L2 精煉日記 | `100_Journal/daily/YYYY-MM-DD.md` |
| `./bin/agent dayflow [日期] [--force]` | 從 Dayflow 螢幕記錄產出活動摘要 | `100_Journal/daily/YYYY-MM-DD-dayflow.md` |
| `./bin/agent extract [日期\|all] [options]` | 從日記萃取知識（學習/反思/靈感） | memory/ + 800_System/knowledge/ + 500_Content/insights/ |
| `./bin/agent collect-threads [--limit N] [--force]` | 從 Threads API 抓取貼文作為風格範例 | `800_System/references/examples/threads/` |
| `./bin/agent extract-style <channel>` | 從範例萃取風格 DNA | `800_System/references/style-dna/<channel>-dna.md` |
| `./bin/agent topic-create <insight-file>` | 從 insight 建立主題 | `500_Content/topics/<slug>/TOPIC.md` |
| `./bin/agent topic-to-thread <topic-slug>` | 主題 → Threads 草稿 | `500_Content/topics/<slug>/threads-draft.md` |
| `./bin/agent weekly-review [日期] [--force]` | 產出個人週回顧 | `100_Journal/weekly/YYYY-Wxx.md` |
| `./bin/agent weekly-newsletter [日期] [--type TYPE] [--force]` | 產出電子報草稿 | `500_Content/newsletter/drafts/YYYY-Wxx-{type}.md` |
| `./bin/agent sync` | 將 canonical/ 規則同步到所有 IDE | `.agent/` `.cursor/` `.claude/` |
| `./bin/agent help` | 顯示使用說明 | 終端機輸出 |

**參數說明：**
- `[日期]`：YYYY-MM-DD 格式，省略則使用今天（extract 預設 `all`）
- `[--force]`：強制覆蓋已存在的檔案（不詢問確認）/ 強制重新處理已萃取的日記
- `[--dry-run]`：只顯示將處理什麼，不寫入任何檔案（僅 extract）
- `[--type TYPE]`：指定萃取類型 learnings / blockers / insights / all（僅 extract，預設 all）
- `[--global]`：同時更新全域 `~/CLAUDE.md` 的「累積學習」區段（僅 extract）
- `[--limit N]`：抓取筆數上限（僅 collect-threads，預設 50）
- `[--token TOKEN]`：直接傳入 Threads API token（僅 collect-threads，預設讀 .env）

### IDE 內指令（Claude Code `/` 指令）

在 Claude Code 對話中輸入：

| 指令 | 用途 | 前置條件 |
|------|------|----------|
| `/work-log` | 產出今天的 L1 完整工作日誌 | 當天有 Claude Code 對話 |
| `/work-log 2026-02-06` | 產出指定日期的 L1 工作日誌 | 該日有 Claude Code 對話記錄 |
| `/daily-journal` | 觸發 daily-journal workflow | 已有 L1 日誌 |
| `/daily-review` | 互動式每日回顧 | 已有 L1 或 L2 日記 |
| `/daily-dayflow-digest` | 觸發 Dayflow 活動摘要 | Dayflow 有記錄 |
| `/daily-content [日期]` | 完整內容管線：L1 → L2 + Dayflow → 6 篇 Threads | 當天有工作記錄 |
| `/weekly-content [日期]` | 完整週報管線：週回顧 + 電子報草稿 | 該週有 L2 日記 |

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
下班前 / 睡前（方式 A — 一鍵完成）：
  1. /daily-content                     → L1 + L2 + Dayflow + 6 篇 Threads 草稿
  2. ./bin/agent extract                → 萃取知識到記憶庫
  3. /daily-review（選用）              → 互動回顧，補充洞察

下班前 / 睡前（方式 B — 分步執行）：
  1. /work-log                         → 產出 L1 完整工作日誌
  2. ./bin/agent dayflow                → 產出 Dayflow 活動摘要
  3. ./bin/agent journal                → 從 L1 產出 L2 精煉日記
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
    └─ 「洞察 & 靈感」→ 500_Content/insights/ 或 000_Inbox/ideas/ 或 600_Life/personal/
```

### 三層分級記憶架構

| 層級 | 位置 | 載入時機 | 行數限制 | 用途 |
|------|------|---------|---------|------|
| 全域速查表 | `~/CLAUDE.md` 末尾 | **所有專案每個 session** | ≤40 行 | 跨專案通用教訓 |
| 專案記憶 | `~/.claude/projects/.../memory/` | **dex-agent-os 每個 session** | learnings ≤120 行、reflections ≤80 行 | 專案內詳細學習 |
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
| `learnings` | 「學到什麼」 | `memory/learnings.md` + `knowledge/learnings-archive.md` | LLM 合併去重，四分類：技術/工具/方法論/認知 |
| `blockers` | 「卡在哪裡」 | `memory/reflections.md` + `knowledge/reflections-archive.md` | LLM 轉化為反思教訓，五分組：資源管理/技術債/決策品質/流程效率/其他 |
| `insights` | 「洞察 & 靈感」 | 依分類分流（見下方） | LLM 分類 + 自動產生個別檔案 |

### Insight 分流

每條洞察由 LLM 判斷分類，自動寫入對應目錄：

| 分類 | 目的地 | 條件 |
|------|--------|------|
| `content` | `500_Content/insights/` | 有明確頻道標記（→ Threads / Blog / Newsletter 等） |
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
  3. ./bin/agent journal                → L2 精煉日記
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
L1 工作日誌  ──→ /daily-content ──→ 3 篇 Threads（Dayflow+L1 視角）
L2 精煉日記  ──→ /daily-content ──→ 3 篇 Threads（L2 視角）
                                      ↑
                              Style DNA（風格指紋）
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
./bin/agent topic-create 500_Content/insights/2026-02-07-xxx.md

# 手動建立
./bin/agent topic-create --title "用 Claude Code 打造個人 Agent OS"

# 列出可用 insights
./bin/agent topic-create
```

**輸出：** `500_Content/topics/<slug>/TOPIC.md`（含核心論點、關鍵素材、頻道適合度、已產出 checklist）

### 主題轉 Threads（topic-to-thread）

從 TOPIC.md 產出 Threads 草稿，自動套用 Style DNA：

```bash
./bin/agent topic-to-thread <topic-slug>          # 產出草稿
./bin/agent topic-to-thread <topic-slug> --force  # 覆蓋既有
```

**輸出：** `500_Content/topics/<slug>/threads-draft.md`（自動更新 TOPIC.md 的 checklist）

### 每日內容管線（/daily-content）

一鍵從工作紀錄產出 6 篇 Threads 草稿的完整管線：

```
/daily-content                    → 今天
/daily-content 2026-02-09         → 指定日期
/daily-content --skip-worklog     → 跳過 L1（已有工作日誌時）
```

**完整流程：**

```
Step 1: L1 工作日誌（/work-log，如不存在自動觸發）
Step 2: Dayflow 活動摘要 + L2 精煉日記（平行執行）
Step 3: 讀取素材 + Style DNA
Step 4: 生成 6 篇 Threads 草稿（兩組各 3 篇，平行執行）
        ├── Dayflow + L1 → 3 篇（日常活動視角）
        └── L2 → 3 篇（深度反思視角）
Step 5: 寫入檔案 + 產出摘要
```

**輸出目錄：**
- `500_Content/topics/YYYY-MM-DD-threads-from-dayflow-l1/`（3 篇）
- `500_Content/topics/YYYY-MM-DD-threads-from-l2/`（3 篇）

> **提醒：** 兩組來源可能產出類似主題（因為同一天的內容），發布前請檢查去重。

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
7 天 L2 日記 + Topics + Insights ──→ 電子報草稿（500_Content/newsletter/drafts/）
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

**輸出：** `500_Content/newsletter/drafts/YYYY-Wxx-{type}.md`

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

### 建議每週操作流程

```
每週日 / 週一：
  1. /weekly-content（或分步）     → 週回顧 + 電子報草稿
  2. 審閱週回顧                    → 可直接發布或作為個人參考
  3. 審閱電子報草稿                → 修改後發送
  4. 發送後歸檔到 500_Content/newsletter/archive/
```

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
│   ├── generators/         daily_journal.py / daily_dayflow_digest.py / topic_create.py / topic_to_thread.py / weekly_review.py / weekly_newsletter.py
│   ├── extractors/         journal_knowledge_extract.py（知識萃取）
│   ├── analyzers/          extract_style.py（風格 DNA 萃取）
│   ├── collectors/         threads_collector.py（Threads API 抓取）
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
| 發展一個主題 | `500_Content/topics/topic-slug/TOPIC.md` |
| 寫 Threads 草稿 | `500_Content/topics/topic-slug/threads-draft.md` |
| 寫電子報 | `500_Content/newsletter/drafts/` |
| 存已發布的內容 | `700_Archive/<channel>/` |
| 看累積學到什麼 | `~/.claude/projects/.../memory/learnings.md` |
| 看卡關反思教訓 | `~/.claude/projects/.../memory/reflections.md` |
| 看洞察素材庫 | `500_Content/insights/` |
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
| 主題草稿 | `500_Content/topics/<slug>/` |
| 電子報草稿 | `500_Content/newsletter/drafts/` |
| 各頻道草稿 | `500_Content/<channel>/queue/` |
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

### 場景六：從工作紀錄一鍵產出 Threads 草稿

```bash
# 在 Claude Code 中執行完整內容管線
/daily-content

# 指定日期
/daily-content 2026-02-09

# 如果 L1 已存在，跳過 work-log 步驟
/daily-content --skip-worklog

# 完成！6 篇 Threads 草稿已產出：
# 500_Content/topics/2026-02-09-threads-from-dayflow-l1/  ← Dayflow+L1 視角 x3
# 500_Content/topics/2026-02-09-threads-from-l2/          ← L2 深度反思 x3
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
cat 500_Content/newsletter/drafts/2026-W07-deep-dive.md
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
ls 500_Content/insights/

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
| 每日內容管線（6 篇 Threads） | `/daily-content` | 3 |
| 個人週回顧 | `./bin/agent weekly-review` | 4 |
| 電子報草稿（4 種月度輪替類型） | `./bin/agent weekly-newsletter` | 4 |
| 一鍵週報管線 | `/weekly-content` | 4 |

### 尚未實作（計畫中）

| 功能 | 計畫 Phase |
|------|------------|
| 其餘頻道（FB / Blog / Podcast / 短影音 / 影評） | Phase 5 |
| 會議筆記 / 諮詢紀錄 workflow | Phase 6 |
| 專案管理 / 訂閱管理 | Phase 6 |
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

### `bin/sync` 的 awk 誤判 YAML frontmatter

**原因：** 如果 Markdown 內容中包含 `---` 分隔線，awk 可能誤認為 frontmatter 結束。
**解法：** 目前為已知限制。避免在 workflow markdown 中使用 `---` 作為分隔線，改用 `***` 或空行。
