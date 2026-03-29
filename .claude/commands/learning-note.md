
# Learning Note — 互動式深讀筆記

單篇文章的深度學習：抓全文 → LLM 結構化 → 跟你互動 → 產出有你想法的學習筆記。

跟 daily-learning 的差異：daily-learning = 每天批次快聊 3-5 篇摘要，learning-note = 針對一篇全文深讀。

## 觸發方式

```bash
# CLI（自動結構化，不互動）
./bin/agent learning-note --url "URL" [--type TYPE] [--force]
./bin/agent learning-note --file PATH --title "..." [--type TYPE]

# IDE 內（互動式，推薦）
/learning-note https://example.com/article
/learning-note（無 URL 時，從 Sheet 最近文章挑選）
```

## 互動流程

### Step 1：取得全文

- **有 URL**：`extract_url_content()` 抓全文
- **無 URL**：讀 Google Sheet「Readings」最近 7 天，列出 5-10 篇讓 Dex 選
- **有本地檔案**：直接讀取

### Step 2：LLM 結構化

跑 `./bin/agent learning-note --url "URL" --force`（或 --file），產出結構化筆記到 `300_Learning/input/`。

讀取產出的筆記檔案，印給 Dex 看。

### Step 3：互動對話（核心）

針對 LLM 產出的筆記，跟 Dex 聊 3-5 輪：

**提問模式（跟 daily-learning 一樣）：**

蘇格拉底式：
- 「這篇提到 X，你覺得跟你的經驗有什麼關聯？」
- 「作者的觀點跟你的做法一致嗎？有沒有矛盾的地方？」

考試式：
- 「這個方法的前提假設是什麼？什麼情況下會失效？」
- 「如果要用一句話反駁作者的觀點，你會怎麼說？」

深聊式：
- 「如果你要向朋友解釋這篇的重點，你會怎麼說？」
- 「讀完後最想記住的一件事是什麼？」

**注意**：因為有全文（最多 80,000 字），可以聊得比 daily-learning 更深、更技術。

### Step 4：收斂

- 整理 Dex 的回答，填入筆記的「我的想法」section
- 問 Dex：「這篇有沒有值得變成 Insight 的觀點？」

### Step 5：存檔

1. **更新本地筆記**：把「我的想法」寫回 `300_Learning/input/` 的筆記檔案
2. **寫入 Sheet**：摘要一行到「Readings」工作表（如果還沒有的話）
3. **Insight**（如果有）：
   - 本地精簡版 → `510_Insights/`
   - Notion 完整版 → 內容 DB（Phase E 完成後）
4. **日記**：學習紀錄寫進今日日記「今日學習」section

## CLI 模式（非互動）

直接跑 `./bin/agent learning-note --url "URL"` 仍然可以用，產出自動結構化筆記但沒有互動。
適合批次處理或不想聊的時候。

## 參數

| 參數 | 說明 | 預設 |
|------|------|------|
| `--type` | 筆記類型：articles / books / courses / tech | articles |
| `--title` | 手動指定標題（--file 必填） | 自動擷取 |
| `--date` | 指定日期 (YYYY-MM-DD) | 今天 |
| `--force` | 覆蓋已存在的筆記 | false |
| `--url` | 網頁 URL | - |
| `--file` | 本地檔案路徑 | - |

## 輸出

- 本地筆記：`300_Learning/input/<type>/YYYY-MM-DD-<slug>.md`
- Sheet：「Readings」一行摘要
- Insight（可選）：`510_Insights/` + Notion
- 日記：`100_Journal/daily/` 「今日學習」section
