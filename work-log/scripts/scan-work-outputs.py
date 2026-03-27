#!/usr/bin/env python3
"""掃描當日的會議筆記、諮詢紀錄、專案狀態更新，輸出結構化 Markdown 參考清單。

供 /work-log skill 在 Step 3.9 呼叫，結果併入 L1 工作日誌。

Usage:
    python3 scan-work-outputs.py [--date YYYY-MM-DD]
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── 路徑設定 ──────────────────────────────────────────

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
from scripts.lib.config import (  # noqa: E402
    MEETINGS_DIR,
    CONSULTATIONS_DIR,
    PROJECTS_SOFTWARE_DIR,
    PROJECTS_PRODUCTS_DIR,
    WORK_REPOS,
)


# ── 工具函式 ──────────────────────────────────────────


def _parse_frontmatter(filepath: Path) -> dict:
    """讀取 Markdown 檔案的 YAML frontmatter，回傳 dict。"""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}

    if not text.startswith("---"):
        return {}

    end_idx = text.find("---", 3)
    if end_idx == -1:
        return {}

    fm_block = text[3:end_idx].strip()
    result = {}
    for line in fm_block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _scan_meetings(target_date: str) -> list[dict]:
    """掃描 200_Work/meetings/{target_date}-*/ 下的 notes.md。"""
    if not MEETINGS_DIR.exists():
        return []

    results = []
    for d in sorted(MEETINGS_DIR.iterdir()):
        if not d.is_dir() or not d.name.startswith(target_date):
            continue
        notes = d / "notes.md"
        if not notes.exists():
            continue
        fm = _parse_frontmatter(notes)
        results.append({
            "title": fm.get("title", d.name),
            "attendees": fm.get("attendees", ""),
            "source": fm.get("source", ""),
            "path": str(notes.relative_to(ROOT_DIR)),
        })
    return results


def _scan_consultations(target_date: str) -> list[dict]:
    """掃描 200_Work/consultations/{target_date}-*/ 下的 notes.md。"""
    if not CONSULTATIONS_DIR.exists():
        return []

    results = []
    for d in sorted(CONSULTATIONS_DIR.iterdir()):
        if not d.is_dir() or not d.name.startswith(target_date):
            continue
        notes = d / "notes.md"
        if not notes.exists():
            continue
        fm = _parse_frontmatter(notes)
        results.append({
            "title": fm.get("title", d.name),
            "person": fm.get("person", ""),
            "direction": fm.get("direction", ""),
            "path": str(notes.relative_to(ROOT_DIR)),
        })
    return results


def _scan_project_status(target_date: str) -> list[dict]:
    """掃描 400_Projects/ 下當日有更新的 STATUS.md。"""
    results = []
    for ptype, base_dir in [("software", PROJECTS_SOFTWARE_DIR), ("products", PROJECTS_PRODUCTS_DIR)]:
        if not base_dir.exists():
            continue
        for d in sorted(base_dir.iterdir()):
            if not d.is_dir():
                continue
            status_file = d / "STATUS.md"
            if not status_file.exists():
                continue
            # 用檔案修改時間判斷是否當日更新
            mtime = datetime.fromtimestamp(status_file.stat().st_mtime)
            if mtime.strftime("%Y-%m-%d") == target_date:
                results.append({
                    "project": d.name,
                    "type": ptype,
                    "path": str(status_file.relative_to(ROOT_DIR)),
                })
    return results


def _scan_git_logs(target_date: str) -> list[dict]:
    """掃描 WORK_REPOS 中每個 repo 的 git log。"""
    results = []
    next_date = (datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    for repo_path in WORK_REPOS:
        if not repo_path.exists() or not (repo_path / ".git").exists():
            continue
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--all",
                 f"--since={target_date}T00:00:00",
                 f"--until={next_date}T00:00:00"],
                capture_output=True, text=True, timeout=10,
                cwd=str(repo_path),
            )
            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().splitlines()
                results.append({
                    "repo": repo_path.name,
                    "path": str(repo_path),
                    "commits": commits,
                })
        except (subprocess.TimeoutExpired, OSError):
            continue
    return results


def _format_output(meetings: list, consultations: list, projects: list, git_logs: list = None) -> str:
    """將掃描結果格式化為 Markdown。"""
    git_logs = git_logs or []
    lines = ["# 當日工作紀錄產出\n"]

    if not meetings and not consultations and not projects and not git_logs:
        lines.append("該日無會議筆記、諮詢紀錄、專案狀態更新或 git commit。\n")
        return "\n".join(lines)

    if meetings:
        lines.append("## 會議筆記")
        lines.append("| 標題 | 與會者 | 來源 | 路徑 |")
        lines.append("|------|--------|------|------|")
        for m in meetings:
            lines.append(f"| {m['title']} | {m['attendees'] or '—'} | {m['source'] or '—'} | `{m['path']}` |")
        lines.append("")

    if consultations:
        lines.append("## 諮詢紀錄")
        lines.append("| 主題 | 對象 | 方向 | 路徑 |")
        lines.append("|------|------|------|------|")
        for c in consultations:
            direction_label = "提供" if c["direction"] == "giving" else "接受" if c["direction"] == "receiving" else c["direction"]
            lines.append(f"| {c['title']} | {c['person'] or '—'} | {direction_label or '—'} | `{c['path']}` |")
        lines.append("")

    if projects:
        lines.append("## 專案狀態更新")
        lines.append("| 專案 | 類型 | 路徑 |")
        lines.append("|------|------|------|")
        for p in projects:
            lines.append(f"| {p['project']} | {p['type']} | `{p['path']}` |")
        lines.append("")

    if git_logs:
        lines.append("## Git Commit 紀錄")
        for repo in git_logs:
            lines.append(f"### {repo['repo']} (`{repo['path']}`)")
            for commit in repo["commits"]:
                lines.append(f"- {commit}")
            lines.append("")

    return "\n".join(lines)


# ── 主程式 ──────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="掃描當日工作紀錄產出（會議/諮詢/專案狀態）")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="目標日期 YYYY-MM-DD（預設今天）",
    )
    args = parser.parse_args()

    meetings = _scan_meetings(args.date)
    consultations = _scan_consultations(args.date)
    projects = _scan_project_status(args.date)
    git_logs = _scan_git_logs(args.date)

    output = _format_output(meetings, consultations, projects, git_logs)
    print(output)


if __name__ == "__main__":
    main()
