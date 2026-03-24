# 每日全流程 — Daily All

一鍵整合四大管線的每日全流程：學習輸入 + 工作管理 + 日記系統 + 內容生產。使用繁體中文。

## 觸發方式

- IDE 內：`/daily-all`
- 可選參數：`/daily-all YYYY-MM-DD`（指定日期）
- 可選參數：`/daily-all --skip-interactive`（跳過互動步驟 10-11）

## 完整流程總覽

```
自動同步（1-4）→ 日記系統（5-7）→ 閱讀消化（8-9）→ 互動（10-11）→ 收斂+內容產出（12-15）
     │                 │                │                │                  │
 sync-all         L1+Dayflow+L2    digest+insight    learning+review    extract+topic+draft
```

## 執行步驟

### Step 0：解析參數與確認日期

- 如果 `$ARGUMENTS` 中包含 YYYY-MM-DD 格式的日期，用它作為 `TARGET_DATE`
- 否則用 `date "+%Y-%m-%d"` 取得今天
- 檢查是否包含 `--skip-interactive` 參數（設為 `SKIP_INTERACTIVE` 旗標）
- 向 Dex 確認：「今日全流程，日期：TARGET_DATE，互動模式：開啟/關閉，開始？」

---

## 自動部分（Step 1-9）

### Step 1：同步外部資料源

批次匯入 Readwise + RSS + Anybox + Gmail。無 token 的服務自動跳過。

```bash
./bin/agent sync-all
```

**驗證：** 觀察輸出，記錄成功匯入的來源和數量。如果全部 skip（無 token）也算通過。

### Step 2：Fireflies 會議逐字稿同步

```bash
python3 scripts/collectors/fireflies_sync.py --latest 5
```

- 無 API key → 印引導訊息，繼續下一步（不中斷）
- 有匯入 → 記錄筆數

### Step 3：Google Classroom 同步

```bash
python3 scripts/collectors/classroom_sync.py --courses --active-only
```

- 無 token 或無課程 → 跳過，繼續下一步
- 有資料 → 記錄課程數

### Step 4：專案狀態更新

```bash
python3 scripts/generators/project_status.py
```

- 此指令不帶參數時會列出所有可用專案
- 如果有專案，對每個專案名稱執行：
  ```bash
  python3 scripts/generators/project_status.py <專案名> --force
  ```
- 無專案 → 跳過

### Step 5：L1 工作日誌

- 檢查 `~/work-logs/YYYY/MM/TARGET_DATE.md` 是否已存在
- 如果已存在 → 跳過，顯示「L1 已存在」
- 如果不存在 → **執行 `/work-log TARGET_DATE` skill** 來產生 L1
  - 如果巢狀 skill 無法執行，提示 Dex 先手動跑 `/work-log TARGET_DATE`，等完成後繼續

### Step 6：Dayflow 活動摘要

```bash
python3 scripts/generators/daily_dayflow_digest.py TARGET_DATE --force
```

- 輸出：`100_Journal/daily/TARGET_DATE-dayflow.md`
- 無 Dayflow 資料 → 跳過（不影響後續）

### Step 7：L2 精煉日記

```bash
python3 scripts/generators/daily_journal.py TARGET_DATE --force
```

- 輸出：`100_Journal/daily/TARGET_DATE.md`
- **依賴 Step 5 + 6**（L1 + Dayflow 作為輸入）

**驗證：** 確認 `100_Journal/daily/TARGET_DATE.md` 存在且非空

### Step 8：每日學習消化報告

```bash
python3 scripts/generators/daily_digest.py TARGET_DATE --force
```

- 輸出：`100_Journal/digest/TARGET_DATE-digest.md`
- **依賴 Step 1**（sync-all 匯入的閱讀素材）
- 如果無閱讀素材 → 產出空 digest 或跳過，在摘要中註明

**驗證：** 確認 digest 檔案存在

### Step 9：從 Digest + 素材池萃取 Insights

讀取 Step 8 產出的 digest 檔案，找到「今日洞察」或類似區塊。
同時讀取素材池 `000_Inbox/daily/TARGET_DATE.md`（如果存在），從「心得」和「靈感」section 中找到可能的 insight 種子。

**對每條洞察（來自 digest 或素材池），產出一個 insight 檔案到 `510_Insights/`：**

- 檔名格式：`TARGET_DATE-<slug>.md`
- 使用標準 insight 格式：

```markdown
---
date: TARGET_DATE
source: 100_Journal/digest/TARGET_DATE-digest.md
classification: content
channel_tags: ["Threads"]
status: raw
---

# <洞察標題>

<核心洞察，1-2 段>

## 潛在切入角度
<適合的內容形式和延伸方向>
```

- 檢查 `510_Insights/` 是否已有同 slug 的檔案，避免重複
- 記錄本步驟產出的 insight 檔案清單

**如果 digest 無「今日洞察」且素材池無「心得」「靈感」→ 跳過本步，記錄「無 insights 來源」**

---

## 互動部分（Step 10-11）

> **如果 `SKIP_INTERACTIVE` 為 true → 直接跳到 Step 12**

### Step 10：互動學習對話（/daily-learning 精簡版）

**行為限制（重要）：**
1. 讀取 Step 8 的 digest 檔案
2. 先列出 Step 9 已萃取的 insights，告訴 Dex「這些已經從 digest 自動萃取了」
3. 從 digest 中挑出 3-5 篇內容，讓 Dex 選或隨機推薦
4. **每篇只聊 1 件事**，1-2 輪問答即可
5. 收斂：整理 takeaway，問 Dex 哪些值得變成 insight
6. 只寫被 Dex 確認的 insight → `510_Insights/TARGET_DATE-<slug>.md`
7. 記錄本步驟新增的 insight 檔案清單

**提問風格：** 同 /daily-learning（蘇格拉底式 / 考試式 / 深聊式交替），但更精簡。

### Step 11：每日回顧（/daily-review）

1. 讀取 L1（`~/work-logs/YYYY/MM/TARGET_DATE.md`）和 L2（`100_Journal/daily/TARGET_DATE.md`）
2. 呈現回顧摘要（完成了什麼 / 花最多時間在 / 值得深入的點 / 未完成）
3. 問 Dex 3 個問題：
   - 「今天有什麼特別值得記下來的想法？」
   - 「有哪個洞察想發展成內容？」
   - 「明天最重要的一件事是什麼？」
4. 如果 Dex 補充了想法 → **更新 L2 日記的洞察區塊**

---

## 收斂 + 內容產出（Step 12-15）

### Step 12：萃取 Insights + Learnings + Reflections

從 L2 精煉日記（含 Step 11 可能的更新）萃取全部知識：

```bash
python3 scripts/extractors/journal_knowledge_extract.py TARGET_DATE --type all --force
```

- 產出：新的 insights → `510_Insights/`、learnings → `memory/learnings.md`、reflections → `memory/reflections.md`
- 記錄本步驟新增的 insight 檔案清單

### Step 13：從 Insights 建立 Topics

**收集所有新 insight 來源（Step 9 + 10 + 12）：**

```bash
# 列出所有 TARGET_DATE 的 insight 檔案
ls 510_Insights/TARGET_DATE-*.md
```

**對每個新 insight 檔案，建立 topic：**

```bash
python3 scripts/generators/topic_create.py 510_Insights/TARGET_DATE-<slug>.md --force
```

- **必須加 `--force`**（不加會 `input()` 卡住）
- 如果 `520_Topics/<slug>/TOPIC.md` 已存在 → 跳過該 insight
- 記錄產出的 topic slug 清單

### Step 14：從 Topics 產出多頻道草稿

對 Step 13 產出的每個新 topic：

**14a. Threads 草稿：**
```bash
python3 scripts/generators/topic_to_thread.py <slug> --force
```

**14b. Facebook 貼文草稿：**
```bash
python3 scripts/generators/topic_to_fb.py <slug> --force
```

**驗證：** 檢查 `530_Channels/threads/TARGET_DATE/` 和 `530_Channels/facebook/TARGET_DATE/` 中有對應草稿

**14c. 印出 Threads 草稿預覽：**

產出草稿後，讀取 `530_Channels/threads/TARGET_DATE/*.md` 全部檔案，將每篇 Threads 草稿的主文直接印在對話中，方便 Dex 快速瀏覽：

```
### Threads 草稿預覽

#### 1. <slug>
（主文內容）

#### 2. <slug>
（主文內容）

...
```

### Step 15：產出最終摘要

完成後輸出完整摘要：

```
## Daily All 產出總覽 — TARGET_DATE

### 素材池
| 來源 | 狀態 | 筆數 |
|------|------|------|
| 000_Inbox/daily/TARGET_DATE.md | ✓ / 無 | N 條（會議/經驗/心得/靈感/筆記） |

### 同步結果
| 來源 | 狀態 | 筆數 |
|------|------|------|
| sync-all（Readwise/RSS/Anybox/Gmail） | ✓ / skipped | N 筆 |
| Fireflies | ✓ / skipped | N 筆 |
| Classroom | ✓ / skipped | N 門課 |
| 專案狀態 | ✓ / skipped | N 個專案 |

### 日記系統
| 檔案 | 類型 | 狀態 |
|------|------|------|
| ~/work-logs/.../TARGET_DATE.md | L1 工作日誌 | 新建 / 已存在 |
| 100_Journal/daily/TARGET_DATE-dayflow.md | Dayflow 摘要 | ✓ / skipped |
| 100_Journal/daily/TARGET_DATE.md | L2 精煉日記 | ✓ |
| 100_Journal/digest/TARGET_DATE-digest.md | 學習消化報告 | ✓ / skipped |

### 互動
| 步驟 | 狀態 |
|------|------|
| /daily-learning | 完成 / 跳過 |
| /daily-review | 完成 / 跳過 |

### Insights → Topics → Drafts
| Insight | 來源 | Topic | Thread | FB |
|---------|------|-------|--------|----|
| TARGET_DATE-xxx.md | digest/learning/extract | ✓ / — | ✓ / — | ✓ / — |
| ... | ... | ... | ... | ... |

### 知識萃取
| 類型 | 狀態 |
|------|------|
| Insights | N 個新增 |
| Learnings | ✓ 已更新 |
| Reflections | ✓ 已更新 |
```

**提醒：**
- 所有草稿狀態為 `draft`，需人工審閱後才發布
- 可用 `topic-to-blog`、`topic-to-short-video` 等指令從同一 topic 產出其他頻道草稿
- 不自動 commit，讓 Dex 審閱後再決定

---

## 注意事項

- **執行時間**：自動部分約 7-12 分鐘（含 15+ 次 LLM 呼叫），互動部分視對話長度
- **每步容錯**：任何步驟失敗不中斷整體流程，記錄失敗原因繼續下一步
- **不自動 commit**：生成的檔案不加入 git，讓 Dex 審閱後決定
- **topic-create 必須加 `--force`**：不加會 `input()` 卡住自動化流程
- **Step 9 insight 重複檢查**：寫入前先檢查 `510_Insights/` 是否已有同 slug
- **與 /daily-content 的關係**：/daily-all 是超集，涵蓋 /daily-content 的全部功能並擴充同步和互動
