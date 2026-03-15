---
topic: nested-skill-invocation-limitation
channel: facebook
status: draft
created: 2026-02-22
---

我花了一整天 debug 一個「bug」，最後發現——它根本不是 bug。

事情是這樣的。我在設計一個一鍵執行的自動化流程，需要在一個 AI skill 裡面呼叫另一個 skill。聽起來很合理吧？就像函式呼叫函式一樣自然。

結果，卡住了。行為不可預期，狀態亂掉，怎麼調都不對。

直到我退一步想，才搞懂這不是實作問題，而是架構的刻意取捨。

函式呼叫是同步的呼叫棧，A 叫 B，B 回傳，乾淨俐落。但 AI skill 不一樣——每個 skill 本質上是一段獨立的 LLM 對話 context。巢狀呼叫意味著 context 套 context，token 爆炸，狀態根本追不動。

這不是某個工具沒做好。Claude Code、Cursor、Copilot——目前主流的 agent 框架全都面臨同樣的限制。組合能力被 context window 和對話狀態管理卡死了。

想通之後，解法反而很簡單：別硬塞巢狀，改用管線串接。每個 skill 做完把結果寫到檔案，下一個 skill 從檔案讀入。用檔案系統當 skill 之間的介面。

聽起來很土對吧？但這就是 Unix 哲學——每個工具做好一件事，用標準介面串起來。半世紀前的設計智慧，在 AI agent 時代依然成立。

這件事給我最大的啟發是：當你在用新工具時，撞牆的第一反應通常是「這東西有 bug」。但很多時候，那個限制是設計者在兩個矛盾的目標之間做的取捨。理解取捨，你才能繞過它，而不是跟它對著幹。

你在用 AI 工具自動化工作流程時，有遇過什麼「以為是 bug，後來發現是 by design」的經驗嗎？
