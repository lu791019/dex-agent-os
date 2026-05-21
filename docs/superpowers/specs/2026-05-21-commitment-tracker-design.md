# 承諾追蹤器（Commitment Tracker）設計文件

> 日期：2026-05-21
> 階段：Phase 6 P3（原 C 路線）
> 狀態：設計核可中

## 背景與問題

Phase 6 P2 交付了輕量版「持續性意識」方案 `situation-board.md`（CXO 承諾 + 現況 + 近期決策三合一）。但實際運作後發現：

- `situation-board.md` 最後更新停在 2026-04-15，到設計當下已 35 天未動
- P2 設計的維護機制是「CXO 任務完成後 CoS 順手更新」——依賴人/AI 記得，實際上沒有發生

**核心問題**：輕量版的弱點不是能力不足，而是**手動維護不會發生，board 必然過期**。承諾散落在各 session 對話中、沒有被系統性捕捉，跨 session 就遺忘。

「board 變爛」和「承諾被遺忘」是同一件事的兩面。

## 目標

建立一個**不依賴維護紀律**的承諾追蹤機制：

- 自動從每個 session 捕捉「明確交付物承諾」
- 自動偵測既有承諾的完成
- 經使用者確認後寫入對應 board（防誤報污染）
- 同時追蹤 AI 的承諾與 Dex 的 to-do，以「負責人」區分

## 非目標（YAGNI）

- 不做原始重型設計的 Session Handoff 機制（P2 已決定 $CMEM + MEMORY.md 足夠）
- 不做 shared situation room 重構（situation-board.md 已涵蓋）
- 不抓模糊承諾（「我來看看」這類）——只抓有明確動作 + 可驗證完成的
- 不重新設計 situation-board.md 格式

## 設計決策紀錄

| 決策 | 選擇 | 理由 |
|------|------|------|
| 捕捉機制 | Stop hook 抽取 → queue → 下次 SessionStart 確認 | 觸發靠事件不靠紀律；確認步驟擋誤報；複用專案已驗證的 `/reflect` queue pattern |
| 抽取標準 | 嚴格——只抓明確交付物承諾 | 寧可漏，不可污染。queue 被雜訊淹沒會導致失信→棄用 |
| 承諾主體 | AI 承諾 + Dex to-do 都追蹤 | 以 owner 欄位區分 |
| 結案機制 | 下次抽取時自動偵測完成 | 與新承諾共用同一 review 流程 |
| 監看範圍 | 所有 session，分流兩目的地 | CXO 承諾 → situation-board.md；dev 承諾 → 200_Work/commitments.md |
| 實作形式 | standalone，鏡像 claude-reflect pattern | claude-reflect 是第三方 plugin，改了會被更新覆蓋 |

## 架構與資料流

```
session 進行中：你 / AI 產生承諾
        │ session 結束
        ▼
Stop hook → commitment_extract.py
  1. 便宜預篩：heuristic 掃 transcript，無承諾語感則跳過
  2. claude --print 抽明確交付物承諾（嚴格）
  3. 比對現有 board 承諾，偵測已完成
  4. 每筆分類 cxo / dev
  5. 背景執行，hook 立即返回（不卡 session 結束）
        │ 寫入
        ▼
data/commitment_queue.json（pending queue）
        │ 下次 SessionStart hook 讀取
        ▼
提示「📌 N 個待確認承諾，跑 /承諾」
        │ 使用者執行 slash command
        ▼
/承諾 review：逐筆 確認 / 編輯 / 刪除 / 結案
        │ 確認後分流寫入
   ┌────┴────┐
   ▼         ▼
CXO 承諾    dev 承諾
situation-  200_Work/
board.md    commitments.md
```

**核心原則**：觸發靠 Stop hook 事件，不靠任何人記得 → 跨過「board 變爛」的根因。確認步驟（`/承諾`）擋誤報 → board 保持可信。

## 元件

| 元件 | 位置 | 職責 |
|------|------|------|
| 抽取 hook 腳本 | `scripts/hooks/commitment_extract.py` | Stop hook 呼叫；預篩 → LLM 抽取 → 偵測完成 → 寫 queue |
| pending queue | `data/commitment_queue.json` | 待確認承諾候選 |
| SessionStart 提示 | `~/.claude/settings.json` hook | 讀 queue，非空則印提示 |
| `/承諾` slash command | `canonical/commands/承諾.md` → `bin/sync` | 逐筆 review → 分流寫入 |
| dev 承諾追蹤檔 | `200_Work/commitments.md` | 新檔，存非 CXO 的開發承諾 |

### 效能設計

1. **便宜預篩**：Stop hook 先用關鍵字 heuristic 掃 transcript，沒有承諾語感的 session 直接跳過 LLM 呼叫——避免每個 session 結束都燒一次 `claude --print`。
2. **背景執行**：抽取腳本 fork 到背景，hook 立即返回，不阻塞 session 結束。結果非同步落進 queue，下次 SessionStart 接手。

## 檔案格式

### queue：`data/commitment_queue.json`

```json
[{
  "id": "c-20260521-01",
  "type": "new",
  "text": "審閱 AI-First DE 長文版並決定發布管道",
  "owner": "Dex",
  "category": "cxo",
  "cxo_role": "CMO",
  "deadline": "",
  "source_session": "a1ddb947...",
  "extracted_at": "2026-05-21"
}]
```

- `type`：`new`（新承諾）| `completion`（偵測到完成）
- `owner`：`Dex` | `AI`
- `category`：`cxo` | `dev`
- `cxo_role`：`category=cxo` 時才有，否則 `null`
- `completion` 型額外帶 `matched_board_item`（指回 board 現有承諾文字）+ `evidence`（這次 session 做了什麼）

### dev 承諾檔：`200_Work/commitments.md`（新檔）

```markdown
# Dev Commitments
> 最近更新：2026-05-21

## 未結案
| 事項 | 負責人 | 期限 | 狀態 | 來源 |
|------|--------|------|------|------|

## 近期結案（保留 30 天）
```

### situation-board.md

格式**不動**。C 只在既有「承諾」表格 append 新列，沿用現有欄位（事項 / 誰提的 / 期限 / 狀態）。結案的承諾從表格移除。

## `/承諾` review 流程

1. 讀 queue，空則回「無待確認承諾」並結束
2. 逐筆呈現：
   - **新承諾**：顯示 text / owner / category / deadline → 使用者選 確認 / 編輯文字 / 刪除（誤報）
   - **已完成**：顯示對應 board 承諾 + evidence → 使用者選 確認結案 / 否決
3. review 完一次性寫入：
   - 確認的新承諾依 category 分流 append（situation-board.md 或 commitments.md）
   - 確認結案的從對應 board 移除
   - 更新目標檔的「最近更新」日期
   - 清空 queue

## 邊界處理

| 情境 | 處理 |
|------|------|
| queue 空 / 檔案損壞 | graceful，不中斷 |
| Stop hook 抽取失敗（LLM timeout 等） | log 後靜默退出，絕不卡住 session 結束 |
| 跨 session 重複抽到同一承諾 | 用文字相似度去重 |
| situation-board.md 路徑不存在 | 警告但不崩 |
| transcript path 未提供 | 跳過抽取 |

## 測試策略

- **單元**：分類（cxo/dev）、文字相似度去重、分流路由邏輯
- **整合**：餵一份 fixture transcript → 驗證 queue 輸出正確
- **E2E**：模擬完整 loop（抽取 → queue → review → 兩個目的地寫入）

## 開放問題

無。設計已完整，待使用者 review 後進入實作計畫。
