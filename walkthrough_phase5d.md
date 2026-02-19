# Phase 5d Walkthrough — 500_Content 結構重組

> 完成日期：2026-02-19
> Branch：`phase-5d-restructure` → merged to `master`

## 變更摘要

將 `500_Content/` 拆為三層獨立目錄，統一內容管線流程。

### 新目錄結構

```
510_Insights/           ← 洞察素材庫（extract 產出）
520_Topics/             ← 結構化主題（TOPIC.md → 多頻道草稿）
530_Channels/           ← 各頻道草稿
  ├── threads/YYYY-MM-DD/   ← Threads 按日期
  ├── facebook/YYYY-MM-DD/
  ├── blog/YYYY-MM-DD/
  ├── newsletter/
  ├── short-video/YYYY-MM-DD/
  ├── film-reviews/YYYY-MM-DD/
  ├── podcast/{solo,collab}/
  └── presentations/
```

## Commits（5 個）

| Commit | 說明 |
|--------|------|
| `971a438` | Section A：資料夾建立 + 檔案搬遷（git mv） |
| `1da19ff` | Section B：config.py + 9 個 generator/extractor 腳本路徑更新 |
| `9fa4945` | Section C：`sync-all` 一鍵批次匯入指令 |
| `cbb6ffd` | Section D：`/daily-content` 改走完整流水線 |
| `78934d6` | Section E：68 檔文件更新 |

## 關鍵變更

### 1. config.py 路徑常數（`scripts/lib/config.py`）

移除：`CONTENT_DIR`, `CONTENT_INSIGHTS_DIR`, `NEWSLETTER_DRAFTS_DIR`, `NEWSLETTER_ARCHIVE_DIR`

新增：
- `INSIGHTS_DIR` → `510_Insights/`
- `TOPICS_DIR` → `520_Topics/`
- `CHANNELS_DIR` → `530_Channels/`
- `THREADS_DIR`, `FACEBOOK_DIR`, `BLOG_DIR`, `NEWSLETTER_DIR`, `SHORT_VIDEO_DIR`
- `FILM_REVIEWS_DIR`, `PODCAST_CONTENT_DIR`, `PRESENTATIONS_DIR`

### 2. file_utils.py 新增 helper

`extract_created_date(content)` — 從 TOPIC.md frontmatter 讀 `created:` 日期，用於決定輸出的日期資料夾。

### 3. `/daily-content` 新流程

```
L1 → Dayflow → L2 → extract insights → topic-create × N → topic-to-thread × N
```

取代舊的「直接 LLM 生成 6 篇 Threads」模式。

### 4. `sync-all` 指令

`./bin/agent sync-all` 一鍵跑 Readwise Reader + RSS + Anybox + Gmail 匯入。

## 文件更新範圍

| 類別 | 檔案數 | 說明 |
|------|--------|------|
| canonical/rules | 1 | 00-core.md 檔案位置表 |
| canonical/workflows | 7 | 所有涉及路徑的 workflow |
| .claude/commands | 9 | 所有涉及路徑的 command |
| 主要文件 | 4 | CLAUDE.md, AGENTS.md, GUIDE.md, PLAN.md |
| 內容檔案 | 6 | PODCAST_BIBLE × 2, TOPIC.md × 3, learning note × 1 |
| bin/sync 同步 | 全部 | .agent/ + .cursor/ 自動更新 |

## 端到端測試結果（2026-02-19）

完整 `/daily-content 2026-02-19` 流程：
- L2 精煉日記 → 46 行（1281 字元）
- Extract → 3 個 insights
- Topic-create → 3 個 TOPIC.md
- Topic-to-thread → 3 篇 Threads 草稿（`530_Channels/threads/2026-02-19/`）
- TOPIC.md checklist 自動更新 ✓
