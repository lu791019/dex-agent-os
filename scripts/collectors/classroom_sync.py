#!/usr/bin/env python3
"""Classroom Sync — Google Classroom 課程、公告、作業批次匯入

使用方式（教師端）：
  ./bin/agent classroom-sync --courses                           # 列出所有課程
  ./bin/agent classroom-sync --courses --active-only             # 僅列出進行中課程
  ./bin/agent classroom-sync --courses --student-name "王小明"   # 搜尋含特定學生名的課程
  ./bin/agent classroom-sync --course-id ID --announcements      # 匯入課程公告
  ./bin/agent classroom-sync --course-id ID --coursework         # 匯入作業 + 學生繳交狀態
  ./bin/agent classroom-sync --course-id ID --announcements --latest 5  # 最新 5 則公告

  公告輸出：200_Work/meetings/YYYY-MM-DD-classroom-announcement-<slug>/notes.md
  作業輸出：200_Work/consultations/YYYY-MM-DD-classroom-coursework-<slug>/notes.md

  需要：
    pip install google-auth google-auth-oauthlib google-api-python-client
    GCP 啟用 Google Classroom API + OAuth scope 加入 classroom.courses.readonly 等
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import MEETINGS_DIR, CONSULTATIONS_DIR
from lib.file_utils import ensure_dir, today_str, write_text


# ── Google Classroom API ─────────────────────────────

def _get_classroom_service():
    """取得 Google Classroom API service，使用 google_api.py 的 OAuth。"""
    try:
        from lib.google_api import authenticate
    except ImportError:
        print("[classroom-sync] 無法載入 google_api 模組", file=sys.stderr)
        return None

    creds = authenticate()
    if not creds:
        return None

    try:
        from googleapiclient.discovery import build
        return build("classroom", "v1", credentials=creds)
    except Exception as e:
        print(f"[classroom-sync] Classroom API 建立失敗：{e}", file=sys.stderr)
        return None


# ── 工具 ─────────────────────────────────────────────

def _slugify(text: str) -> str:
    """標題轉 slug（檔名安全）。"""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60].strip("-")


def _submission_state_label(state: str) -> str:
    """學生繳交狀態轉中文標籤。"""
    mapping = {
        "NEW": "未開始",
        "CREATED": "已建立",
        "TURNED_IN": "已繳交",
        "RETURNED": "已退回",
        "RECLAIMED_BY_STUDENT": "學生收回",
    }
    return mapping.get(state, state)


# ── 列出課程 ─────────────────────────────────────────

def list_courses(service, active_only: bool = False, student_name: str | None = None):
    """列出教師的所有課程。

    Args:
        service: Classroom API service
        active_only: 僅顯示 ACTIVE 課程
        student_name: 篩選課程名稱中包含此字串的課程
    """
    try:
        results = service.courses().list(pageSize=100).execute()
        courses = results.get("courses", [])
    except Exception as e:
        print(f"[classroom-sync] 取得課程失敗：{e}", file=sys.stderr)
        return

    if not courses:
        print("[classroom-sync] 沒有找到任何課程。")
        print("  確認你的 Google 帳號有 Google Classroom 教師身份。")
        return

    # 篩選
    if active_only:
        courses = [c for c in courses if c.get("courseState") == "ACTIVE"]

    if student_name:
        keyword = student_name.lower()
        courses = [c for c in courses if keyword in c.get("name", "").lower()]

    if not courses:
        print("[classroom-sync] 篩選後沒有符合條件的課程。")
        return

    print(f"\n[classroom-sync] 找到 {len(courses)} 門課程：\n")
    for i, c in enumerate(courses, 1):
        state = c.get("courseState", "?")
        name = c.get("name", "Untitled")
        section = c.get("section", "")
        course_id = c.get("id", "?")
        section_label = f" ({section})" if section else ""
        print(f"  {i:2d}. [{state}] {name}{section_label}")
        print(f"      ID: {course_id}")

    print(f"\n使用 --course-id <ID> --announcements 或 --coursework 匯入課程內容")


# ── 公告 ─────────────────────────────────────────────

def fetch_announcements(service, course_id: str, latest: int = 10):
    """取得課程公告並存檔。

    Args:
        service: Classroom API service
        course_id: 課程 ID
        latest: 最多取幾則（預設 10）
    """
    try:
        results = service.courses().announcements().list(
            courseId=course_id, pageSize=latest, orderBy="updateTime desc"
        ).execute()
        announcements = results.get("announcements", [])
    except Exception as e:
        print(f"[classroom-sync] 取得公告失敗：{e}", file=sys.stderr)
        return

    if not announcements:
        print(f"[classroom-sync] 課程 {course_id} 沒有公告。")
        return

    # 取得課程名稱
    course_name = _get_course_name(service, course_id)

    print(f"[classroom-sync] 找到 {len(announcements)} 則公告，開始匯入...")
    ensure_dir(MEETINGS_DIR)
    count = 0

    for ann in announcements:
        text = ann.get("text", "（無內容）")
        created = ann.get("creationTime", "")
        updated = ann.get("updateTime", "")
        creator_id = ann.get("creatorUserId", "")
        ann_id = ann.get("id", "unknown")

        # 日期：取 creationTime 的前 10 碼
        date_str = created[:10] if created else today_str()

        # 標題：取前 40 字做 slug
        title_preview = text[:40].replace("\n", " ").strip()
        slug = _slugify(title_preview) or f"ann-{ann_id}"

        # 輸出路徑
        dir_name = f"{date_str}-classroom-announcement-{slug}"
        output_dir = MEETINGS_DIR / dir_name
        output_path = output_dir / "notes.md"

        if output_path.exists():
            print(f"  SKIP: {dir_name}（已存在）")
            continue

        # 處理附件
        materials = ann.get("materials", [])
        attachments_md = _format_materials(materials)

        content = f"""---
title: "Classroom 公告 — {title_preview}"
source: google-classroom
type: announcement
course: "{course_name}"
course_id: "{course_id}"
announcement_id: "{ann_id}"
created: {created}
updated: {updated}
---

# Classroom 公告

> 課程：{course_name}
> 發布時間：{created}

## 內容

{text}
{attachments_md}
"""
        write_text(output_path, content)
        print(f"  OK: {dir_name}")
        count += 1

    print(f"\n[classroom-sync] 完成：匯入 {count} 則公告")


# ── 作業 + 學生繳交 ──────────────────────────────────

def fetch_coursework(service, course_id: str, latest: int = 10):
    """取得課程作業及學生繳交狀態並存檔。

    Args:
        service: Classroom API service
        course_id: 課程 ID
        latest: 最多取幾個作業（預設 10）
    """
    try:
        results = service.courses().courseWork().list(
            courseId=course_id, pageSize=latest, orderBy="updateTime desc"
        ).execute()
        coursework_list = results.get("courseWork", [])
    except Exception as e:
        print(f"[classroom-sync] 取得作業失敗：{e}", file=sys.stderr)
        return

    if not coursework_list:
        print(f"[classroom-sync] 課程 {course_id} 沒有作業。")
        return

    course_name = _get_course_name(service, course_id)

    print(f"[classroom-sync] 找到 {len(coursework_list)} 份作業，開始匯入...")
    ensure_dir(CONSULTATIONS_DIR)
    count = 0

    for cw in coursework_list:
        title = cw.get("title", "Untitled")
        description = cw.get("description", "（無說明）")
        created = cw.get("creationTime", "")
        updated = cw.get("updateTime", "")
        due_date = cw.get("dueDate", {})
        max_points = cw.get("maxPoints", "")
        state = cw.get("state", "")
        cw_id = cw.get("id", "unknown")

        date_str = created[:10] if created else today_str()
        slug = _slugify(title) or f"cw-{cw_id}"

        dir_name = f"{date_str}-classroom-coursework-{slug}"
        output_dir = CONSULTATIONS_DIR / dir_name
        output_path = output_dir / "notes.md"

        if output_path.exists():
            print(f"  SKIP: {dir_name}（已存在）")
            continue

        # 格式化截止日
        due_str = ""
        if due_date:
            y = due_date.get("year", "")
            m = due_date.get("month", "")
            d = due_date.get("day", "")
            if y and m and d:
                due_str = f"{y}-{int(m):02d}-{int(d):02d}"
                due_time = cw.get("dueTime", {})
                if due_time:
                    h = due_time.get("hours", 0)
                    mi = due_time.get("minutes", 0)
                    due_str += f" {int(h):02d}:{int(mi):02d}"

        # 附件
        materials = cw.get("materials", [])
        attachments_md = _format_materials(materials)

        # 學生繳交狀態
        submissions_md = _fetch_submissions(service, course_id, cw_id)

        points_label = f" / {max_points}" if max_points else ""

        content = f"""---
title: "{title}"
source: google-classroom
type: coursework
course: "{course_name}"
course_id: "{course_id}"
coursework_id: "{cw_id}"
state: "{state}"
max_points: {max_points or '""'}
due: "{due_str}"
created: {created}
updated: {updated}
---

# {title}

> 課程：{course_name}
> 狀態：{state} | 滿分：{max_points or 'N/A'}{points_label}
> 截止：{due_str or '未設定'}
> 建立：{created}

## 作業說明

{description}
{attachments_md}
## 學生繳交狀態

{submissions_md}
"""
        write_text(output_path, content)
        print(f"  OK: {dir_name}")
        count += 1

    print(f"\n[classroom-sync] 完成：匯入 {count} 份作業")


# ── 輔助：學生繳交 ───────────────────────────────────

def _fetch_submissions(service, course_id: str, coursework_id: str) -> str:
    """取得某作業的所有學生繳交狀態，回傳 Markdown 表格。"""
    try:
        results = service.courses().courseWork().studentSubmissions().list(
            courseId=course_id, courseWorkId=coursework_id, pageSize=100
        ).execute()
        submissions = results.get("studentSubmissions", [])
    except Exception as e:
        return f"（取得繳交狀態失敗：{e}）"

    if not submissions:
        return "（尚無學生繳交）"

    lines = ["| 學生 ID | 狀態 | 分數 | 繳交時間 |",
             "|---------|------|------|----------|"]

    for sub in submissions:
        user_id = sub.get("userId", "?")
        state = _submission_state_label(sub.get("state", "?"))
        grade = sub.get("assignedGrade", "")
        grade_str = str(grade) if grade != "" else "-"
        update_time = sub.get("updateTime", "-")

        lines.append(f"| {user_id} | {state} | {grade_str} | {update_time} |")

    return "\n".join(lines)


# ── 輔助：課程名稱 ───────────────────────────────────

def _get_course_name(service, course_id: str) -> str:
    """取得課程名稱，失敗時回傳 course_id。"""
    try:
        course = service.courses().get(id=course_id).execute()
        return course.get("name", course_id)
    except Exception:
        return course_id


# ── 輔助：附件 ───────────────────────────────────────

def _format_materials(materials: list) -> str:
    """將 Classroom materials 格式化為 Markdown 附件區塊。"""
    if not materials:
        return ""

    lines = ["\n## 附件\n"]
    for mat in materials:
        if "driveFile" in mat:
            df = mat["driveFile"].get("driveFile", {})
            title = df.get("title", "未命名檔案")
            url = df.get("alternateLink", "")
            lines.append(f"- [{title}]({url})")
        elif "youtubeVideo" in mat:
            yt = mat["youtubeVideo"]
            title = yt.get("title", "YouTube 影片")
            url = yt.get("alternateLink", "")
            lines.append(f"- [YouTube: {title}]({url})")
        elif "link" in mat:
            lk = mat["link"]
            title = lk.get("title", lk.get("url", "連結"))
            url = lk.get("url", "")
            lines.append(f"- [{title}]({url})")
        elif "form" in mat:
            fm = mat["form"]
            title = fm.get("title", "Google 表單")
            url = fm.get("formUrl", "")
            lines.append(f"- [表單: {title}]({url})")

    return "\n".join(lines) + "\n\n"


# ── 主程式 ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Classroom Sync — Google Classroom 課程、公告、作業匯入（教師端）"
    )

    # 模式選擇
    parser.add_argument("--courses", action="store_true",
                        help="列出所有課程")
    parser.add_argument("--announcements", action="store_true",
                        help="匯入指定課程的公告（需搭配 --course-id）")
    parser.add_argument("--coursework", action="store_true",
                        help="匯入指定課程的作業 + 學生繳交狀態（需搭配 --course-id）")

    # 篩選
    parser.add_argument("--course-id", type=str, default=None,
                        help="指定課程 ID")
    parser.add_argument("--active-only", action="store_true",
                        help="僅列出進行中（ACTIVE）的課程")
    parser.add_argument("--student-name", type=str, default=None,
                        help="依課程名稱關鍵字篩選")
    parser.add_argument("--latest", type=int, default=10,
                        help="最多匯入幾筆（預設 10）")

    args = parser.parse_args()

    # 驗證參數
    if args.announcements or args.coursework:
        if not args.course_id:
            print("[classroom-sync] --announcements 和 --coursework 需要搭配 --course-id <ID>")
            print("  先用 --courses 查看課程清單取得 ID")
            sys.exit(1)

    if not args.courses and not args.announcements and not args.coursework:
        print("[classroom-sync] 請指定操作模式：")
        print("  --courses                          列出課程")
        print("  --course-id ID --announcements     匯入公告")
        print("  --course-id ID --coursework        匯入作業")
        sys.exit(1)

    # 建立 service
    service = _get_classroom_service()
    if not service:
        sys.exit(1)

    # 分發
    if args.courses:
        list_courses(service, active_only=args.active_only, student_name=args.student_name)
    if args.announcements:
        fetch_announcements(service, args.course_id, latest=args.latest)
    if args.coursework:
        fetch_coursework(service, args.course_id, latest=args.latest)


if __name__ == "__main__":
    main()
