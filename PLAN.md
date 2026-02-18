# Dex Agent OS — 完整專案規劃

> 個人 AI 代理人作業系統
> 涵蓋：生產力、學習、輸入輸出、工作管理、專案、產品、寫作
> 最後更新：2026-02-11

---

## 目錄

- [1. 專案願景](#1-專案願景)
- [2. 系統架構](#2-系統架構)
- [3. 目錄結構](#3-目錄結構)
- [4. 跨平台同步架構](#4-跨平台同步架構)
- [5. 規則系統](#5-規則系統)
- [6. 內容生產管線](#6-內容生產管線)
- [7. 風格 DNA 系統](#7-風格-dna-系統)
- [8. 工具生態系統](#8-工具生態系統)
- [9. Token 管理策略](#9-token-管理策略)
- [10. API 費用策略](#10-api-費用策略)
- [11. 實作階段 Phase 1-7](#11-實作階段-phase-1-7)
- [12. 關鍵決策紀錄](#12-關鍵決策紀錄)

---

## 1. 專案願景

### 核心概念

Dex Agent OS 是一套「個人 Agent OS」，由四層組成：

| 層級 | 說明 | 對應實作 |
|------|------|----------|
| **資料層（Input）** | 每天的數位足跡 | `data/`、`000_Inbox/`、work-log、Dayflow |
| **規則層（Persona）** | AI 的思考方式、寫作風格、安全護欄 | `canonical/rules/`、`AGENTS.md` |
| **執行層（Tools）** | AI 能做的事 | `scripts/`、`bin/agent`、`claude --print` |
| **流程層（Workflow）** | 觸發詞串起工作 | `canonical/workflows/`、`bin/agent`、launchd |

### 覆蓋範疇

```
┌──────────────────────────────────────────┐
│              Dex Agent OS                │
│                                          │
│  工作        學習        創作 & 發布      │
│  ├ 會議      ├ 閱讀      ├ 電子報        │
│  ├ 諮詢      ├ 課程      ├ Threads       │
│  ├ 程式開發  ├ 技術實驗  ├ Facebook      │
│  ├ 產品管理  └ TIL       ├ Blog          │
│  ├ 專案管理              ├ Podcast       │
│  ├ 行銷                  ├ 短影音        │
│  └ 訂閱管理              └ 影評          │
│  個人                                    │
│  ├ 職涯思考                              │
│  ├ 每日反思                              │
│  └ 生活靈感                              │
└──────────────────────────────────────────┘
```

---

## 2. 系統架構

### 資料流全貌

```
                    ┌──────────────┐
                    │  你的一天     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ 工作     │ │ 學習     │ │ 靈感     │
        │ Dayflow  │ │ 閱讀     │ │ 對話     │
        │ Git      │ │ 課程     │ │ 社群     │
        │ 會議     │ │          │ │          │
        │ 諮詢     │ │          │ │          │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             ▼            ▼            ▼
     ┌───────────┐ ┌───────────┐ ┌───────────┐
     │/work-log  │ │/learning  │ │/idea      │
     │(全域指令) │ │-note      │ │-capture   │
     └────┬──────┘ └─────┬─────┘ └─────┬─────┘
          │              │              │
          ▼              ▼              ▼
  ~/work-logs/    300_Learning/    000_Inbox/
          │              │              │
          └──────┬───────┴──────────────┘
                 ▼
          /daily-journal
                 │
                 ▼
          100_Journal/daily/YYYY-MM-DD.md
                 │
          ┌──────┴──────────────┐
          ▼                     ▼
   /weekly-review         /topic-create
          │                     │
          ▼                     ▼
   週回顧 + 學習摘要    500_Content/topics/<slug>/TOPIC.md
                                │
          ┌──────┬──────┬───────┼───────┬──────┬──────┐
          ▼      ▼      ▼      ▼       ▼      ▼      ▼
       Thread   FB   Newsletter Blog  Podcast  短影音  影評
          │      │      │       │       │      │      │
          │  各自讀取對應的 style-dna + template        │
          │      │      │       │       │      │      │
          ▼      ▼      ▼       ▼       ▼      ▼      ▼
        草稿   草稿   草稿    草稿    草稿   草稿   草稿
          │      │      │       │       │      │      │
          └──────┴──────┴───┬───┴───────┴──────┴──────┘
                            ▼
                     你審稿 & 修改
                            │
                            ▼
                     發布 → 700_Archive/
                            │
                            ▼
                  好的成品回存 examples/
                            │
                            ▼
                  定期 /extract-style 更新 DNA
```

### work-log 整合架構

work-log 合併進 Agent OS，但 `/work-log` 指令保持全域可用：

```
資料流層級：

L0 — 自動記錄    git commit hook 自動追加         ~/work-logs/YYYY/MM/
L1 — 完整日誌    /work-log 產出詳細工作日誌       ~/work-logs/YYYY/MM/
L2 — 精煉日記    Agent OS 讀 L1 → 摘要/洞察/行動  100_Journal/daily/
L3 — 週報        Agent OS 讀 7 天 L2 → 主題+草稿  500_Content/newsletter/drafts/
```

### Dayflow 活動摘要（與 L1→L2 平行的獨立管線）

```
Dayflow SQLite DB
  ├── timeline_cards (螢幕活動記錄)
  └── observations (AI 觀察)
         │
         ▼
  ./bin/agent dayflow [YYYY-MM-DD]
         │  讀取 SQLite → 格式化 → claude --print 整理
         ▼
  100_Journal/daily/YYYY-MM-DD-dayflow.md
```

**與 L2 的差異：**

| | L2 精煉日記 | Dayflow 活動摘要 |
|---|---|---|
| 輸入 | L1 工作日誌 + Dayflow 摘要（如存在） | Dayflow SQLite 直接讀取 |
| 視角 | 「做了什麼 + 行為模式洞察」 | 「螢幕上怎麼度過一天」 |
| 觸發 | `./bin/agent journal` | `./bin/agent dayflow` |
| 輸出 | `YYYY-MM-DD.md` | `YYYY-MM-DD-dayflow.md` |

### 完整日記產出順序

```
1. /work-log YYYY-MM-DD          → 產出 L1（完整工作日誌）
2. ./bin/agent dayflow YYYY-MM-DD → 產出 Dayflow 活動摘要
3. ./bin/agent journal YYYY-MM-DD → 從 L1 + Dayflow 摘要產出 L2（精煉日記，需先跑完 step 2）
```

---

## 3. 目錄結構

```
dex-agent-os/

  # ============================================
  # 跨平台同步系統
  # ============================================

  canonical/                          # 唯一真實來源（只改這裡）
    rules/
      00-core.md                      #   身份 + 決策原則 + IPO
      10-writing-style.md             #   各頻道寫作風格
      20-safety.md                    #   安全護欄
    workflows/
      # --- 每日 ---
      daily-collect.md                #   收集今日數位足跡 → data/raw/
      daily-journal.md                #   ✅ 讀 work-log → 精煉日記
      daily-review.md                 #   ✅ 今日回顧：做了什麼、學了什麼、卡在哪
      daily-dayflow-digest.md         #   ✅ Dayflow 螢幕活動 → 活動摘要日記
      daily-idea-capture.md           #   整理今天的靈感 → 000_Inbox/ideas/
      # --- 工作 ---
      meeting-notes.md                #   會議結束 → 摘要 + 行動項
      consultation-notes.md           #   諮詢結束 → 摘要 + 建議 + 內容萃取
      subscription-review.md          #   月度掃描訂閱 → 續約建議
      # --- 學習 ---
      learning-note.md                #   消化文章/影片 → 學習筆記
      learning-weekly.md              #   本週學了什麼 → 摘要
      # --- 專案 & 產品 ---
      project-status.md               #   掃描所有專案 → 狀態摘要
      project-kickoff.md              #   新專案啟動 checklist
      product-feature-spec.md         #   寫功能規格
      product-roadmap-update.md       #   更新 roadmap
      # --- 內容生產 ---
      topic-create.md                 #   從洞察建立主題 → topics/
      topic-to-thread.md              #   主題 → Threads 草稿
      topic-to-fb.md                  #   主題 → FB 貼文草稿
      topic-to-newsletter.md          #   主題 → 電子報段落
      topic-to-blog.md                #   主題 → Blog 長文草稿
      topic-to-podcast.md             #   主題 → Podcast 文稿
      topic-to-short-video.md         #   主題 → 短影音腳本
      # --- 影評 ---
      film-review.md                  #   看完電影 → 影評草稿
      film-analysis.md                #   深度主題分析
      # --- 職涯 ---
      career-reflection.md            #   定期職涯反思
      opportunity-evaluate.md         #   評估一個機會
      # --- 彙整 ---
      weekly-newsletter.md            #   組裝完整電子報
      weekly-review.md                #   週回顧：進度、偏離、調整
      # --- 風格 ---
      extract-style.md                #   分析範例 → 更新 style-dna
      # --- 發布 ---
      wp-sync.md                      #   推 WordPress 草稿
      wp-archive.md                   #   發布後抓回存檔
    skills/
      daily-journal/SKILL.md
      weekly-newsletter/SKILL.md
      project-tracker/SKILL.md
      learning-note/SKILL.md
      content-repurpose/SKILL.md
      style-extractor/SKILL.md

  AGENTS.md                           # 跨平台共用核心人格（三邊都讀）
  CLAUDE.md                           # Claude Code 專案指令（< 200 tokens）

  .agent/                             # Antigravity（由 bin/sync 產生）
    rules/
    workflows/
    skills/
  .cursor/                            # Cursor（由 bin/sync 產生）
    rules/                            #   .mdc 格式 + YAML frontmatter
    commands/                         #   含同步的全域 skills + commands
  .claude/                            # Claude Code（由 bin/sync 產生）
    skills/
    commands/

  # ============================================
  # 系統記憶 & 上下文（有機生長）
  # ============================================

  context/
    preferences.md                    # AI 從互動中學到的偏好
    feedback-log.md                   # 你對 AI 輸出的修正紀錄
    topic-registry.md                 # 長期關注的主題 + 權重
    active-projects.md                # 目前進行中的專案清單
    learning-queue.md                 # 想學 / 正在學的東西

  # ============================================
  # 資料層
  # ============================================

  data/
    raw/YYYY-MM-DD/                   # 每日原始收集（gitignore）
      discord.json
      notion.md
      dayflow.md
    processed/YYYY-MM-DD/             # AI 整理後的中間產物
      summary.md

  # ============================================
  # 內容區（編號 = 從輸入到輸出的流向）
  # ============================================

  # --- 000: 所有東西的入口 ---
  000_Inbox/
    ideas/                            # 隨手記的靈感 & 閃念
    readings/                         # 閱讀摘要 & 筆記
    bookmarks/                        # 待讀 / 待看 / 待聽

  # --- 100: 每日紀錄 ---
  100_Journal/
    daily/                            # 每日紀錄
      YYYY-MM-DD.md                   #   ✅ L2 精煉日記（from L1 work-log）
      YYYY-MM-DD-dayflow.md           #   ✅ Dayflow 活動摘要（from SQLite）
    weekly/                           # 每週回顧
      YYYY-Wxx.md

  # --- 200: 工作 ---
  200_Work/
    meetings/                         # 會議紀錄
      YYYY-MM-DD-title/
        transcript.md                 #   文字稿
        notes.md                      #   會後摘要 & 行動項
        recording.md                  #   錄影連結（不存檔案本體）
    consultations/                    # 諮詢紀錄（給予 & 接受）
      YYYY-MM-DD-person-topic/
        transcript.md                 #   文字稿
        notes.md                      #   諮詢摘要 & 建議 & 行動項
        recording.md                  #   錄影/錄音連結
    code-lab/                         # 程式實驗 & 程式片段
      experiment-name/
        README.md
    marketing/                        # 行銷
      ideas/                          #   靈感池
      campaigns/                      #   進行中的 campaign
      competitive/                    #   競品觀察
    subscriptions/                    # 訂閱 & 工具管理
      overview.md                     #   所有訂閱一覽
      evaluations/                    #   工具評估筆記

  # --- 300: 學習 ---
  300_Learning/
    input/                            # 學習輸入
      courses/                        #   課程筆記
      books/                          #   讀書筆記
      tech/                           #   技術學習
    output/                           # 學習輸出
      til/                            #   Today I Learned 短篇
      tutorials/                      #   教學文草稿
    weekly/                           # 每週學習摘要
    podcasts/                         # ✅ Podcast 系統
      episodes/                       #   結構化 episode 筆記
      weekly/                         #   週度消化報告
      transcripts/                    #   原始逐字稿（gitignore）
    youtube/                          # ✅ YouTube 學習筆記

  # --- 400: 專案 & 產品 ---
  400_Projects/
    software/                         # 軟體/技術專案
      project-name/
        STATUS.md
        DECISIONS.md
    products/                         # 產品管理
      product-name/
        overview.md                   #   產品定位 & 目標
        roadmap.md                    #   功能規劃 & 排程
        features/                     #   功能規格
        metrics.md                    #   關鍵指標追蹤

  # --- 500: 內容生產管線 ---
  500_Content/
    presentations/                    # ✅ 簡報輸出
    topics/                           # 主題庫（內容原子）
      topic-slug/
        TOPIC.md                      #   核心論點 + 素材 + 進度追蹤
        threads-draft.md
        fb-draft.md
        newsletter-section.md
        blog-draft.md
        podcast-script.md
        short-video-script.md
    newsletter/                       # 電子報
      drafts/
      archive/
    threads/                          # Threads
      queue/                          #   待發草稿
      posted/                         #   已發存檔
    facebook/                         # Facebook
      queue/
      posted/
    blog/                             # WordPress 長文
      drafts/
      posted/
    podcast/                          # Podcast
      episodes/
        ep-xx-title/
          script.md
          show-notes.md
      ideas/
    short-video/                      # 短影音
      ideas/
      scripts/

  # --- 600: 個人 ---
  600_Life/
    career/                           # 職涯思考
      reflections/                    #   階段性反思
      goals/                          #   短中長期目標
      opportunities/                  #   機會評估
    film/                             # 影評 & 文化評論
      reviews/                        #   影評文案
      analysis/                       #   深度分析
      watchlist.md                    #   待看清單
    personal/                         # 其他個人想法
      reflections/
      ideas/

  # --- 700: 已發布存檔 ---
  700_Archive/
    newsletter/
    blog/
    threads/
    facebook/
    podcast/
    film-reviews/

  # --- 800: 系統設定 ---
  800_System/
    templates/                        # 各頻道輸出模板
      journal-template.md             #   ✅ L2 精煉日記模板
      dayflow-digest-template.md      #   ✅ Dayflow 活動摘要模板
      consultation-notes-template.md  #   ✅ 諮詢紀錄模板
      topic-template.md               #   ✅ TOPIC.md 格式模板
      thread-template.md              #   ✅ Threads 草稿格式模板
      podcast-episode-template.md     #   ✅ Podcast episode 筆記模板
      youtube-note-template.md        #   ✅ YouTube 學習筆記模板
      podcast-digest-template.md      #   ✅ 週度消化報告模板
      podcast-pptx-template.md        #   ✅ 簡報內容結構模板
      meeting-notes-template.md
      project-status-template.md
      product-feature-template.md
      fb-post-template.md
      newsletter-template.md
      blog-template.md
      podcast-script-template.md
      short-video-template.md
      film-review-template.md
    references/                       # 風格參考
      examples/                       #   過去的真實範例
        threads/
        facebook/
        newsletter/
        blog/
        podcast/
        short-video/
        film-reviews/
      style-dna/                      #   從範例提取的抽象風格文件
        threads-dna.md
        facebook-dna.md
        newsletter-dna.md
        blog-dna.md
        podcast-dna.md
        short-video-dna.md
        film-review-dna.md

  # ============================================
  # 工具 & 腳本
  # ============================================

  scripts/
    collectors/                       # 資料收集
      threads_collector.py            #   ✅ Threads API 自動抓取（直接 token）
      youtube_transcript.py           #   ✅ YouTube 字幕 → 學習筆記
      podcast_transcript.py           #   ✅ Podcast 逐字稿 → episode 筆記
      discord_collector.py            #   (future)
      notion_collector.py             #   (future)
    generators/                       # 內容生成
      daily_journal.py                #   ✅ L1→L2 精煉日記生成器
      daily_dayflow_digest.py         #   ✅ Dayflow 活動摘要生成器
      topic_create.py                 #   ✅ insight → TOPIC.md
      topic_to_thread.py              #   ✅ TOPIC.md → Threads 草稿
      podcast_digest.py               #   ✅ YouTube + Podcast 週度消化 + 簡報
      weekly_newsletter.py
      weekly_learning.py
    publishers/                       # 發布
      wp_draft.py
      wp_archive.py
    analyzers/                        # 分析
      extract_style.py                #   ✅ 範例 → 風格 DNA
    lib/                              # 共用模組
      __init__.py                     #   ✅ Package marker
      llm.py                          #   ✅ claude --print 封裝
      config.py                       #   ✅ 路徑與常數設定
      file_utils.py                   #   ✅ 檔案操作工具

  bin/
    agent                             # ✅ CLI 入口（journal、dayflow、sync、collect-threads、extract-style、topic-create、topic-to-thread、youtube-add、podcast-add、podcast-digest）
    sync                              # ✅ 跨平台同步腳本
    setup                             # 一鍵安裝（launchd、依賴）

  config/
    schedules/                        # launchd plist 排程
      com.dex.daily-collect.plist
      com.dex.daily-journal.plist
      com.dex.weekly-digest.plist
    .env.example                      # 環境變數範本

  work-log/                           # ✅ 從 ~/work-logs/ 合併進來
    scripts/
      extract-sessions.py             #   ✅ 支援 --date 參數
      post-commit-log.sh
    templates/
      daily-template.md

  .gitignore
  requirements.txt
  PLAN.md                             # ← 本文件
```

---

## 4. 跨平台同步架構

### 三個 IDE 各自讀取什麼

| 檔案/目錄 | Claude Code | Antigravity | Cursor |
|-----------|:-----------:|:-----------:|:------:|
| `AGENTS.md` | ✅ 自動載入 | ✅ 自動載入 | ✅ 自動載入 |
| `CLAUDE.md` | ✅ 自動載入 | ❌ | ❌ |
| `.agent/rules/*.md` | ❌ | ✅ 自動載入 | ❌ |
| `.agent/workflows/*.md` | ❌ | ✅ `/` 觸發 | ❌ |
| `.agent/skills/*/SKILL.md` | ❌ | ✅ 按需載入 | ❌ |
| `.cursor/rules/*.mdc` | ❌ | ❌ | ✅ 自動載入 |
| `.cursor/commands/*.md` | ❌ | ❌ | ✅ `/` 觸發 |
| `~/.claude/skills/*/SKILL.md` | ✅ 按需載入 | ❌ | ❌ |
| `~/.claude/commands/*.md` | ✅ `/` 觸發 | ❌ | ❌ |
| `~/.gemini/antigravity/skills/` | ❌ | ✅ 按需載入 | ❌ |
| `~/.gemini/antigravity/global_workflows/` | ❌ | ✅ `/` 觸發 | ❌ |

### 同步機制

```
canonical/（你只改這裡）
    │
    │  bin/sync
    │
    ├──→ .agent/rules/          直接複製 .md
    ├──→ .agent/workflows/      加 YAML frontmatter (description)
    ├──→ .agent/skills/         直接複製
    │
    ├──→ .cursor/rules/         加 YAML frontmatter (description, alwaysApply) → .mdc
    ├──→ .cursor/commands/      去掉 YAML frontmatter → 純 .md
    │
    ├──→ .claude/skills/        直接複製
    └──→ .claude/commands/      去掉 YAML frontmatter → 純 .md

全域同步（bin/sync 也處理）：
    ~/.claude/skills/ (41個) ──→ ~/.gemini/antigravity/skills/
    ~/.claude/commands/ (11個) ──→ ~/.gemini/antigravity/global_workflows/
                               ──→ .cursor/commands/
```

### 日常操作

```bash
# 修改規則後
vim ~/dex-agent-os/canonical/rules/10-writing-style.md
~/dex-agent-os/bin/sync
# 完成，三個 IDE 下次開都會讀到新規則
```

---

## 5. 規則系統

### 00-core.md — 身份與決策原則

- Dex 的定位（資料工程 / AI / 內容創作者）
- IPO 決策權限（低風險自動 / 高風險確認）
- 檔案寫入位置規則（含 Dayflow 活動摘要路徑）
- 產出格式偏好（Markdown、條列、繁體中文）

### 10-writing-style.md — 各頻道寫作風格

- 電子報框架（開場 → 3-5 主題 → 收尾推薦）
- Threads 風格（Hook → 條列 → 金句，150-250 字）
- Facebook 風格（社群感、故事展開、開放提問）
- Blog 風格（SEO 標題、H2/H3 結構、教學步驟）
- Podcast/短影音/影評風格（各自特性）
- 禁止事項（不雞湯、不假裝、不過度行銷）

### 20-safety.md — 安全護欄

- 絕對禁止自動執行的操作（刪除、發布、金流）
- 必須先問 Dex 的操作（對外公開、不可逆）
- API Token 安全規則
- 資料隱私規則

---

## 6. 內容生產管線

### 核心概念：一個主題，七種輸出

```
一個洞察/主題 (TOPIC.md)
    │
    ├→ /topic-to-thread     → Threads 草稿（短、銳利）
    ├→ /topic-to-fb         → Facebook 草稿（社群感）
    ├→ /topic-to-newsletter  → 電子報段落（深度）
    ├→ /topic-to-blog       → Blog 長文（SEO、教學）
    ├→ /topic-to-podcast    → Podcast 文稿（口語化）
    ├→ /topic-to-short-video → 短影音腳本（視覺節奏）
    └→ /film-review          → 影評（觀點 + 啟發）
```

### TOPIC.md 格式

```markdown
# 主題：用 Claude Code 打造個人 Agent OS

## 狀態：drafting
## 來源：2026-02-07 日記洞察
## 標籤：AI, 效率, 工具

## 核心論點
一句話：個人化 AI 不是黑科技，是「規則＋資料＋工具＋流程」的工程問題。

## 關鍵素材
- 自己的實作經驗
- 三個 IDE 的比較
- IPO 原則

## 已產出的格式
- [x] Threads
- [ ] Facebook
- [x] Newsletter 段落
- [ ] Blog
- [ ] Podcast
- [ ] 短影音
```

### 內容生產流程

| 步驟 | 觸發詞 | 輸入 | 輸出 |
|------|--------|------|------|
| 1. 捕捉 | `/daily-idea-capture` | 今日對話/閱讀/靈感 | `000_Inbox/ideas/` |
| 2. 消化 | `/learning-note` | 文章/課程/影片 | `300_Learning/input/` |
| 3. 提煉主題 | `/topic-create` | Journal + Learning + Ideas | `500_Content/topics/<slug>/TOPIC.md` |
| 4. 多格式產出 | `/topic-to-<channel>` | TOPIC.md + style-dna + template | `500_Content/topics/<slug>/<channel>-draft.md` |
| 5. 彙整電子報 | `/weekly-newsletter` | 本週多個主題段落 | `500_Content/newsletter/drafts/` |
| 6. 發布 + 存檔 | 手動發布 → `/wp-archive` | 已發布內容 | `700_Archive/` |

---

## 7. 風格 DNA 系統

### 概念

從你過去的真實貼文中提取抽象寫作模式，讓 AI 產出的新內容「像你寫的」。

### 運作方式

```
800_System/references/examples/threads/
  001-agent-os.md        ← 你過去的真實 Threads 貼文
  002-data-pipeline.md
  003-career-switch.md
  ...
        │
        │  /extract-style threads
        ▼
800_System/references/style-dna/threads-dna.md   ← AI 分析後的抽象風格文件
```

### Style DNA 包含的維度

| 維度 | 說明 |
|------|------|
| 結構模式 | 常見的段落結構（例如 Hook → 條列 → 金句） |
| 開場 Hook 模式 | 反差型、提問型、宣告型等 |
| 語氣特徵 | 精準、口語比例、用字習慣 |
| CTA / 收尾模式 | 金句收尾、開放提問、行動呼籲 |
| 長度 / 格式 | 典型字數、段落數、標點習慣 |
| 高互動特徵 | 從互動數據回推的成功模式 |
| 禁忌 | 應避免的模式 |

### 範例存放格式

```markdown
<!-- 800_System/references/examples/threads/001-agent-os.md -->

## 元資料
- 發布日期：2026-01-15
- 互動數據：❤️ 234 💬 45 🔄 67
- 表現評估：高互動

## 原文
（貼上完整原文）
```

### DNA 的有機生長

```
初始 → 放 10 篇範例 → /extract-style → v1 DNA
用了一個月 → 加入 20 篇新貼文 → 重跑 → v2 DNA
持續 → DNA 隨你的風格演化而演化
```

---

## 8. 工具生態系統

### 現有工具

| 工具 | 角色 | 狀態 |
|------|------|------|
| Claude Code | 主力 IDE + 腳本執行 | ✅ 使用中 |
| Cursor | 程式開發 IDE | ✅ 使用中 |
| Antigravity | Agentic IDE | ✅ 使用中 |
| Dayflow | 螢幕活動追蹤 | ✅ 使用中（已整合 SQLite 讀取） |
| work-log | 工作日誌系統 | ✅ 合併進 Agent OS |
| WordPress | Blog 發布 | ✅ 使用中 |

### 未來整合（預留規劃）

| 工具 | 角色 | 整合方式 |
|------|------|----------|
| Readwise Reader | 輸入 | API → `000_Inbox/readings/` |
| Heptabase | 輸入 + 輸出 | API → `300_Learning/` + `500_Content/topics/` |
| Notion | 輸出 | API → 日記、專案追蹤、訂閱、內容日曆、人脈 |
| Obsidian | 輸入 + 輸出 | symlink → `000_Inbox/`、`600_Life/` |
| Discord | 輸入 | Bot API → `data/raw/` |

### Notion 未來分工（預留）

| 面向 | Agent OS 本地 | Notion |
|------|:------------:|:------:|
| 日記 / 反思 | ✅ | 同步 |
| 專案追蹤 | ✅ | 同步 |
| 產品 roadmap | ✅ | 同步 |
| 訂閱管理 | ✅ | 同步 |
| 內容日曆 | | ✅ |
| 人脈管理 | | ✅ (or Obsidian) |

---

## 9. Token 管理策略

### 原則：永遠載入的越少越好

| 層級 | 機制 | Token 策略 |
|------|------|-----------|
| **L1 永遠載入** | `CLAUDE.md` | < 200 tokens |
| **L1 永遠載入** | `AGENTS.md` | < 400 tokens |
| **L2 永遠載入** | `memory/MEMORY.md` | < 200 行（系統截斷） |
| **L3 按需載入** | Skills (`SKILL.md`) | 只讀 name+description，匹配時才載入全文 |
| **L4 手動載入** | Commands | 只在你打 `/xxx` 時載入 |
| **L5 需要時讀取** | `canonical/rules/` | AI 用 Read 工具讀，不自動注入 |
| **L5 需要時讀取** | `context/` | 同上 |

---

## 10. API 費用策略

### Claude Pro vs Claude API

| 產品 | 費用 | 涵蓋什麼 |
|------|------|----------|
| **Claude Pro** ($20/月) | 訂閱制 | claude.ai 網頁 + Claude Code CLI |
| **Claude API** (api.anthropic.com) | 按 token | Python 腳本直接呼叫 |

### 策略：全部走 Pro 訂閱

腳本使用 `claude --print` 而非直接呼叫 API：

```python
# scripts/lib/llm.py
import subprocess

def ask_claude(system_prompt: str, user_prompt: str) -> str:
    """透過 Claude Code CLI，走 Pro 訂閱額度"""
    result = subprocess.run(
        ["claude", "--print", "--system-prompt", system_prompt],
        input=user_prompt,
        capture_output=True, text=True
    )
    return result.stdout
```

| 場景 | 方式 | 費用 |
|------|------|------|
| 日記生成（每天 1 次） | `claude --print` | Pro 訂閱內 |
| Dayflow 摘要（每天 1 次） | `claude --print` | Pro 訂閱內 |
| 週報生成（每週 1 次） | `claude --print` | Pro 訂閱內 |
| 即時互動（IDE 內） | 正常使用 | Pro 訂閱內 |
| 批量處理（大量） | 考慮 API (Haiku) | API 費用 |

---

## 11. 實作階段 Phase 1-7

### Phase 1：骨架 + Rules + 跨平台同步 ✅ 已完成

**完成日期：** 2026-02-07

**已完成項目：**
- [x] `git init ~/dex-agent-os`
- [x] 完整目錄骨架（000-800，124 個檔案）
- [x] `canonical/rules/` 三件套（00-core, 10-writing-style, 20-safety）
- [x] `AGENTS.md`（跨平台核心人格）
- [x] `CLAUDE.md`（< 200 tokens）
- [x] `bin/sync` 腳本
- [x] 同步到 `.agent/`、`.cursor/`、`.claude/`
- [x] 36 個全域 Skills → Antigravity + Cursor
- [x] 11 個全域 Commands → Antigravity workflows
- [x] `.gitignore` + `requirements.txt` + `.env.example`
- [x] Initial commit (`48ca9bd`)

**驗證方式：**
- Claude Code: `cd ~/dex-agent-os && claude` → `/context` 確認載入
- Cursor: 開啟資料夾 → 問 AI 身份 → 輸入 `/` 看 commands
- Antigravity: 開啟資料夾 → 確認 rules 載入 → 輸入 `/` 看 workflows

---

### Phase 2：work-log 合併 + daily-journal + daily-review + Dayflow digest ✅ 已完成

**完成日期：** 2026-02-08

**已完成項目：**
- [x] 將 `~/work-logs/scripts/` 和 `templates/` 搬進 `dex-agent-os/work-log/`
- [x] 更新 `extract-sessions.py`（支援 `--date` 參數）和 `post-commit-log.sh` 的路徑
- [x] 更新 `~/.claude/commands/work-log.md`（全域指令，指向新路徑，支援指定日期）
- [x] 寫 `scripts/lib/llm.py`（`claude --print` 封裝）
- [x] 寫 `scripts/lib/config.py`（路徑與常數設定）
- [x] 寫 `scripts/lib/file_utils.py`（檔案操作工具）
- [x] 寫 `800_System/templates/journal-template.md`
- [x] 寫 `canonical/workflows/daily-journal.md`
- [x] 寫 `scripts/generators/daily_journal.py`
- [x] 寫 `canonical/workflows/daily-review.md`
- [x] 寫 `bin/agent` CLI 入口（journal、dayflow、sync 指令）
- [x] 測試：`./bin/agent journal 2026-02-05` 產出 L2 精煉日記（壓縮比 39%）
- [x] 測試：`./bin/agent journal 2026-02-07` 產出 L2 精煉日記（壓縮比 23%）
- [x] 跑 `bin/sync` 同步新 workflows
- [x] Commit (`c356c41`)

**額外完成 — Dayflow 活動摘要日記：**
- [x] 寫 `800_System/templates/dayflow-digest-template.md`
- [x] 寫 `canonical/workflows/daily-dayflow-digest.md`
- [x] 寫 `scripts/generators/daily_dayflow_digest.py`（讀 Dayflow SQLite → claude --print → 活動摘要）
- [x] 更新 `bin/agent` 加入 `dayflow` 指令
- [x] 更新 `canonical/rules/00-core.md` 加入 Dayflow 活動摘要輸出位置
- [x] 跑 `bin/sync` 同步
- [x] 測試：`./bin/agent dayflow 2026-02-07` 產出活動摘要（4,533 字元）
- [x] Commit (`6e18ee7`)

**額外完成 — 諮詢系統規劃（Phase 6 前置）：**
- [x] 寫 `800_System/templates/consultation-notes-template.md`
- [x] 更新 PLAN.md 加入諮詢系統
- [x] 更新 `canonical/rules/00-core.md` 加入諮詢紀錄輸出位置
- [x] Commit (`975bb71`)

**已驗證的產出：**

| 檔案 | 類型 | 來源 |
|------|------|------|
| `100_Journal/daily/2026-02-05.md` | L2 精煉日記 | `./bin/agent journal` |
| `100_Journal/daily/2026-02-07.md` | L2 精煉日記 | `./bin/agent journal` |
| `100_Journal/daily/2026-02-07-dayflow.md` | Dayflow 活動摘要 | `./bin/agent dayflow` |
| `~/work-logs/2026/02/2026-02-07.md` | L1 工作日誌 | `/work-log 2026-02-07` |
| `~/work-logs/2026/02/2026-02-08.md` | L1 工作日誌 | `/work-log 2026-02-08` |

**已知問題：**
- `bin/sync` 的 awk 處理 YAML frontmatter 偏脆弱（markdown 中的 `---` 可能誤判）
- `daily_dayflow_digest.py` 的 LLM 回應清理邏輯是 heuristic
- `/work-log` 指令更新後需開新 session 才生效（Claude Code 快取機制）

---

### Phase 3：topic-create + topic-to-thread + style-dna + Threads collector ✅ 已完成

**完成日期：** 2026-02-09

**詳細計畫：** 見 `implementation_plan_phase3.md`
**任務追蹤：** 見 `task_phase3.md`

**已完成項目：**
- [x] 模板：`topic-template.md`、`thread-template.md`
- [x] Workflow：`topic-create.md`、`topic-to-thread.md`、`extract-style.md`
- [x] 更新 `config.py`、`.gitignore`、`.env.example`
- [x] 實作 `scripts/collectors/threads_collector.py`（Threads API 自動抓取，直接 token 方式）
- [x] 實作 `scripts/analyzers/extract_style.py`（範例 → 風格 DNA）
- [x] 實作 `scripts/generators/topic_create.py`（insight → TOPIC.md）
- [x] 實作 `scripts/generators/topic_to_thread.py`（TOPIC.md → Threads 草稿）
- [x] 更新 `bin/agent`（collect-threads / extract-style / topic-create / topic-to-thread）
- [x] 設定 Meta App → 抓取 78 篇 Threads 範例 → 萃取 threads-dna.md
- [x] 端到端測試：`/daily-content` 產出 6 篇 Threads 草稿
- [x] 建立 `/daily-content` skill（.claude/commands/daily-content.md）
- [x] 更新 GUIDE.md + PLAN.md

**額外完成 — 每日內容管線 skill：**
- [x] `/daily-content` — 一鍵從 L1 → L2 + Dayflow → 6 篇 Threads 草稿
- [x] 支援 `--skip-worklog` 跳過 L1、指定日期參數
- [x] 兩組 Threads 來源（Dayflow+L1 視角 × 3 + L2 深度反思 × 3）

**關鍵設計決策：**
- OAuth 完全移除 — Meta 的 OAuth 不支援 localhost redirect URI，改用 Dashboard「用戶權杖產生器」直接取得 token
- Style DNA 基於 78 篇真實 Threads 萃取，涵蓋 7 個維度
- `/daily-content` 使用 `claude --print` 背景平行執行，一次產出 6 篇草稿

**已驗證的產出：**

| 檔案 | 類型 | 來源 |
|------|------|------|
| `800_System/references/examples/threads/` (78 篇) | Threads 範例 | `collect-threads` |
| `800_System/references/style-dna/threads-dna.md` | Style DNA | `extract-style` |
| `500_Content/topics/2026-02-09-threads-from-dayflow-l1/` (3 篇) | Threads 草稿 | `/daily-content` |
| `500_Content/topics/2026-02-09-threads-from-l2/` (3 篇) | Threads 草稿 | `/daily-content` |

---

### Phase 4：weekly-newsletter + weekly-review ✅

**目標：** 每週自動產出電子報選題 + 草稿

**任務：**
- [x] 寫 `800_System/templates/newsletter-template.md`
- [x] 寫 `800_System/templates/weekly-review-template.md`
- [x] 更新 `scripts/lib/config.py` 新增路徑常數
- [x] 在 `scripts/lib/file_utils.py` 新增 `week_date_range()` helper
- [x] 寫 `scripts/generators/weekly_review.py`
- [x] 寫 `scripts/generators/weekly_newsletter.py`（4 種月度輪替類型）
- [x] 寫 `canonical/workflows/weekly-review.md`
- [x] 寫 `canonical/workflows/weekly-newsletter.md`
- [x] 更新 `bin/agent` 新增 weekly-review + weekly-newsletter 子命令
- [x] 寫 `.claude/commands/weekly-content.md` 一鍵週報 skill
- [x] 跑 `bin/sync` 同步到三個 IDE
- [x] 更新 `GUIDE.md` 新增週報系統說明
- [x] 測試完整週報流程
- [x] Commit
- [ ] 你放入過去電子報範例到 `800_System/references/examples/newsletter/`（使用者手動）
- [ ] 跑 `/extract-style newsletter` 產出 `newsletter-dna.md`（需先有範例）

---

### Phase 5a：Podcast + YouTube Weekly Digest ✅ 已完成

**完成日期：** 2026-02-11

**詳細計畫：** 見 `implementation_plan_phase5a.md`
**任務追蹤：** 見 `task_phase5a.md`

**已完成項目：**
- [x] 目錄結構：`300_Learning/{podcasts/{episodes,weekly,transcripts},youtube}`、`500_Content/presentations`
- [x] 模板：podcast-episode / youtube-note / podcast-digest / podcast-pptx（4 個）
- [x] 更新 `config.py` 新增 6 個路徑常數
- [x] 更新 `.gitignore` 加入 `transcripts/`
- [x] 設定 `.mcp.json`（YouTube Transcript MCP）
- [x] 實作 `scripts/collectors/youtube_transcript.py`（youtube-transcript-api → LLM 結構化筆記）
- [x] 實作 `scripts/collectors/podcast_transcript.py`（手動文字稿 P4 + Apple TTML P3）
- [x] 實作 `scripts/generators/podcast_digest.py`（合併 YouTube + Podcast 週度消化 + --pptx）
- [x] 更新 `bin/agent`（youtube-add / podcast-add / podcast-digest 三個子命令）
- [x] Skills：`/youtube-add`、`/podcast-add`、`/podcast-weekly`（3 個）
- [x] Canonical workflow：`podcast-weekly.md`
- [x] `bin/sync` 同步完成
- [x] 更新 GUIDE.md + PLAN.md

**關鍵設計決策：**
- YouTube 線與 Podcast 線獨立，在 podcast-digest 層合併
- youtube-transcript-api v1.2 使用 `.text` 屬性（非 dict）
- Podcast 支援兩種模式：P4 手動文字稿（零依賴）+ P3 Apple TTML 快取
- 簡報產出為 markdown 結構，可用 `/pptx` skill 轉為 .pptx

**已驗證的產出：**

| 測試 | 結果 |
|------|------|
| `./bin/agent youtube-add "URL"` | ✅ 端到端通過 |
| `./bin/agent podcast-add --transcript test.txt --title "Test"` | ✅ 端到端通過 |
| `./bin/agent podcast-add --apple` | ✅ 目錄不存在時正確提示 |
| `./bin/agent podcast-digest` | ✅ 端到端通過 |
| `./bin/agent podcast-digest --pptx` | ✅ 端到端通過 |

---

### Phase 5a-ext：Podwise Notion/Readwise API 串接 ✅ 已完成

**完成日期：** 2026-02-13

**任務追蹤：** 見 `task_phase5a.md` Section G

**已完成項目：**
- [x] 更新 `config.py` 新增 3 個 env var（NOTION_TOKEN / NOTION_PODWISE_DB_ID / READWISE_TOKEN）
- [x] 在 `podcast_transcript.py` 新增 P5 Notion API（query_db + read_blocks + blocks_to_text）
- [x] 在 `podcast_transcript.py` 新增 P6 Readwise API（export highlights + book_to_text）
- [x] 擴展 argparse 加入 `--notion` / `--readwise` / `--all`
- [x] 更新 `bin/agent` help text + `.claude/commands/podcast-add.md` skill
- [x] 更新 `config/.env.example` 新增 Podwise 設定說明
- [x] 更新 GUIDE.md（Podwise 串接設定 + 疑難排解）

**關鍵設計決策：**
- 零新依賴：全部用 requests + urllib fallback
- Token 未設定時顯示清楚的 setup 引導（不 crash）
- 程式碼已就緒，等訂閱 Podwise 後設定 env vars 即可使用
- Notion API 用純 requests（不裝 notion-client），rate limit 0.35s/req
- Readwise auth 用 `Token` scheme（非 Bearer）

**驗證結果：**

| 測試 | 結果 |
|------|------|
| `python3 -c "import scripts.collectors.podcast_transcript"` | ✅ 無錯誤 |
| `./bin/agent podcast-add --notion`（無 token） | ✅ 顯示 setup 引導 |
| `./bin/agent podcast-add --readwise`（無 token） | ✅ 顯示 setup 引導 |
| argparse `--notion` / `--readwise` / `--all` | ✅ 正確解析 |

---

### Phase 5b：其餘頻道

**目標：** 補齊 FB、Blog、短影音、影評的管線

**任務：**
- [x] 各頻道 template + workflow（fb-post / blog / short-video / film-review）
- [x] Generator scripts（topic_to_fb / topic_to_blog / topic_to_short_video / film_review）
- [x] CLI 整合（bin/agent +4 commands + help）
- [x] topic-template.md checklist 更新（+ShortVideo +Podcast）
- [x] CLAUDE.md CLI 速查表更新
- [ ] Facebook：放入範例 → extract-style（等範例）
- [ ] Blog：放入範例 → extract-style（等範例）
- [ ] 影評：放入範例 → extract-style（等範例）
- [ ] wp-sync + wp-archive（WordPress 發布串接，需 WP 憑證，另案）
- [x] Commit

---

### Phase 5c：學習輸入管線 + 每日消化系統

**目標：** 建立完整的「每日學習消化系統」：多來源匯入 → 每日摘要報告 → 互動學習對話 → 結構化洞察產出

**詳細計畫：** 見 `implementation_plan_phase5c.md`
**任務追蹤：** 見 `task_phase5c.md`

**範圍拆分（5 個 Section）：**

| Section | 內容 | 預估檔案 |
|---------|------|---------|
| A | 核心基礎：Readwise API 共用模組 + config + template | 4 |
| B | learning-note：--url / --file / --readwise / --rss | 2 |
| C | 批次匯入：readwise-sync (Plan A) + rss-sync (Plan B) + MCP 設定 | 5 |
| D | 每日消化報告：daily-digest + Google Docs API + Gmail 寄送 | 4 |
| E | 互動學習對話：/daily-learning skill + CLI 整合 + 收尾 | 5 |

**任務：**
- [x] Section A：readwise_api.py 共用模組 + config + template + podcast_transcript.py 重構 ✅
- [x] Section B：learning_note.py（--url / --file / --readwise / --rss / --anybox 五種模式）✅
- [x] Section C：readwise_sync.py + rss_sync.py + anybox_sync.py + subscriptions.opml ✅
- [x] Section D：daily_digest.py + google_api.py + Google Docs/Gmail 整合 ✅
- [x] Section E：/daily-learning skill + bin/agent +5 指令 + CLAUDE.md / PLAN.md 更新 ✅
- [x] Commit + merge ✅（merged to master, walkthrough.md 已產出）

---

### Phase 6：專案/產品管理 + 會議筆記 + 諮詢紀錄 + 訂閱管理

**目標：** 工作面完善

**任務：**
- [ ] `800_System/templates/meeting-notes-template.md`
- [ ] `canonical/workflows/meeting-notes.md`
- [x] `800_System/templates/consultation-notes-template.md`（✅ Phase 2 中已完成，含方向、核心問題、建議、內容萃取欄位）
- [ ] `canonical/workflows/consultation-notes.md`（諮詢結束 → 摘要 + 行動項 + 內容萃取建議）
- [ ] `800_System/templates/project-status-template.md`
- [ ] `canonical/workflows/project-status.md` + `project-kickoff.md`
- [ ] `canonical/workflows/product-feature-spec.md` + `product-roadmap-update.md`
- [ ] `200_Work/subscriptions/overview.md` 初始版
- [ ] `canonical/workflows/subscription-review.md`
- [ ] Commit

---

### Phase 7：職涯 + launchd 排程自動化

**目標：** 全自動，每天起床看到日記草稿

**任務：**
- [ ] `canonical/workflows/career-reflection.md`
- [ ] `canonical/workflows/opportunity-evaluate.md`
- [ ] `config/schedules/com.dex.daily-collect.plist`（每天 23:50）
- [ ] `config/schedules/com.dex.daily-journal.plist`（每天 00:05）
- [ ] `config/schedules/com.dex.weekly-digest.plist`（每週日 21:00）
- [ ] `bin/setup` 一鍵安裝排程
- [ ] 測試排程連續運作 3 天
- [ ] Commit

---

### Phase 8：成本最佳化 + 外部載體整合

**目標：** 付費最小化 + 串接 Obsidian / NotebookLM 作為輸出載體

**8a — 付費最小化規劃：**
- 盤點所有付費服務（Podwise、Readwise、Notion 等），找免費替代方案
- 目標：能用免費就用免費，以省最多為目標
- 例：Podwise → 直接用 Whisper/Deepgram 本地轉錄 + LLM 摘要？
- 例：Readwise → 直接抓來源（RSS + 瀏覽器 extension export）？
- 產出：成本對照表 + 遷移計畫

**8b — Obsidian + NotebookLM 輸出載體：**
- Obsidian：dex-agent-os 的 markdown 輸出同步到 Obsidian vault，利用 graph view / backlinks
- NotebookLM：學習筆記 / digest 推送到 NotebookLM，利用 AI 問答 + Audio Overview
- 設計雙向或單向同步機制

---

## 12. 關鍵決策紀錄

| 日期 | 決策 | 原因 |
|------|------|------|
| 2026-02-07 | Repo 位置：`~/dex-agent-os/` | 獨立於其他專案 |
| 2026-02-07 | Private repo | 包含私人內容（會議、職涯、訂閱費用） |
| 2026-02-07 | 不用 n8n，全本地方案 | 避免雲端同步痛點，直接讀寫本地檔案 |
| 2026-02-07 | 用 `claude --print` 不用 API | 走 Pro 訂閱，不額外花錢 |
| 2026-02-07 | `canonical/` 為唯一真實來源 | 避免三個平台各自維護導致不一致 |
| 2026-02-07 | CLAUDE.md 專案級，不碰 ~/CLAUDE.md | 零風險，不影響其他專案 |
| 2026-02-07 | work-log 合併但全域可用 | `/work-log` 留在 `~/.claude/commands/` |
| 2026-02-07 | Obsidian/Notion/Readwise/Heptabase 預留 | 先建 Agent OS 骨架，未來再整合 |
| 2026-02-07 | 全部 36 個 skills 同步 | 跨平台一致體驗 |
| 2026-02-07 | 風格 DNA 系統 | 讓 AI 產出越來越像你的風格 |
| 2026-02-07 | 諮詢紀錄與會議同級 | 給予/接受諮詢都有獨特的內容萃取價值 |
| 2026-02-08 | Dayflow 活動摘要獨立於 L2 精煉日記 | journal_entries 為空，timeline_cards + observations 有豐富資料，兩種日記視角互補 |
| 2026-02-08 | /work-log 支援指定日期 | 允許回溯產出過去的工作日誌 |
| 2026-02-08 | LLM 回應清理邏輯（去除思考殘留） | claude --print 偶爾輸出思考過程，需在腳本中過濾 |
| 2026-02-09 | Threads collector 用直接 token 取代 OAuth | Meta OAuth 不支援 localhost redirect URI，Dashboard「用戶權杖產生器」30 秒搞定 |
| 2026-02-09 | Style DNA 基於 78 篇真實範例 | 50 篇以下 DNA 精準度不足，78 篇能涵蓋足夠的風格變異 |
| 2026-02-09 | `/daily-content` 用 claude --print 平行產出 | 兩組 × 3 篇用背景任務平行，總時間約 2-3 分鐘 |
| 2026-02-09 | Threads 草稿分兩組視角（Dayflow+L1 vs L2） | 同一天素材不同切面，避免主題雷同 |
| 2026-02-11 | YouTube 線與 Podcast 線獨立設計，digest 層合併 | 兩種來源獲取邏輯差異大，但週度彙整需要跨來源歸納趨勢 |
| 2026-02-11 | Podcast 先做 P4（手動）+ P3（Apple TTML），不做 Whisper/Deepgram | 零依賴方案先跑通，進階模式按需擴展 |
| 2026-02-11 | 簡報產出為 markdown 結構而非直接 .pptx | 可用已有的 `/pptx` skill 轉換，保持管線解耦 |
| 2026-02-13 | Podwise 串接先寫好程式碼，等訂閱後設定 env vars | 架構先行，避免未來重新設計 |
| 2026-02-13 | Notion API 用純 requests 不裝 notion-client | 零新依賴，requests 已是現有依賴 |
