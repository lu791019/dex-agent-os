
# Learning Note — 學習筆記產生器

將任何閱讀素材轉為結構化學習筆記，輸出到 `300_Learning/input/<type>/`。

## 使用方式

### 1. URL 模式（網頁文章）
```bash
./bin/agent learning-note --url "https://example.com/article" --force
./bin/agent learning-note --url "URL" --type tech --force
```

### 2. 本地檔案模式
```bash
./bin/agent learning-note --file ~/Downloads/paper.md --title "論文名" --type tech --force
```

### 3. Readwise 模式

**v2 Highlights（已標註的文章/書籍）：**
```bash
./bin/agent learning-note --readwise                    # 列出最近 7 天
./bin/agent learning-note --readwise --latest 3 --force # 匯入最新 3 篇
./bin/agent learning-note --readwise --all --force      # 匯入全部
```

**v3 Reader（RSS / 閱讀清單）：**
```bash
./bin/agent learning-note --readwise --reader                    # 列出 Reader 文件
./bin/agent learning-note --readwise --reader --latest 3 --force # 匯入最新 3 篇
```

### 4. RSS 模式
```bash
./bin/agent learning-note --rss "https://jvns.ca/atom.xml" --latest 1 --force
```

### 5. Anybox 模式
```bash
./bin/agent learning-note --anybox --starred --latest 3 --force
./bin/agent learning-note --anybox --tag "to-read" --latest 5 --force
```

## 參數

| 參數 | 說明 | 預設 |
|------|------|------|
| `--type` | 筆記類型：articles / books / courses / tech | articles |
| `--title` | 手動指定標題（--file 必填） | 自動擷取 |
| `--date` | 指定日期 (YYYY-MM-DD) | 今天 |
| `--force` | 覆蓋已存在的筆記 | false |
| `--latest N` | 匯入最新 N 篇 | 全部 |
| `--all` | 匯入全部（不限日期） | false |
| `--reader` | 使用 Readwise Reader v3（搭配 --readwise） | false |
| `--tag` | Anybox 標籤過濾 | - |
| `--folder` | Anybox 資料夾過濾 | - |
| `--starred` | Anybox 只抓星號書籤 | false |

## 輸出

檔案存放在 `300_Learning/input/<type>/YYYY-MM-DD-<slug>.md`，使用 learning-note template。

## 環境設定

- **Readwise**：`.env` 中設定 `READWISE_TOKEN`
- **Anybox**：`.env` 中設定 `ANYBOX_API_KEY`，且 Anybox app 需運行中
