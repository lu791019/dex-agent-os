---
topic: nested-skill-invocation-limitation
channel: threads
status: draft
created: 2026-02-22
---

你以為 AI agent 的 skill 不能互相呼叫是 bug，其實這是刻意的設計取捨。

我在做一鍵自動化流程時踩到這個坑——skill 裡面呼叫另一個 skill，不是卡住就是行為亂掉。debug 了一整天才搞懂：

skill 不是函式。函式是同步呼叫棧，skill 是獨立的 LLM 對話 context。巢狀呼叫 = context 套 context，token 直接爆炸，狀態根本追不了。

想通之後，解法其實很簡單：

- 別想「巢狀呼叫」，改想「管線串接」
- 每個 skill 輸出到檔案，下一個 skill 從檔案讀入
- 用檔案系統當 skill 之間的介面
- 好的 agent skill 像 Unix 工具——做一件事、做好、用標準介面串接

Claude Code、Cursor、Copilot 都有這個限制，不是哪家沒做好，是 context window 的物理限制決定了架構邊界。

理解限制，才能設計出真正跑得動的自動化流程，而不是一直在 debug 一個根本不是 bug 的東西。
