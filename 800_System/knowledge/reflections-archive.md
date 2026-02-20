# Reflections Archive

## 2026-02-05
- 尚未做競品分析，不確定市場上已有方案的深度，可能導致定位不夠差異化
- 缺少真實使用者回饋來驗證功能優先順序，目前的模組排序是基於直覺
- LLM 產生 Airflow DAG 的品質尚未驗證，這是 Phase 2 的技術風險

## 2026-02-07
- Rate limit 反覆觸發：大量對話 + 多 session 導致頻繁撞限，購買 Extra usage 暫時緩解
- bin/sync 的 awk 處理 YAML frontmatter 偏脆弱：markdown 內含 `---` 分隔線會誤判

## 2026-02-08
- Rate limit 三連斷：上午、下午、晚間各觸發一次，三項工作全部中斷
- 多專案並行的代價：同時推進三個專案，資源分散導致沒有一項能完整收尾
- 技術債累積：bin/sync awk 脆弱、LLM 回應清理 heuristic、feature branch 未合併

## 2026-02-09
- OAuth redirect URI 連環失敗：花 20 分鐘嘗試 localhost/https/Postman callback，根因是沒先讀 Meta 平台限制文件
- 注意力碎片化：上午 HR 表單、銀行驗證、面試改期等雜務穿插，下午才進入開發，context switch 成本明顯
- 技術債累積：Threads API token 60 天過期需手動更新；collector 無 rate limiting 保護

## 2026-02-10
- Rate limit 反覆觸發：多 session 切換 + 高 token 消耗，每日內容管線無法完成首次執行
- 工作日誌 / 文件修改未 commit：變更停留在 working tree 有遺失風險
- 注意力分散：MCP 插件、NotebookLM、AgentSkill、OpenSpec 四條線同時推進，每條都淺嚐即止

## 2026-02-11
- Rate limit 兩次中斷：上午 10:48 撞 session limit 浪費 ~15 分鐘，Agent Skills 優化因 limit 未完成
- Context switch 過載：開發 → 課程定價 → 工具研究 → 工作坊 → 教學，五面向切換導致深度工作被切碎
- nvm/npm globalconfig 衝突：`~/.npmrc` prefix 與 nvm 不相容，僅繞過未根治

---

**合併摘要：**

| 操作 | 說明 |
|------|------|
| 🔀 合併 | 「Rate Limit 資源耗盡」+ 2/10、2/11 新 rate limit 記錄 → 升級為「Rate Limit 慢性失血」（連續五天模式） |
| 🔀 合併 | 「多專案並行失控」+ 2/9、2/10、2/11 注意力分散 → 升級為「注意力碎片化」（含雜務穿插、工具探索混合） |
| ➕ 新增 | 決策品質：「未讀文件就動手」（OAuth 教訓） |
| ➕ 新增 | 技術債：「API Token / 環境設定欠缺自動化」（token 過期 + 無 rate limiter + 未 commit） |
| ➕ 新增 | 技術債：「nvm/npm globalconfig 衝突未根治」 |
| ➕ 新增 | 流程效率：「雜務與開發混合降低產出」（從注意力碎片化中拆出可執行策略） |
| 📊 行數 | 精簡版共 30 行內容（含標題空行共約 45 行），在 80 行限制內 ✅ |

## 2026-02-12
- **Context switch 成本**：上午同時處理非技術（定價提案）和技術（Agent OS）任務，切換有摩擦。Dayflow 數據顯示提案階段實際高度聚焦，真正切換發生在提案前後過渡期
- **提案收尾拖延**：Dayflow 捕捉到約 6 分鐘靜止期，可能反覆猶豫措辭。LINE 提案花了近 2 小時，下次先在 markdown 定稿再貼
- **Podwise 實作待啟動**：Notion API / Readwise API 研究完成但串接尚未動手
