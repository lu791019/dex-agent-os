---
topic: multi-ide-sync-best-practice
channel: threads
status: draft
created: 2026-05-20
---

你以為多開幾個 AI IDE 是生產力加成，其實你只是在養三份會慢慢吵架的規則檔。

Claude Code 讀 CLAUDE.md、Cursor 要 .mdc 加 YAML frontmatter、Windsurf 走 .agent/ 三層結構——格式全不一樣。你在 Cursor 改了 coding style，Claude Code 根本不知道，等 code review 才發現風格不一致要返工。

我自己的解法只有一句：規則只寫一個地方。

連結：https://www.notion.so/36552f3feb91814ab564ef2a897cf40c

留言處接著講 canonical 怎麼運作。

---

canonical 單一真實來源，做法其實很笨但很有效：

所有規則寫在 canonical/ 一個目錄，跑一支 bin/sync 腳本，自動轉成各 IDE 的格式、丟到它們各自的設定位置。改規則只改一處，其餘自動分發。

幾個踩過的坑：

sync 腳本要處理 YAML frontmatter 注入，還有「awk 解析遇到 --- 分隔線會誤判」這種眉角，別用土炮 parser。

規則要分三層：rules 永遠載入、workflows 觸發載入、skills 按需載入，全載入只會塞爆 context。

還有一條鐵律——「永遠不要直接編輯 .agent/、.cursor/、.claude/ 裡的同步檔案」，那些是產物，不是原始碼。

工具不是重點，單一真實來源才是。你現在是幾個 AI IDE 各養一份規則？
