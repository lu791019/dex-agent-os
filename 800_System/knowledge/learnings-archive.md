# Learnings Archive

## 2026-02-05
- Schema-aware 是核心價值：AI 產出的程式碼必須基於實際資料庫結構，不能盲猜
- Template + AI 混合模式：常見 pattern 用 template，複雜邏輯才用 AI 生成
- 先規劃再動手的紀律很重要，能避免後續大幅架構調整

## 2026-02-07
- Antigravity .agent/ 三層結構：rules → workflows → skills，與 Claude Code 邏輯不同
- AGENTS.md 是跨平台公約數：Claude Code、Cursor、Antigravity 三者都會讀取
- claude --print 走 Pro 額度，腳本自動化不需要額外花 API 費用
- Cursor .mdc 格式需要 YAML frontmatter（description + alwaysApply）

## 2026-02-08
- Dayflow 資料結構：timeline_cards 和 observations 有資料，journal_entries 是 beta 鎖碼
- claude --print 的髒輸出：LLM 回應偶爾夾帶思考過程殘留，需 heuristic 清理
- Claude Code session 快取機制：更新 /command 後必須開新 session 才生效
- Rate limit 並行陷阱：同時跑 6 個 subagent 會瞬間燒完 quota

## 2026-02-05
- **Schema-aware 是核心價值**：AI 產出的程式碼必須基於實際資料庫結構，不能盲猜，這是與一般 Text-to-SQL 工具拉開差距的關鍵
- **Template + AI 混合模式**：常見 pattern 用 template 確保品質，複雜邏輯才用 AI 生成——務實的工程策略
- **先規劃再動手**的紀律很重要，能避免後續大幅架構調整

## 2026-02-07
- **Antigravity .agent/ 三層結構**：rules → workflows → skills，與 Claude Code 的 CLAUDE.md + skills 邏輯不同
- **AGENTS.md 是跨平台公約數**：Claude Code、Cursor、Antigravity 三者都會讀取，適合放核心人格
- **claude --print 走 Pro 額度**：腳本自動化不需要額外花 API 費用
- **Cursor .mdc 格式**：需要 YAML frontmatter（description + alwaysApply），不能直接丟 markdown

## 2026-02-08
- **Dayflow 資料結構**：三張表中只有 timeline_cards 和 observations 有資料，journal_entries 是 beta 鎖碼功能
- **claude --print 的髒輸出**：LLM 回應偶爾夾帶思考過程殘留，腳本層需要 heuristic 清理
- **Claude Code session 快取機制**：`/command` 在 session 啟動時載入，更新指令後必須開新 session 才生效
- **Rate limit 的並行陷阱**：同時跑 6 個 subagent 會瞬間燒完 quota，需要控制並行數量

---

**合併摘要：**

本次新增的學習記錄（2026-02-05、02-07、02-08）全部與現有知識庫中的條目重複，無新增知識點。精簡版知識庫維持原樣不變（共 17 行條目，遠低於 120 行上限）。歸檔區塊則完整記錄了每日原始學習內容，供歷史追溯。

## 2026-02-09
- Meta 用戶權杖產生器遠比 OAuth 簡單：localhost redirect URI 被 Meta 全面封殺，個人開發者直接用 Dashboard 產 token
- Style DNA 萃取效果超出預期：78 篇真實範例的分析精準捕捉寫作風格特徵，比手動整理品質高
- OAuth 嘗試 3 次才轉向：應先查平台限制文件再動手，可省去多輪無效嘗試

## 2026-02-10
- AgentSkill 設計哲學：協議與人格分離、原則導向優於功能導向、測試三問、Level 2/3 Skill 觸發 Skill 架構
- Patchright 不能與已開啟的 Chrome 共存，需先關閉所有 Chrome 程序
- NotebookLM 認證有效期僅 7 天，需建立定期重新認證的提醒機制
- OpenSpec 可作為 Claude Code 的結構化開發流程工具，已完成初始化

## 2026-02-11
- Threads 寫作反 AI 腔：關鍵字植入標題和第一段、重點放倒數第二段、少用 emoji 和括號英文
- 課程定價要拆項：授課費、教材開發、office hour、作業批改、影像上架授權分開計價
- OpenSpec managed block 會吃掉原始內容：CLAUDE.md 裡沒有其他錨定內容時 update 會覆蓋全檔
- Claude Code 記憶路徑編碼：`~/.claude/projects/{path}` 的 `/` 替換成 `-`，`.md` 檔自動注入 system prompt

## 2026-02-12
- **無 API 服務的中介層整合**：Podwise 沒有直接 API，但透過 Notion/Readwise 中介層仍可程式化存取——「沒有 API」不等於「無法整合」，找中介層是常見解法
- **課程拆項定價實證**：用 AI 拆項後發現隱形工作量（QA、履歷諮詢、活動主導）被低估 2-3 倍——比直覺估價靠譜（合併至既有「課程定價要拆項」條目）
- **架構決策品味**：L2 作為「精煉後的單一來源」比擴大 extract 掃描範圍更乾淨，避免兩個入口的複雜度——優先選擇收斂的架構

## 2026-02-21
- **跨平台同步來源唯一性**：直接改 .claude/commands/ 會被 bin/sync 覆蓋白做工，永遠編輯 canonical/ 來源——同步架構下來源唯一是鐵律
- **流程設計先於實作**：先畫完 15 步流程圖再寫 code，省掉大量返工成本（合併至「先規劃再動手」）

---

### 合併說明

1. **「永遠編輯 canonical/ 來源」** → 新增為工具類「**跨平台同步來源唯一性**」，這是具體的工具操作知識，放在工具分類比方法論更適合。

2. **「流程設計先於實作」** → 合併進方法論「**先規劃再動手**」，原本只提到 implementation_plan.md + task.md，現在補充「複雜流程先畫完步驟圖再寫 code」，更完整。

3. 精簡版共 **38 條，約 55 行**（不含標題），在 120 行限制內。
