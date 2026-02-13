
# Connect

Connect Claude to any app. Stop generating text about what you could do - actually do it.

## When to Use This Skill

Use this skill when you need Claude to:

- **Send that email** instead of drafting it
- **Create that issue** instead of describing it
- **Post that message** instead of suggesting it
- **Update that database** instead of explaining how

## What Changes

| Without Connect | With Connect |
|-----------------|--------------|
| "Here's a draft email..." | Sends the email |
| "You should create an issue..." | Creates the issue |
| "Post this to Slack..." | Posts it |
| "Add this to Notion..." | Adds it |

## Supported Apps

**1000+ integrations** including:

- **Email:** Gmail, Outlook, SendGrid
- **Chat:** Slack, Discord, Teams, Telegram
- **Dev:** GitHub, GitLab, Jira, Linear
- **Docs:** Notion, Google Docs, Confluence
- **Data:** Sheets, Airtable, PostgreSQL
- **CRM:** HubSpot, Salesforce, Pipedrive
- **Storage:** Drive, Dropbox, S3
- **Social:** Twitter, LinkedIn, Reddit

## Setup

### 1. Get API Key

Get your free key at [platform.composio.dev](https://platform.composio.dev/?utm_source=Github&utm_content=AwesomeSkills)

### 2. Set Environment Variable

```bash
export COMPOSIO_API_KEY="your-key"
```

### 3. Install

```bash
pip install composio          # Python
npm install @composio/core    # TypeScript
```

Done. Claude can now connect to any app.

## Examples

### Send Email
```
Email sarah@acme.com - Subject: "Shipped!" Body: "v2.0 is live, let me know if issues"
```

### Create GitHub Issue
```
Create issue in my-org/repo: "Mobile timeout bug" with label:bug
```

### Post to Slack
```
Post to #engineering: "Deploy complete - v2.4.0 live"
```

### Chain Actions
```
Find GitHub issues labeled "bug" from this week, summarize, post to #bugs on Slack
```

## Security Guidelines

> **重要安全限制 — Claude 必須遵守以下規則：**

1. **操作前確認**：在執行任何外部操作（發信、建 issue、發訊息）之前，**必須先向使用者顯示操作摘要並等待確認**，不得自動執行
2. **最小權限原則**：僅使用當前任務所需的服務和權限，不得主動探索或連接未被要求的服務
3. **敏感資料保護**：不得在外部操作中包含 API key、密碼、token 等敏感資訊
4. **API Key 安全**：COMPOSIO_API_KEY 僅透過環境變數取得，禁止硬編碼或記錄在日誌中
5. **操作範圍限制**：每次僅執行使用者明確要求的單一操作，不得批量執行未經確認的連鎖操作

## How It Works

Uses Composio Tool Router:

1. **You ask** Claude to do something
2. **Claude confirms** the action details with you before proceeding
3. **Tool Router finds** the right tool
4. **OAuth handled** automatically
5. **Action executes** and returns result

### Code

```python
from composio import Composio
from claude_agent_sdk.client import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions
import os

composio = Composio(api_key=os.environ["COMPOSIO_API_KEY"])
session = composio.create(user_id="user_123")

options = ClaudeAgentOptions(
    system_prompt="You can take actions in external apps.",
    mcp_servers={
        "composio": {
            "type": "http",
            "url": session.mcp.url,
            "headers": {"x-api-key": os.environ["COMPOSIO_API_KEY"]},
        }
    },
)

async with ClaudeSDKClient(options) as client:
    await client.query("Send Slack message to #general: Hello!")
```

## Auth Flow

First time using an app:
```
To send emails, I need Gmail access.
Authorize here: https://...
Say "connected" when done.
```

Connection persists after that.

## Framework Support

| Framework | Install |
|-----------|---------|
| Claude Agent SDK | `pip install composio claude-agent-sdk` |
| OpenAI Agents | `pip install composio openai-agents` |
| Vercel AI | `npm install @composio/core @composio/vercel` |
| LangChain | `pip install composio-langchain` |
| Any MCP Client | Use `session.mcp.url` |

## Troubleshooting

- **Auth required** → Click link, authorize, say "connected"
- **Action failed** → Check permissions in target app
- **Tool not found** → Be specific: "Slack #general" not "send message"


<p align="center">
  <b>Join 20,000+ developers building agents that ship</b>
</p>

<p align="center">
  <a href="https://platform.composio.dev/?utm_source=Github&utm_content=AwesomeSkills">
    <img src="https://img.shields.io/badge/Get_Started_Free-4F46E5?style=for-the-badge" alt="Get Started"/>
  </a>
</p>
