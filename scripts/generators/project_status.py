#!/usr/bin/env python3
"""Project Status — 讀取專案資料 → LLM 更新 STATUS.md"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib.config import PROJECTS_SOFTWARE_DIR, PROJECTS_PRODUCTS_DIR, TEMPLATES_DIR
from lib.file_utils import read_text, today_str, write_text
from lib.llm import ask_claude

# ── 常數 ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
你是 Dex 的個人 AI 代理人，負責更新專案狀態文件。

規則：
- 嚴格依照提供的模板結構輸出
- 只根據提供的原始資料（現有 STATUS、DECISIONS、README、git log）產出內容
- 不要捏造不在資料中的內容
- 使用繁體中文
- 直接輸出 Markdown 內容，不要加程式碼區塊包裹
- 保持精簡扼要，條列優先
"""

PROJECT_DIRS = {
    "software": PROJECTS_SOFTWARE_DIR,
    "products": PROJECTS_PRODUCTS_DIR,
}


# ── 工具函式 ──────────────────────────────────────────


def _find_project(
    name: str, project_type: Optional[str] = None
) -> Optional[tuple[Path, str]]:
    """搜尋專案目錄，回傳 (project_dir, type_str) 或 None。"""
    search_types = [project_type] if project_type else ["software", "products"]

    for ptype in search_types:
        base_dir = PROJECT_DIRS[ptype]
        if not base_dir.exists():
            continue
        # 精確比對
        candidate = base_dir / name
        if candidate.is_dir():
            return candidate, ptype
        # 模糊比對：名稱包含關鍵字
        for d in sorted(base_dir.iterdir()):
            if d.is_dir() and name.lower() in d.name.lower():
                return d, ptype

    return None


def _list_projects() -> None:
    """列出所有可用專案。"""
    found = False
    for ptype, base_dir in PROJECT_DIRS.items():
        if not base_dir.exists():
            continue
        dirs = sorted(d.name for d in base_dir.iterdir() if d.is_dir())
        if dirs:
            found = True
            print(f"\n[{ptype}]")
            for name in dirs:
                print(f"  - {name}")

    if not found:
        print("[project-status] 沒有找到任何專案。")


def _get_git_log(project_dir: Path, limit: int = 30) -> str:
    """取得 git log，回傳字串。若專案目錄非 git repo，改用 ROOT_DIR。"""
    project_dir = project_dir.resolve()
    # 判斷 project_dir 是否在獨立 git repo 中
    cwd = project_dir
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            cwd = ROOT_DIR
        else:
            git_root = Path(result.stdout.strip())
            # 如果 git root 就是 ROOT_DIR，用專案名稱篩選 log
            if git_root == ROOT_DIR:
                # 嘗試用 project_dir 相對路徑限制 git log 範圍
                rel = project_dir.relative_to(ROOT_DIR)
                log_result = subprocess.run(
                    ["git", "log", f"--oneline", f"-{limit}", "--", str(rel)],
                    cwd=str(ROOT_DIR),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if log_result.returncode == 0 and log_result.stdout.strip():
                    return log_result.stdout.strip()
                # 若該路徑無 commit，改回全 repo log
                cwd = ROOT_DIR
    except (subprocess.TimeoutExpired, FileNotFoundError):
        cwd = ROOT_DIR

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{limit}"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return ""


def _build_prompt(
    project_name: str,
    project_type: str,
    template: str,
    existing_status: str,
    decisions: str,
    readme: str,
    git_log: str,
) -> str:
    """組裝送給 LLM 的提示。"""
    prompt = f"""\
請根據以下資料，更新「{project_name}」的專案狀態文件。

## 模板格式（請嚴格遵循此結構）
{template}

## 專案資訊
- 名稱：{project_name}
- 類型：{project_type}
- 更新日期：{today_str()}
"""

    if existing_status:
        prompt += f"""
## 現有 STATUS.md
{existing_status}
"""

    if decisions:
        prompt += f"""
## DECISIONS.md（架構決策紀錄）
{decisions}
"""

    if readme:
        prompt += f"""
## README.md
{readme}
"""

    if git_log:
        prompt += f"""
## 近期 Git Log
{git_log}
"""

    prompt += """
## 輸出要求
- 直接輸出完整的 STATUS.md 內容（Markdown 格式）
- 根據 git log 和現有資料判斷哪些已完成、哪些進行中
- 如果現有 STATUS.md 已有資訊且 git log 無新變化，保留原內容但更新日期
- 不要加 YAML frontmatter，直接從 H1 標題開始
"""
    return prompt


# ── 主程式 ──────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Project Status — 讀取專案資料 → LLM 更新 STATUS.md"
    )
    parser.add_argument(
        "project_name",
        nargs="?",
        default=None,
        help="專案名稱（不給則列出所有專案）",
    )
    parser.add_argument(
        "--type",
        choices=["software", "products"],
        default=None,
        dest="project_type",
        help="限定搜尋範圍（software 或 products）",
    )
    parser.add_argument(
        "--force", action="store_true", help="強制覆蓋，不詢問確認"
    )
    args = parser.parse_args()

    # 若無專案名稱，列出所有專案後離開
    if args.project_name is None:
        print("[project-status] 可用專案：")
        _list_projects()
        return

    # 1. 搜尋專案
    result = _find_project(args.project_name, args.project_type)
    if result is None:
        print(
            f"[project-status] 找不到專案：{args.project_name}",
            file=sys.stderr,
        )
        print("[project-status] 可用專案：")
        _list_projects()
        sys.exit(1)

    project_dir, project_type = result
    project_name = project_dir.name
    status_path = project_dir / "STATUS.md"

    # 2. 確認覆蓋
    if status_path.exists() and not args.force:
        response = (
            input(
                f"[project-status] {status_path.relative_to(ROOT_DIR)} 已存在，覆蓋？(y/N) "
            )
            .strip()
            .lower()
        )
        if response != "y":
            print("[project-status] Cancelled.")
            sys.exit(0)

    # 3. 讀取專案資料
    existing_status = read_text(status_path)
    decisions = read_text(project_dir / "DECISIONS.md")
    readme = read_text(project_dir / "README.md")
    template = read_text(TEMPLATES_DIR / "project-status-template.md")
    git_log = _get_git_log(project_dir)

    # 4. LLM 產出
    print(f"[project-status] Generating status for '{project_name}'...")
    prompt = _build_prompt(
        project_name=project_name,
        project_type=project_type,
        template=template,
        existing_status=existing_status,
        decisions=decisions,
        readme=readme,
        git_log=git_log,
    )
    output = ask_claude(user_prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 5. 寫入
    write_text(status_path, output.strip() + "\n")
    print(
        f"[project-status] Done: {status_path.relative_to(ROOT_DIR)}"
    )


if __name__ == "__main__":
    main()
