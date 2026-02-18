# Phase 5c Walkthrough：學習輸入管線 + 每日消化系統

> Branch: `feature/phase5c-learning-input` → merged to `master`
> 日期：2026-02-18
> Commits: 8 commits + 1 merge commit

---

## 概覽

Phase 5c 建立了完整的「每日學習消化循環」：

```
多來源匯入 → 原文存檔 / LLM 學習筆記 → 每日消化報告 → 互動學習對話 → 洞察產出
```

新增 6 個 CLI 指令 + 1 個互動 skill，涵蓋 37 個檔案變更（+4103 / -197 行）。

---

## 新增功能

### 1. 學習輸入管線（Section A-C）

#### 共用模組
| 檔案 | 說明 |
|------|------|
| `scripts/lib/readwise_api.py` | Readwise v2（highlights）+ v3（Reader）雙 API 共用模組 |
| `scripts/lib/web_extract.py` | 三層 fallback 網頁擷取（trafilatura → requests+trafilatura → BeautifulSoup）|

#### Sync 指令（批次匯入原文，不用 LLM）
| 指令 | 說明 | 輸出 |
|------|------|------|
| `readwise-sync` | Readwise v2 highlights + v3 Reader 批次匯入 | `000_Inbox/readings/` |
| `rss-sync` | RSS feed 批次匯入（支援 OPML） | `000_Inbox/readings/` |
| `anybox-sync` | Anybox 書籤批次匯入（本地 API） | `000_Inbox/readings/` |

#### Learning Note（LLM 消化學習筆記）
| 指令 | 說明 | 輸出 |
|------|------|------|
| `learning-note --url URL` | 單篇 URL → 結構化學習筆記 | `300_Learning/input/<type>/` |
| `learning-note --file PATH` | 本地檔案 → 學習筆記 | 同上 |
| `learning-note --readwise [--reader]` | Readwise → 學習筆記 | 同上 |
| `learning-note --rss FEED` | RSS → 學習筆記 | 同上 |
| `learning-note --anybox` | Anybox → 學習筆記 | 同上 |

### 2. 每日消化報告（Section D）

| 指令 | 說明 | 輸出 |
|------|------|------|
| `daily-digest [--today]` | 掃描 4 目錄 + 去重 + LLM 摘要 | `100_Journal/digest/` |
| `daily-digest --send` | 同上 + Google Doc + Gmail | Google Docs + Gmail |

**掃描範圍：**
- `000_Inbox/readings/` — sync 原文
- `300_Learning/input/**/` — learning-note 學習筆記
- `300_Learning/youtube/` — youtube-add 產出
- `300_Learning/podcasts/episodes/` — podcast-add 產出

**去重邏輯：** 同 URL 出現在 readings/ 和 input/ 時，優先保留 input/ 版本。

**Google API 整合：**
- `scripts/lib/google_api.py` — OAuth2 認證 + Google Docs API + Gmail API
- 未設定時優雅 fallback（只存本地，不 crash）
- 憑證：`config/google-credentials.json`，token 自動存 `config/google-token.json`

### 3. 互動學習對話（Section E）

| Skill | 說明 |
|-------|------|
| `/daily-learning` | 讀取 digest → 三種提問模式（蘇格拉底/考試/深聊）→ 歸納洞察 → 自動產出 |

---

## 重構

- `scripts/collectors/podcast_transcript.py`：移除 ~130 行重複 Readwise API 碼，改用 `from lib.readwise_api import ...`
- `bin/agent`：加入 `.env` 載入（`set -a; source "$ROOT_DIR/.env"; set +a`）

---

## 新增檔案清單

### Scripts（8 個）
```
scripts/lib/readwise_api.py          ← 共用 Readwise v2+v3 API
scripts/lib/web_extract.py           ← 三層 fallback 網頁擷取
scripts/lib/google_api.py            ← Google Docs + Gmail API
scripts/generators/learning_note.py  ← 5 模式學習筆記
scripts/generators/daily_digest.py   ← 每日消化報告
scripts/collectors/readwise_sync.py  ← Readwise 批次匯入
scripts/collectors/rss_sync.py       ← RSS 批次匯入
scripts/collectors/anybox_sync.py    ← Anybox 書籤批次匯入
```

### Workflows（6 個）
```
canonical/workflows/learning-note.md
canonical/workflows/readwise-sync.md
canonical/workflows/rss-sync.md
canonical/workflows/anybox-sync.md
canonical/workflows/daily-digest.md
canonical/workflows/daily-learning.md
```

### Templates（2 個）
```
800_System/templates/learning-note-template.md
800_System/templates/daily-digest-template.md
```

### Config（1 個）
```
config/subscriptions.opml            ← RSS 訂閱清單（jvns.ca + simonwillison.net）
```

---

## 環境變數

| 變數 | 用途 | 設定位置 |
|------|------|----------|
| `READWISE_TOKEN` | Readwise v2 + v3 API | `.env` |
| `ANYBOX_API_KEY` | Anybox 本地 API | `.env` |
| `DIGEST_EMAIL` | daily-digest 寄信收件者 | `.env` |
| Google credentials | OAuth 憑證 | `config/google-credentials.json` |

---

## 依賴

```bash
# Section A-C
pip3 install trafilatura feedparser beautifulsoup4 lxml_html_clean

# Section D
pip3 install google-auth google-auth-oauthlib google-api-python-client markdown
```

---

## 實作中發現的問題與解法

| 問題 | 解法 |
|------|------|
| Readwise v2 和 v3 是不同 API | 同一 token，readwise_api.py 統一封裝雙 API |
| Anybox auth 用 `X-API-Key`（非 Bearer） | 修正 header 格式 |
| Anybox tags 是 dict 不是 string | `t.get("name", str(t)) if isinstance(t, dict)` |
| `claude --print` 偶帶思考殘留 | `_clean_llm_output()` 清理 prefix |
| Google OAuth 403 access_denied | 需在 GCP 同意畫面加自己為測試者 |
| `pip` 找不到 | macOS 用 `pip3` |
| trafilatura 缺 lxml_html_clean | 額外 `pip3 install lxml_html_clean` |
| bs4 不隨 trafilatura 安裝 | 額外 `pip3 install beautifulsoup4` |
| bin/agent 未載入 .env | 加入 `set -a; source "$ROOT_DIR/.env"; set +a` |

---

## Git Log

```
eb47cce feat: Phase 5c Section D+E — daily-digest + Google API + daily-learning skill
9280401 chore: update task_phase5c.md progress — 5c-1 Section A~C complete
c142579 feat: Phase 5c Section C — readwise/rss/anybox sync + cross-module verification
7ab1f10 feat: Phase 5c Section B — learning-note script + web extract module
07c1822 feat: Phase 5c Section A — readwise_api shared module + .env loading
22c927b feat: add Anybox integration + dual-strategy matrix to Phase 5c plan
77fc914 docs: Phase 5c planning + GUIDE.md align to Phase 5b
31cbc73 feat: sync 累積學習 to both ~/CLAUDE.md and ~/.claude/CLAUDE.md
```

---

## 驗證結果

| 驗證項目 | 結果 |
|----------|------|
| `readwise-sync --latest 3 --force` | ✅ 匯入 3 筆 |
| `rss-sync --feed jvns.ca --latest 3 --force` | ✅ 匯入 3 篇 |
| `anybox-sync --starred --latest 1 --force` | ✅ 匯入 1 筆 |
| `learning-note --file GUIDE.md` | ✅ tech 筆記 |
| `learning-note --url simonwillison.net` | ✅ articles 筆記 |
| `learning-note --readwise --latest 1` | ✅ 跨模組 |
| `learning-note --rss jvns.ca --latest 1` | ✅ 跨模組 |
| `daily-digest --today` | ✅ 掃描 11 檔、去重 10 篇 |
| `daily-digest --today --send` | ✅ Google Doc + Gmail |
| `bin/agent help` | ✅ 6 新指令 |
| `bin/sync` | ✅ 6 新 skills 同步 |
