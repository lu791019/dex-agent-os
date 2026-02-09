# Journal Knowledge Extraction Implementation Plan

## Goal Description
將每日 L2 精煉日記中的「學到什麼」「卡在哪裡」「洞察 & 靈感」三個高價值區段自動萃取、分類、累積，採用三層分級寫入 + 指標觸發架構，讓 Claude 能跨 session 和跨專案「記住」學習，並將靈感歸檔到正確的內容管線位置。

## User Review Required
> **NOTE**
> - 使用 `claude --print` 呼叫 LLM（走 Pro 訂閱額度，不花 API）
> - **三層分級寫入**：全域速查表（~/CLAUDE.md ≤40 行）→ 專案記憶（memory/ ≤120+80 行）→ 歸檔（800_System/）
> - **指標觸發**：~/CLAUDE.md 末尾 P1/P2 條件控制何時讀取詳細 memory 檔案
> - **--global flag**：手動控制全域 ~/CLAUDE.md 更新（非每次 extract 都更新）
> - LLM 呼叫策略：固定 3 次（learnings / blockers / insights 各一次），不管多少篇日記
> - Insight 分流：content → `500_Content/insights/`、idea → `000_Inbox/ideas/`、personal → `600_Life/personal/reflections/`

## Memory Architecture（方案 D+）

### 三層分級寫入
```
層級 1：全域速查表（~/CLAUDE.md inline）
  ├── ≤40 行 ~500 tokens
  ├── 四分類：工具與環境 / 跨平台 / 工程原則 / 反思教訓
  ├── 每條格式：「情境 + 具體做法/避坑」，可直接套用
  ├── LLM 負責淘汰舊的、合併重複的，維持行數硬限制
  └── 用 --global flag 手動觸發更新

層級 1.5：指標觸發（~/CLAUDE.md 末尾 ~8 行）
  ├── P1 必讀 — Plan Mode 或寫 implementation_plan.md 前
  │     讀 ~/.claude/projects/-Users-dex-dex-agent-os/memory/learnings.md
  │     和 ~/.claude/projects/-Users-dex-dex-agent-os/memory/reflections.md
  ├── P2 選讀 — 同一問題連續失敗 2 次以上，讀 reflections.md
  └── 不讀 — 一般 coding、內容撰寫、git 操作用速查表即可

層級 2：專案記憶（~/.claude/projects/-Users-dex-dex-agent-os/memory/）
  ├── learnings.md ≤120 行 ~1500 tokens（專案內自動載入）
  └── reflections.md ≤80 行 ~1000 tokens（專案內自動載入）

層級 3：歸檔（800_System/knowledge/）
  ├── learnings-archive.md — 完整歷史，不載入，版控
  └── reflections-archive.md — 完整歷史，不載入，版控
```

### LLM 呼叫策略
- 固定 3 次 LLM call（不管多少篇日記）
- Call #1 Learnings：所有新日記的「學到什麼」+ 現有 learnings.md → memory 版 + archive 新增條目
- Call #2 Blockers：所有新日記的「卡在哪裡」+ 現有 reflections.md → memory 版 + archive 新增條目
- Call #3 Insights：所有新日記的「洞察 & 靈感」→ JSON array（classification + slug + metadata）
- 用 `=== OUTPUT_MEMORY ===` / `=== OUTPUT_ARCHIVE ===` marker 分隔 Call #1/#2 的雙輸出
- --global 時多一次 LLM call：將 memory 版精煉為全域速查表（≤40 行）寫入 ~/CLAUDE.md

### 冪等性
- 800_System/knowledge/.processed JSON 追蹤已處理日記的 hash + types
- 相同 hash + 相同 types → 跳過
- hash 變了 → 重新處理
- --force → 忽略記錄

## Proposed Changes

### Project Structure
```
dex-agent-os/
  scripts/
    extractors/
      journal_knowledge_extract.py   [NEW] 主腳本
    lib/
      journal_parser.py              [NEW] 日記區段解析器
      config.py                      [MODIFY] +5 路徑常數
  bin/
    agent                            [MODIFY] +extract 指令
  800_System/
    knowledge/
      learnings-archive.md           [NEW] 完整學習歸檔
      reflections-archive.md         [NEW] 反思完整歸檔
      .processed                     [NEW] 已處理日記追蹤（JSON）
  500_Content/
    insights/                        [NEW] 內容素材目錄
  000_Inbox/
    ideas/                           [NEW] 原始想法目錄
  ~/CLAUDE.md                        [MODIFY] +累積學習區段（≤40 行）+ 指標觸發（~8 行）
  ~/.claude/.../memory/
    learnings.md                     [NEW] 專案 Memory 詳細版（≤120 行）
    reflections.md                   [NEW] 專案 Memory 詳細版（≤80 行）
    MEMORY.md                        [已更新] 已記錄架構決策
```

### Components

- `[NEW] scripts/lib/journal_parser.py`
  用 `## ` heading regex 切割日記，提供 `extract_learnings()`、`extract_blockers()`、`extract_insights()` 三個函式

- `[NEW] scripts/extractors/journal_knowledge_extract.py`
  主腳本：argparse CLI → 掃描日記 → 冪等性檢查 → LLM 呼叫 × 3 → 寫入 memory + archive + insight 檔案
  --global 時額外：讀取 memory 版 → LLM 精煉為全域速查表 → 原地更新 ~/CLAUDE.md 的「累積學習」區段

- `[MODIFY] scripts/lib/config.py`
  新增 5 個路徑常數：INBOX_IDEAS_DIR、CONTENT_INSIGHTS_DIR、LIFE_PERSONAL_DIR、KNOWLEDGE_DIR、CLAUDE_MEMORY_DIR

- `[MODIFY] bin/agent`
  新增 `extract` 指令分支 + help 文字更新

- `[MODIFY] ~/CLAUDE.md`
  末尾新增「## 累積學習」區段（inline ≤40 行 + 指標觸發 ~8 行）
  腳本用 regex 定位 `## 累積學習` 到檔案結尾做原地替換

- `[NEW] 800_System/knowledge/learnings-archive.md`
  Learnings 完整歸檔（含日期，版控）

- `[NEW] 800_System/knowledge/reflections-archive.md`
  Blocker 反思完整歸檔（含日期，版控）

- `[NEW] 800_System/knowledge/.processed`
  JSON — 追蹤已處理日記的 hash（冪等性）

## Verification Plan

### Manual Verification
- `./bin/agent extract --dry-run` 確認偵測到 3 篇日記（02-05, 02-07, 02-08）
- `./bin/agent extract` 處理所有日記，檢查輸出正確性
- 驗證 learnings.md ≤ 120 行、reflections.md ≤ 80 行
- 驗證 insight 檔案正確分類到 500_Content/insights/
- 再跑一次確認冪等性（跳過已處理）
- `--force` 強制重處理正常
- `./bin/agent extract --global` 驗證 ~/CLAUDE.md 正確更新「累積學習」區段
- 確認 ~/CLAUDE.md 原有內容未被破壞

### Automated Tests
- journal_parser.py 的單元測試：三個區段解析正確
- .processed JSON hash 變更偵測
- ~/CLAUDE.md 區段替換邏輯的單元測試
