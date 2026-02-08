---
description: "Dayflow 活動摘要日記"
---

# Dayflow 活動摘要日記

從 Dayflow 的螢幕活動記錄和 AI 觀察，整理出一天的活動摘要日記。

## 觸發方式

- 指令：`./bin/agent dayflow [YYYY-MM-DD]`
- IDE 內：`/daily-dayflow-digest`

## 輸入來源

1. **Timeline cards**：Dayflow 自動記錄的螢幕活動時間軸
2. **Observations**：Dayflow AI 產生的行為觀察
3. **模板**：`800_System/templates/dayflow-digest-template.md`

## 處理邏輯

1. 從 Dayflow SQLite 資料庫讀取指定日期的 timeline cards 和 observations
2. 如果無資料，提示該日無 Dayflow 記錄
3. 將原始資料交給 LLM 整理：
   - **今日節奏**：一句話描述這天的工作節奏（例如「上午學習、下午開發、晚上規劃」）
   - **時間分布**：按活動類別統計時間和佔比
   - **活動時間軸**：簡化的時間軸（合併碎片活動、去掉閒置）
   - **AI 觀察摘要**：從 observations 中提取有意義的行為模式
   - **行為模式 & 洞察**：跨活動的模式分析（例如「頻繁切換視窗」「深度工作時段集中在晚上」）
   - **值得注意的事**：異常行為、有趣發現、可以改進的習慣

## 輸出

- 路徑：`100_Journal/daily/YYYY-MM-DD-dayflow.md`
- 如果已存在，詢問是否覆蓋

## 整理原則

- **行為導向**：不只列活動，要分析「你怎麼度過這一天」
- **誠實客觀**：閒置就寫閒置，不美化
- **可行動**：洞察要指向「明天可以怎麼調整」
- **繁體中文**
