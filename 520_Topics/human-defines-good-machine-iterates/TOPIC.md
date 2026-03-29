---

```
---
title: 「人類定義好，機器跑迭代」是通用模式
status: drafting
source: 510_Insights/2026-03-29-human-defines-good-machine-iterates.md
tags: [AI工作流, 自動迭代, Autoresearch, prompt工程, 人機協作]
created: 2026-03-29
---

# 「人類定義好，機器跑迭代」是通用模式

## 核心論點
AI 時代最被低估的槓桿不是寫更好的 prompt，而是把「什麼叫好」定義成 yes/no 判準，然後讓機器跑 100 輪你永遠不會手動做的迭代——這個框架適用於任何文字產出。

## 關鍵素材
1. **Karpathy 的 Autoresearch 實驗**：一晚自動跑 100 輪迭代、成本僅 $25，產出品質超越手動調整——說明迭代次數才是品質的真正瓶頸
2. **三檔案機制（task / rubric / output）**：把「好」拆成可評分的 rubric，讓 AI 同時當執行者和評審，形成自我改進迴圈
3. **適用邊界條件**：只要能把品質標準壓縮成 yes/no 問題就能套用——廣告文案、email、Skill 檔案、影片腳本皆可，但高度主觀的藝術創作不適合
4. **人類角色的轉變**：從「親手打磨每一版」變成「定義評判標準 + 抽查最終結果」，是管理者思維而非工匠思維
5. **成本效率對比**：手動改 5 輪 vs. 自動跑 50 輪，時間差 10 倍、品質更穩定——反直覺的是「放手」比「親力親為」產出更好

## 頻道適合度
- ✅ **Threads**：「你還在手動改 prompt 嗎？」的反差開場極適合 Threads 短文的衝擊感，三檔案機制可用條列拆解，結尾用「人類最重要的能力不是寫，是定義什麼叫好」收尾，容易引發轉發
- ✅ **Newsletter**：適合做完整的深度指南——拆解 Autoresearch 原理、三檔案機制、6 個應用場景（文案/email/腳本/Skill/簡報/社群貼文），附實操步驟，是高價值的教學型內容
- ✅ **Facebook**：可以用「我昨晚讓 AI 自動改了 100 次文案」的故事開場，帶出框架概念，FB 適合略長的敘事型貼文，這個主題有足夠的故事張力
- ❌ **Blog**：核心概念一篇 Threads + 一篇 Newsletter 已能完整覆蓋，獨立寫 Blog 會與 Newsletter 內容高度重疊，除非要做成帶程式碼的技術教學才值得另開

## 已產出的格式
- [x] Threads
- [x] Facebook
- [ ] Newsletter
- [ ] Blog
- [ ] ShortVideo
- [ ] Podcast
```

---

寫入路徑：`520_Topics/human-defines-good-machine-iterates/TOPIC.md`

需要你授權寫入權限，我再存檔。