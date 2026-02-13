# Phase 3 實作計畫：topic-create + topic-to-thread + style-dna + Threads collector

## Context

Phase 2.5 完成後，`500_Content/insights/` 已累積 12 張 insight 卡片（從日記自動萃取），但這些素材目前沒有自動化的管線將其轉為可發布的內容。Phase 3 的目標是建立 **「insight → 主題 → Threads 草稿」** 的完整生產管線，並透過 style-dna 系統讓 AI 產出的內容「像你寫的」。

新增範圍：自動抓取使用者的 Threads 文章（透過官方 API），轉為結構化範例，免手動複製。

## 實作範圍

### 0. Threads Collector（`scripts/collectors/threads_collector.py`）

**功能**：透過 Threads API 自動抓取使用者的貼文 + 互動數據，存為結構化範例。

```
./bin/agent collect-threads [--limit 50] [--since 2025-01-01] [--force]
```

**前置需求**（使用者需完成）：
1. 在 developers.facebook.com 建立 Meta App（選 Threads API）
2. 設定 OAuth redirect URI（可用 localhost）
3. 取得 App ID + App Secret → 存入 `.env`
4. 首次執行時會開瀏覽器走 OAuth 授權流程

**流程**：
1. 檢查 `.env` 中的 `THREADS_APP_ID`、`THREADS_APP_SECRET`
2. 檢查 token 是否存在/有效（存在 `config/.threads-token`，gitignore）
3. 若無 token → 啟動 OAuth 流程（開瀏覽器 → localhost callback → 取得 short-lived token → 換 long-lived token）
4. `GET /me/threads?fields=id,text,timestamp,permalink,media_type&limit=100` 取得貼文
5. 每篇呼叫 `GET /{id}/insights?metric=views,likes,replies,reposts,quotes` 取得互動數據
6. 轉換為結構化格式，寫入 `800_System/references/examples/threads/NNN-slug.md`
7. 已存在的檔案跳過（除非 --force）

**token 管理**：
- Long-lived token 有效期 60 天
- 過期前可用 refresh endpoint 延展
- 存在 `config/.threads-token`（已 gitignore）

### 1. extract-style 腳本（`scripts/analyzers/extract_style.py`）

**功能**：讀取某頻道的所有真實範例，LLM 分析後產出風格 DNA 文件。

```
./bin/agent extract-style <channel>          # 例如 threads
./bin/agent extract-style <channel> --force  # 強制覆蓋
```

**流程**：
1. 讀取 `800_System/references/examples/<channel>/*.md` 所有範例
2. LLM 分析維度：結構模式、開場 Hook、語氣特徵、CTA/收尾、長度格式、高互動特徵、禁忌
3. 輸出 `800_System/references/style-dna/<channel>-dna.md`

**設計**：
- System prompt 定義分析維度（對齊 PLAN.md §7）
- 一次 LLM 呼叫（所有範例合併為一個 prompt）
- 範例格式：每篇含元資料（日期、互動數據）+ 原文

### 2. topic-create 腳本（`scripts/generators/topic_create.py`）

**功能**：從 insight 或手動描述建立主題檔案。

```
./bin/agent topic-create <insight-file>          # 從 insight 建立
./bin/agent topic-create --title "主題名稱"      # 手動描述
./bin/agent topic-create                         # 列出可用 insights
```

**流程**：
1. 讀取 insight 檔案（或接收手動輸入）
2. LLM 擴展為完整 TOPIC.md：核心論點、關鍵素材、頻道適合度、潛在切入角度
3. 自動產生 slug（從標題），建立 `500_Content/topics/<slug>/TOPIC.md`

**TOPIC.md 格式**（YAML frontmatter + 結構化內容）：
```markdown
---
title: 主題標題
status: drafting
source: 500_Content/insights/2026-02-07-xxx.md
tags: [AI, 效率, 工具]
created: 2026-02-09
---

# 主題標題

## 核心論點
一句話概括...

## 關鍵素材
- 素材 1
- 素材 2

## 頻道適合度
- Threads：✅（適合短觀點）
- Blog：✅（可展開為教學）
- Newsletter：❌

## 已產出的格式
- [ ] Threads
- [ ] Facebook
- [ ] Newsletter
- [ ] Blog
```

### 3. topic-to-thread 腳本（`scripts/generators/topic_to_thread.py`）

**功能**：從主題產出 Threads 草稿。

```
./bin/agent topic-to-thread <topic-slug>          # 產出 Threads 草稿
./bin/agent topic-to-thread <topic-slug> --force  # 覆蓋既有草稿
```

**流程**：
1. 讀取 `500_Content/topics/<slug>/TOPIC.md`
2. 讀取 `800_System/references/style-dna/threads-dna.md`（如存在）
3. 讀取 `canonical/rules/10-writing-style.md` 的 Threads 風格規則
4. LLM 產出 Threads 草稿（遵循風格 + DNA）
5. 寫入 `500_Content/topics/<slug>/threads-draft.md`
6. 更新 TOPIC.md 的「已產出」checklist（`- [x] Threads`）

### 4. 模板

- `800_System/templates/topic-template.md` — TOPIC.md 的佔位符模板
- `800_System/templates/thread-template.md` — Threads 草稿格式

### 5. Workflow 文件

- `canonical/workflows/topic-create.md` — topic-create 使用說明
- `canonical/workflows/topic-to-thread.md` — topic-to-thread 使用說明
- `canonical/workflows/extract-style.md` — extract-style 使用說明

### 6. CLI 整合（`bin/agent`）

新增四個指令：
```
collect-threads [--limit N] [--since DATE] [--force]    自動抓取 Threads 文章
extract-style <channel> [--force]                       提取風格 DNA
topic-create [insight-file|--title "..."]               從 insight 建立主題
topic-to-thread <topic-slug> [--force]                  主題 → Threads 草稿
```

## 關鍵檔案清單

| 操作 | 檔案 |
|------|------|
| 新增 | `scripts/collectors/threads_collector.py` |
| 新增 | `scripts/analyzers/extract_style.py` |
| 新增 | `scripts/generators/topic_create.py` |
| 新增 | `scripts/generators/topic_to_thread.py` |
| 新增 | `800_System/templates/topic-template.md` |
| 新增 | `800_System/templates/thread-template.md` |
| 新增 | `canonical/workflows/topic-create.md` |
| 新增 | `canonical/workflows/topic-to-thread.md` |
| 新增 | `canonical/workflows/extract-style.md` |
| 修改 | `bin/agent`（新增 4 個 case + help） |
| 修改 | `.gitignore`（加 `config/.threads-token`） |
| 修改 | `.env.example`（加 `THREADS_APP_ID`、`THREADS_APP_SECRET`） |
| 複用 | `scripts/lib/llm.py`（ask_claude） |
| 複用 | `scripts/lib/config.py`（路徑常數，可能新增） |
| 複用 | `scripts/lib/file_utils.py`（read_text、today_str） |

## 實作順序

### Section 0：規劃文件
- 建立 `implementation_plan_phase3.md`（本文件）
- 建立 `task_phase3.md`（步驟 1-17 的 checklist）
- 更新 `PLAN.md` Phase 3 區塊（加入 Threads collector + 更新任務清單）

### Section 1：基礎設施
1. 模板：topic-template.md、thread-template.md
2. Workflow：topic-create.md、topic-to-thread.md、extract-style.md
3. 更新 config.py（如需新路徑常數）
4. 更新 .gitignore + .env.example

### Section 2：Threads Collector
5. 實作 threads_collector.py（OAuth + 抓取 + 轉換格式）
6. 更新 bin/agent（collect-threads 指令）
7. 使用者設定 Meta App → 執行 collect-threads 抓取範例

### Section 3：Style DNA
8. 實作 extract_style.py
9. 更新 bin/agent（extract-style 指令）
10. 執行 extract-style threads 產出 threads-dna.md

### Section 4：內容生產管線
11. 實作 topic_create.py
12. 實作 topic_to_thread.py
13. 更新 bin/agent（topic-create、topic-to-thread 指令）

### Section 5：驗證 + 收尾
14. 端到端測試：insight → topic-create → topic-to-thread
15. bin/sync 同步新 workflow
16. 更新 GUIDE.md + PLAN.md
17. Commit

## 驗證方式

1. `./bin/agent collect-threads --limit 10` — 確認抓取 + 存為結構化範例
2. `./bin/agent extract-style threads` — 確認讀取範例 + 產出 threads-dna.md
3. `./bin/agent topic-create 500_Content/insights/2026-02-07-multi-ide-sync-best-practice.md` — 確認產出 TOPIC.md
4. `./bin/agent topic-to-thread multi-ide-sync-best-practice` — 確認產出 threads-draft.md
5. 檢查 TOPIC.md 的 checklist 自動更新
6. 冪等性：重複執行時正確提示已存在
7. `./bin/sync` 同步新 workflow 到各 IDE
