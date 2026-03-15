# Dex Agent OS

> 個人 AI 代理人作業系統 — 知識管理、內容生產、工作流自動化

Dex Agent OS 是一套以 CLI + AI 驅動的個人生產力系統，將每天的數位足跡（工作紀錄、學習筆記、閱讀摘要）透過 AI 加工，自動產出日記、洞察、多頻道內容草稿。

## 系統架構

```
┌──────────────────────────────────────────┐
│              Dex Agent OS                │
│                                          │
│  工作        學習        創作 & 發布      │
│  ├ 會議      ├ 閱讀      ├ Threads       │
│  ├ 諮詢      ├ 課程      ├ Facebook      │
│  ├ 程式開發  ├ Podcast   ├ Blog          │
│  ├ 專案管理  ├ YouTube   ├ 電子報        │
│  └ 訂閱管理  └ RSS/書籤  ├ 短影音        │
│                          └ 影評          │
│  個人                                    │
│  ├ 每日反思 & 週回顧                      │
│  └ 知識萃取 & 記憶管理                    │
└──────────────────────────────────────────┘
```

### 資料流

```
輸入源（Git / Dayflow / RSS / Readwise / 會議逐字稿 / ...）
  │
  ▼
收集器（collectors） → 000_Inbox/ + 300_Learning/
  │
  ▼
產生器（generators） → 100_Journal/（日記）→ 510_Insights/（洞察）
  │
  ▼
主題企劃（520_Topics/）→ 多頻道草稿（530_Channels/threads/facebook/blog/...）
  │
  ▼
人工審稿 → 發布 → 700_Archive/
```

## 目錄結構

| 目錄 | 用途 |
|------|------|
| `000_Inbox/` | 靈感、閱讀素材、待辦 |
| `100_Journal/` | 每日 / 每週日記、消化報告 |
| `200_Work/` | 會議紀錄、諮詢紀錄 |
| `300_Learning/` | 學習筆記（Podcast、YouTube、文章） |
| `400_Projects/` | 專案與產品狀態追蹤 |
| `510_Insights/` | 洞察卡片（seed ideas） |
| `520_Topics/` | 主題企劃（TOPIC.md） |
| `530_Channels/` | 各頻道草稿 |
| `600_Life/` | 職涯、影評、個人反思 |
| `700_Archive/` | 已發布存檔 |
| `800_System/` | 模板、範例、風格 DNA |

## 快速開始

### 環境需求

| 需求 | 說明 |
|------|------|
| Python 3.9+ | 腳本執行 |
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | LLM 呼叫（`claude --print`） |
| Claude Pro 訂閱 | 所有 LLM 呼叫走 Pro 額度，不花 API 費用 |
| Git | 版本控制、工作日誌 |

### 安裝（macOS / Linux）

```bash
# 1. Clone
git clone https://github.com/lu791019/dex-agent-os.git
cd dex-agent-os

# 2. 安裝 Python 依賴
pip install -r requirements.txt

# 3. 設定環境變數
cp config/.env.example .env
# 編輯 .env 填入你的 API tokens（見下方說明）

# 4. 查看可用指令
./bin/agent help
```

### 安裝（Windows）

```powershell
# 1. Clone
git clone https://github.com/lu791019/dex-agent-os.git
cd dex-agent-os

# 2. 安裝 Python 依賴
pip install -r requirements.txt

# 3. 設定環境變數
copy config\.env.example .env
# 用記事本或 VS Code 編輯 .env 填入你的 API tokens（見下方說明）

# 4. 查看可用指令
python bin\agent.py help
# 或
bin\agent.bat help

# 5. 驗證跨平台功能
python -m pytest tests\ -v
```

> **Windows 注意事項：**
> - 使用 `python bin\agent.py <command>` 或 `bin\agent.bat <command>` 執行指令
> - Dayflow、Apple Podcast 為 macOS 專屬功能，Windows 上會自動跳過
> - Google OAuth 流程（Gmail、Classroom）在 Windows 上相同，需要瀏覽器授權

### .env 環境變數設定

從 `config/.env.example` 複製為 `.env` 後，依需求填入以下 token：

| 變數 | 必要性 | 用途 | 取得方式 |
|------|--------|------|----------|
| `THREADS_ACCESS_TOKEN` | 選用 | Threads 內容收集 + 風格分析 | [Meta Developer Dashboard](https://developers.facebook.com) → 建立 App → Threads API → 用戶權杖產生器 |
| `READWISE_TOKEN` | 選用 | 閱讀摘要 + Reader 文章批次匯入 | [readwise.io/access_token](https://readwise.io/access_token) |
| `ANYBOX_API_KEY` | 選用 | Anybox 書籤匯入（macOS） | Anybox app 設定 → API |
| `NOTION_TOKEN` | 選用 | Podwise Podcast 匯入 | [notion.so/my-integrations](https://www.notion.so/my-integrations) → 建立 Integration |
| `NOTION_PODWISE_DB_ID` | 選用 | Podwise 資料庫 ID | Notion database URL 中的 32 碼 ID |
| `FIREFLIES_API_KEY` | 選用 | 會議逐字稿同步 | [Fireflies Dashboard](https://app.fireflies.ai/integrations/custom/fireflies)（需 Business plan） |
| `DIGEST_EMAIL` | 選用 | 每日消化報告寄送 | 你的 Gmail 地址 |

**Google OAuth（Gmail / Classroom / Google Docs）：** 需要另外設定 `config/google-credentials.json`，詳見 [GUIDE.md](GUIDE.md) 第 13 節疑難排解。

> **提醒：** `.env` 已在 `.gitignore` 中，不會被推到 GitHub。所有 token 都是選用的，沒有設定的功能會自動跳過或顯示提示。

## CLI 指令速查

### 每日記錄

```bash
./bin/agent journal [YYYY-MM-DD]          # L1 工作日誌 → L2 精煉日記
./bin/agent dayflow [YYYY-MM-DD]          # Dayflow 螢幕活動 → 行為分析摘要
./bin/agent extract [date|all]            # 日記 → 知識萃取（學習/反思/洞察）
```

### 學習輸入

```bash
./bin/agent readwise-sync --reader --latest 5   # Readwise Reader 批次匯入
./bin/agent rss-sync --latest 5                  # RSS 批次匯入
./bin/agent anybox-sync --starred --latest 5     # Anybox 書籤匯入
./bin/agent gmail-sync --latest 5                # Gmail 電子報匯入
./bin/agent sync-all                             # 一鍵匯入所有來源
./bin/agent youtube-add "URL"                    # YouTube → 學習筆記
./bin/agent podcast-add --transcript FILE --title "..."  # Podcast → episode 筆記
./bin/agent daily-digest [--today]               # 每日學習消化報告
```

### 內容生產

```bash
./bin/agent topic-create <insight-file>           # 洞察 → 主題企劃
./bin/agent topic-to-thread <topic-slug>          # 主題 → Threads 草稿
./bin/agent topic-to-fb <topic-slug>              # 主題 → Facebook 草稿
./bin/agent topic-to-blog <topic-slug>            # 主題 → 部落格草稿
./bin/agent topic-to-short-video <topic-slug>     # 主題 → 短影音腳本
./bin/agent film-review --title "..." --rating N  # 影評
```

### 工作管理

```bash
./bin/agent meeting-notes --title "..." --transcript FILE    # 會議筆記
./bin/agent consultation-notes --title "..." --person "..."  # 諮詢紀錄
./bin/agent project-status [專案名]                           # 專案狀態更新
./bin/agent classroom-sync --courses                         # Google Classroom 同步
./bin/agent fireflies-sync --list                            # Fireflies 逐字稿列表
```

### 週報

```bash
./bin/agent weekly-review [YYYY-MM-DD]       # 個人週回顧
./bin/agent weekly-newsletter [--type TYPE]  # 電子報草稿
./bin/agent podcast-digest [--pptx]          # 週度 Podcast 消化報告
```

## 跨平台同步

修改 `canonical/` 的規則和 workflow 後，執行同步：

```bash
./bin/sync
```

會自動將內容同步到三個 AI 編輯器：

| 平台 | 目標目錄 |
|------|----------|
| Claude Code | `.claude/commands/` + `.claude/skills/` |
| Cursor | `.cursor/rules/` + `.cursor/commands/` |
| Antigravity | `.agent/rules/` + `.agent/workflows/` + `.agent/skills/` |

## 技術棧

- **語言：** Python 3 + Bash
- **LLM：** Claude Code CLI（`claude --print`）
- **外部 API：** Readwise、Threads (Meta)、Google (Gmail/Classroom/Docs)、Fireflies.ai、Notion、Anybox
- **資料格式：** Markdown（所有輸出皆為 `.md`）
- **無資料庫：** 純檔案系統，Git 版控

## 文件

| 文件 | 說明 |
|------|------|
| [GUIDE.md](GUIDE.md) | 完整操作手冊（指令用法、流程、疑難排解） |
| [PLAN.md](PLAN.md) | 專案架構、Phase 規劃、決策紀錄 |
| [AGENTS.md](AGENTS.md) | AI 代理人人格設定 |

## License

MIT
