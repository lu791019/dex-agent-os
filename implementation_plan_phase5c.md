# Phase 5c：學習輸入管線 + 每日消化系統 — Implementation Plan

## Goal Description

建立完整的「每日學習消化系統」：多來源匯入 → 每日摘要報告 → 互動學習對話 → 結構化洞察產出。

Phase 5a 已建立 YouTube + Podcast 學習輸入管線，Phase 5c 在此基礎上擴展為完整的學習消化循環。

## 完整流程

```
┌─ 來源匯入（持續 / 批次）─────────────────────────────────────┐
│  RSS / Substack  ──→  Plan A: Readwise Reader Feed            │
│  Gmail newsletter──→  Plan A: auto-forward to Reader          │
│  Anybox 書籤     ──→  Plan A: 瀏覽器 extension                │
│                                                               │
│  RSS / Substack  ──→  Plan B: rss-reader-mcp + feedparser     │
│  Gmail newsletter──→  Plan B: workspace-mcp (Gmail read-only) │
│  Anybox 書籤     ──→  Plan B: anybox MCP                      │
│                                                               │
│  URL / 本地檔案  ──→  trafilatura / 讀檔                      │
│  YouTube         ──→  現有 youtube-add                        │
│  Podcast         ──→  現有 podcast-add                        │
│  課程            ──→  learning-note --file                    │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─ 每日消化報告（daily-digest）──────────────────────────────────┐
│  掃描今日所有新內容（依 created/modified date）：               │
│    000_Inbox/readings/  300_Learning/input/                    │
│    300_Learning/youtube/  300_Learning/podcasts/episodes/      │
│  → LLM 產出詳細摘要（含連結）                                  │
│  → 建立 Google Doc（完整版）                                   │
│  → 寄 Gmail（Markdown 摘要 + Google Doc 連結）                 │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─ 互動學習對話（/daily-learning skill）─────────────────────────┐
│  1. Claude 讀取當日 digest                                    │
│  2. 對每篇內容深入提問（蘇格拉底式 / 考試式 / 深聊式）        │
│     「這篇提到 X，你覺得跟你做的 Y 有什麼關聯？」              │
│     「這三個趨勢，哪個最可能影響你的工作？為什麼？」            │
│  3. 引導使用者歸納：想法 / 心得 / 見解 / 洞察                  │
│  4. 自動產出結構化筆記 → 500_Content/insights/ + learnings     │
└───────────────────────────────────────────────────────────────┘
```

## User Review Required

> **NOTE — 需確認的決策**
>
> 1. **Readwise API 重構**：從 `podcast_transcript.py` 抽取共用模組到 `scripts/lib/readwise_api.py`，原有行為不變
> 2. **Google API（Section D）**：daily-digest 的 `--send` 需要 Google Docs + Gmail API，首次設定需 GCP Console 建專案 + 啟用 Docs/Gmail API + 建立 OAuth 桌面憑證（~30 分鐘）。之後 refresh token 自動更新。如不需要寄信功能，Section D 可先只做本地摘要
> 3. **依賴安裝**：
>    - Section A-C：`pip install trafilatura feedparser`
>    - Section D：`pip install google-auth google-auth-oauthlib google-api-python-client markdown`
> 4. **MCP 設定（Section C4）**：readwise-mcp、rss-reader-mcp、gmail-mcp、anybox-mcp 設定寫入 `.claude/settings.local.json`，視實際需求啟用
> 5. **Anybox MCP**：非 PyPI 套件，需手動 clone + 設定 Python 路徑，且需 Anybox app 運行中，建議列為 optional

## Proposed Changes

### 範圍拆分（5 個 Section）

| Section | 內容 | 預估檔案 |
|---------|------|---------|
| A | 核心基礎：template + config + 共用模組 | 4 |
| B | learning-note：--url / --file / --readwise / --rss / --anybox | 2 |
| C | 批次匯入：readwise-sync + rss-sync + anybox-sync + MCP 設定 | 7 |
| D | 每日消化報告：daily-digest script + Google Docs API + Gmail 寄送 | 4 |
| E | 互動學習對話：/daily-learning skill + CLI 整合 + 收尾 | 5 |

### Components

#### Section A：核心基礎

**A1. 共用 Readwise API 模組**

從 `scripts/collectors/podcast_transcript.py`（L75-140, L445-601）抽取：

- `[NEW] scripts/lib/readwise_api.py`
  ```python
  check_readwise_setup()      # token 檢查
  readwise_headers()          # auth headers
  api_request()               # 統一 API 請求（retry + rate limit + urllib fallback）
  readwise_export(category)   # 通用匯出（接受 category 參數: podcasts/articles/books）
  book_to_text(book)          # highlights → text
  slugify(text)               # 標題 → slug
  ```

- `[MODIFY] scripts/collectors/podcast_transcript.py`
  重構為 `from lib.readwise_api import ...`，移除重複程式碼，行為不變

**A2. Config 新增**

- `[MODIFY] scripts/lib/config.py` +3 常數：
  ```python
  LEARNING_INPUT_DIR = ROOT_DIR / "300_Learning" / "input"
  READINGS_DIR = ROOT_DIR / "000_Inbox" / "readings"
  DIGEST_DIR = ROOT_DIR / "100_Journal" / "digest"
  ```

**A3. Template**

- `[NEW] 800_System/templates/learning-note-template.md`
  ```markdown
  ---
  title: {{TITLE}}
  source: {{SOURCE}}
  type: {{TYPE}}
  date: {{DATE}}
  tags: []
  ---
  # {{TITLE}}
  ## 一句話摘要
  ## 核心觀點
  ## 關鍵引述
  ## 實作筆記
  ## 我的想法
  <!-- 手動補充 -->
  ## 可轉化為內容
  ```

**A4. 依賴**

`pip install trafilatura feedparser`

**驗證 A**

`./bin/agent podcast-add --readwise` — 確認重構沒壞

---

#### Section B：learning-note Script

- `[NEW] scripts/generators/learning_note.py`
  ```
  ./bin/agent learning-note --url "URL" [--type TYPE] [--force]
  ./bin/agent learning-note --file PATH --title "..." [--type TYPE] [--force]
  ./bin/agent learning-note --readwise [--latest N] [--all] [--type TYPE] [--force]
  ./bin/agent learning-note --rss "FEED_URL" [--latest N] [--type TYPE] [--force]
  ./bin/agent learning-note --anybox [--tag TAG] [--starred] [--latest N] [--type TYPE] [--force]
  ```

  | 模式 | 來源 | 工具 |
  |------|------|------|
  | `--url` | 網頁文章 | trafilatura 擷取（含 fallback 鏈）→ LLM 消化 |
  | `--file` | 本地檔案 | 讀檔 → LLM 消化 |
  | `--readwise` | Readwise highlights | Export API v2 (category=articles/books) → LLM 消化 |
  | `--rss` | RSS feed | feedparser → trafilatura 全文 → LLM 消化 |
  | `--anybox` | Anybox 書籤 | Anybox 本地 API → URL → web_extract 全文 → LLM 消化 |

  - `--type`：articles（預設）/ books / courses / tech
  - 輸出：`300_Learning/input/<type>/YYYY-MM-DD-<slug>.md`

  **`--url` 模式 fallback 鏈：**
  1. trafilatura fetch + extract（主要）
  2. requests fetch + trafilatura extract（trafilatura fetcher 失敗時）
  3. requests fetch + BeautifulSoup 基本擷取（找 `<article>`/`<main>` 區塊）
  4. 顯示提示：建議用 firecrawl 抓取後以 `--file` 模式處理

- `[NEW] canonical/workflows/learning-note.md`

**驗證 B**
```
./bin/agent learning-note --file README.md --title "Test" --type tech --force
./bin/agent learning-note --url "https://simonwillison.net/" --force
```

---

#### Section C：批次匯入 + MCP 設定

**C1. readwise-sync（Plan A）**

- `[NEW] scripts/collectors/readwise_sync.py`
  ```
  ./bin/agent readwise-sync [--category articles|books|all] [--latest N] [--all] [--since DATE] [--force]
  ```
  - 輸出：`000_Inbox/readings/YYYY-MM-DD-<slug>.md`
  - 無 LLM，直接結構化 highlights 為 Markdown
  - 預設 7 天內更新

**C2. rss-sync（Plan B）**

- `[NEW] scripts/collectors/rss_sync.py`
  ```
  ./bin/agent rss-sync [--opml FILE] [--feed URL] [--latest N] [--force]
  ```
  - 輸入：`config/subscriptions.opml` 或單一 feed URL
  - 用 feedparser 取 RSS 條目
  - 用 trafilatura 取全文（RSS 僅有摘要時）
  - 輸出：`000_Inbox/readings/YYYY-MM-DD-<slug>.md`
  - 無 LLM，直接存原文 + metadata

- `[NEW] config/subscriptions.opml`（初始 RSS 訂閱清單）

**C3. anybox-sync（API 路線）**

- `[NEW] scripts/collectors/anybox_sync.py`
  ```
  ./bin/agent anybox-sync [--tag TAG] [--folder FOLDER] [--starred] [--latest N] [--force]
  ```
  - 直接呼叫 Anybox 本地 HTTP API（`http://127.0.0.1:6391`，需 API key）
  - 搜尋書籤 → 取得 URL 列表 → `web_extract.py` 取全文 → 存 Markdown
  - 輸出：`000_Inbox/readings/YYYY-MM-DD-<slug>.md`
  - 無 LLM，直接存原文 + metadata（與 rss-sync 同設計）
  - 冪等性：skip if exists + --force
  - Anybox app 未運行時優雅 fallback（提示啟動 app）
  - 環境變數：`ANYBOX_API_KEY`（從 Anybox Preferences → General 取得）

**C4. MCP 設定（含 Anybox MCP 路線）**

- `[MODIFY] .claude/settings.local.json`
  ```json
  {
    "mcpServers": {
      "readwise": { "command": "npx", "args": ["-y", "@readwise/readwise-mcp"], "env": { "ACCESS_TOKEN": "..." } },
      "rss-reader": { "command": "npx", "args": ["-y", "rss-reader-mcp"] },
      "gmail": { "command": "uvx", "args": ["workspace-mcp", "--read-only", "--tools", "gmail", "--tool-tier", "core"], "env": { "GOOGLE_OAUTH_CLIENT_ID": "...", "GOOGLE_OAUTH_CLIENT_SECRET": "..." } },
      "anybox": { "command": "python3", "args": ["path/to/anybox_mcp_server.py"], "env": { "ANYBOX_API_KEY": "..." } }
    }
  }
  ```

- `[NEW] canonical/workflows/readwise-sync.md`（含 MCP 用法說明：用 readwise MCP 互動式操作）
- `[NEW] canonical/workflows/rss-sync.md`（含 MCP 用法說明：用 rss-reader MCP 互動式操作）
- `[NEW] canonical/workflows/anybox-sync.md`（含 MCP 用法說明：用 anybox MCP 互動式操作）

**驗證 C**
```
./bin/agent readwise-sync --latest 3 --force
./bin/agent rss-sync --feed "https://jvns.ca/atom.xml" --latest 3 --force
./bin/agent anybox-sync --starred --latest 3 --force
./bin/agent learning-note --readwise --latest 1 --force
./bin/agent learning-note --rss "https://jvns.ca/atom.xml" --latest 1 --force
./bin/agent learning-note --anybox --starred --latest 1 --force
```

---

#### Section D：每日消化報告（daily-digest）

- `[NEW] scripts/generators/daily_digest.py`
  ```
  ./bin/agent daily-digest [YYYY-MM-DD] [--send] [--force]
  ```

  **流程：**
  1. 掃描指定日期的所有新內容（依檔名日期前綴，建議 D 天掃描 D-1 天）：
     - `000_Inbox/readings/YYYY-MM-DD-*.md`（Readwise sync / RSS sync）
     - `300_Learning/input/**/YYYY-MM-DD-*.md`（learning-note 產出）
     - `300_Learning/youtube/YYYY-MM-DD-*.md`（youtube-add 產出）
     - `300_Learning/podcasts/episodes/YYYY-MM-DD-*.md`（podcast-add 產出）
     > 注意：readwise-sync / rss-sync 檔名使用 sync 日（進入系統的日期），frontmatter 記錄原始日期
  2. LLM 產出每日摘要：
     - 每篇內容：標題 + 來源連結 + 5-8 句摘要 + 關鍵 takeaway
     - 分類排列（文章 / Podcast / YouTube / 課程）
     - 結尾統整：今日主題趨勢
  3. 本地存檔：`100_Journal/digest/YYYY-MM-DD-digest.md`
  4. `--send` 時：
     - 建立 Google Doc（Google Docs API）
     - 寄 Gmail（Markdown 摘要信 + Google Doc 連結）

**Google Workspace API 整合**

共用 OAuth 認證（workspace-mcp 的 Client ID/Secret）：
- Google Docs API：`documents.create` + `documents.batchUpdate`（插入內容）
- Gmail API：`messages.send`（寄送摘要信）

- `[NEW] scripts/lib/google_api.py`
  ```python
  authenticate()                      # OAuth2 認證（首次開瀏覽器，之後用 refresh token）
  create_google_doc(title, content)   # 建立 Google Doc，回傳 URL
  send_gmail(to, subject, body_md, doc_url)  # 寄送摘要信（Markdown → HTML）
  ```

  依賴：`pip install google-auth google-auth-oauthlib google-api-python-client markdown`

- `[NEW] 800_System/templates/daily-digest-template.md`
- `[NEW] canonical/workflows/daily-digest.md`

**驗證 D**
```
./bin/agent daily-digest                # 產出本地摘要
./bin/agent daily-digest --send         # 產出 + 建立 Google Doc + 寄信
```

---

#### Section E：互動學習對話 + CLI 收尾

**E1. /daily-learning Skill**

- `[NEW] canonical/workflows/daily-learning.md`

  Skill 啟動時的流程：
  1. 載入當日 digest：讀 `100_Journal/digest/YYYY-MM-DD-digest.md`
  2. 逐篇深入提問（三種模式隨機/交替）：
     - 蘇格拉底式：「這篇提到 X，你覺得這跟你之前的經驗有什麼關聯？」
     - 考試式：「這篇文章的核心論點是什麼？你同意嗎？為什麼？」
     - 深聊式：「如果你要向一個朋友解釋這篇的重點，你會怎麼說？」
  3. 收斂歸納：引導使用者整理出：
     - 想法（thoughts）
     - 心得（takeaways）
     - 見解（insights）
     - 洞察（observations）
  4. 自動產出：
     - 結構化筆記 → `100_Journal/daily/YYYY-MM-DD.md`（融入每日日記）
     - 高品質 insights → `500_Content/insights/`（可轉為內容）
     - 學習收穫 → 觸發 extract（learnings/reflections）

**E2. CLI 整合**

- `[MODIFY] bin/agent`（+5 commands + help）：
  ```
  learning-note --url/--file/--readwise/--rss/--anybox  文章 → 學習筆記
  readwise-sync [--category] [--latest N]              Readwise highlights 批次匯入
  rss-sync [--opml FILE] [--feed URL]                  RSS 批次匯入
  anybox-sync [--tag TAG] [--starred] [--latest N]     Anybox 書籤批次匯入
  daily-digest [--send]                                每日消化報告
  ```

- `[MODIFY] CLAUDE.md` — CLI 速查表 +4 指令
- `[MODIFY] PLAN.md` — Phase 5c 狀態
- `bin/sync` 同步 workflows

**驗證 E**
```
./bin/agent help                              # 確認所有新指令
./bin/agent sync                              # 同步正常
# 啟動 /daily-learning skill 做一次互動對話測試
```

---

## 修改檔案清單（共 ~23 個）

| 類型 | 檔案 | Section |
|------|------|---------|
| Lib | `scripts/lib/readwise_api.py` | A — NEW |
| Lib | `scripts/lib/web_extract.py` | B — NEW |
| Lib | `scripts/lib/google_api.py` | D — NEW |
| Lib | `scripts/lib/config.py` | A — MODIFY |
| Refactor | `scripts/collectors/podcast_transcript.py` | A — MODIFY |
| Template | `800_System/templates/learning-note-template.md` | A — NEW |
| Template | `800_System/templates/daily-digest-template.md` | D — NEW |
| Script | `scripts/generators/learning_note.py` | B — NEW |
| Script | `scripts/collectors/readwise_sync.py` | C — NEW |
| Script | `scripts/collectors/rss_sync.py` | C — NEW |
| Script | `scripts/generators/daily_digest.py` | D — NEW |
| Script | `scripts/collectors/anybox_sync.py` | C — NEW |
| Config | `config/subscriptions.opml` | C — NEW |
| Workflow | `canonical/workflows/learning-note.md` | B — NEW |
| Workflow | `canonical/workflows/readwise-sync.md` | C — NEW |
| Workflow | `canonical/workflows/rss-sync.md` | C — NEW |
| Workflow | `canonical/workflows/anybox-sync.md` | C — NEW |
| Workflow | `canonical/workflows/daily-digest.md` | D — NEW |
| Workflow | `canonical/workflows/daily-learning.md` | E — NEW |
| MCP | `.claude/settings.local.json` | C — MODIFY |
| CLI | `bin/agent` | E — MODIFY |
| CLAUDE.md | `CLAUDE.md` | E — MODIFY |
| PLAN.md | `PLAN.md` | E — MODIFY |

## 依賴清單

```
pip install trafilatura feedparser google-auth google-auth-oauthlib google-api-python-client markdown
```

## 設計決策（討論結論）

| # | 決策 | 結論 |
|---|------|------|
| 1 | learning-note --readwise / --rss 保留或砍掉 | **保留**，作為未來可用的獨立工具，雖然主要深度消化由 /daily-learning 負責 |
| 2 | Google API 策略 | **Option B**：`--send` 優雅 fallback，未設定時顯示引導、不 crash |
| 3 | 整體架構 | **消化漏斗**：sync 收集 → digest 彙整 → /daily-learning 深度對話 → 產出 |
| 4 | 冪等性 | **skip if exists + --force**，不追蹤 JSON（靠檔案存在判斷） |
| 5 | digest 掃描邏輯 | **檔名日期前綴**（sync 日），D 天撈 D-1 天 |
| 6 | 拆階段 | **5c-1（A+B+C）先 merge → 5c-2（D+E）**，各自獨立驗證 |
| 7 | trafilatura fallback | **三層 fallback 鏈**：trafilatura → requests+trafilatura extract → requests+BeautifulSoup → 提示 |
| 8 | digest 摘要長度 | **每篇 5-8 句** + 關鍵 takeaway |
| 9 | digest 重複內容 | daily-digest 做簡單去重（比對標題/slug），同一篇優先取 `300_Learning/input/` 版本 |
| 10 | web extract 共用模組 | fallback 鏈抽成 `scripts/lib/web_extract.py` 的 `extract_url_content(url)` 共用函式，learning-note --url 和 rss-sync 都呼叫 |
| 11 | beautifulsoup4 依賴 | 確認 trafilatura 是否已含 BS4，若否則加入依賴清單 |
| 12 | GUIDE.md 更新 | 5c-2 收尾時更新 GUIDE.md，加入 Phase 5c 的完整使用說明 |
| 13 | 5c-1 測試資料 | 用 `learning-note --file` + `rss-sync --feed` 產出，不依賴 Readwise 設定 |
| 14 | 全來源雙技術路線 | **所有來源統一雙路線並行**：API 路線（Python 腳本 CLI 批次）+ MCP 路線（MCP 設定 + workflow 描述用法），三個來源（Readwise / RSS / Anybox）一致，之後再選用哪條 |
| 15 | Plan A / Plan B 雙策略 | **兩套來源策略都建**：Plan A（Readwise 中心化，所有來源匯入 Readwise 後統一拉回）+ Plan B（各來源直接串接：rss-sync / anybox-sync），之後依使用體驗和成本選擇主力策略 |

**決策 #14 × #15 速查矩陣：**

|  | API 路線（Python 腳本 CLI） | MCP 路線（互動式 workflow） |
|--|---------------------------|--------------------------|
| **Plan A：Readwise 中心化** | `readwise_sync.py` — 統一拉回 | readwise MCP — 對話中查 highlights |
| **Plan B：RSS 直接串接** | `rss_sync.py` — feedparser + web_extract | rss-reader MCP — 對話中讀 feed |
| **Plan B：Anybox 直接串接** | `anybox_sync.py` — 本地 HTTP API + web_extract | anybox MCP — 對話中搜書籤 |

> - **Plan A** = 所有來源先匯入 Readwise，一個入口統一管理（依賴付費服務）
> - **Plan B** = 各來源獨立串接，不經中介（免費但多管道維護）
> - **API 路線** = `./bin/agent xxx-sync` CLI 批次，可離線跑
> - **MCP 路線** = Claude session 內互動式操作，零自訂程式碼
> - 所有格子都實作，之後依使用體驗和成本選擇主力組合

## 風險與注意事項

- **Google OAuth**：首次設定需 30 分鐘（GCP Console 建專案 + 啟用 Docs/Gmail API + 建立 OAuth 桌面憑證）。之後 refresh token 自動更新。未設定時 `--send` 優雅 fallback
- **Readwise API 重構**：必須完整測試 `podcast-add --readwise` 和 `--notion`
- **trafilatura fallback 鏈**：抽成 `scripts/lib/web_extract.py` 共用模組，learning-note --url 和 rss-sync 共用，三層 fallback 第 4 層才顯示人工介入提示
- **Anybox 雙路線**：API 路線需 `ANYBOX_API_KEY` + Anybox app 運行中；MCP 路線需手動 clone tommertron/anyboxMCP + 設定 Python 路徑 + Anybox app 運行中。兩者都依賴 Anybox app
- **daily-learning skill**：本質是 prompt engineering，需迭代調整對話品質
- **scope 拆分**：5c-1（A+B+C）和 5c-2（D+E）分開 merge，各自 ≤3 天。5c-1 結束時留測試資料給 5c-2
- **5c-1 測試資料**：用 `learning-note --file` + `rss-sync --feed` 產出，不依賴 Readwise 設定
- **daily-digest 去重**：同一篇出現在 readings/ 和 input/ 時，優先取 input/ 版本（LLM 已消化）
