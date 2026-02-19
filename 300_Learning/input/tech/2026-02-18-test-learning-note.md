---
title: Test Learning Note
source: /Users/dex/dex-agent-os/GUIDE.md
type: tech
date: 2026-02-18
tags: [agent-os, 個人知識管理, 內容自動化, CLI工具]
---
# Test Learning Note

## 一句話摘要
個人 Agent OS 的完整操作手冊，涵蓋日記、知識萃取、多頻道內容生產管線。

## 核心觀點
1. **三層日記管線**：L0 自動記錄 → L1 完整工作日誌 → L2 精煉日記，逐層壓縮，搭配 Dayflow 螢幕行為分析形成完整每日回顧閉環
2. **三層分級記憶架構**：全域速查表（≤40 行）→ 專案記憶（自動注入 session）→ 歸檔（無限制），透過 P1/P2 指標觸發機制控制何時讀取深層記憶，平衡 token 成本與知識可及性
3. **一主題多頻道**：從 Insight 卡片建立 TOPIC.md，再分流產出 Threads / Facebook / Blog / 短影音 / 電子報，所有產出自動套用 Style DNA 風格指紋
4. **冪等性 + LLM 呼叫策略**：知識萃取用 SHA-256 hash 追蹤已處理日記，固定 3 次 LLM 呼叫（不隨日記數量增長），所有呼叫走 `claude --print` Pro 額度零 API 費用
5. **canonical 單一真實來源**：所有規則、workflow 只改 `canonical/` 目錄，`bin/sync` 一鍵同步到 Claude Code / Cursor / Antigravity 三個 IDE，杜絕多份設定不一致

## 關鍵引述
- 「只改 `canonical/`，然後跑 `bin/sync`。永遠不要直接修改 `.agent/`、`.cursor/`、`.claude/` 裡的檔案。」
- 「每次 extract 固定 3 次 LLM 呼叫（learnings / blockers / insights 各一次），不管處理多少篇日記」
- 「低風險 — 自動執行（整理、摘要、分類、產草稿）；高風險 — 必須問 Dex（發布、刪除、金流、對外寄信）」
- 「DNA 會隨著你持續發文而演化（定期重抓 + 重萃取）」

## 實作筆記
- **每日最小流程**：`/daily-content` 一鍵完成 L1 → Dayflow → L2 + 6 篇 Threads 草稿；或分步執行 `/work-log` → `dayflow` → `journal` → `extract`
- **Style DNA 建立**：`collect-threads --limit 100` 抓範例 → `extract-style threads` 萃取 7 維度風格指紋（結構、Hook、語氣、CTA、長度、高互動特徵、禁忌）
- **知識萃取分流**：「學到什麼」→ learnings.md、「卡在哪裡」→ reflections.md、「洞察」→ 依 LLM 分類寫入 `510_Insights/` 或 `000_Inbox/ideas/` 或 `600_Life/personal/`
- **電子報月度輪替**：W1 策展 / W2 深度 / W3 混合 / W4 月度反思，可用 `--type` 覆寫
- **Podwise 串接**：Notion Integration + Readwise Token 設定完成後，`podcast-add --notion --latest 5` 即可自動匯入
- **冪等性機制**：`800_System/knowledge/.processed` JSON 記錄 hash，內容未變不重處理，`--force` 可強制覆蓋

## 我的想法
<!-- 手動補充 -->

## 可轉化為內容
- 🧵 **Threads**：「用 AI 打造個人知識 OS 的 5 個核心設計決策」— 從三層記憶架構、Style DNA、冪等性等角度切入
- 🧵 **Threads**：「我如何用一條指令產出 6 篇社群貼文」— `/daily-content` 的完整流程拆解
- 📰 **Newsletter**：「個人 Agent OS 架構全解析」— 從日記系統到內容管線的設計哲學與技術實作
- 📝 **Blog**：「打造你的 AI 寫作風格指紋：Style DNA 系統設計」— collect → extract → apply 的完整教學
- 🎬 **短影音**：「下班前 5 分鐘，AI 幫你寫完日記 + 6 篇貼文」— 展示 `/daily-content` 一鍵流程
