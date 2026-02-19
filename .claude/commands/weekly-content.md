# 每週內容生產管線

一鍵產出個人週回顧 + 電子報草稿。使用繁體中文。

## 觸發方式
- IDE 內：`/weekly-content`
- 可選參數：`/weekly-content YYYY-MM-DD`（指定日期所在週）
- 可選參數：`/weekly-content --type TYPE`（指定電子報類型）

## 完整流程

```
7 天 L2 日記 + Dayflow ──→ 週回顧
                              ↓
7 天 L2 日記 + Topics + Insights ──→ 電子報草稿
                                        ↑ Newsletter DNA
```

## 執行步驟

### Step 0：解析參數與確認日期

- 如果 `$ARGUMENTS` 中包含 YYYY-MM-DD 格式的日期，用它作為目標日期
- 否則用 `date "+%Y-%m-%d"` 取得今天
- 檢查是否包含 `--type` 參數
- 將日期存為 `TARGET_DATE` 變數

### Step 1：產出週回顧

執行：
```bash
python3 scripts/generators/weekly_review.py [TARGET_DATE] [--force]
```

- 輸出：`100_Journal/weekly/YYYY-Wxx.md`
- 如果已存在，加 `--force` 覆蓋

**驗證：** 確認輸出檔案存在且非空

### Step 2：產出電子報草稿

執行：
```bash
python3 scripts/generators/weekly_newsletter.py [TARGET_DATE] [--type TYPE] [--force]
```

- 輸出：`530_Channels/newsletter/YYYY-Wxx-{type}.md`
- 類型會自動根據月內週數輪替：
  - Week 1: curated（主題策展）
  - Week 2: deep-dive（長篇深度）
  - Week 3: mixed（混合）
  - Week 4+: monthly-reflection（月度心得反思）
- 如果已存在，加 `--force` 覆蓋

**驗證：** 確認輸出檔案存在且非空

### Step 3：產出摘要

完成後輸出摘要表格：

```
## 產出總覽

### 週回顧
| 檔案 | 說明 |
|------|------|
| 100_Journal/weekly/YYYY-Wxx.md | 個人週回顧 |

### 電子報草稿
| 檔案 | 類型 |
|------|------|
| 530_Channels/newsletter/YYYY-Wxx-{type}.md | {type_label} |
```

並提醒使用者：
- 週回顧可直接發布或作為個人參考
- 電子報草稿狀態為 `draft`，需人工審閱後才發送
- 如需不同類型的電子報，可用 `--type` 指定

## 注意事項

- **日記是基礎**：如果該週沒有 L2 日記，產出品質會大幅下降。建議先確認有日記資料
- **Newsletter DNA 提升品質**：如有 `800_System/references/style-dna/newsletter-dna.md`，電子報會更貼近個人風格
- **不自動 commit**：生成的檔案只寫入磁碟，不自動加入 git
