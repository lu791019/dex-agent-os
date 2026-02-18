# Phase 5c：學習輸入管線 + 每日消化系統 — Tasks

## Project Initialization
- [x] Create implementation_plan_phase5c.md and task_phase5c.md
- [x] Create feature branch `feature/phase5c-learning-input`
- [x] 加入 Phase 5c 到 PLAN.md
- [x] GUIDE.md 對齊到 Phase 5b
- [x] 設計決策討論完成（15 項決策，見 implementation_plan 的「設計決策」區塊）
- [x] Install dependencies (A-C): `pip install trafilatura feedparser`
- [x] 確認 beautifulsoup4 是否隨 trafilatura 安裝，若否則加裝（需手動 `pip install beautifulsoup4 lxml_html_clean`）

---
## ═══ Phase 5c-1：學習輸入管線（A + B + C）═══

## Section A：核心基礎 ✅ committed `07c1822`
- [x] A1. 建立 `scripts/lib/readwise_api.py` — 共用 API 模組（v2 + v3 Reader 雙 API 支援）
- [x] A2. 重構 `scripts/collectors/podcast_transcript.py` — 改用 `from lib.readwise_api import ...`，移除 ~130 行重複碼
- [x] A3. 更新 `scripts/lib/config.py` — 新增 LEARNING_INPUT_DIR / READINGS_DIR / DIGEST_DIR
- [x] A4. 建立 `800_System/templates/learning-note-template.md`
- [x] A5. 驗證：`./bin/agent podcast-add --readwise` 重構後行為不變
- [x] 額外：bin/agent 加入 .env 載入（source $ROOT_DIR/.env）

## Section B：learning-note Script ✅ committed `7ab1f10`
- [x] B1. 建立 `scripts/lib/web_extract.py` — 三層 fallback 鏈（trafilatura → requests+trafilatura → BeautifulSoup）
- [x] B2. 建立 `scripts/generators/learning_note.py` — 五種模式 + --reader flag 支援 Readwise Reader v3
- [x] B3. 建立 `canonical/workflows/learning-note.md`
- [x] B4. 驗證：`--file` 模式 — GUIDE.md → tech 筆記 ✅
- [x] B5. 驗證：`--url` 模式 — simonwillison.net → articles 筆記 ✅

## Section C：批次匯入 + MCP 設定 ✅ committed `c142579`
- [x] C1. 建立 `scripts/collectors/readwise_sync.py` — v2 highlights + v3 Reader 雙模式
- [x] C2. 建立 `scripts/collectors/rss_sync.py` — feedparser + trafilatura 全文
- [x] C3. 建立 `scripts/collectors/anybox_sync.py` — 本地 HTTP API（X-API-Key auth）
- [x] C4. 建立 `config/subscriptions.opml` — 初始 RSS 訂閱清單（jvns.ca + simonwillison.net）
- [x] C5. 建立 `canonical/workflows/readwise-sync.md` + `rss-sync.md` + `anybox-sync.md`
- [ ] C6. 更新 `.claude/settings.local.json` — MCP 設定（暫緩，需實際 MCP server 路徑）
- [x] C7. 驗證：`readwise-sync --latest 3 --force` — 匯入 3 筆 ✅
- [x] C8. 驗證：`rss-sync --feed jvns.ca --latest 3 --force` — 匯入 3 篇 ✅
- [x] C9. 驗證：`anybox-sync --starred --latest 1 --force` — 匯入 1 筆 ✅
- [x] C10. 驗證跨模組：`learning-note --readwise --latest 1 --force` ✅
- [x] C11. 驗證跨模組：`learning-note --rss jvns.ca --latest 1 --force` ✅
- [ ] C12. 驗證跨模組：`learning-note --anybox --starred --latest 1 --force`（待補）

### 實作中發現的額外變更
- Readwise Reader v3 API 加入 readwise_api.py（reader_list + reader_doc_to_text）
- Anybox auth header 修正：Bearer → X-API-Key
- Anybox tags 解析修正：dict → string
- NOTION_PODWISE_DB_ID 未設定（非必要，Podwise → Notion 路線暫不使用）

## 5c-1 收尾
- [x] 更新 `bin/agent` — 新增 4 指令（learning-note / readwise-sync / rss-sync / anybox-sync）
- [x] 確保測試資料存在：learning-note + rss-sync + anybox-sync 產出
- [ ] 更新 bin/agent help 文字
- [ ] Commit + merge 到 main

---
## ═══ Phase 5c-2：每日消化 + 互動學習（D + E）═══

## Section D：每日消化報告
- [ ] D1. Install dependencies (D): `pip install google-auth google-auth-oauthlib google-api-python-client markdown`
- [ ] D2. 建立 `scripts/generators/daily_digest.py` — 掃描檔名日期前綴（D 天撈 D-1 天）+ LLM 摘要（每篇 5-8 句）+ 本地存檔 + 簡單去重（同篇優先取 input/ 版本）
- [ ] D3. 建立 `scripts/lib/google_api.py` — OAuth 認證 + Google Docs API + Gmail API，未設定時優雅 fallback
- [ ] D4. 建立 `800_System/templates/daily-digest-template.md`
- [ ] D5. 建立 `canonical/workflows/daily-digest.md`
- [ ] D6. 驗證：`./bin/agent daily-digest` — 本地摘要產出
- [ ] D7. 驗證：`./bin/agent daily-digest --send` — Google Doc + Gmail（或 fallback 提示）

## Section E：互動學習對話 + CLI 收尾
- [ ] E1. 建立 `canonical/workflows/daily-learning.md` — 互動學習 skill（消化漏斗核心：蘇格拉底/考試/深聊式提問 → 歸納 → 自動產出 insights + learnings）
- [ ] E2. 更新 `bin/agent` — 新增 daily-digest 指令 + help 更新
- [ ] E3. 更新 `CLAUDE.md` CLI 速查表 +5 指令
- [ ] E4. 更新 `PLAN.md` Phase 5c 狀態為完成
- [ ] E5. 更新 `GUIDE.md` — 加入 Phase 5c 完整使用說明
- [ ] E6. 執行 `bin/sync` 同步 workflows
- [ ] E7. 驗證：`./bin/agent help` — 確認所有新指令
- [ ] E8. 驗證：`./bin/agent sync` — 同步正常
- [ ] E9. 驗證：啟動 /daily-learning skill 做互動對話測試

## Finalize
- [ ] 產出 walkthrough.md
