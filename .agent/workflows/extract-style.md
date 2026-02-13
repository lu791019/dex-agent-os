---
description: "Extract Style — 提取風格 DNA"
---

# Extract Style — 提取風格 DNA

從真實範例中提取抽象寫作模式，產出風格 DNA 文件，讓 AI 產出的內容「像你寫的」。

## 觸發方式
- 指令：`./bin/agent extract-style <channel>`
- 指令：`./bin/agent extract-style <channel> --force`

## 輸入來源
1. **範例文章**：`800_System/references/examples/<channel>/*.md`
2. 每篇範例格式：
   ```markdown
   ## 元資料
   - 發布日期：YYYY-MM-DD
   - 互動數據：❤️ N 💬 N 🔄 N
   - 表現評估：高互動 / 中互動 / 低互動

   ## 原文
   （完整貼文內容）
   ```

## 處理邏輯
1. 讀取指定頻道的所有範例（至少需要 5 篇）
2. LLM 分析七個維度：
   - **結構模式**：常見的段落結構
   - **開場 Hook 模式**：反差型、提問型、宣告型等
   - **語氣特徵**：精準度、口語比例、用字習慣
   - **CTA / 收尾模式**：金句收尾、開放提問、行動呼籲
   - **長度 / 格式**：典型字數、段落數、標點習慣
   - **高互動特徵**：從互動數據回推的成功模式
   - **禁忌**：應避免的模式
3. 產出結構化的 DNA 文件

## 輸出
- 路徑：`800_System/references/style-dna/<channel>-dna.md`
- 存在時：提示覆蓋或使用 --force

## DNA 的有機生長
```
初始 → 放 10 篇範例 → extract-style → v1 DNA
用了一個月 → 加入新貼文 → 重跑 → v2 DNA
持續 → DNA 隨你的風格演化而演化
```

## 目前支援的頻道
- `threads` — Threads 貼文
- 未來：`facebook`、`blog`、`newsletter`、`podcast`、`short-video`、`film-review`
