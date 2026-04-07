---
date: 2026-03-31
source: 100_Journal/digest/2026-03-31-digest.md
classification: content
channel_tags: ["Threads", "Blog"]
status: raw
---

# 系統層決定 Agent 品質，不是模型

TerminalBench 2.0 基準測試顯示：同一個 AI 模型搭配不同的 harness（工具呼叫、context 管理、錯誤處理），排名可以從第 30 名躍升前 5。金融 AI 新創拆掉 LlamaIndex 和 MCP，換成純 Python + 自製 ReAct 引擎後才達到生產等級。

核心洞察：Agent 競爭已從「模型層」轉向「系統層」。與其花時間換模型或調 prompt，不如先把 harness 做好。

## 潛在切入角度
- Threads：一句話版本「你在調 prompt 的時候，高手在調系統」
- Blog：深度拆解 harness engineering 的核心要素（工具定義精確度、context window 管理、失敗恢復），結合 Dex Agent OS 實戰經驗
- 與 Nvidia DLSS 的類比：AI 補幀的邏輯和 agent harness 一樣——重點不是算力/模型多強，而是系統如何聰明利用有限資源
