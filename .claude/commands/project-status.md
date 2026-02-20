
# Project Status — 專案狀態更新

讀取專案的 STATUS.md 和 git log，產出最新的專案進度報告。

## 觸發方式

- 指令：`./bin/agent project-status --project <slug>`
- 指令：`./bin/agent project-status --all`（掃描所有專案）
- IDE 內：`/project-status`

## 輸入來源

1. **專案 STATUS.md**：`400_Projects/<slug>/STATUS.md`
2. **Git log**：最近 7 天的 commit 記錄（可用 `--days N` 調整）
3. **Task 檔案**：`400_Projects/<slug>/task.md`（如存在）
4. **Implementation Plan**：`400_Projects/<slug>/implementation_plan.md`（如存在）

## 處理邏輯

1. 掃描 `400_Projects/` 找到目標專案（或全部專案）
2. 讀取現有 STATUS.md（如存在）
3. 讀取該專案目錄下的 git log（`--since` 過濾）
4. 讀取 task.md 的完成狀態（勾選比例）
5. 將以上資訊交給 LLM 更新：
   - 整體進度百分比
   - 本週完成項目
   - 進行中的工作
   - 阻塞問題與風險
   - 下一步優先事項
6. 更新 STATUS.md

## 輸出

- 路徑：`400_Projects/<slug>/STATUS.md`（就地更新）
- `--all` 模式額外產出：`400_Projects/OVERVIEW.md`（所有專案總覽）
- frontmatter：project / updated / phase / progress

## 原則

- **客觀**：進度基於 git log 和 task 勾選，不靠猜測
- **可行動**：阻塞問題要提出解法建議
- **簡潔**：每個專案的狀態報告不超過 30 行
- **繁體中文**
