---
title: "OpenClaw Creator: Why 80% Of Apps Will Disappear"
channel: Y Combinator
date: 2026-03-29
duration:
source: https://www.youtube.com/watch?v=4uzGDAoNOZc
language: en
tags: [AI-agent, open-source, personal-AI, app-disruption, bot-to-bot, local-first]
---

# OpenClaw Creator: Why 80% Of Apps Will Disappear

## 一句話摘要
本地運行的 AI agent 將取代 80% 的 app，記憶與工具回歸使用者手中。

## 核心觀點

### 1. 本地運行是關鍵差異化——「在你的電腦上跑」改變一切
OpenClaw 爆紅（GitHub 16 萬星）的核心原因不是模型更強，而是它跑在使用者自己的電腦上。雲端 agent 只能做有限的事，但本地 agent 能控制滑鼠、鍵盤、智慧家電、Tesla、Sonos，甚至床的溫度。這讓 agent 從「聊天助手」升級為「全能數位替身」。

### 2. 80% 的 App 會消失——只管資料的 App 將被 agent 取代
任何本質上只是「管理資料」的 App（健身追蹤、待辦清單、記帳）都能被 agent 以更自然的方式處理。使用者不需要打開 MyFitnessPal，agent 已經知道你在吃什麼並自動記錄。只有擁有實體感測器的 App 可能存活。

### 3. Coding 模型的真正能力是「創意問題解決」
Peter 的 aha moment：agent 收到一段沒有副檔名的語音檔，自主判斷格式、用 ffmpeg 轉檔、發現沒裝 whisper 就改用 curl 打 OpenAI API 完成轉錄——全程 9 秒，沒有任何預先設計。Coding 模型擅長的不是寫程式，而是抽象的創意問題解決能力，這能力可直接遷移到真實世界任務。

### 4. 記憶所有權是護城河也是隱私風險
大公司（ChatGPT、Gemini）把記憶鎖在自己的資料孤島裡，無法匯出。OpenClaw 的記憶就是一堆本地 Markdown 檔案，使用者完全擁有。但這些記憶極度敏感——人們很快就會把最私密的問題交給 agent。

### 5. 反 MCP、反 worktree——用最簡單的工具鏈建最強的系統
Peter 刻意不支援 MCP，改用自己的工具把 MCP 轉成 CLI。理由：bot 擅長 Unix CLI，不需要為 bot 發明新協議。開發上也不用 git worktree，直接多份 repo copy 在 main 上平行開發，減少心智負擔。

## 關鍵引述

> "Everything I saw so far runs in the cloud. If you run on your computer, it can do every effing thing."

> "Every app that basically just manages data could be managed in a better way, in a more natural way, by agents."

> "Coding is really like creative problem solving that maps very well back into the real world."

> "The beauty of OpenClaw is it kind of claws into the data silos... everyone owns their own memories as a bunch of markdown files on their own machines."

> "No insane human tries to call an MCP manually. You just want to use CLIs. That's the future."

> "I don't think I could have built the thing with Claude Code. I love Codex because it looks through way more files before it decides what to change."

## 市場趨勢相關

- **Agent 平台戰開打**：本地 agent（OpenClaw）vs 雲端 agent（ChatGPT、Gemini）成為新戰線，差異化在「能控制什麼」而非「模型多聰明」
- **模型商品化加速**：Peter 觀察到每次新模型發布都是同樣循環——驚嘆→適應→抱怨，開源模型持續追上一年前的閉源水準
- **Bot-to-Bot 經濟浮現**：agent 之間直接協商（訂餐廳、排行程），甚至 agent 僱用真人完成實體世界任務（Maltbook 專案）
- **App 層的價值正在坍塌**：純資料管理類 App 面臨存亡危機，有硬體/感測器綁定的 App 相對安全
- **記憶可攜性成為新議題**：資料孤島 vs 本地擁有，歐洲法規可能推動記憶匯出權
- **MCP 協議遇到實務挑戰**：OpenClaw 的成功證明 CLI-first 路線可行，MCP 的複雜度（需重啟、不能動態載入）是實際痛點

## 我的想法
<!-- 手動補充 -->

## 可轉化為內容

### Threads 素材
1. **「80% App 會消失」論點拆解**——用 MyFitnessPal 和待辦 App 的例子說明 agent 如何取代純資料管理 App，結尾問：你手機上哪些 App 其實只是在「管資料」？
2. **「9 秒語音辨識」故事**——Peter 沒有預先設計，agent 自己找到 ffmpeg + OpenAI API 完成轉錄。引出觀點：coding 模型的真正能力是創意問題解決，不是寫程式
3. **「你的記憶是一堆 Markdown」**——對比大公司資料孤島 vs 本地 Markdown 檔案，帶出資料所有權議題

### Newsletter 素材
1. **深度分析：本地 Agent vs 雲端 Agent 的護城河差異**——從 OpenClaw 爆紅切入，分析為什麼「在哪裡跑」比「模型多強」更重要
2. **Builder 觀點：Peter 的反直覺開發哲學**——不用 worktree、不支援 MCP、用 Codex 不用 Claude Code、10 個平行 session，這套方法論背後的邏輯

### Blog 素材
1. **「App 消亡論」的完整論述**——從 OpenClaw 的設計哲學出發，分析哪些類別的 App 會被 agent 取代、哪些會存活、Builder 該如何應對
