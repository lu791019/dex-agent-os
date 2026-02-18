"""Dex Agent OS — 路徑與常數設定"""

import os
from pathlib import Path

# 專案根目錄
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 工作日誌（L0/L1 輸出位置，保持在 ~/work-logs/）
WORK_LOGS_DIR = Path.home() / "work-logs"

# 精煉日記（L2 輸出位置）
JOURNAL_DIR = ROOT_DIR / "100_Journal" / "daily"
WEEKLY_DIR = ROOT_DIR / "100_Journal" / "weekly"

# 模板
TEMPLATES_DIR = ROOT_DIR / "800_System" / "templates"

# 規則
RULES_DIR = ROOT_DIR / "canonical" / "rules"

# 內容
CONTENT_DIR = ROOT_DIR / "500_Content"
TOPICS_DIR = CONTENT_DIR / "topics"

# 系統
STYLE_DNA_DIR = ROOT_DIR / "800_System" / "references" / "style-dna"
EXAMPLES_DIR = ROOT_DIR / "800_System" / "references" / "examples"

# work-log 腳本（已合併進 agent-os）
WORKLOG_SCRIPTS_DIR = ROOT_DIR / "work-log" / "scripts"
WORKLOG_TEMPLATES_DIR = ROOT_DIR / "work-log" / "templates"

# 知識萃取
INBOX_IDEAS_DIR = ROOT_DIR / "000_Inbox" / "ideas"
CONTENT_INSIGHTS_DIR = ROOT_DIR / "500_Content" / "insights"
LIFE_PERSONAL_DIR = ROOT_DIR / "600_Life" / "personal" / "reflections"
KNOWLEDGE_DIR = ROOT_DIR / "800_System" / "knowledge"
CLAUDE_MEMORY_DIR = Path.home() / ".claude" / "projects" / "-Users-dex-dex-agent-os" / "memory"

# Threads API
THREADS_TOKEN_PATH = ROOT_DIR / "config" / ".threads-token"

# 電子報
NEWSLETTER_DRAFTS_DIR = CONTENT_DIR / "newsletter" / "drafts"
NEWSLETTER_ARCHIVE_DIR = CONTENT_DIR / "newsletter" / "archive"

# Podcast & YouTube
PODCAST_EPISODES_DIR = ROOT_DIR / "300_Learning" / "podcasts" / "episodes"
PODCAST_WEEKLY_DIR = ROOT_DIR / "300_Learning" / "podcasts" / "weekly"
PODCAST_TRANSCRIPTS_DIR = ROOT_DIR / "300_Learning" / "podcasts" / "transcripts"
YOUTUBE_DIR = ROOT_DIR / "300_Learning" / "youtube"
PRESENTATIONS_DIR = CONTENT_DIR / "presentations"

# Apple Podcast TTML 快取
APPLE_PODCAST_TTML_DIR = (
    Path.home()
    / "Library"
    / "Group Containers"
    / "243LU875E5.groups.com.apple.podcasts"
    / "Library"
    / "Cache"
    / "Assets"
    / "TTML"
)

# Dayflow
DAYFLOW_DB = Path.home() / "Library" / "Application Support" / "Dayflow" / "chunks.sqlite"

# 學習輸入 & 每日消化
LEARNING_INPUT_DIR = ROOT_DIR / "300_Learning" / "input"
READINGS_DIR = ROOT_DIR / "000_Inbox" / "readings"
DIGEST_DIR = ROOT_DIR / "100_Journal" / "digest"

# Podwise 串接（Notion + Readwise）
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PODWISE_DB_ID = os.getenv("NOTION_PODWISE_DB_ID", "")
READWISE_TOKEN = os.getenv("READWISE_TOKEN", "")
