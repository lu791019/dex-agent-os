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

# 內容管線（510/520/530）
INSIGHTS_DIR = ROOT_DIR / "510_Insights"
TOPICS_DIR = ROOT_DIR / "520_Topics"
CHANNELS_DIR = ROOT_DIR / "530_Channels"
THREADS_DIR = CHANNELS_DIR / "threads"
FACEBOOK_DIR = CHANNELS_DIR / "facebook"
BLOG_DIR = CHANNELS_DIR / "blog"
NEWSLETTER_DIR = CHANNELS_DIR / "newsletter"
SHORT_VIDEO_DIR = CHANNELS_DIR / "short-video"
FILM_REVIEWS_DIR = CHANNELS_DIR / "film-reviews"
PODCAST_CONTENT_DIR = CHANNELS_DIR / "podcast"
PRESENTATIONS_DIR = CHANNELS_DIR / "presentations"

# 系統
STYLE_DNA_DIR = ROOT_DIR / "800_System" / "references" / "style-dna"
EXAMPLES_DIR = ROOT_DIR / "800_System" / "references" / "examples"

# work-log 腳本（已合併進 agent-os）
WORKLOG_SCRIPTS_DIR = ROOT_DIR / "work-log" / "scripts"
WORKLOG_TEMPLATES_DIR = ROOT_DIR / "work-log" / "templates"

# 每日素材池
DAILY_POOL_DIR = ROOT_DIR / "000_Inbox" / "daily"

# 知識萃取
INBOX_IDEAS_DIR = ROOT_DIR / "000_Inbox" / "ideas"
LIFE_PERSONAL_DIR = ROOT_DIR / "600_Life" / "personal" / "reflections"
KNOWLEDGE_DIR = ROOT_DIR / "800_System" / "knowledge"
CLAUDE_MEMORY_DIR = Path.home() / ".claude" / "projects" / "-Users-dex-dex-agent-os" / "memory"

# Threads API
THREADS_TOKEN_PATH = ROOT_DIR / "config" / ".threads-token"

# Podcast & YouTube
PODCAST_EPISODES_DIR = ROOT_DIR / "300_Learning" / "podcasts" / "episodes"
PODCAST_WEEKLY_DIR = ROOT_DIR / "300_Learning" / "podcasts" / "weekly"
PODCAST_TRANSCRIPTS_DIR = ROOT_DIR / "300_Learning" / "podcasts" / "transcripts"
YOUTUBE_DIR = ROOT_DIR / "300_Learning" / "youtube"

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

# 工作（會議 & 諮詢）
MEETINGS_DIR = ROOT_DIR / "200_Work" / "meetings"
CONSULTATIONS_DIR = ROOT_DIR / "200_Work" / "consultations"

# 專案 & 產品
PROJECTS_SOFTWARE_DIR = ROOT_DIR / "400_Projects" / "software"
PROJECTS_PRODUCTS_DIR = ROOT_DIR / "400_Projects" / "products"

# Podwise 串接（Notion + Readwise）
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PODWISE_DB_ID = os.getenv("NOTION_PODWISE_DB_ID", "")
READWISE_TOKEN = os.getenv("READWISE_TOKEN", "")

# Fireflies.ai
FIREFLIES_API_KEY = os.getenv("FIREFLIES_API_KEY", "")

# 多 Repo 工作日誌追蹤（逗號分隔的絕對路徑）
WORK_REPOS = [
    Path(p.strip()) for p in os.getenv("WORK_REPOS", "").split(",") if p.strip()
]
if not WORK_REPOS:
    WORK_REPOS = [ROOT_DIR]
