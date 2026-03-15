
# Classroom Sync — Google Classroom 同步

以教師身份同步 Google Classroom 課程資料，匯入公告、作業和學生提交狀態。

## 觸發方式

- 指令：`./bin/agent classroom-sync`
- 指令：`./bin/agent classroom-sync --course "課程名稱" --type announcements`
- IDE 內：`/classroom-sync`

## 輸入來源

1. **Google Classroom API**：透過 `google_api.py`（需 classroom.readonly scope）
2. **篩選參數**：
   - `--course "名稱"` — 指定課程（預設：全部）
   - `--type announcements|coursework|all` — 資料類型（預設：all）
   - `--latest N` — 最新 N 筆（預設：10）
   - `--days N` — 最近 N 天（預設：7）
   - `--active-only` — 只同步進行中的課程

## 處理邏輯

1. 透過 Google Classroom API 列出教師課程
2. 根據篩選條件取得公告 / 作業
3. 對每筆資料擷取：
   - 公告：標題、內容、附件連結、發布日期
   - 作業：標題、說明、截止日期、提交狀態摘要
4. 轉換為 Markdown 格式
5. 無 LLM，純 API 擷取

## 輸出

- 路徑：`200_Work/classroom/YYYY-MM-DD-<course-slug>-<type>.md`
- frontmatter：course / type / synced_at / item_count
- 列表模式（無 `--force`）只顯示摘要不寫檔

## 前置需求

- Google API 已設定（`config/google-credentials.json`）
- 需要 `classroom.courses.readonly` + `classroom.announcements.readonly` + `classroom.coursework.readonly` scope
- 首次使用需重新授權（新增 Classroom scope）

## 原則

- **教師視角**：以課程管理和追蹤為主
- **不修改**：唯讀同步，不透過 API 修改 Classroom 資料
- **增量更新**：已匯入的項目不重複匯入
- **繁體中文**
