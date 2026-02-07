# Dex Agent OS — 完整專案規劃

> 個人 AI 代理人作業系統
> 涵蓋：生產力、學習、輸入輸出、工作管理、專案、產品、寫作
> 最後更新：2026-02-07

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
      daily-journal.md                #   讀 work-log → 精煉日記
      daily-review.md                 #   今日回顧：做了什麼、學了什麼、卡在哪
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
    commands/                         #   含同步的 36 個全域 skills
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
    daily/                            # 每日精煉日記
      YYYY-MM-DD.md
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
      journal-template.md
      meeting-notes-template.md
      consultation-notes-template.md  #   諮詢紀錄模板
      project-status-template.md
      product-feature-template.md
      topic-template.md
      thread-template.md
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
      discord_collector.py
      notion_collector.py             #   (future)
    generators/                       # 內容生成
      daily_journal.py
      weekly_newsletter.py
      weekly_learning.py
    publishers/                       # 發布
      wp_draft.py
      wp_archive.py
    analyzers/                        # 分析
      extract_style.py
    lib/                              # 共用模組
      llm.py                          #   claude --print 封裝
      config.py
      file_utils.py

  bin/
    agent                             # CLI 入口
    sync                              # 跨平台同步腳本
    setup                             # 一鍵安裝（launchd、依賴）

  config/
    schedules/                        # launchd plist 排程
      com.dex.daily-collect.plist
      com.dex.daily-journal.plist
      com.dex.weekly-digest.plist
    .env.example                      # 環境變數範本

  work-log/                           # 從 ~/work-logs/ 合併進來
    scripts/
      extract-sessions.py
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
    ~/.claude/skills/ (36個) ──→ ~/.gemini/antigravity/skills/
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
- 檔案寫入位置規則
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
| Dayflow | 螢幕活動追蹤 | ✅ 使用中 |
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

### Phase 2：work-log 合併 + daily-journal + daily-review

**目標：** 每天能產出精煉日記

**任務：**
- [ ] 將 `~/work-logs/scripts/` 和 `templates/` 搬進 `dex-agent-os/work-log/`
- [ ] 更新 `extract-sessions.py` 和 `post-commit-log.sh` 的路徑
- [ ] 更新 `~/.claude/commands/work-log.md`（全域指令，指向新路徑）
- [ ] 寫 `scripts/lib/llm.py`（`claude --print` 封裝）
- [ ] 寫 `800_System/templates/journal-template.md`
- [ ] 寫 `canonical/workflows/daily-journal.md`
- [ ] 寫 `scripts/generators/daily_journal.py`
- [ ] 寫 `canonical/workflows/daily-review.md`
- [ ] 測試：`./bin/agent journal` 能產出 `100_Journal/daily/YYYY-MM-DD.md`
- [ ] 跑 `bin/sync` 同步新 workflows
- [ ] Commit

---

### Phase 3：topic-create + topic-to-thread + style-dna 提取

**目標：** 一個主題能快速產出 Threads 草稿，風格像你寫的

**任務：**
- [ ] 寫 `800_System/templates/topic-template.md`
- [ ] 寫 `800_System/templates/thread-template.md`
- [ ] 寫 `canonical/workflows/topic-create.md`
- [ ] 寫 `canonical/workflows/topic-to-thread.md`
- [ ] 寫 `canonical/workflows/extract-style.md`
- [ ] 寫 `scripts/analyzers/extract_style.py`
- [ ] 你放入 10+ 篇 Threads 過去範例到 `800_System/references/examples/threads/`
- [ ] 跑 `/extract-style threads` 產出 `threads-dna.md`
- [ ] 測試：`/topic-create` → `/topic-to-thread` 完整流程
- [ ] Commit

---

### Phase 4：weekly-newsletter + weekly-review

**目標：** 每週自動產出電子報選題 + 草稿

**任務：**
- [ ] 寫 `800_System/templates/newsletter-template.md`
- [ ] 寫 `canonical/workflows/weekly-newsletter.md`
- [ ] 寫 `canonical/workflows/weekly-review.md`
- [ ] 寫 `scripts/generators/weekly_newsletter.py`
- [ ] 你放入過去電子報範例到 `800_System/references/examples/newsletter/`
- [ ] 跑 `/extract-style newsletter` 產出 `newsletter-dna.md`
- [ ] 測試完整週報流程
- [ ] Commit

---

### Phase 5：其餘頻道

**目標：** 補齊 FB、Blog、Podcast、短影音、影評的管線

**任務：**
- [ ] 各頻道 template + workflow + style-dna
- [ ] Facebook：放入範例 → extract-style → topic-to-fb
- [ ] Blog/WordPress：放入範例 → extract-style → topic-to-blog + wp-sync + wp-archive
- [ ] Podcast：參考其他 podcast 範例 → template + workflow
- [ ] 短影音：template + workflow（無範例，先建結構）
- [ ] 影評：放入過去範例 → extract-style → film-review workflow
- [ ] Commit

---

### Phase 6：專案/產品管理 + 會議筆記 + 諮詢紀錄 + 訂閱管理

**目標：** 工作面完善

**任務：**
- [ ] `800_System/templates/meeting-notes-template.md`
- [ ] `canonical/workflows/meeting-notes.md`
- [ ] `800_System/templates/consultation-notes-template.md`（含方向、核心問題、建議、內容萃取欄位）
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
