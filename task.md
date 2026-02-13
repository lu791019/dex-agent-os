# Journal Knowledge Extraction Tasks

## Project Initialization
- [x] Create task.md and implementation_plan.md
- [x] Create feature branch `feature/journal-knowledge-extraction`
- [x] 記錄架構決策到 MEMORY.md

## Phase 1: 基礎建設
- [x] 新增 config.py 路徑常數（5 個）
- [x] 建立目錄：500_Content/insights/、800_System/knowledge/、000_Inbox/ideas/、scripts/extractors/
- [x] 實作 scripts/lib/journal_parser.py（regex 解析三個區段）

## Phase 2: 核心腳本
- [x] 實作 journal_knowledge_extract.py 骨架（argparse、find_journals、冪等性）
- [x] 實作 process_learnings()（LLM call + marker 解析 + 寫 memory ≤120 行 + archive）
- [x] 實作 process_blockers()（LLM call + 反思 + 寫 memory ≤80 行 + archive）
- [x] 實作 process_insights()（LLM call + JSON 解析 + 寫個別檔案到分流目的地）

## Phase 3: 全域更新（--global）
- [x] 實作 update_global_claude_md()：讀 memory 版 → LLM 精煉 ≤40 行 → 原地替換 ~/CLAUDE.md 的「累積學習」區段
- [x] ~/CLAUDE.md 初始化「累積學習」區段骨架 + 指標觸發 P1/P2 區塊

## Phase 4: CLI 整合
- [x] 修改 bin/agent 新增 extract 入口 + help 更新（含 --global flag）
- [x] 更新 MEMORY.md（如需要）

## Phase 5: 回溯處理 + 驗證
- [x] ./bin/agent extract --dry-run 確認偵測到 3 篇日記
- [x] ./bin/agent extract 處理所有日記
- [x] 驗證 learnings.md ≤ 120 行（實際 21 行）、reflections.md ≤ 80 行（實際 22 行）
- [x] 驗證 insight 檔案分類正確（12 個 insight → 500_Content/insights/）
- [x] 再跑一次確認冪等性（跳過已處理）
- [x] --force 強制重處理正常
- [x] ./bin/agent extract --global 驗證 ~/CLAUDE.md 正確更新（34 行累積學習）
- [x] 確認 ~/CLAUDE.md 原有內容未被破壞（修復 LLM 多餘輸出問題）

## Phase 6: 收尾
- [x] Commit 所有變更
- [x] 產出 walkthrough.md
