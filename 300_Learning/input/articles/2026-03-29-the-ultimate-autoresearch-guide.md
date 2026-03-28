---
title: The Ultimate Autoresearch Guide
source: https://www.aibyaakash.com/p/autoresearch-guide?lli=1
type: articles
date: 2026-03-29
tags: [autoresearch, AI-automation, prompt-optimization, Karpathy, self-improving-systems]
---
# The Ultimate Autoresearch Guide

## 一句話摘要
Karpathy 的 autoresearch 迴圈能自動迭代優化任何可量化的產出。

## 核心觀點
1. **核心機制極簡**：三個檔案驅動——一個可編輯檔（被優化的目標）、一個鎖定的評分標準、一個人類撰寫的指令檔。每輪改一處，分數提升就 git commit，下降就 git reset
2. **超越 ML 的通用模式**：只要滿足三個條件——產出可用數字評分、評分不需人類介入、每輪只改一個檔案——這個迴圈就適用於廣告文案、email、影片腳本、技能檔等任何領域
3. **Eval 是成敗關鍵**：評分標準必須是 binary（yes/no），3-6 題最佳。模糊標準、中途修改 eval、或題目過多是三大致命錯誤
4. **成本極低、產出驚人**：每小時 12 輪迭代，整晚約 100 輪、$25 美元。Karpathy 跑兩天找到 20 個手動優化漏掉的改進；Shopify CEO 一晚 93 次自動 commit 讓模板渲染快 53%
5. **人類的角色是定義「好」**：人負責寫出 yes/no 評分問題，機器負責跑 50 輪你永遠不會手動做的迭代

## 關鍵引述
- "Three files power the system. One file the agent edits. One file the agent can never touch. And one instruction file written by the human that tells the agent what to try and how to behave."
- "Score went up? The change gets committed to git. Score went down or stayed flat? git reset wipes it clean."
- "The moment you introduce a 1-7 rating, the agent starts optimizing for 4s that technically score well but read like garbage."
- "If the agent could edit the scoring criteria too, it would just make the test easier instead of making the output better."
- "The creative ideas are still yours. The structural consistency is the machine's job."
- "Most marketing teams run ~30 experiments a year. This loop runs 36,500+."

## 實作筆記
- **Setup 三步驟**：`git clone` Karpathy repo → 撰寫 binary eval 標準 → 一段 prompt 啟動 Claude Code 迴圈
- **Eval 撰寫法**：從「現在產出哪裡爛」反推 yes/no 問題，例如「標題有沒有具體數字？」「有沒有禁用詞？」
- **適用工具**：Claude Code、Cursor、Windsurf、Codex、Antigravity——任何能讀寫檔案＋用 git 的 coding agent
- **六個即用場景**：① 自我改進的 Skill 檔 ② Cold email ③ 廣告文案 ④ 短影音腳本 ⑤ Onboarding email 序列 ⑥ 職缺描述
- **三大地雷**：❌ 模糊 eval（「文案有沒有吸引力」→ 無法評分）❌ 中途改 eval（數據全廢）❌ 超過 6 題（agent 開始刷 checklist 而非提升品質）
- **進階**：連接 email/廣告平台 API + GitHub Actions cron，可做到 live 持續優化

## 我的想法
Autoresearch 的核心不是 ML 工具，而是「定義好什麼是好的，讓機器跑你不會手動做的 50 輪迭代」這個概念。我的做法更進一步 — 不用固定 binary eval，而是讓人類專家當 eval function，再萃取審核前後的抽象差異存進系統（style-dna/rules），形成持續進化的品質標準。Autoresearch 是靜態 eval + 自動迭代，我的做法是動態 eval + 知識萃取，兩者可以結合。

## 可轉化為內容
- **Threads 主題**：「Karpathy 的 autoresearch 不只是 ML 工具——它是任何 AI 產出的自動 A/B testing 框架」，拆解三個檔案機制 + eval 撰寫心法
- **Threads 主題**：「你的 AI Skill 還是靜態指令嗎？」——用 autoresearch 讓 Skill 自我進化的實作流程
- **Newsletter 素材**：「一晚 $25、100 輪迭代」——autoresearch 的 6 個非 ML 應用場景完整指南
- **教學素材**：實作工作坊——帶學員用 Claude Code 跑一輪 autoresearch，從寫 eval 到看結果
