# Journal Knowledge Extraction Walkthrough

從 L2 精煉日記中自動萃取「學到什麼」「卡在哪裡」「洞察 & 靈感」三類知識，採用三層分級寫入 + 指標觸發架構，讓 Claude 跨 session 和跨專案累積學習。使用 Python + `claude --print`（Pro 訂閱額度）實作，含冪等性追蹤和全域更新機制。

## Changes Implemented

### Core Features
- **journal_parser.py**：用 regex 切割日記 `## ` heading，提供 `extract_learnings()`、`extract_blockers()`、`extract_insights()` 三個函式
- **journal_knowledge_extract.py**：主腳本（490 行），含 argparse CLI、冪等性（SHA-256 hash 追蹤）、固定 3 次 LLM 呼叫、`=== OUTPUT_MEMORY ===` / `=== OUTPUT_ARCHIVE ===` marker 分隔雙輸出
- **process_learnings()**：合併新舊學習記錄，四分類（技術/工具/方法論/認知），寫入 memory ≤120 行 + archive
- **process_blockers()**：合併新舊卡關記錄為深度反思，五分組（資源管理/技術債/決策品質/流程效率/其他），寫入 memory ≤80 行 + archive
- **process_insights()**：LLM 輸出 JSON array，每個 insight 自動分流（content → 500_Content/insights/、idea → 000_Inbox/ideas/、personal → 600_Life/personal/）

### Global Update（--global flag）
- **update_global_claude_md()**：讀取 memory 版 → LLM 精煉 ≤40 行全域速查表 → 原地替換 `~/CLAUDE.md` 的「累積學習」區段
- **指標觸發**：P1（Plan Mode 前必讀 memory 檔案）、P2（連續失敗 2 次讀 reflections）、不讀（日常操作）

### CLI Integration
- **bin/agent extract**：`[date|all] [--type TYPE] [--force] [--dry-run] [--global]`

## Verification Results

### 1. Dry-run 偵測
- **Action**：`./bin/agent extract --dry-run`
- **Result**：正確偵測 3 篇日記（02-05, 02-07, 02-08），顯示各類型處理數量

### 2. 實際萃取
- **Action**：`./bin/agent extract`
- **Result**：
  - learnings.md：21 行（4 技術 + 5 工具 + 2 方法論 + 1 認知）
  - reflections.md：22 行（2 資源管理 + 4 技術債 + 2 決策品質 + 1 流程效率）
  - 12 個 insight 檔案全部分類到 500_Content/insights/
  - .processed JSON 正確記錄 3 篇日記的 hash 和處理類型

### 3. 冪等性
- **Action**：再次執行 `./bin/agent extract`
- **Result**：「所有日記已處理過（用 --force 強制重新處理）」— 正確跳過

### 4. --force 重處理
- **Action**：`./bin/agent extract --force --type learnings --global`
- **Result**：重新處理 learnings + 更新 ~/CLAUDE.md 累積學習區段（34 行）

### 5. ~/CLAUDE.md 完整性
- **Action**：檢查 ~/CLAUDE.md 原有內容
- **Result**：原有 146 行開發流程文件完整保留，累積學習區段正確附加在末尾

## Next Steps
- Phase 3（PLAN.md）的 topic-create + style-dna extraction 可利用 500_Content/insights/ 的素材
- 週報系統（Phase 4）可從 memory/learnings.md + reflections.md 彙整週度回顧
- 未來可加入 `--type insights --channel Threads` 篩選特定頻道的 insight
