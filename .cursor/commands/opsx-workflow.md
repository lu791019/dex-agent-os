
# OPSX 規格驅動開發流程

## 核心概念

OPSX 是 artifact-driven 的開發流程：先產出規格文件（proposal → specs → design → tasks），再按 tasks 實作。所有指令都是 `/opsx:xxx` slash commands。

## 工作流路由

根據使用者的意圖，引導到正確的指令：

```
想法模糊，需要探索
  └─→ /opsx:explore

想法清楚，要開始新功能
  ├─→ /opsx:new       （逐步產出 artifacts，一次一個）
  └─→ /opsx:ff        （一口氣產出所有 artifacts，適合明確的需求）

已有 change，繼續產 artifact
  └─→ /opsx:continue

artifacts 完成，開始寫 code
  └─→ /opsx:apply

實作完成，驗證是否符合規格
  └─→ /opsx:verify

驗證通過，歸檔
  ├─→ /opsx:archive        （單一 change）
  └─→ /opsx:bulk-archive   （批次歸檔）

規格有更新，同步到主 specs
  └─→ /opsx:sync

第一次用，想了解流程
  └─→ /opsx:onboard
```

## 典型流程

```
/opsx:explore → /opsx:new → /opsx:continue (×N) → /opsx:apply → /opsx:verify → /opsx:archive
                    or
              → /opsx:ff  ─────────────────────→ /opsx:apply → /opsx:verify → /opsx:archive
```

## 判斷原則

| 情境 | 推薦指令 | 原因 |
|------|---------|------|
| 「我想做 X 但還不確定怎麼做」 | `/opsx:explore` | 先釐清再動手 |
| 「幫我加一個 Y 功能」 | `/opsx:ff` | 需求明確，快速產出所有 artifacts |
| 「我想仔細規劃 Z」 | `/opsx:new` → `/opsx:continue` | 逐步產出，每步可 review |
| 「繼續之前的 change」 | `/opsx:continue` | 接續未完成的 artifact |
| 「開始實作」 | `/opsx:apply` | artifacts 已就位 |
| 「做完了，收工」 | `/opsx:verify` → `/opsx:archive` | 驗證後歸檔 |

## 注意事項

- 每個 `/opsx:xxx` command 內部已有完整的操作步驟和 guardrails，此 skill 只負責路由
- 不要在此 skill 裡重複各 command 的細節，直接觸發對應的 command
- `openspec` CLI 是底層工具，所有操作透過 `/opsx:xxx` 進行
