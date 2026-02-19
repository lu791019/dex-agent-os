
# Anybox Sync — Anybox 書籤批次同步

將 Anybox 書籤批次匯入到 `000_Inbox/readings/`。

## API 路線（CLI 批次）

```bash
./bin/agent anybox-sync --starred --latest 3 --force       # 星號書籤
./bin/agent anybox-sync --tag "to-read" --latest 5 --force # 標籤過濾
./bin/agent anybox-sync --folder "Tech" --force             # 資料夾過濾

# 列出書籤
./bin/agent anybox-sync --starred
```

## MCP 路線（互動式）

在 Claude Code session 中，使用 anybox MCP 工具互動操作：
- 搜尋書籤（search_bookmarks）
- 瀏覽標籤（list_tags）和資料夾（list_folders）
- 儲存新書籤（save_bookmark）
- 適合即時查看和管理書籤

## 環境設定

- `.env` 中設定 `ANYBOX_API_KEY`（從 Anybox Preferences → General 取得）
- Anybox app 需運行中（本地 HTTP API：127.0.0.1:6391）
