---
source: "[[static-vs-dynamic-eval-in-ai-iteration/TOPIC]]"
topic: static-vs-dynamic-eval-in-ai-iteration
channel: threads
status: draft
created: 2026-03-29
---

兩個檔案都需要你授權寫入，先直接輸出 Threads 草稿：

---

**【主文】**

你以為讓 AI 自動跑 prompt 優化就是迭代，其實那只是迭代的一半。

另一半多數人根本沒碰——不是怎麼跑更快，是誰來定義「跑對了」。

最近在研究自動化 prompt 優化，發現一個有趣的現象：同樣的框架，有些任務三輪收斂，有些二十輪還卡在同一個水準。

差別不在速度。在你拿什麼尺在量。

---

**【串文】**

背後其實是兩種完全不同的 eval 邏輯：

**靜態 eval** — 寫死標準，pass 或 fail。格式對不對、欄位有沒有漏，讓 AI 自己跑就好。但碰到「這段文案好不好」，固定 rubric 只會逼出安全但平庸的東西。

**動態 eval** — 人類審一輪，把「這次覺得好或不好」的差異萃取回評分系統。不是永遠拿同一把尺，而是讓尺跟著你的標準一起長。

完整的迴圈是兩者結合：靜態 eval 把速度跑起來，動態 eval 讓 pass 的門檻持續墊高。

AI 跑得快是工程問題，定義什麼叫好是設計問題——你解了哪一個？
