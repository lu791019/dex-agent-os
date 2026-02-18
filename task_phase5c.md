# Phase 5c：學習輸入管線 + 每日消化系統 — Tasks

## Project Initialization
- [x] Create implementation_plan_phase5c.md and task_phase5c.md
- [x] Create feature branch `feature/phase5c-learning-input`
- [x] 加入 Phase 5c 到 PLAN.md
- [x] GUIDE.md 對齊到 Phase 5b
- [x] 設計決策討論完成（15 項決策，見 implementation_plan 的「設計決策」區塊）
- [ ] Install dependencies (A-C): `pip install trafilatura feedparser`
- [ ] 確認 beautifulsoup4 是否隨 trafilatura 安裝，若否則加裝

---
## ═══ Phase 5c-1：學習輸入管線（A + B + C）═══

## Section A：核心基礎
- [ ] A1. 建立 `scripts/lib/readwise_api.py` — 從 podcast_transcript.py 抽取共用 API 模組（check_readwise_setup / readwise_headers / api_request / readwise_export / book_to_text / slugify）
- [ ] A2. 重構 `scripts/collectors/podcast_transcript.py` — 改用 `from lib.readwise_api import ...`，行為不變
- [ ] A3. 更新 `scripts/lib/config.py` — 新增 LEARNING_INPUT_DIR / READINGS_DIR / DIGEST_DIR
- [ ] A4. 建立 `800_System/templates/learning-note-template.md`
- [ ] A5. 驗證：`./bin/agent podcast-add --readwise` 重構後行為不變

## Section B：learning-note Script
- [ ] B1. 建立 `scripts/lib/web_extract.py` — 共用 `extract_url_content(url)` 函式，三層 fallback 鏈
- [ ] B2. 建立 `scripts/generators/learning_note.py` — 五種模式（--url / --file / --readwise [--all] / --rss / --anybox），含 --type 和 --force
  - --url、--rss、--anybox 使用 web_extract.py 的 fallback 鏈
- [ ] B3. 建立 `canonical/workflows/learning-note.md`
- [ ] B4. 驗證：`--file` 模式 — `./bin/agent learning-note --file README.md --title "Test" --type tech --force`
- [ ] B5. 驗證：`--url` 模式 — `./bin/agent learning-note --url "https://simonwillison.net/" --force`

## Section C：批次匯入 + MCP 設定
- [ ] C1. 建立 `scripts/collectors/readwise_sync.py` — Readwise highlights 批次匯入（--category / --latest / --all / --since / --force），冪等性：skip if exists + --force 覆蓋，檔名用 sync 日
- [ ] C2. 建立 `scripts/collectors/rss_sync.py` — RSS 批次匯入（--opml / --feed / --latest / --force），用 web_extract.py 取全文，冪等性同上
- [ ] C3. 建立 `scripts/collectors/anybox_sync.py` — Anybox 書籤批次匯入（API 路線：本地 HTTP API），支援 --tag / --folder / --starred / --latest / --force，用 web_extract.py 取全文
- [ ] C4. 建立 `config/subscriptions.opml` — 初始 RSS 訂閱清單
- [ ] C5. 建立 `canonical/workflows/readwise-sync.md` + `rss-sync.md` + `anybox-sync.md`（每個 workflow 都包含 API 路線 + MCP 路線的用法說明）
- [ ] C6. 更新 `.claude/settings.local.json` — MCP 設定（readwise / rss-reader / gmail / anybox）
- [ ] C7. 驗證：`./bin/agent readwise-sync --latest 3 --force`
- [ ] C8. 驗證：`./bin/agent rss-sync --feed "https://jvns.ca/atom.xml" --latest 3 --force`
- [ ] C9. 驗證：`./bin/agent anybox-sync --starred --latest 3 --force`
- [ ] C10. 驗證跨模組：`./bin/agent learning-note --readwise --latest 1 --force`
- [ ] C11. 驗證跨模組：`./bin/agent learning-note --rss "https://jvns.ca/atom.xml" --latest 1 --force`
- [ ] C12. 驗證跨模組：`./bin/agent learning-note --anybox --starred --latest 1 --force`

## 5c-1 收尾
- [ ] 更新 `bin/agent` — 新增 4 指令（learning-note / readwise-sync / rss-sync / anybox-sync）+ help
- [ ] 確保測試資料存在：`learning-note --file` + `rss-sync --feed` + `anybox-sync --starred` 產出（不依賴 Readwise）
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
