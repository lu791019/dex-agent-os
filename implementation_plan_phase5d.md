# Phase 5d — 500_Content 結構重組 + sync-all + daily-content 改造

> 日期：2026-02-19
> 狀態：**已完成** — 2026-02-19 merged to master
> 目標：將 500_Content 拆為 510/520/530 三層，統一內容管線流程

---

## 背景

500_Content 目前有以下問題：
1. `insights/` 和 `topics/` 混在同一層，內容越來越多會混亂
2. Threads 草稿散落兩種格式（`/daily-content` 直出 vs `topic-create` 流程）
3. 各頻道分 queue/posted 子資料夾，實際上從未使用
4. 多個 sync 指令需分開跑，無一鍵匯入

## 決策

1. **500_Content 拆為 510/520/530**
   - `510_Insights/` — 洞察種子
   - `520_Topics/` — 主題企劃（每個主題一個資料夾）
   - `530_Channels/` — 各頻道草稿，按日期資料夾分
2. **530_Channels 用日期資料夾**（`threads/2026-02-18/xxx.md`）
   - 不區分待發/已發，全部存同一處，手動發布
3. **`/daily-content` 改走完整流程**
   - 日記 → extract insights → topic-create → topic-to-thread
   - 產出到 `530_Channels/threads/YYYY-MM-DD/`
4. **新增 `sync-all` 指令**
   - 一鍵跑完 readwise-sync + rss-sync + anybox-sync + gmail-sync

---

## Section A：資料夾建立 + 檔案搬遷

### A1. 建立新目錄結構

```
510_Insights/
520_Topics/
530_Channels/
  threads/
  facebook/
  blog/
  newsletter/
  podcast/
    solo/
    collab/
  short-video/
  film-reviews/
  presentations/
```

### A2. 搬遷現有檔案

| 來源 | 目標 | 數量 |
|------|------|------|
| `500_Content/insights/*.md` | `510_Insights/` | ~30 篇 |
| `500_Content/topics/<slug>/` （有 TOPIC.md 的） | `520_Topics/<slug>/`（只搬 TOPIC.md） | 4 個 |
| `500_Content/topics/<slug>/threads-draft.md` | `530_Channels/threads/<created-date>/<slug>.md` | 4 篇 |
| `500_Content/topics/YYYY-MM-DD-threads-from-*/thread-*.md` | `530_Channels/threads/YYYY-MM-DD/<slug>.md` | ~24 篇 |
| `500_Content/podcast/{solo,collab}/` | `530_Channels/podcast/{solo,collab}/` | 有內容就搬 |
| `500_Content/presentations/` | `530_Channels/presentations/` | 有內容就搬 |
| `500_Content/newsletter/drafts/` | `530_Channels/newsletter/` | 有內容就搬 |

### A3. 刪除舊 500_Content

- 確認搬遷完成後刪除 `500_Content/`
- 更新 `.gitignore` 如有相關條目

---

## Section B：config.py + 腳本路徑更新

### B1. `scripts/lib/config.py`

更新路徑常數：

```python
# 舊
INSIGHTS_DIR = ROOT_DIR / "500_Content" / "insights"
TOPICS_DIR = ROOT_DIR / "500_Content" / "topics"
# ... 各頻道

# 新
INSIGHTS_DIR = ROOT_DIR / "510_Insights"
TOPICS_DIR = ROOT_DIR / "520_Topics"
CHANNELS_DIR = ROOT_DIR / "530_Channels"
THREADS_DIR = CHANNELS_DIR / "threads"
FACEBOOK_DIR = CHANNELS_DIR / "facebook"
BLOG_DIR = CHANNELS_DIR / "blog"
NEWSLETTER_DIR = CHANNELS_DIR / "newsletter"
SHORT_VIDEO_DIR = CHANNELS_DIR / "short-video"
FILM_REVIEWS_DIR = CHANNELS_DIR / "film-reviews"
PODCAST_CONTENT_DIR = CHANNELS_DIR / "podcast"
PRESENTATIONS_DIR = CHANNELS_DIR / "presentations"
```

### B2. 更新所有 generator 腳本的輸出路徑

| 腳本 | 改動 |
|------|------|
| `topic_create.py` | 輸出到 `520_Topics/<slug>/TOPIC.md` |
| `topic_to_thread.py` | 輸出到 `530_Channels/threads/YYYY-MM-DD/<slug>.md` |
| `topic_to_fb.py` | 輸出到 `530_Channels/facebook/YYYY-MM-DD/<slug>.md` |
| `topic_to_blog.py` | 輸出到 `530_Channels/blog/YYYY-MM-DD/<slug>.md` |
| `topic_to_short_video.py` | 輸出到 `530_Channels/short-video/YYYY-MM-DD/<slug>.md` |
| `film_review.py` | 輸出到 `530_Channels/film-reviews/YYYY-MM-DD/<slug>.md` |
| `journal_knowledge_extract.py` | insights 輸出到 `510_Insights/` |
| `weekly_newsletter.py` | 輸出到 `530_Channels/newsletter/` |
| `podcast_digest.py` | 簡報輸出到 `530_Channels/presentations/` |

### B3. 各腳本加入日期資料夾建立邏輯

所有寫到 `530_Channels/` 的腳本需要：
1. 從 TOPIC.md frontmatter 或參數取得日期
2. `ensure_dir(THREADS_DIR / date_str)`
3. 寫入到日期資料夾內

---

## Section C：sync-all 指令

### C1. `bin/agent` 加入 `sync-all` 子命令

```bash
sync-all)
    echo "[sync-all] 開始批次匯入..."
    python3 "$ROOT_DIR/scripts/collectors/readwise_sync.py" --reader --latest 10 "$@"
    python3 "$ROOT_DIR/scripts/collectors/rss_sync.py" --latest 10 "$@"
    python3 "$ROOT_DIR/scripts/collectors/anybox_sync.py" --latest 10 "$@"
    python3 "$ROOT_DIR/scripts/collectors/gmail_sync.py" --latest 10 "$@"
    echo "[sync-all] 批次匯入完成"
    ;;
```

- 預設每個來源最新 10 筆
- 可透過 `--force` 覆蓋已存在檔案
- 個別 sync 的 token 未設定時會顯示引導訊息而非 crash

---

## Section D：`/daily-content` 改造

### D1. 改走完整流程

新的 `/daily-content` 流程：

```
Step 1: 產出日記（Dayflow → L2，同舊版）
Step 2: extract insights（從 L2 萃取 insights 到 510_Insights/）
Step 3: topic-create（從 insights 建立 TOPIC.md 到 520_Topics/）
Step 4: topic-to-thread（從 TOPIC.md 產出草稿到 530_Channels/threads/YYYY-MM-DD/）
```

### D2. 更新 `.claude/commands/daily-content.md`

重寫 skill 定義，步驟改為：
1. Step 0: 解析參數、確認日期
2. Step 1: 生成 L1 + Dayflow + L2（同舊版）
3. Step 2: 呼叫 `extract` 從 L2 萃取 insights
4. Step 3: 對每個新 insight 呼叫 `topic-create`
5. Step 4: 對每個新 topic 呼叫 `topic-to-thread`
6. Step 5: 產出摘要

### D3. 保持向下相容

- `topic-to-thread` 等腳本仍可單獨使用
- `/daily-content` 只是串接它們的流水線

---

## Section E：文件更新 + 收尾

### E1. 更新 CLAUDE.md

- CLI 速查表加入 `sync-all`
- 專案結構表更新（500 → 510/520/530）

### E2. 更新 GUIDE.md

- 目錄結構說明
- 內容管線流程圖
- sync-all 用法
- /daily-content 新流程

### E3. 更新 PLAN.md

- 加入 Phase 5d 區段

### E4. 更新 MEMORY.md

- 記錄 Phase 5d 完成狀態

### E5. 更新 canonical/ workflows

- 涉及路徑的 workflow 檔案更新
- `bin/sync` 同步

### E6. 更新 `canonical/rules/00-core.md`

- 檔案位置規則反映新結構

---

## 風險與注意事項

1. **搬遷現有檔案**：需確認 git 追蹤正確（`git mv` 保留歷史）
2. **舊的 `/daily-content` 產出**：`topics/YYYY-MM-DD-threads-from-*` 搬完後刪除
3. **extract 腳本**：確認 insights 輸出路徑已改，不會寫回舊位置
4. **測試**：每個 generator 都要跑一次確認路徑正確
