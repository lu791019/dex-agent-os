# Cross-Platform Support Design

> 讓 Dex Agent OS 在 Windows 上也能執行，同時不影響現有 macOS 工作流

## 目標

- Windows 使用者可以 `git clone` 後直接執行
- macOS 現有功能零影響
- macOS 專屬功能（Dayflow、Apple Podcast）在 Windows 上優雅降級

## 方案：全面 Python 化（方案 B）

將 `bin/agent` 和 `bin/sync` 的邏輯從 bash 改寫為 Python，bash 腳本改為 thin wrapper。

## 改動清單

### 新增檔案

| 檔案 | 用途 |
|------|------|
| `bin/agent.py` | 跨平台 CLI 路由（~80 行） |
| `bin/agent.bat` | Windows 入口 wrapper（1 行） |
| `bin/sync.py` | 跨平台同步邏輯（~120 行） |
| `tests/test_agent_cli.py` | CLI 路由測試 |
| `tests/test_sync.py` | 同步邏輯測試 |
| `tests/test_config_platform.py` | 平台偵測測試 |
| `tests/conftest.py` | 共用 fixtures |

### 修改檔案

| 檔案 | 改什麼 | Mac 影響 |
|------|--------|----------|
| `bin/agent` | 250 行 bash → 2 行 thin wrapper 呼叫 agent.py | 無（`./bin/agent journal` 行為一樣） |
| `bin/sync` | 同上，改為呼叫 sync.py | 無（`./bin/sync` 行為一樣） |
| `scripts/lib/config.py` | 3 個 macOS 路徑加 `if _IS_MAC` 分支 | 無（Mac 走原值） |
| `scripts/extractors/journal_knowledge_extract.py` | 硬編碼路徑改用 `config.CLAUDE_MEMORY_DIR` | 無（值相同） |

## 技術細節

### bin/agent.py

- 用 `python-dotenv` 載入 `.env`（取代 bash `source`）
- COMMANDS dict 映射指令名 → Python 腳本路徑
- `subprocess.run()` + `sys.exit(result.returncode)` 確保 exit code 傳遞
- `KeyboardInterrupt` 處理 → `sys.exit(130)`

### bin/sync.py

- 用 `pathlib` + `shutil` 取代 bash 的 `cp`、`mkdir -p`
- 用 Python regex 取代 `awk` 做 YAML frontmatter 處理
- `_strip_frontmatter()` / `_add_frontmatter()` 函式

### config.py 平台偵測

```python
import platform
_IS_MAC = platform.system() == "Darwin"
_IS_WIN = platform.system() == "Windows"
```

三個路徑改為分支：
1. `DAYFLOW_DB` — Mac: `~/Library/...`, Windows: `%APPDATA%/...`, else: `None`
2. `APPLE_PODCAST_TTML_DIR` — Mac: 原值, else: `None`
3. `CLAUDE_MEMORY_DIR` — 動態計算，不再硬編碼 `-Users-dex-dex-agent-os`

### bash → Python 行為差異處理

| 差異 | 解法 |
|------|------|
| exit code 不傳遞 | `sys.exit(result.returncode)` |
| Ctrl+C 印 traceback | `except KeyboardInterrupt: sys.exit(130)` |
| `.env` 載入 | `python-dotenv`（格式為純 `KEY=VALUE`，相容） |

## 測試策略

- `test_agent_cli.py` — 路由正確性、未知指令 exit 1、.env 載入
- `test_sync.py` — 檔案複製、frontmatter 加/去、idempotent
- `test_config_platform.py` — 用 `@patch("platform.system")` 模擬各平台路徑

## 不動的部分

- 所有 `scripts/generators/*.py` — 已用 pathlib，跨平台
- 所有 `scripts/collectors/*.py` — 同上
- `scripts/lib/file_utils.py`、`llm.py`、`google_api.py` — 已跨平台
- `canonical/`、`.agent/`、`.cursor/`、`.claude/` — 不動
- `.env`、`config/` — 不動
