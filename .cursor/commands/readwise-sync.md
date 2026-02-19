
# Readwise Sync — Readwise 批次同步

將 Readwise highlights 和 Reader 閱讀清單批次匯入到 `000_Inbox/readings/`。

## API 路線（CLI 批次）

### v2 Highlights
```bash
./bin/agent readwise-sync                              # 列出最近 7 天
./bin/agent readwise-sync --latest 3 --force           # 匯入最新 3 筆
./bin/agent readwise-sync --category articles --force   # 只匯入文章
./bin/agent readwise-sync --since 2026-02-01 --force   # 匯入指定日期後
```

### v3 Reader
```bash
./bin/agent readwise-sync --reader                     # 列出 Reader 文件
./bin/agent readwise-sync --reader --latest 5 --force  # 匯入最新 5 篇
```

## MCP 路線（互動式）

在 Claude Code session 中，使用 readwise MCP 工具互動操作：
- 搜尋特定書籍或文章的 highlights
- 瀏覽 Reader 閱讀清單
- 適合需要即時查看和篩選的場景

## 環境設定

`.env` 中設定 `READWISE_TOKEN`（同時支援 v2 和 v3 API）
