# Podcast Add — Podcast 逐字稿 → 結構化 episode 筆記

從 Podcast 逐字稿產出結構化 episode 筆記。使用繁體中文。

## 觸發方式
- IDE 內：`/podcast-add`
- 可選參數：`/podcast-add --transcript FILE --title "..."`
- 可選參數：`/podcast-add --apple`
- 可選參數：`/podcast-add --notion`
- 可選參數：`/podcast-add --readwise`

## 執行步驟

### Step 1：確認輸入模式

如果 `$ARGUMENTS` 包含 `--transcript`，使用手動文字稿模式。
如果 `$ARGUMENTS` 包含 `--apple`，使用 Apple Podcast 快取模式。
如果 `$ARGUMENTS` 包含 `--notion`，使用 Notion Podwise 模式。
如果 `$ARGUMENTS` 包含 `--readwise`，使用 Readwise 模式。
否則詢問使用者要用哪種模式。

### Step 2：手動文字稿模式（P4）

需要兩個資訊：
- 文字稿檔案路徑
- Episode 標題

```bash
python3 scripts/collectors/podcast_transcript.py --transcript "FILE" --title "TITLE" [--date YYYY-MM-DD] [--force]
```

### Step 3：Apple Podcast 快取模式（P3）

```bash
python3 scripts/collectors/podcast_transcript.py --apple [--latest N]
```

先列出可用快取，讓使用者選擇或指定 `--latest N`。

### Step 4：Notion Podwise 模式（P5）

```bash
python3 scripts/collectors/podcast_transcript.py --notion [--latest N] [--all] [--force]
```

需要先設定 `NOTION_TOKEN` 和 `NOTION_PODWISE_DB_ID`（見 GUIDE.md）。
先列出可用 episodes，讓使用者選擇或指定 `--latest N` / `--all`。

### Step 5：Readwise 模式（P6）

```bash
python3 scripts/collectors/podcast_transcript.py --readwise [--latest N] [--all] [--force]
```

需要先設定 `READWISE_TOKEN`（見 GUIDE.md）。
先列出可用 episodes，讓使用者選擇或指定 `--latest N` / `--all`。

### Step 6：確認結果
- 確認 `300_Learning/podcasts/episodes/YYYY-MM-DD-slug.md` 已產出
- 顯示筆記摘要

### Step 7：詢問後續
- 是否要手動補充「我的想法」區塊？
- 是否要將某些內容種子轉為 Topic？

## 注意事項
- Apple Podcast 快取需要 macOS 且有使用 Apple Podcasts app
- Notion/Readwise 模式需要先完成 Podwise 設定（見 GUIDE.md）
- 不自動 commit
