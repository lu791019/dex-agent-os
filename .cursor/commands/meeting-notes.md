
# Meeting Notes — 會議筆記產生器

從會議逐字稿、手寫筆記或 Google Doc 產出結構化會議紀錄。

## 觸發方式

- 指令：`./bin/agent meeting-notes --title "會議名稱" --source <來源>`
- IDE 內：`/meeting-notes`

## 輸入來源

1. **逐字稿檔案**：`--file <path>`（純文字或 Markdown）
2. **Google Doc**：`--gdoc <doc-id>`（需 Google API 授權）
3. **Fireflies 會議**：`--fireflies <meeting-id>`（自動拉取逐字稿）
4. **手動筆記**：`--notes "重點筆記"`（搭配 --title 使用）
5. **寫作規則**：`canonical/rules/10-writing-style.md`

## 處理邏輯

1. 讀取指定來源的會議內容
2. 如果是 Fireflies 來源，先呼叫 `fireflies_collector.py` 取得逐字稿
3. 如果是 Google Doc 來源，透過 `google_api.py` 讀取文件內容
4. 將原始內容交給 LLM 提煉：
   - 會議基本資訊（日期、參與者、時長）
   - 討論摘要（分主題條列）
   - 決議事項（Action Items）
   - 待追蹤項目
   - 關鍵引述（選用）
5. 組裝 frontmatter + 結構化內容

## 輸出

- 路徑：`200_Work/meetings/YYYY-MM-DD-<slug>.md`
- frontmatter：title / date / attendees / source / type:meeting
- 如果已存在，詢問是否覆蓋或使用 `--force`

## 原則

- **精準**：Action Items 必須明確指定負責人和期限
- **簡潔**：摘要是原始內容的 1/5~1/3 長度
- **不遺漏**：所有決議事項必須被捕捉
- **繁體中文**
