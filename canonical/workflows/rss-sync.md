---
description: RSS 批次同步 — feedparser + trafilatura → 000_Inbox/readings/
alwaysApply: false
---

# RSS Sync — RSS 批次同步

將 RSS feed 文章批次匯入到 `000_Inbox/readings/`。

## API 路線（CLI 批次）

```bash
# 單一 feed
./bin/agent rss-sync --feed "https://jvns.ca/atom.xml" --latest 3 --force

# OPML 批次（多個 feed）
./bin/agent rss-sync --opml config/subscriptions.opml --latest 5 --force

# 列出 feed 內容
./bin/agent rss-sync --feed "URL"
```

## MCP 路線（互動式）

在 Claude Code session 中，使用 rss-reader MCP 工具互動操作：
- 即時瀏覽 RSS feed 內容
- 搜尋特定關鍵字的文章
- 適合探索性閱讀和篩選

## 訂閱管理

編輯 `config/subscriptions.opml` 管理 RSS 訂閱清單。
