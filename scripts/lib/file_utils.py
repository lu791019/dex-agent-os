"""Dex Agent OS — 檔案操作工具"""

from datetime import datetime, timedelta
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """確保目錄存在，回傳該路徑。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text(path: Path) -> str:
    """讀取文字檔，檔案不存在時回傳空字串。"""
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def write_text(path: Path, content: str) -> Path:
    """寫入文字檔，自動建立父目錄。"""
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def today_str() -> str:
    """回傳今天日期字串 YYYY-MM-DD。"""
    return datetime.now().strftime("%Y-%m-%d")


def extract_created_date(content: str) -> str:
    """從 frontmatter 取 created 日期，找不到則回傳 today。"""
    import re
    match = re.search(r"^created:\s*(\d{4}-\d{2}-\d{2})", content, re.MULTILINE)
    return match.group(1) if match else today_str()


def week_date_range(date_str: str = None) -> tuple[str, str, int, int]:
    """回傳 (week_start_mon, week_end_sun, iso_week, week_of_month)。"""
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now()
    mon = dt - timedelta(days=dt.isoweekday() - 1)
    sun = mon + timedelta(days=6)
    iso_week = dt.isocalendar()[1]
    week_of_month = (dt.day - 1) // 7 + 1
    return mon.strftime("%Y-%m-%d"), sun.strftime("%Y-%m-%d"), iso_week, week_of_month


def newsletter_type_for_week(week_of_month: int) -> str:
    """根據月內週數自動選擇電子報類型。"""
    types = {1: "curated", 2: "deep-dive", 3: "mixed"}
    return types.get(week_of_month, "monthly-reflection")


def work_log_path(date_str: str) -> Path:
    """回傳指定日期的 work-log 路徑。"""
    from .config import WORK_LOGS_DIR

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return WORK_LOGS_DIR / dt.strftime("%Y") / dt.strftime("%m") / f"{date_str}.md"


def journal_path(date_str: str) -> Path:
    """回傳指定日期的精煉日記路徑。"""
    from .config import JOURNAL_DIR

    return JOURNAL_DIR / f"{date_str}.md"
