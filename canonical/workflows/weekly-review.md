# Weekly Review — 個人週回顧

從一週的 L2 日記 + Dayflow 摘要產出結構化週回顧。

## 觸發方式
- 指令：`./bin/agent weekly-review`
- 指令：`./bin/agent weekly-review 2026-02-10`（包含該日期的那一週）
- 指令：`./bin/agent weekly-review --force`（強制覆蓋）
- IDE 內：`/weekly-content`（一鍵週報 + 電子報）

## 輸入來源
1. **L2 精煉日記**：`100_Journal/daily/YYYY-MM-DD.md`（7 天）
2. **Dayflow 活動摘要**：`100_Journal/daily/YYYY-MM-DD-dayflow.md`（7 天）
3. **模板**：`800_System/templates/weekly-review-template.md`

## 處理邏輯
1. 從指定日期計算該週 Mon-Sun 範圍
2. 收集範圍內的 L2 日記和 Dayflow 摘要
3. LLM 產出結構化週回顧（1 次呼叫）
4. 寫入 `100_Journal/weekly/YYYY-Wxx.md`

## 輸出
- 路徑：`100_Journal/weekly/YYYY-Wxx.md`
- 存在時：使用 `--force` 覆蓋

## 回顧涵蓋
- 本週一句話總結
- 完成了什麼（具體事項）
- 學到什麼（關鍵知識）
- 本週數據（量化指標）
- 模式與趨勢（跨天觀察）
- 卡住的地方
- 下週重點
- 能量曲線
