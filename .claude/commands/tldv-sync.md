
# tl;dv Sync — tl;dv 會議逐字稿同步到 Notion

從 tl;dv 網頁抓取會議逐字稿，自動分類後寫入 Notion。需要 Chrome 已登入 tl;dv。

## 觸發方式

- `/tldv-sync` — 同步最新 5 場
- `/tldv-sync --latest 3` — 同步最新 3 場
- `/tldv-sync --all` — 同步所有可見的會議

## 分類規則

```
1. 標題包含「專一」或「專二」→ 諮詢紀錄 DB（NOTION_CONSULT_DB）
2. 標題包含「靈感日日村」「Launch」「流量經營課」「日更工作區」「創作營」→ 學習 DB（NOTION_LEARNING_DB）
3. 其他 → 會議記錄 DB（NOTION_MEETING_DB）
```

## 執行步驟

### Step 1：開啟 tl;dv 會議列表

1. 用 `tabs_create_mcp` 建新 tab
2. 導航到 `https://tldv.io/app/meetings`
3. 等待 3 秒讓頁面載入

### Step 2：抽取會議清單

用 JavaScript 抽取所有會議標題和日期：

```javascript
const results = [];
document.querySelectorAll('a').forEach(a => {
  const text = a.innerText || '';
  if (text.includes('年') || text.includes('mins') || text.includes('min')) {
    const parts = text.split('\n').map(s => s.trim()).filter(Boolean);
    if (parts.length >= 2) {
      results.push({ title: parts[0], date: parts[1], duration: parts[2] || '' });
    }
  }
});
```

根據 `$ARGUMENTS` 決定同步幾場（預設 5），列出清單含自動分類結果給 Dex 確認。

### Step 3：逐場抽取逐字稿

對每場要同步的會議：

1. **點擊會議連結**（用 `read_page` 找到對應的 link ref，再用 `computer` left_click）
2. **等待 2 秒**
3. **點擊右上角「Transcript」tab**（截圖確認位置後點擊）
4. **等待 2 秒**讓逐字稿載入
5. **用 JavaScript 抽取逐字稿**：

```javascript
const allDivs = [...document.querySelectorAll('div')];
let transcriptDiv = null;
let maxLen = 0;
allDivs.forEach(div => {
  const rect = div.getBoundingClientRect();
  if (rect.left > 800) {
    const t = div.innerText || '';
    if (t.length > maxLen && !t.includes('Manual notes') && /\n\n/.test(t) && t.length > 200) {
      transcriptDiv = div;
      maxLen = t.length;
    }
  }
});
if (transcriptDiv) {
  let raw = transcriptDiv.innerText;
  // 移除頭部雜訊（Video / Transcript / Improve transcription）
  const speakerStart = raw.search(/^[A-Za-z\u4e00-\u9fff""\(\)（）\s]{2,30}\n/m);
  if (speakerStart > 0) raw = raw.substring(speakerStart);
  // 移除尾部播放器控制
  const cutoff = raw.indexOf('Back to current time');
  if (cutoff > 0) raw = raw.substring(0, cutoff).trim();
  raw;
}
```

6. 如果逐字稿容器需要捲動，先滾到底再抽取
7. **回到會議列表**：導航回 `https://tldv.io/app/meetings`

### Step 4：解析講者 + 日期

- **講者**：從逐字稿中提取不重複的名稱（每段格式：「講者名\n內容」）
- **日期**：從 Step 2 的日期文字解析為 YYYY-MM-DD（「2026年3月29日 上午10:00」→「2026-03-29」）
- **學員名稱**（諮詢用）：從標題 `Dex_姓名_專一討論_N` 解析出姓名

### Step 4.5：去重檢查（寫入前必做）

對每場會議，寫入前先查目標 Notion DB 是否已有同標題的紀錄：

```python
from lib.notion_api import query_database
import os

# 根據分類決定查哪個 DB
db_id = os.environ['NOTION_CONSULT_DB']  # 或 NOTION_MEETING_DB / NOTION_LEARNING_DB

existing = query_database(db_id, filter_obj={
    "property": "標題",
    "title": {"equals": title},
}, page_size=1)

if existing:
    print(f"  SKIP: {title}（Notion 已存在）")
    continue  # 跳過此場
```

**每場都要查，確保不重複寫入。**

### Step 5：寫入 Notion

根據分類規則寫入對應 DB：

**諮詢紀錄（專一/專二討論）：**
```python
from lib.notion_api import add_page, prop_title, prop_rich_text, prop_select, prop_date, block_paragraph
import os
db_id = os.environ['NOTION_CONSULT_DB']
props = {
    "標題": prop_title(title),
    "日期": prop_date(date_str),
    "對象": prop_rich_text(student_name),
    "來源": prop_select("tl;dv"),
    "摘要": prop_rich_text(transcript[:2000]),
}
children = [block_paragraph(transcript[i:i+1900]) for i in range(0, min(len(transcript), 20000), 1900)]
add_page(db_id, properties=props, children=children)
```

**學習（社群/課程）：**
```python
from lib.notion_sync import sync_learning_to_notion
sync_learning_to_notion(
    title=title, full_text=transcript,
    date_str=date_str, source_type='會議',
    author=speakers, summary=transcript[:500],
)
```

**會議記錄（其他）：**
```python
from lib.notion_sync import sync_meeting_to_notion
sync_meeting_to_notion(
    title=title, content=transcript,
    date_str=date_str, source='tl;dv',
    speakers=speakers, summary=transcript[:500],
)
```

### Step 6：回報結果

```
## tl;dv Sync 完成

| 會議 | 日期 | 類型 | Notion |
|------|------|------|--------|
| Dex_黃虹勳_專一討論_8 | 2026-03-29 | 諮詢 | ✅ |
| Threads流量經營課_Launch | 2026-03-26 | 學習 | ✅ |
| Dex x 緯育 講座討論 | 2026-03-28 | 會議 | ✅ |
```

## 注意事項

- **需要 Chrome 已登入 tl;dv**（免費版即可）
- **STT 輸出可能是簡體中文**，視 tl;dv 語言設定
- **去重**：寫入前查 Notion DB 是否已有同標題 + 同日期的紀錄，有就跳過
- **Notion 文字限制**：已在 `notion_api.py` 用 UTF-16 安全切分處理
- **每場會議約 4 個 Chrome 操作**（click → wait → click Transcript → JS extract）
- 新社群/課程關鍵字直接加到 Step 2 的分類規則即可
