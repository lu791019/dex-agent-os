
# Project Docs Workflow

## 核心概念

專案開發需要四層文件，各有不同目的和讀者：

```
PLAN（為什麼、做什麼）
  └→ task.md（做到哪了）
  └→ implementation_plan.md（怎麼接手）
GUIDE.md（專案是什麼、怎麼跑）
```

## 四份文件的角色

| 文件 | 目的 | 讀者 | 何時建立 |
|------|------|------|----------|
| **PLAN** | 設計決策 + 完整實作步驟 | 執行者（人或 AI） | 功能規劃完成時 |
| **task.md** | 進度追蹤（checkbox） | 任何人快速掌握狀態 | 開始實作時 |
| **implementation_plan.md** | 執行摘要 + 依賴關係 | 接手的 session/人 | handoff 時 |
| **GUIDE.md** | 專案全貌導覽 | 新加入者或新 session | 專案有基本雛形時 |

## 原則

### PLAN 不等於 task.md

- **PLAN** 是「食譜」：完整程式碼、檔案路徑、測試命令、commit 訊息
- **task.md** 是「購物清單打勾」：只記錄做了沒、commit hash
- 不要在 task.md 重複 PLAN 的內容，用引用指向即可

### implementation_plan.md 是 handoff 橋梁

- 比 PLAN 精簡（摘要級，不含完整程式碼）
- 比 task.md 豐富（有依賴關係、技術要點、前置條件）
- 用途：新 session 讀這份就知道怎麼繼續

### GUIDE.md 是活文件

- 隨功能完成持續更新（新模組、新端點、新慣例）
- 結構固定但內容成長
- 新 session 用 `@GUIDE.md` 注入即可快速理解專案

## 建立流程

### 1. PLAN（設計 + 實作計畫）

**觸發**：接到新功能需求，brainstorming 完成後

**產出位置**：`docs/plans/YYYY-MM-DD-<feature>-design.md` + `docs/plans/YYYY-MM-DD-<feature>-plan.md`

**內容結構**：
- Design doc：架構、資料模型、API、元件、限制條件
- Plan doc：逐 task 的完整實作步驟（含程式碼、測試、commit）

**品質標準**：
- 每個 task 都有明確的檔案清單（Create / Modify / Test）
- 包含完整可執行的程式碼（不是 pseudo code）
- 包含測試命令和預期結果
- 包含 commit 訊息

### 2. task.md（進度追蹤）

**觸發**：開始實作第一個 task 時

**產出位置**：專案根目錄 `task.md`

**內容結構**：
```markdown
# Feature Name — Task Tracker

> **Plan**: `docs/plans/xxx-plan.md`
> **Branch**: `feature/xxx`

## Section A (完成)
- [x] Task 1: Description → `commit_hash`
- [x] Task 2: Description → `commit_hash`

## Section B (待做)
- [ ] Task 3: Description
  - Create: `path/to/file.py`
  - Modify: `path/to/existing.py`

## Notes
- 重要發現或決策變更
```

**原則**：
- 完成的 task 附上 commit hash
- 待做的 task 列出關鍵檔案（方便快速評估範圍）
- 按邏輯分組（如 backend / frontend），不必一個個列

### 3. implementation_plan.md（執行摘要）

**觸發**：session 即將結束、需要 handoff 時

**產出位置**：專案根目錄 `implementation_plan.md`

**內容結構**：
```markdown
# Feature — Implementation Plan

> **完整 plan 見**: `docs/plans/xxx-plan.md`

## 前置條件
- 已完成的 tasks、branch、最後 commit

## 執行順序
- 依賴關係圖（哪些 task 可以並行、哪些有先後）

## 各 Task 摘要
- 每個 task 2-3 行：做什麼、關鍵檔案、驗證方式

## 技術要點
- 接手者需要知道的慣例、坑、注意事項
```

### 4. GUIDE.md（專案導覽）

**觸發**：專案有基本雛形（至少有 backend + frontend 可跑）

**產出位置**：專案根目錄 `GUIDE.md`

**內容結構**：
```markdown
# Project Name — Developer Guide

## 專案概述（1-2 句）
## 快速啟動（backend / frontend / docker）
## 專案結構（tree + 每個目錄的用途）
## 後端慣例（models, schemas, service, router, auth, exceptions）
## 前端慣例（API client, store, routing, UI）
## API 端點一覽（表格）
## 測試方式
## 資料庫 + Migration
## 外部整合（LLM, storage, etc.）
## 開發進度（phase tracker）
## 相關文件連結
```

**原則**：
- 用程式碼片段展示慣例（不要只描述，要 show code）
- 保持可執行：複製貼上就能跑
- 隨新功能更新（每完成一個 phase 更新一次）

## 文件之間的關係

```
需求進來
  │
  ▼
PLAN（brainstorm → design doc → implementation plan）
  │
  ├→ task.md（開始實作時建立，逐步勾選）
  │
  ├→ implementation_plan.md（handoff 時建立/更新）
  │
  └→ GUIDE.md（功能完成後更新）
```

## 何時更新這份 Skill

| 情境 | 更新什麼 |
|------|----------|
| 發現新的文件類型需求 | 四份文件的角色表 |
| 文件格式迭代改進 | 對應的內容結構 |
| 建立流程有新的最佳實踐 | 建立流程章節 |
