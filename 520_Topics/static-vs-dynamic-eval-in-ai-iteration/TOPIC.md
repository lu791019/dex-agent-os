---

```
---
title: 靜態 eval vs 動態 eval：AI 迭代的兩種層次
status: drafting
source: "[[2026-03-29-static-vs-dynamic-eval-in-ai-iteration]]"
tags: [AI, eval, prompt-engineering, 內容品質, 自動化迭代]
created: 2026-03-29
---

# 靜態 eval vs 動態 eval：AI 迭代的兩種層次

## 核心論點
AI 自動迭代 prompt 很酷，但真正的瓶頸不是迭代速度，而是「誰來定義什麼是好的」——靜態 eval 讓機器跑得快，動態 eval 讓標準跟著進化，兩者結合才是完整的 AI 品質迴圈。

## 關鍵素材
1. **Autoresearch 的靜態 eval 模式**：用固定 binary 標準（pass/fail）讓 AI 自動迭代 prompt，適合結構明確、對錯分明的任務（如格式檢查、欄位驗證），但碰到主觀品質就觸頂
2. **動態 eval 的三步迴圈**：人類專家審核 → 萃取審核差異 → 寫回評分系統，讓品質標準本身持續進化，而不是永遠拿同一把尺量不同階段的產出
3. **兩者結合的實戰架構**：靜態 eval 負責基礎迭代（跑到 pass 為止），動態 eval 定期升級評分標準（讓 pass 的門檻越來越高），形成「速度 × 品質」雙螺旋
4. **寫作品質的 eval 困境**：文章好不好沒有 binary 答案，用固定 rubric 評分會讓 AI 產出趨向「安全但平庸」，需要動態 eval 注入人類對「好」的最新理解

## 頻道適合度
- ✅ **Threads**：「AI 自動改 prompt 很酷，但誰來定義什麼是好的？」這個切入點天然適合 Threads 的短篇翻轉格式，對工程師和 AI 創作者有即時共鳴，一句話就能勾起討論
- ✅ **Newsletter**：可以展開完整的技術脈絡——從 Autoresearch 的機制講到動態 eval 的設計哲學，適合給想深入理解 AI 迭代方法論的讀者，篇幅足夠放實戰案例
- ❌ **Facebook**：概念偏技術、受眾偏工程師，FB 的泛受眾不容易消化「靜態 vs 動態 eval」的區分，硬寫會變成科普但失去觀點銳度
- ❌ **Blog**：主題有深度但素材密度不夠撐一篇長文，除非補充更多實作案例（如具體的 eval pipeline 設計），否則容易寫成 Newsletter 的加長版而非獨立價值的文章

## 已產出的格式
- [x] Threads
- [x] Facebook
- [ ] Newsletter
- [ ] Blog
- [ ] ShortVideo
- [ ] Podcast
```

---

檔案需要寫入 `520_Topics/static-vs-dynamic-eval-in-ai-iteration/TOPIC.md`，請授權目錄寫入權限，我再存檔。