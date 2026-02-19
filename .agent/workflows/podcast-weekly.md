---
description: "Podcast Weekly — 每週 Podcast & YouTube 消化"
---

# Podcast Weekly — 每週 Podcast & YouTube 消化

一鍵產出本週的 Podcast & YouTube 消化報告 + 可選簡報。使用繁體中文。

## 觸發方式
- IDE 內：`/podcast-weekly`
- 可選參數：`/podcast-weekly YYYY-MM-DD`（指定日期所在週）
- 可選參數：`/podcast-weekly --pptx`（同時產出簡報）

## 完整流程

```
YouTube 筆記 + Podcast episode 筆記
            ↓
     podcast-digest（週度彙整）
            ↓
    ┌───────┴────────┐
    ▼                ▼
Markdown 週摘要   .pptx 簡報（可選）
```

## 執行步驟

### Step 0：解析參數

- 如果 `$ARGUMENTS` 中包含 YYYY-MM-DD 格式的日期，用它作為目標日期
- 否則用 `date "+%Y-%m-%d"` 取得今天
- 檢查是否包含 `--pptx` 參數

### Step 1：確認本週素材

列出本週已有的 episodes：
```bash
ls 300_Learning/podcasts/episodes/ 300_Learning/youtube/ | grep "$(date range)"
```

如果沒有任何 episode，提醒使用者先用 `youtube-add` 或 `podcast-add` 新增。

### Step 2：產出週度消化報告

```bash
python3 scripts/generators/podcast_digest.py [TARGET_DATE] [--force]
```

- 輸出：`300_Learning/podcasts/weekly/YYYY-Wxx-podcast-digest.md`

**驗證：** 確認輸出檔案存在且非空

### Step 3：簡報產出（可選）

如果使用者要求簡報或在參數中包含 `--pptx`：

```bash
python3 scripts/generators/podcast_digest.py [TARGET_DATE] --pptx [--force]
```

- 輸出 markdown：`530_Channels/presentations/YYYY-Wxx-market-trends.md`
- 可用 `/pptx` skill 轉為 .pptx

### Step 4：產出摘要

```
## 產出總覽

### 週度消化報告
| 檔案 | 說明 |
|------|------|
| 300_Learning/podcasts/weekly/YYYY-Wxx-podcast-digest.md | Podcast & YouTube 週度消化 |

### 簡報（如有）
| 檔案 | 說明 |
|------|------|
| 530_Channels/presentations/YYYY-Wxx-market-trends.md | 簡報結構化內容 |
```

## 注意事項

- **先有 episodes 再做 digest**：如果本週沒有 episode 筆記，digest 品質會大幅下降
- **簡報是 markdown 格式**：產出後可用 `/pptx` skill 轉為 .pptx 檔案
- **不自動 commit**：生成的檔案只寫入磁碟，不自動加入 git
