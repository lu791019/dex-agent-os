# Phase 5a — Podcast + YouTube Weekly Digest + 市場趨勢簡報

## Context

Phase 1-4 已完成日記系統 + 內容管線 + 週回顧/電子報。使用者每週聽 3-5 集跨領域 podcast（科技/商業/職涯），但聽完容易忘記。

**需求：**
1. 下載 podcast 逐字稿 / YouTube 影片字幕，結構化存進系統
2. 每週自動彙整為「市場趨勢 + 學習摘要」
3. 產出 markdown（自用回顧）+ pptx（團隊/社群分享）
4. 打包成可重複使用的 skill

**架構決策：分成兩條獨立線**

```
YouTube 線（影片字幕 → 學習筆記 → 可餵進任何 workflow）
Podcast 線（音檔逐字稿 → episode 筆記 → 週度消化 → 簡報）
                    ↓                ↓
              共用：podcast-digest（週度彙整 + pptx）
```

---

## 逐字稿來源方案

### YouTube 線

| 方案 | 類型 | 說明 |
|------|:----:|------|
| **Y1. YouTube Transcript MCP** | MCP | `@kimtaeyoon83/mcp-server-youtube-transcript`，Claude Code 直接呼叫 |
| Y2. youtube-transcript-api | Python | 腳本自動化用 |
| Y3. yt-dlp 字幕 | CLI | 可同時下載音檔 |

### Podcast 線

| 方案 | 類型 | 說明 |
|------|:----:|------|
| **P1. Whisper MCP** | MCP | `jwulff/whisper-mcp`，100% 本地 |
| P3. Apple Podcast 快取 | Python | TTML 格式，已聽過的集數 |
| P4. 手動貼文字稿 | CLI | 萬用方案 |
| P5. Deepgram/AssemblyAI | API | 免費額度 |

**實作優先順序：Y2 + P4 先跑通 → P3 → MCP 路線**

---

## 資料流

```
YouTube URL → youtube-transcript-api → LLM 結構化 → 300_Learning/youtube/YYYY-MM-DD-slug.md
音檔/手動文字/Apple 快取 → LLM 結構化 → 300_Learning/podcasts/episodes/YYYY-MM-DD-slug.md
                                            ↓
                            podcast-digest（合併 YouTube + Podcast）
                                     ↓            ↓
                               Markdown 週摘要   .pptx 簡報
```

---

## 新增/修改檔案

### 新增（11 個）

| 檔案 | 用途 |
|------|------|
| `800_System/templates/podcast-episode-template.md` | 單集筆記模板 |
| `800_System/templates/youtube-note-template.md` | YouTube 筆記模板 |
| `800_System/templates/podcast-digest-template.md` | 週度消化模板 |
| `800_System/templates/podcast-pptx-template.md` | 簡報結構模板 |
| `scripts/collectors/youtube_transcript.py` | YouTube 字幕收集器 |
| `scripts/collectors/podcast_transcript.py` | Podcast 逐字稿收集器 |
| `scripts/generators/podcast_digest.py` | 週度消化報告生成器 |
| `canonical/workflows/podcast-weekly.md` | Podcast 週度 workflow |
| `.claude/commands/podcast-weekly.md` | `/podcast-weekly` skill |
| `.claude/commands/podcast-add.md` | `/podcast-add` skill |
| `.claude/commands/youtube-add.md` | `/youtube-add` skill |

### 修改（5 個）

| 檔案 | 變更 |
|------|------|
| `scripts/lib/config.py` | 新增路徑常數 |
| `bin/agent` | 新增子命令 |
| `.claude/settings.local.json` | MCP server 設定 |
| `GUIDE.md` | 新增系統說明 |
| `PLAN.md` | 更新完成狀態 |

---

## 儲存結構

```
300_Learning/
├── podcasts/
│   ├── episodes/      # 結構化筆記
│   ├── weekly/        # 週度消化報告
│   └── transcripts/   # 原始逐字稿（gitignore）
└── youtube/           # YouTube 學習筆記

500_Content/
└── presentations/     # 簡報輸出
```

---

## 核心邏輯

### youtube-add（youtube_transcript.py）
- youtube-transcript-api 取字幕 → `claude --print` 結構化 → 學習筆記
- CLI: `./bin/agent youtube-add "URL" [--force] [--date YYYY-MM-DD]`

### podcast-add（podcast_transcript.py）
- 多模式輸入：`--transcript`(手動) / `--apple`(TTML快取) / `--audio`(Whisper)
- 共用 LLM 結構化 → episode 筆記
- CLI: `./bin/agent podcast-add --transcript file.txt --title "..."`

### podcast-digest（podcast_digest.py）
- 合併 YouTube + Podcast episodes → 週度消化報告
- `--pptx` 同時產出簡報
- CLI: `./bin/agent podcast-digest [date] [--pptx] [--force]`

---

## 環境需求

| 套件 | 用途 | 必要性 |
|------|------|:------:|
| youtube-transcript-api | YouTube 字幕 | YouTube 線必要 |
| python-pptx | 簡報產出 | --pptx 時必要 |

**最低要求：** 手動貼逐字稿（P4）不需額外套件
**推薦安裝：** `pip install youtube-transcript-api python-pptx`
