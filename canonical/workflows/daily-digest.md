---
description: 每日學習消化報告 — 掃描當日所有學習內容 → LLM 摘要 → 本地存檔 / Google Doc / Gmail
alwaysApply: false
---

# Daily Digest — 每日學習消化報告

掃描指定日期的所有學習內容，LLM 產出消化摘要報告。

## 使用方式

```bash
# 基本使用（掃描昨天的內容）
./bin/agent daily-digest

# 指定日期
./bin/agent daily-digest 2026-02-18

# 掃描今天
./bin/agent daily-digest --today

# 覆蓋已存在的 digest
./bin/agent daily-digest --today --force

# 建立 Google Doc + 寄 Gmail（需先設定 Google API）
./bin/agent daily-digest --today --send
```

## 掃描範圍

依檔名日期前綴 `YYYY-MM-DD-*.md` 掃描：

| 目錄 | 來源 |
|------|------|
| `000_Inbox/readings/` | readwise-sync / rss-sync / anybox-sync 原文 |
| `300_Learning/input/**/` | learning-note 產出（已 LLM 消化） |
| `300_Learning/youtube/` | youtube-add 產出 |
| `300_Learning/podcasts/episodes/` | podcast-add 產出 |

## 去重邏輯

同一篇文章可能同時存在於 `readings/`（原文）和 `input/`（學習筆記）。
去重時以 URL 為 key，優先保留 `input/` 版本（已消化，品質較高）。

## 輸出

`100_Journal/digest/YYYY-MM-DD-digest.md`

## Google API 設定（選用）

`--send` 需要 Google Docs + Gmail API：

1. GCP Console → 建專案 → 啟用 Docs API + Gmail API
2. OAuth 同意畫面 → External → 加測試者
3. 建立 OAuth 桌面應用程式憑證 → 下載 JSON
4. 存為 `config/google-credentials.json`
5. `.env` 設定 `DIGEST_EMAIL=you@gmail.com`
6. 首次 `--send` 會開瀏覽器授權

未設定時 `--send` 會優雅跳過，僅存本地檔案。
