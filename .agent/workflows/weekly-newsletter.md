---
description: "Weekly Newsletter — 電子報草稿"
---

# Weekly Newsletter — 電子報草稿

從一週的 L2 日記 + topics + insights 產出電子報草稿，月度輪替 4 種類型。

## 觸發方式
- 指令：`./bin/agent weekly-newsletter`
- 指令：`./bin/agent weekly-newsletter 2026-02-10`（指定日期所在週）
- 指令：`./bin/agent weekly-newsletter --type deep-dive`（指定類型）
- 指令：`./bin/agent weekly-newsletter --force`（強制覆蓋）
- IDE 內：`/weekly-content`（一鍵週報 + 電子報）

## 月度輪替設計

| 月內週數 | 類型 | 說明 |
|---------|------|------|
| Week 1 | `curated` | 主題策展：3-5 精選主題 |
| Week 2 | `deep-dive` | 長篇深度：1 深度 + 2-3 短 highlight |
| Week 3 | `mixed` | 混合：1 深度 + 3-4 短洞察 + 推薦資源 |
| Week 4+ | `monthly-reflection` | 月度心得反思 |

`--type` 可 override 自動輪替。

## 輸入來源
1. **L2 精煉日記**：`100_Journal/daily/YYYY-MM-DD.md`（7 天）
2. **Topics**：`500_Content/topics/` 中該週建立的
3. **Insights**：`500_Content/insights/` 中該週的
4. **Newsletter DNA**：`800_System/references/style-dna/newsletter-dna.md`（如存在）
5. **寫作規則**：`canonical/rules/10-writing-style.md`
6. **月度補充**（僅 monthly-reflection）：整月日記 + 週回顧

## 處理邏輯
1. 計算週日期範圍 + 月內週數
2. 決定電子報類型（auto 或 --type override）
3. 收集對應素材
4. LLM 產出電子報草稿（1 次呼叫）
5. 加上 frontmatter → 寫入

## 輸出
- 路徑：`500_Content/newsletter/drafts/YYYY-Wxx-{type}.md`
- 存在時：使用 `--force` 覆蓋

## 原則
- 開場直接進入有價值的內容，不要寒暄
- 標題吸引人，不用「週報」開頭
- 有觀點、有立場，不做中立派
- 有 Newsletter DNA 時優先遵循
