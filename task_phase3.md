# Phase 3 Tasks: Content Pipeline + Threads Collector

## Section 0: 規劃文件
- [x] 建立 implementation_plan_phase3.md
- [x] 建立 task_phase3.md
- [x] 更新 PLAN.md Phase 3 區塊

## Section 1: 基礎設施
- [x] 1. 模板：topic-template.md、thread-template.md
- [x] 2. Workflow：topic-create.md、topic-to-thread.md、extract-style.md
- [x] 3. 更新 config.py（新增 THREADS_TOKEN_PATH）
- [x] 4. 更新 .gitignore + .env.example

## Section 2: Threads Collector
- [x] 5. 實作 threads_collector.py（改為直接 token，移除 OAuth）
- [x] 6. 更新 bin/agent（collect-threads 指令）
- [x] 7. 設定 Meta App + 執行 collect-threads 抓取 38 篇範例 ✅

## Section 3: Style DNA
- [x] 8. 實作 extract_style.py
- [x] 9. 更新 bin/agent（extract-style 指令）
- [x] 10. 執行 extract-style threads 產出 threads-dna.md ✅

## Section 4: 內容生產管線
- [x] 11. 實作 topic_create.py
- [x] 12. 實作 topic_to_thread.py
- [x] 13. 更新 bin/agent（topic-create、topic-to-thread 指令）

## Section 5: 驗證 + 收尾
- [x] 14. 端到端測試：insight → topic-create → topic-to-thread ✅
- [x] 15. bin/sync 同步新 workflow ✅
- [ ] 16. 更新 GUIDE.md + PLAN.md
- [ ] 17. Commit
