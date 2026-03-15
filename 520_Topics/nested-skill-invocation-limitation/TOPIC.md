---

```markdown
---
title: 巢狀 Skill 呼叫不是 Bug，是 Agent 架構的設計取捨
status: drafting
source: 510_Insights/2026-02-21-nested-skill-invocation-limitation.md
tags: [AI Agent, Agent Architecture, Composability, IDE Skill, 開發經驗]
created: 2026-02-22
---

# 巢狀 Skill 呼叫不是 Bug，是 Agent 架構的設計取捨

## 核心論點
IDE skill 不能像函式一樣自由巢狀呼叫，這不是沒做好，而是 agent 架構在「可組合性」和「可控性」之間的刻意取捨——理解這個限制，才能設計出真正能跑的自動化流程。

## 關鍵素材
1. **實際踩坑場景**：在設計 `/daily-all` 一鍵流程時，發現 skill 內呼叫另一個 skill 會卡住或行為不可預期，最終改為序列化執行
2. **函式 vs. Skill 的根本差異**：函式是同步呼叫棧，skill 是獨立的 LLM 對話 context——巢狀意味著 context 套 context，token 爆炸且狀態難以追蹤
3. **Agent 架構的 composability 困境**：目前主流 agent 框架（Claude Code、Cursor、Copilot）都面臨同樣問題，組合能力受限於 context window 和對話狀態管理
4. **務實的解法**：把「巢狀呼叫」改成「管線串接」——每個 skill 輸出到檔案，下一個 skill 從檔案讀入，用檔案系統當作 skill 之間的介面
5. **設計啟示**：好的 agent skill 應該像 Unix 工具——做一件事、做好、用標準介面串接，而不是試圖在內部呼叫其他 skill

## 頻道適合度
- ✅ **Threads**：最適合。「你以為是 bug，其實是 by design」的反直覺切角完美契合 Threads 的 hook 結構，150-250 字就能把概念講清楚，目標受眾（開發者、AI 工具使用者）在 Threads 活躍
- ✅ **Facebook**：適合。可以用「我花了一整天 debug 才發現這不是 bug」的故事展開，結尾用開放提問（「你在用 AI agent 時遇過什麼反直覺的限制？」）帶動討論
- ❌ **Newsletter**：單獨成篇太薄，但適合作為週報中「本週技術發現」的一個段落素材
- ✅ **Blog**：可以延伸為「Agent 架構的 Composability 問題」技術文，加入架構圖、程式碼範例、與傳統函式呼叫的對比，SEO 關鍵字潛力高

## 已產出的格式
- [x] Threads
- [x] Facebook
- [ ] Newsletter
- [ ] Blog
- [ ] ShortVideo
- [ ] Podcast
```

---

授權寫入後我會把檔案存到 `520_Topics/nested-skill-invocation-is-by-design/TOPIC.md`。