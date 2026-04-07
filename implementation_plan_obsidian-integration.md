# Obsidian Vault 整合 — 進度與下一步

> 日期：2026-04-07
> 目標：把 dex-agent-os 變成 Obsidian vault，建立網狀知識結構

---

## 已完成

### 1. Vault 基礎設定
- [x] dex-agent-os 開為 Obsidian vault（502 檔案、170 資料夾）
- [x] `.obsidian/app.json` 排除規則：scripts、bin、config、data、tests、.git、.claude、.cursor、.agent、node_modules、openspec、work-log
- [x] obsidian-skills v1.0.1 已安裝（kepano/obsidian-skills）
- [x] Obsidian CLI 啟用且測試通過

### 2. Daily Note 系統
- [x] 模板：`800_System/templates/daily-note.md`（人寫 + AI 寫共用）
- [x] Obsidian 設定 → Core plugin Daily notes 指向 `100_Journal/daily/`
- [x] 日期格式 `YYYY-MM-DD`，模板路徑指向新模板

### 3. 跨 vault 整合
- [x] 志業筆記從 iCloud Dex vault → `600_Life/志業/`（26 篇）
- [x] 知識管理褲 vault 書評筆記 → `300_Learning/input/books/`（27 篇）
- [x] DayDreamDex knowledge symlink → `daydreamdex-kb/`
- [x] DayDreamDex CXO 組織圖 Canvas → `daydreamdex-kb/_CXO-MAP.canvas`

### 4. Wikilink 知識網建立
- [x] **71 篇 Insights**：`source` frontmatter 從純文字路徑 → wikilink
- [x] **33 篇 Topics**：`source` frontmatter 從純文字路徑 → wikilink
- [x] **66 篇 Channel drafts**（Threads + Facebook 4 個日期）：自動加 `source: "[[topic-slug/TOPIC]]"` 連回 Topic
- [x] **5 篇今日新草稿**（4/6）：`insight:` 欄位轉 wikilink
- [x] **7 篇 dayflow** 檔案：加 frontmatter + `source: "[[date]]"` 連到當日 journal
- [x] **6 篇 digest** 檔案：修復 frontmatter + 加 `source: "[[date]]"`

### 5. CLI 腳本修改（影響未來產出）
- [x] `scripts/extractors/journal_knowledge_extract.py:403`：新 Insight 自動帶 wikilink source
- [x] `800_System/templates/daily-digest-template.md`：digest 模板加 `source: "[[{date}]]"`
- [x] `scripts/generators/daily_digest.py`：digest 中本地檔案用 `[[檔名|標題]]` wikilink 格式

### 6. Dataview Dashboard
- [x] `_dashboard.md` 取代手動 _INDEX.md
- [x] 動態查詢：最近洞察、主題進度、今日學習輸入、最近學習消化、孤兒筆記、書籍筆記、CXO

---

## 知識鏈現狀

```
000_Inbox/readings → daily_digest → 100_Journal/daily → 510_Insights → 520_Topics → 530_Channels → 700_Archive
   (待連)              (已連)         (中心)              (已連 71)     (已連 33)      (已連 66)
```

---

## 已知問題

### 1. 仍是孤兒的內容（可接受或需 follow-up）
| 區域 | 數量 | 狀態 |
|------|------|------|
| `000_Inbox/readings/` | ~30 篇 | inbox 性質，不需強制連結 |
| `300_Learning/input/articles, youtube` | ~5 篇 | 透過機制 A（Dataview）自動關聯 |
| `530_Channels/threads/2026-02-09 ~ 02-12, 02-18` | ~25 篇 | 早期草稿命名不一致，建議搬入 `700_Archive/` |
| `530_Channels/threads/2026-04-06` | 5 篇 | 編號式命名，已透過 `insight:` 連結 |
| `800_System/templates, references` | ~120 篇 | 系統檔案，本來就不該有連結 |
| 較新 Insights（沒對應 Topic 的 raw 洞察） | ~10 篇 | 等發展為 Topic 即可 |

### 2. CLI 腳本修改未完整測試
- `daily_digest.py` 改動已驗證（4/6 重新產生成功）
- `journal_knowledge_extract.py` 改動只修改一行，**尚未實際跑過**
- 03-29 的 digest 重新產生時 LLM timeout（900 秒），目前是 placeholder

### 3. iCloud 其他 vault
- `德斯的人生與志業`（2 篇）— 跳過
- `共讀會/行銷-Kit`（只有圖）— 跳過
- 新 vault `知識管理褲` 的 png 截圖在 `300_Learning/input/books/assets/`

---

## 下一步

### 高優先（影響使用體驗）
1. **驗證 Graph View 效果** — 開 Obsidian 看知識網是否如預期
2. **驗證 dashboard.md 的 Dataview 查詢** — 確認 Dataview 外掛正常運作
3. **跑一次 `./bin/agent extract`** 測試新 Insight 是否自動帶 wikilink

### 中優先（清理收尾）
4. **早期 Threads 草稿** 搬入 `700_Archive/threads/`
5. **修復現有 dataview 查詢** 如果發現 syntax 錯誤
6. **記錄 wikilink 命名慣例** 到 `800_System/` 作為規範

### 低優先（持續成長）
7. **Inbox/readings 的 Dataview 整合** 改機制 B（需改更多腳本）
8. **CXO Canvas 完善** 加入更多視覺化（內容生產管線、知識流向圖）
9. **DayDreamDex Agent Team 測試** — 用這個 vault 整合議題作為 Multi-CXO 派遣的測試案例

---

## 待測試的指令
```bash
./bin/agent extract --today          # 驗證新 Insight 自動帶 wikilink
./bin/agent daily-digest --today     # 驗證 digest 自動連回 journal
./bin/agent topic-create <slug>      # 待確認此腳本是否需要類似改動
```

---

## 待改但未動的腳本
- `topic-create` — 應該也要產出 wikilink 格式的 source（待檢查）
- `topic-to-thread` / `topic-to-fb` — 草稿產出時應自動加 `source: "[[topic/TOPIC]]"`（4/6 的草稿是用編號式命名 + `insight:` 欄位，跟舊草稿不同，需統一）

---

## 連結密度統計（變更前後）
| 指標 | 變更前 | 變更後 |
|------|------|------|
| 有 wikilink 的檔案 | <10 | ~250+ |
| Insight ↔ Journal 連結 | 0 | 71 |
| Topic ↔ Insight 連結 | 0 | 33 |
| Channel Draft ↔ Topic 連結 | 0 | 71 |
| Dayflow ↔ Journal 連結 | 0 | 7 |
| Digest ↔ Journal 連結 | 0 | 6 |
