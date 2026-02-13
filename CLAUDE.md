# Dex Agent OS

個人 AI 代理人系統 — 生產力、學習、內容創作、工作管理。

## 核心原則
- 低風險自動執行，高風險必須問我
- 產出用繁體中文 Markdown，條列優先
- 讀 `canonical/rules/` 取得詳細寫作風格與安全規則
- 讀 `800_System/references/style-dna/` 取得各頻道風格

## 結構速查
- `000_Inbox/` 靈感輸入
- `100_Journal/` 日記
- `200_Work/` 工作
- `300_Learning/` 學習
- `400_Projects/` 專案/產品
- `500_Content/` 內容生產（topics/ → 多頻道）
- `600_Life/` 職涯/影評/個人
- `700_Archive/` 已發布
- `800_System/` 模板/範例/DNA

## 工具
- `bin/agent <action>` CLI 入口
- `bin/sync` 跨平台同步
- `/work-log` 工作日誌（全域指令）

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always use `/opsx:*` skills when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Quick reference:
- `/opsx:new` - Start a new change
- `/opsx:continue` - Continue working on a change
- `/opsx:apply` - Implement tasks

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->
