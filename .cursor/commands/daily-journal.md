# 每日精煉日記

從 L1 工作日誌 + Dayflow 活動摘要（如存在）提煉出簡潔的 L2 每日日記。

## 觸發方式

- 指令：`./bin/agent journal [YYYY-MM-DD]`
- 自動化：launchd 每天 00:05 執行（Phase 7）
- IDE 內：`/daily-journal`

## 輸入來源

1. **L1 工作日誌**：`~/work-logs/YYYY/MM/YYYY-MM-DD.md`
2. **Dayflow 活動摘要**（選用）：`100_Journal/daily/YYYY-MM-DD-dayflow.md`（如存在會自動讀取）
3. **模板**：`800_System/templates/journal-template.md`

## 處理邏輯

1. 讀取指定日期的 L1 工作日誌
2. 如果 L1 不存在，提示使用者先跑 `/work-log`
3. 檢查同日的 Dayflow 活動摘要是否存在，存在則一併讀取
4. 將 L1 + Dayflow 內容交給 LLM 提煉：
   - 從「今日摘要 + 討論過程 + 反思」提煉「今日一句話」和「做了什麼」
   - 從「學到的東西」提煉「學到什麼」
   - 從對話和反思中萃取「洞察 & 靈感」（特別標註適合哪個頻道）
   - 從「遇到的問題」+ Dayflow 行為模式提煉「卡在哪裡」
   - 從「待辦 / 後續追蹤」提煉「明天優先」（最多 3 項）
   - 從整體工作內容 + Dayflow 時間分布推測「能量 & 狀態」
5. 使用 journal-template.md 格式輸出

> **注意**：建議先跑 `./bin/agent dayflow` 再跑 `./bin/agent journal`，讓 L2 能融合行為洞察。沒有 Dayflow 摘要時仍可正常運作。

## 輸出

- 路徑：`100_Journal/daily/YYYY-MM-DD.md`
- 如果已存在，詢問是否覆蓋

## 提煉原則

- **簡潔**：L2 是 L1 的 1/3~1/5 長度
- **洞察導向**：不只記錄做了什麼，更要抓出「值得深入的想法」
- **內容潛力**：每條洞察標註適合轉化的頻道（Threads / Newsletter / Blog）
- **行為洞察**：如果有 Dayflow 摘要，將行為模式、時間分布洞察融入日記
- **誠實**：能量和狀態要從工作量和卡關程度如實推測，不美化；Dayflow 時間分布可作客觀佐證
- **繁體中文**
