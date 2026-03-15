#!/usr/bin/env python3
"""Dex Agent OS — Cross-platform CLI entry point"""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# 載入 .env
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    # 手動載入 .env（fallback，不需要 python-dotenv）
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

# 指令 → 腳本路徑映射
COMMANDS = {
    "journal": "scripts/generators/daily_journal.py",
    "dayflow": "scripts/generators/daily_dayflow_digest.py",
    "extract": "scripts/extractors/journal_knowledge_extract.py",
    "collect-threads": "scripts/collectors/threads_collector.py",
    "extract-style": "scripts/analyzers/extract_style.py",
    "topic-create": "scripts/generators/topic_create.py",
    "topic-to-thread": "scripts/generators/topic_to_thread.py",
    "topic-to-fb": "scripts/generators/topic_to_fb.py",
    "topic-to-blog": "scripts/generators/topic_to_blog.py",
    "topic-to-short-video": "scripts/generators/topic_to_short_video.py",
    "film-review": "scripts/generators/film_review.py",
    "youtube-add": "scripts/collectors/youtube_transcript.py",
    "learning-note": "scripts/generators/learning_note.py",
    "readwise-sync": "scripts/collectors/readwise_sync.py",
    "rss-sync": "scripts/collectors/rss_sync.py",
    "anybox-sync": "scripts/collectors/anybox_sync.py",
    "gmail-sync": "scripts/collectors/gmail_sync.py",
    "daily-digest": "scripts/generators/daily_digest.py",
    "podcast-add": "scripts/collectors/podcast_transcript.py",
    "podcast-digest": "scripts/generators/podcast_digest.py",
    "weekly-review": "scripts/generators/weekly_review.py",
    "weekly-newsletter": "scripts/generators/weekly_newsletter.py",
    "project-status": "scripts/generators/project_status.py",
    "meeting-notes": "scripts/generators/meeting_notes.py",
    "consultation-notes": "scripts/generators/consultation_notes.py",
    "classroom-sync": "scripts/collectors/classroom_sync.py",
    "fireflies-sync": "scripts/collectors/fireflies_sync.py",
}

SYNC_ALL_SCRIPTS = [
    "scripts/collectors/readwise_sync.py",
    "scripts/collectors/rss_sync.py",
    "scripts/collectors/anybox_sync.py",
    "scripts/collectors/gmail_sync.py",
]

HELP_TEXT = """\
Dex Agent OS — CLI

Usage:
  ./bin/agent <command> [options]
  python bin/agent.py <command> [options]

Commands:
  journal [YYYY-MM-DD] [--force]                          產出每日精煉日記（L2）
  dayflow [YYYY-MM-DD] [--force]                          產出 Dayflow 活動摘要日記
  extract [date|all] [--type TYPE] [--force] [--dry-run]  萃取日記知識
  collect-threads [--limit N] [--since DATE] [--force]    自動抓取 Threads 文章
  extract-style <channel> [--force]                       提取風格 DNA
  topic-create [insight-file|--title "..."]               從 insight 建立主題
  topic-to-thread <topic-slug> [--force]                  主題 → Threads 草稿
  topic-to-fb <topic-slug> [--force]                      主題 → Facebook 貼文草稿
  topic-to-blog <topic-slug> [--force]                    主題 → 部落格文章草稿
  topic-to-short-video <topic-slug> [--force]             主題 → 短影音腳本
  film-review --title "..." [--notes "..."] [--rating N]  電影 → 影評
  learning-note --url URL [--type TYPE] [--force]         URL → 學習筆記
  readwise-sync [--category CAT] [--latest N] [--force]   Readwise 批次匯入
  rss-sync [--feed URL] [--opml FILE] [--latest N]        RSS 批次匯入
  anybox-sync [--tag TAG] [--starred] [--latest N]        Anybox 書籤批次匯入
  gmail-sync [--label X] [--from ADDR] [--latest N]       Gmail 電子報批次匯入
  youtube-add "URL" [--force] [--date YYYY-MM-DD]         YouTube → 學習筆記
  podcast-add --transcript FILE --title "..." [--force]   Podcast → episode 筆記
  daily-digest [YYYY-MM-DD] [--today] [--send] [--force]  每日學習消化報告
  podcast-digest [YYYY-MM-DD] [--pptx] [--force]          週度消化報告
  weekly-review [YYYY-MM-DD] [--force]                    產出個人週回顧
  weekly-newsletter [YYYY-MM-DD] [--type TYPE] [--force]  產出電子報草稿
  meeting-notes --title "..." [輸入來源] [--force]        多來源 → 會議筆記
  consultation-notes --title "..." --person "..." [...]   多來源 → 諮詢紀錄
  project-status [專案名] [--type software|products]      專案狀態更新
  classroom-sync [--courses] [--active-only]              Google Classroom 同步
  fireflies-sync [--list] [--latest N] [--force]          Fireflies.ai 逐字稿同步
  sync                                                    跨平台同步 canonical → IDE
  sync-all [--latest N] [--force]                         一鍵批次匯入
  help                                                    顯示此說明
"""


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    if command in ("help", "--help", "-h"):
        print(HELP_TEXT)
        return

    if command == "sync":
        result = subprocess.run(
            [sys.executable, str(ROOT_DIR / "bin" / "sync.py"), *sys.argv[2:]]
        )
        sys.exit(result.returncode)

    if command == "sync-all":
        print("[sync-all] 開始批次匯入...")
        for script in SYNC_ALL_SCRIPTS:
            result = subprocess.run(
                [sys.executable, str(ROOT_DIR / script),
                 "--reader", "--latest", "10", *sys.argv[2:]]
            )
            if result.returncode != 0:
                sys.exit(result.returncode)
        print("[sync-all] 批次匯入完成")
        return

    script = COMMANDS.get(command)
    if not script:
        print(f"Unknown command: {command}")
        print("Run './bin/agent help' or 'python bin/agent.py help' for usage.")
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(ROOT_DIR / script), *sys.argv[2:]]
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
