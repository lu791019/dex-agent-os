#!/usr/bin/env bash
# PostToolUse hook: 當 Bash 工具執行 git commit 時，自動記錄到工作日誌

# 從 stdin 讀取 hook JSON
input=$(cat)

# 取得 tool_input.command
command=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
if [[ -z "$command" ]]; then
  exit 0
fi

# 判斷指令中是否包含 git commit
if ! echo "$command" | grep -qE '\bgit\b.*\bcommit\b'; then
  exit 0
fi

# 檢查是否被中斷
interrupted=$(echo "$input" | jq -r '.tool_response.interrupted // false' 2>/dev/null)
if [[ "$interrupted" == "true" ]]; then
  exit 0
fi

# 取得 hook 執行時的工作目錄
cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null)

# 如果指令中有 -C 參數，提取該路徑作為 repo 目錄
repo_dir=$(echo "$command" | grep -oP '(?<=git\s-C\s)\S+' 2>/dev/null || echo "$command" | sed -n 's/.*git -C \([^ ]*\).*/\1/p' 2>/dev/null || true)

# 決定 git 執行的目錄：優先用 -C 參數，其次用 cwd，最後用 PWD
if [[ -n "$repo_dir" ]]; then
  git_dir="$repo_dir"
elif [[ -n "$cwd" ]]; then
  git_dir="$cwd"
else
  git_dir="$PWD"
fi

# 確認是 git repo
if ! git -C "$git_dir" rev-parse --git-dir &>/dev/null; then
  exit 0
fi

# 取得最新 commit 資訊
hash=$(git -C "$git_dir" log -1 --format='%h' 2>/dev/null) || exit 0
message=$(git -C "$git_dir" log -1 --format='%s' 2>/dev/null) || exit 0
files=$(git -C "$git_dir" diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | head -20) || exit 0

# 取得專案名稱：優先從 remote URL，否則用目錄名
remote_url=$(git -C "$git_dir" remote get-url origin 2>/dev/null || true)
if [[ -n "$remote_url" ]]; then
  project=$(echo "$remote_url" | sed 's|.*/||;s|\.git$||')
else
  project=$(basename "$(git -C "$git_dir" rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")
fi

# 格式化變更檔案清單
files_formatted=$(echo "$files" | sed 's/.*/`&`/' | paste -sd', ' -)

# 取得時間
time_str=$(date '+%H:%M')

# 建立日誌路徑
year=$(date '+%Y')
month=$(date '+%m')
day=$(date '+%Y-%m-%d')
log_dir="$HOME/work-logs/$year/$month"
log_file="$log_dir/$day.md"

mkdir -p "$log_dir"

# 追加記錄
if [[ ! -f "$log_file" ]]; then
  cat > "$log_file" <<EOF
# $day 工作日誌

---
> **自動記錄** [$time_str] \`$hash\` $message （$project）
> 變更：$files_formatted
EOF
else
  cat >> "$log_file" <<EOF

---
> **自動記錄** [$time_str] \`$hash\` $message （$project）
> 變更：$files_formatted
EOF
fi

