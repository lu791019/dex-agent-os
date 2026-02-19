---
description: Gmail Sync — Gmail 電子報批次匯入到 000_Inbox/readings/
alwaysApply: false
---

# Gmail Sync — 電子報批次匯入

搜尋 Gmail 中的電子報，擷取內容存為 Markdown。

## 使用方式

```bash
# 列出最近 7 天電子報（不匯入）
./bin/agent gmail-sync

# 匯入最新 5 封
./bin/agent gmail-sync --latest 5 --force

# 篩選寄件者
./bin/agent gmail-sync --from "newsletter@substack.com" --latest 3 --force

# 指定 Gmail label
./bin/agent gmail-sync --label "newsletters" --latest 5 --force

# 自訂搜尋語法
./bin/agent gmail-sync --query "from:substack.com subject:weekly" --latest 5 --force

# 搜尋最近 30 天
./bin/agent gmail-sync --days 30 --latest 10 --force
```

## 輸出

- 路徑：`000_Inbox/readings/YYYY-MM-DD-gmail-<subject-slug>.md`
- 格式：frontmatter（title / source:gmail / from / date / type:newsletter）+ 信件內容
- 無 LLM，純擷取

## 搭配使用

匯入後可接：
- `daily-digest` — 自動掃描 readings/ 產出消化報告
- `learning-note --file` — 對重要電子報產學習筆記

## 前置需求

- Google API 已設定（`config/google-credentials.json`）
- 首次使用需重新授權（新增 gmail.readonly scope）
