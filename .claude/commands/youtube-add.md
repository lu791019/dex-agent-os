# YouTube Add — YouTube 字幕 → 結構化學習筆記

從 YouTube 影片取得字幕，透過 LLM 產出結構化學習筆記。使用繁體中文。

## 觸發方式
- IDE 內：`/youtube-add`
- 可選參數：`/youtube-add URL`

## 執行步驟

### Step 1：確認 YouTube URL
- 如果 `$ARGUMENTS` 包含 URL，直接使用
- 否則請使用者提供 YouTube URL

### Step 2：執行收集器
```bash
python3 scripts/collectors/youtube_transcript.py "$URL" [--force]
```

### Step 3：確認結果
- 確認 `300_Learning/youtube/YYYY-MM-DD-slug.md` 已產出
- 顯示筆記摘要

### Step 4：詢問後續
- 是否要手動補充「我的想法」區塊？
- 是否要將某些內容種子轉為 Topic？

## 注意事項
- 需要安裝 `youtube-transcript-api`：`pip3 install youtube-transcript-api`
- 支援語言優先序：繁體中文 > 簡體中文 > 英文
- 不自動 commit
