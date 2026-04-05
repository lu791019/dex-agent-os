#!/bin/bash
# scheduled_sync.sh — launchd 排程呼叫的同步腳本
#
# 功能：執行 sync-all --no-llm（快速同步，不跑 LLM）
# 用法：直接執行或由 launchd plist 觸發
#
# 安裝排程：
#   cp config/com.dex.agent-os.sync.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/com.dex.agent-os.sync.plist
#
# 移除排程：
#   launchctl unload ~/Library/LaunchAgents/com.dex.agent-os.sync.plist
#   rm ~/Library/LaunchAgents/com.dex.agent-os.sync.plist
#
# 手動測試：
#   bash scripts/tools/scheduled_sync.sh
#
# 修改執行時間：
#   編輯 config/com.dex.agent-os.sync.plist 中的 StartCalendarInterval

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/scheduled-sync.log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# 檢查網路連線（Google Sheets API 需要）
check_network() {
    if ! curl -s --connect-timeout 5 https://sheets.googleapis.com > /dev/null 2>&1; then
        log "SKIP: 無網路連線，跳過本次同步"
        exit 0
    fi
}

main() {
    log "=== 開始排程同步 ==="
    check_network

    cd "$PROJECT_DIR"

    # 載入 .env
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi

    log "執行 sync-all --no-llm ..."
    if python3 "$PROJECT_DIR/scripts/collectors/sync_all.py" --no-llm >> "$LOG_FILE" 2>&1; then
        log "sync-all 完成"
    else
        log "ERROR: sync-all 失敗 (exit code: $?)"
    fi

    # 保留最近 30 天日誌
    if [ -f "$LOG_FILE" ]; then
        tail -n 3000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi

    log "=== 排程同步結束 ==="
}

main "$@"
