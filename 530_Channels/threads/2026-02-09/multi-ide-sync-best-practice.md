---
topic: multi-ide-sync-best-practice
channel: threads
status: draft
created: 2026-02-09
---

你以為用了三套 AI IDE 就是高效，其實你只是在三個地方維護三份會打架的規則。

Claude Code 讀 CLAUDE.md、Cursor 要 .mdc 加 YAML frontmatter、Windsurf 走 .agent/ 三層結構——格式完全不同。你在 Cursor 改了 coding style，Claude Code 根本不知道，等 code review 才發現風格亂掉，返工的時間比你省下的還多。

解法其實很單純：

1. 所有規則只寫在 canonical/ 一個目錄，這是唯一真實來源
2. 用一支 sync 腳本自動轉格式、分發到各 IDE 的設定位置
3. 找出所有 IDE 都能讀的「最大公約數」格式放核心規則，專屬設定才走各自格式
4. 改規則永遠只改一處，sync 負責剩下的事

工具多不是問題，規則散落才是。一個 canonical 目錄加一支腳本，就能讓所有 AI 助手講同一套語言。
