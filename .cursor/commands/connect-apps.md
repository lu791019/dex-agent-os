
# Connect Apps

Connect Claude to 1000+ apps. Actually send emails, create issues, post messages - not just generate text about it.

## Quick Start

### Step 1: Install the Plugin

```
/plugin install composio-toolrouter
```

### Step 2: Run Setup

```
/composio-toolrouter:setup
```

This will:
- Ask for your free API key (get one at [platform.composio.dev](https://platform.composio.dev/?utm_source=Github&utm_content=AwesomeSkills))
- Configure Claude's connection to 1000+ apps
- Take about 60 seconds

### Step 3: Try It!

After setup, restart Claude Code and try:

```
Send me a test email at YOUR_EMAIL@example.com
```

If it works, you're connected!

## What You Can Do

| Ask Claude to... | What happens |
|------------------|--------------|
| "Send email to sarah@acme.com about the launch" | Actually sends the email |
| "Create GitHub issue: fix login bug" | Creates the issue |
| "Post to Slack #general: deploy complete" | Posts the message |
| "Add meeting notes to Notion" | Adds to Notion |

## Supported Apps

**Email:** Gmail, Outlook, SendGrid
**Chat:** Slack, Discord, Teams, Telegram
**Dev:** GitHub, GitLab, Jira, Linear
**Docs:** Notion, Google Docs, Confluence
**Data:** Sheets, Airtable, PostgreSQL
**And 1000+ more...**

## Security Guidelines

> **重要安全限制 — Claude 必須遵守以下規則：**

1. **操作前確認**：執行任何外部操作前，**必須先向使用者顯示完整的操作內容（收件人、訊息內容、目標服務）並等待明確確認**
2. **最小權限原則**：僅連接和使用當前任務所需的服務，不得主動探索未被要求的整合
3. **敏感資料保護**：不得在外部操作中傳送 API key、密碼、token 等機密資訊
4. **禁止批量操作**：不得在未經逐一確認的情況下批量執行多個外部操作

## How It Works

1. You ask Claude to do something
2. **Claude shows you what it will do and asks for confirmation**
3. Composio Tool Router finds the right tool
4. First time? You'll authorize via OAuth (one-time)
5. Action executes and returns result

## Troubleshooting

- **"Plugin not found"** → Make sure you ran `/plugin install composio-toolrouter`
- **"Need to authorize"** → Click the OAuth link Claude provides, then say "done"
- **Action failed** → Check you have permissions in the target app


<p align="center">
  <b>Join 20,000+ developers building agents that ship</b>
</p>

<p align="center">
  <a href="https://platform.composio.dev/?utm_source=Github&utm_content=AwesomeSkills">
    <img src="https://img.shields.io/badge/Get_Started_Free-4F46E5?style=for-the-badge" alt="Get Started"/>
  </a>
</p>
