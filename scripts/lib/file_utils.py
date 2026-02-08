"""Dex Agent OS — 檔案操作工具"""

from datetime import datetime
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


def work_log_path(date_str: str) -> Path:
    """回傳指定日期的 work-log 路徑。"""
    from .config import WORK_LOGS_DIR

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return WORK_LOGS_DIR / dt.strftime("%Y") / dt.strftime("%m") / f"{date_str}.md"


def journal_path(date_str: str) -> Path:
    """回傳指定日期的精煉日記路徑。"""
    from .config import JOURNAL_DIR

    return JOURNAL_DIR / f"{date_str}.md"
