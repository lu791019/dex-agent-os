---
description: "Topic Create — 從洞察建立主題"
---

# Topic Create — 從洞察建立主題

從 insight 卡片或手動描述建立主題檔案（TOPIC.md），作為多頻道內容生產的起點。

## 觸發方式
- 指令：`./bin/agent topic-create <insight-file>`
- 指令：`./bin/agent topic-create --title "主題名稱"`
- 指令：`./bin/agent topic-create`（列出可用 insights）
- IDE 內：`/topic-create`

## 輸入來源
1. **Insight 卡片**：`510_Insights/*.md`（由 `./bin/agent extract` 自動產出）
2. **手動描述**：用 `--title` 參數直接輸入主題名稱
3. **模板**：`800_System/templates/topic-template.md`

## 處理邏輯
1. 讀取 insight 檔案的完整內容（標題、論點、切入角度）
2. LLM 擴展為完整 TOPIC.md：
   - 核心論點：一句話概括
   - 關鍵素材：支撐論點的 3-5 個素材
   - 頻道適合度：評估每個頻道的適合程度
3. 自動產生 slug（從標題轉換），建立目錄

## 輸出
- 路徑：`520_Topics/<slug>/TOPIC.md`
- 如果目錄已存在，提示使用者是否覆蓋

## 原則
- 「核心論點」必須是一句可直接使用的話
- 「頻道適合度」要具體說明為什麼適合/不適合，不是只打勾
- 保留 insight 原文的觀點，不過度延伸
