# 每日內容生產管線

從今天的工作紀錄一路生成到 Threads 草稿的完整管線。使用繁體中文。

## 觸發方式
- IDE 內：`/daily-content`
- 可選參數：`/daily-content YYYY-MM-DD`（指定日期）
- 可選參數：`/daily-content --skip-worklog`（跳過 L1，假設已存在）

## 完整流程

```
L1 工作日誌 ──→ L2 精煉日記 ──→ 3 篇 Threads 草稿
                                      ↑ Style DNA
Dayflow 活動摘要 ─────────────→ 3 篇 Threads 草稿
      + L1 工作日誌                   ↑ Style DNA
```

## 執行步驟

### Step 0：解析參數與確認日期

- 如果 `$ARGUMENTS` 中包含 YYYY-MM-DD 格式的日期，用它作為目標日期
- 否則用 `date "+%Y-%m-%d"` 取得今天
- 檢查是否包含 `--skip-worklog` 參數
- 將日期存為 `TARGET_DATE` 變數，後續步驟一律使用

### Step 1：生成 L1 工作日誌

**前置條件檢查：**
- 檢查 `~/work-logs/YYYY/MM/TARGET_DATE.md` 是否已存在
- 如果已存在或包含 `--skip-worklog` 參數，跳到 Step 2
- 如果不存在，**執行 `/work-log TARGET_DATE` skill** 來產生 L1
  - 注意：這會觸發完整的工作日誌產生流程（收集 git log、Dayflow 資料、Claude Code session 摘要）
  - 等待 L1 產出完成後再繼續

**驗證：** 確認 `~/work-logs/YYYY/MM/TARGET_DATE.md` 存在且非空

### Step 2：先生成 Dayflow 活動摘要，再生成 L2 精煉日記

**依序執行**（L2 會讀取 Dayflow 摘要，所以 Dayflow 必須先完成）：

1. **Dayflow 活動摘要（先跑）：**
   ```bash
   python3 scripts/generators/daily_dayflow_digest.py [TARGET_DATE]
   ```
   - 輸出：`100_Journal/daily/TARGET_DATE-dayflow.md`
   - 如果已存在，加 `--force` 覆蓋

2. **L2 精煉日記（後跑，會自動讀取上一步的 Dayflow 摘要）：**
   ```bash
   python3 scripts/generators/daily_journal.py [TARGET_DATE]
   ```
   - 輸出：`100_Journal/daily/TARGET_DATE.md`
   - 如果已存在，加 `--force` 覆蓋

**驗證：** 兩個檔案都存在且非空

### Step 3：讀取素材 + Style DNA

讀取以下檔案，準備生成 Threads 草稿：

1. **L1 工作日誌**：`~/work-logs/YYYY/MM/TARGET_DATE.md`
2. **Dayflow 活動摘要**：`100_Journal/daily/TARGET_DATE-dayflow.md`
3. **L2 精煉日記**：`100_Journal/daily/TARGET_DATE.md`
4. **Style DNA**：`800_System/references/style-dna/threads-dna.md`
   - 如不存在，改讀 `canonical/rules/10-writing-style.md` 的 Threads 風格區段

### Step 4：生成 6 篇 Threads 草稿

建立輸出目錄：
- `500_Content/topics/TARGET_DATE-threads-from-dayflow-l1/`
- `500_Content/topics/TARGET_DATE-threads-from-l2/`

**同時發起兩個 LLM 呼叫**（使用 `claude --print`），各生成 3 篇 Threads 草稿：

#### 4A：Dayflow + L1 → 3 篇 Threads

Prompt 要點：
- 角色：Threads 社群內容創作者
- 來源：Dayflow 活動摘要 + L1 工作日誌的**重點摘要**（不要全文，取關鍵事件和洞察）
- 風格要求：嚴格遵循 Style DNA 的所有維度
- 主題選擇：從日記中挑 3 個**不同且獨立**的觀點/經歷/洞察
- 輸出格式：用 `===` 分隔 3 篇，每篇標明主題名稱

風格硬規則（從 Style DNA 提煉）：
- 口語化，像在跟朋友聊天
- 用「我」分享經歷，用「你」直接對話讀者
- 開場用反差型或斷言型 Hook
- 善用「不是 A，而是 B」的對比句式
- 段落短（1-2 句就換行）
- 長度 150-250 字
- 結尾用金句或開放提問
- 不寫教科書語言、不做中立派
- 技術用語自然穿插不額外解釋

#### 4B：L2 → 3 篇 Threads

同上，但來源改為 L2 精煉日記。特別關注 L2 中的：
- 「洞察 & 靈感」區塊（已標註頻道適合度）
- 「學到什麼」區塊
- 「卡在哪裡」區塊（踩坑經歷適合寫成共鳴文）

### Step 5：解析 LLM 輸出，寫入檔案

將每篇 Threads 草稿寫入獨立的 markdown 檔案，格式：

```markdown
---
topic: TARGET_DATE-threads-from-dayflow-l1
channel: threads
status: draft
created: TARGET_DATE
source: Dayflow + L1 工作日誌  # 或 L2 精煉日記
theme: 主題名稱
---

（Threads 貼文內容）
```

命名規則：
- `thread-01-<slug>.md`
- `thread-02-<slug>.md`
- `thread-03-<slug>.md`

### Step 6：產出摘要

完成後輸出摘要表格給使用者：

```
## 產出總覽

### 日記
| 檔案 | 類型 |
|------|------|
| ~/work-logs/.../TARGET_DATE.md | L1 工作日誌 |
| 100_Journal/daily/TARGET_DATE-dayflow.md | Dayflow 活動摘要 |
| 100_Journal/daily/TARGET_DATE.md | L2 精煉日記 |

### Threads 草稿（Dayflow + L1 → 3 篇）
| 檔案 | 主題 |
|------|------|
| thread-01-xxx.md | ... |
| thread-02-xxx.md | ... |
| thread-03-xxx.md | ... |

### Threads 草稿（L2 → 3 篇）
| 檔案 | 主題 |
|------|------|
| thread-01-xxx.md | ... |
| thread-02-xxx.md | ... |
| thread-03-xxx.md | ... |
```

並提醒使用者：
- 檢查 OAuth/Dayflow+L1 兩組是否有主題重複，可挑選或合併
- 所有草稿狀態為 `draft`，需人工審閱後才發布

## 注意事項

- **L1 是基礎**：如果沒有 L1 工作日誌，L2 和 Dayflow+L1 的 Threads 品質會大幅下降。務必先確認 L1 存在
- **Style DNA 是關鍵**：有 DNA 時生成的文章辨識度遠高於純靠規則。如尚未萃取，建議先跑 `./bin/agent collect-threads && ./bin/agent extract-style threads`
- **主題去重**：兩組來源（Dayflow+L1 vs L2）可能產出類似主題（因為同一天的內容），在摘要中提醒使用者檢查
- **平行執行**：Step 2 的兩個日記生成、Step 4 的兩組 Threads 生成，都可以平行執行以節省時間
- **不自動 commit**：生成的草稿只寫入檔案，不自動加入 git，讓使用者審閱後再決定
