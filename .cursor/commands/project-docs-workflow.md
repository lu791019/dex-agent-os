
# Project Docs Workflow

## 核心原則

**每份文件解決一個問題，給一種讀者看。** 如果一份文件試圖同時解決兩個問題，就該拆。

```
PLAN（為什麼、做什麼） → 給執行者
  └→ task.md（做到哪了） → 給任何人快速掌握狀態
  └→ implementation_plan.md（怎麼接手） → 給接手的 session/人
GUIDE.md（專案是什麼、怎麼跑） → 給新加入者
```

## 三個判斷原則

### 1. PLAN 是食譜，task.md 是打勾清單

PLAN 包含完整程式碼、檔案路徑、測試命令。task.md 只記錄「做了沒」和 commit hash。**不要在 task.md 重複 PLAN 的內容**，用引用指向即可。

### 2. implementation_plan.md 是 handoff 橋梁

比 PLAN 精簡（摘要級），比 task.md 豐富（有依賴關係和技術要點）。新 session 讀這份就知道怎麼繼續。只在需要 handoff 時才建立。

### 3. GUIDE.md 是活文件

結構固定但內容隨功能完成成長。用 `@GUIDE.md` 注入即可快速理解專案。**Show code, not describe**——用程式碼片段展示慣例。

## 觸發時機

| 事件 | 產出 |
|------|------|
| 接到新功能需求，brainstorming 完成後 | PLAN（design + plan docs） |
| 開始實作第一個 task | task.md |
| Session 即將結束、需要 handoff | implementation_plan.md |
| 專案有基本雛形 / 完成一個 phase | GUIDE.md（新建或更新） |

## Templates

各文件的結構和格式範本見 `references/templates.md`。

## 與相關 Skill 的關係

| Skill | 角色 | 本 Skill 的定位 |
|-------|------|----------------|
| `superpowers:writing-plans` | 產出 PLAN 文件的方法 | 本 skill 管四份文件的整體工作流 |
| `superpowers:brainstorming` | PLAN 之前的設計探索 | 本 skill 在 brainstorming 之後介入 |
| `sdd-bdd-tdd` | 實作階段的驗證方法論 | 本 skill 管文件，不管實作方法 |

## 何時更新這份 Skill

| 情境 | 更新什麼 |
|------|----------|
| 發現新的文件類型需求 | 核心原則 + 觸發時機表 |
| 文件格式迭代改進 | `references/templates.md` |
| 建立流程有新的最佳實踐 | 判斷原則 |
