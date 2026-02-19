# 每日內容生產管線

從今天的工作紀錄一路生成到 Threads 草稿的完整管線。使用繁體中文。

## 觸發方式
- IDE 內：`/daily-content`
- 可選參數：`/daily-content YYYY-MM-DD`（指定日期）
- 可選參數：`/daily-content --skip-worklog`（跳過 L1，假設已存在）

## 完整流程

```
L1 工作日誌 → L2 精煉日記 → extract insights → topic-create → topic-to-thread
                                  ↓                ↓                ↓
Dayflow 摘要 ─┘              510_Insights/    520_Topics/    530_Channels/threads/
```

## 執行步驟

### Step 0：解析參數與確認日期

- 如果 `$ARGUMENTS` 中包含 YYYY-MM-DD 格式的日期，用它作為目標日期
- 否則用 `date "+%Y-%m-%d"` 取得今天
- 檢查是否包含 `--skip-worklog` 參數
- 將日期存為 `TARGET_DATE` 變數，後續步驟一律使用

### Step 1：生成 L1 工作日誌 + Dayflow + L2 精煉日記

**1a. L1 工作日誌（可跳過）：**
- 檢查 `~/work-logs/YYYY/MM/TARGET_DATE.md` 是否已存在
- 如果已存在或包含 `--skip-worklog` 參數，跳過
- 如果不存在，**執行 `/work-log TARGET_DATE` skill** 來產生 L1

**1b. Dayflow 活動摘要（先跑）：**
```bash
python3 scripts/generators/daily_dayflow_digest.py [TARGET_DATE] [--force]
```
- 輸出：`100_Journal/daily/TARGET_DATE-dayflow.md`

**1c. L2 精煉日記（後跑，會自動讀取 Dayflow 摘要）：**
```bash
python3 scripts/generators/daily_journal.py [TARGET_DATE] [--force]
```
- 輸出：`100_Journal/daily/TARGET_DATE.md`

**驗證：** 確認 L2 檔案存在且非空

### Step 2：萃取 Insights

從 L2 精煉日記萃取洞察到 `510_Insights/`：

```bash
python3 scripts/extractors/journal_knowledge_extract.py TARGET_DATE --type insights --force
```

**驗證：** 檢查 `510_Insights/` 中是否有新產出的 `TARGET_DATE-*.md` 檔案

- 如果沒有新 insight（L2 中無「洞察 & 靈感」區塊），在摘要中註明並跳到 Step 5
- 記錄產出的 insight 檔案清單，供 Step 3 使用

### Step 3：從 Insights 建立 Topics

對 Step 2 產出的每個新 insight，呼叫 topic-create：

```bash
python3 scripts/generators/topic_create.py 510_Insights/TARGET_DATE-<slug>.md --force
```

**對每個 insight 逐一執行。**

**驗證：** 檢查 `520_Topics/` 中是否有對應的新 `<slug>/TOPIC.md`

- 記錄產出的 topic slug 清單，供 Step 4 使用

### Step 4：從 Topics 產出 Threads 草稿

對 Step 3 產出的每個新 topic，呼叫 topic-to-thread：

```bash
python3 scripts/generators/topic_to_thread.py <slug> --force
```

**對每個 topic 逐一執行。**

**驗證：** 檢查 `530_Channels/threads/TARGET_DATE/` 中是否有對應的草稿

### Step 5：產出摘要

完成後輸出摘要表格：

```
## 產出總覽

### 日記
| 檔案 | 類型 |
|------|------|
| ~/work-logs/.../TARGET_DATE.md | L1 工作日誌 |
| 100_Journal/daily/TARGET_DATE-dayflow.md | Dayflow 活動摘要 |
| 100_Journal/daily/TARGET_DATE.md | L2 精煉日記 |

### Insights → Topics → Threads
| Insight | Topic | Thread 草稿 |
|---------|-------|------------|
| 510_Insights/TARGET_DATE-xxx.md | 520_Topics/xxx/ | 530_Channels/threads/TARGET_DATE/xxx.md |
| ... | ... | ... |
```

並提醒使用者：
- 所有草稿狀態為 `draft`，需人工審閱後才發布
- 可用 `topic-to-fb`、`topic-to-blog` 等指令從同一 topic 產出其他頻道草稿
- 如需匯入外部閱讀素材，先跑 `./bin/agent sync-all`

## 注意事項

- **L1 是基礎**：沒有 L1 工作日誌，L2 品質會下降。務必先確認 L1 存在
- **Style DNA 是關鍵**：有 DNA 時生成的 Threads 辨識度遠高於純靠規則。如尚未萃取，建議先跑 `./bin/agent collect-threads && ./bin/agent extract-style threads`
- **各步驟可獨立使用**：`extract`、`topic-create`、`topic-to-thread` 都是獨立 CLI，`/daily-content` 只是串接它們的流水線
- **不自動 commit**：生成的檔案不自動加入 git，讓使用者審閱後再決定
