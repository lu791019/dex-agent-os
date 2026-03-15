
# Developer Growth Analysis

Analyzes your Claude Code chat history (past 24-48 hours), identifies coding patterns and skill gaps, generates a personalized growth report with curated HackerNews resources, and optionally sends it to Slack.

## When to Use

- Review development patterns and habits from recent work
- Identify technical gaps or recurring challenges
- Get curated learning resources tailored to actual work patterns
- Track improvement areas across recent projects

## Security Guidelines

> **重要安全限制 — Claude 必須遵守以下規則：**

1. **資料清洗**：讀取聊天記錄後，**必須先過濾掉任何疑似 API key、密碼、token、憑證的內容**，再進行分析。過濾規則：移除符合 `[A-Za-z0-9_-]{20,}` 模式的疑似金鑰字串
2. **報告預覽**：在發送到 Slack 之前，**必須先在本地顯示完整報告內容，讓使用者確認沒有敏感資訊後再發送**
3. **可選 Slack 發送**：Slack 發送為**可選步驟**，明確詢問使用者「是否要發送到 Slack DMs？」，預設不發送
4. **僅分析模式摘要**：報告中不得引用完整的程式碼片段或對話原文，僅使用技術摘要描述（例如「使用者處理了 TypeScript 型別問題」而非貼出原始程式碼）
5. **專案名稱脫敏**：如果專案名稱包含公司或客戶名稱等敏感資訊，在報告中以代號替代

## Core Workflow

1. **Access Chat History** -- Read `~/.claude/history.jsonl`, filter to past 24-48h, sanitize credentials
2. **Analyze Work Patterns** -- Extract projects, technologies, problem types, challenges, approach patterns
3. **Identify Improvement Areas** -- Find 3-5 specific, evidence-based, actionable, prioritized growth areas
4. **Generate Report** -- Produce structured report: summary, improvements, strengths, action items
5. **Search Learning Resources** -- Use Rube MCP to find relevant HackerNews articles per improvement area
6. **Present Report** -- Display the complete report locally for review
7. **Send to Slack (optional)** -- Only after user explicitly confirms; ask first, default is no

See `references/instructions.md` for full step-by-step details, report template, and example output.

## Reference Files

| File | Contents |
|------|----------|
| `references/instructions.md` | Full instructions (steps 1-7), report template, example usage, tips, quality notes |
