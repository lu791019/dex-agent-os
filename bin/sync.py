#!/usr/bin/env python3
"""Dex Agent OS — Cross-platform sync script

Syncs canonical/ content to .agent/ (Antigravity), .cursor/ (Cursor), .claude/ (Claude Code).
Also syncs global Claude Code skills/commands to Antigravity/Cursor.
"""

import re
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CANONICAL_DIR = ROOT_DIR / "canonical"
AGENT_DIR = ROOT_DIR / ".agent"
CURSOR_DIR = ROOT_DIR / ".cursor"
CLAUDE_DIR = ROOT_DIR / ".claude"

# Claude Code 全域 skills/commands 目錄
HOME = Path.home()
CLAUDE_GLOBAL_SKILLS = HOME / ".claude" / "skills"
CLAUDE_GLOBAL_COMMANDS = HOME / ".claude" / "commands"
AG_GLOBAL_SKILLS = HOME / ".gemini" / "antigravity" / "skills"
AG_GLOBAL_WORKFLOWS = HOME / ".gemini" / "antigravity" / "global_workflows"


def _extract_first_heading(path: Path) -> str:
    """從 Markdown 檔案提取第一個 # 標題"""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _has_frontmatter(text: str) -> bool:
    """檢查是否以 YAML frontmatter 開頭"""
    return text.startswith("---")


def _strip_frontmatter(text: str) -> str:
    """去掉 YAML frontmatter（--- ... ---）"""
    if not text.startswith("---"):
        return text
    # 找到第二個 ---
    end = text.find("---", 3)
    if end == -1:
        return text
    return text[end + 3:].lstrip("\n")


def _add_frontmatter(text: str, description: str) -> str:
    """加上 YAML frontmatter"""
    return f'---\ndescription: "{description}"\n---\n\n{text}'


def _add_cursor_frontmatter(text: str, description: str) -> str:
    """加上 Cursor 格式的 YAML frontmatter（含 alwaysApply）"""
    return f'---\ndescription: "{description}"\nalwaysApply: true\n---\n\n{text}'


def _extract_description_from_frontmatter(text: str) -> str:
    """從 YAML frontmatter 中提取 description 欄位"""
    if not _has_frontmatter(text):
        return ""
    end = text.find("---", 3)
    if end == -1:
        return ""
    frontmatter = text[3:end]
    match = re.search(r'description:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
    return match.group(1) if match else ""


def sync_rules():
    """[1/5] canonical/rules/*.md → .agent/rules/ + .cursor/rules/*.mdc"""
    print("[1/5] 同步 Rules...")

    rules_dir = CANONICAL_DIR / "rules"
    if not rules_dir.exists():
        print("  (無 canonical/rules/ 目錄，跳過)")
        return

    # → Antigravity
    agent_rules = AGENT_DIR / "rules"
    agent_rules.mkdir(parents=True, exist_ok=True)
    for f in sorted(rules_dir.glob("*.md")):
        shutil.copy2(f, agent_rules / f.name)
    print("  ✓ .agent/rules/")

    # → Cursor（加 YAML frontmatter，改副檔名 .mdc）
    cursor_rules = CURSOR_DIR / "rules"
    cursor_rules.mkdir(parents=True, exist_ok=True)
    for f in sorted(rules_dir.glob("*.md")):
        heading = _extract_first_heading(f)
        content = f.read_text(encoding="utf-8")
        mdc_content = _add_cursor_frontmatter(content, heading)
        (cursor_rules / f"{f.stem}.mdc").write_text(mdc_content, encoding="utf-8")
    print("  ✓ .cursor/rules/")

    # → Claude Code: rules 融入 CLAUDE.md（手動維護）
    print("  ✓ CLAUDE.md (手動維護，跳過)")


def sync_workflows():
    """[2/5] canonical/workflows/*.md → 三平台"""
    print("[2/5] 同步 Workflows...")

    workflows_dir = CANONICAL_DIR / "workflows"
    if not workflows_dir.exists():
        print("  (無 canonical/workflows/ 目錄，跳過)")
        return

    # → Antigravity（加 YAML frontmatter）
    agent_wf = AGENT_DIR / "workflows"
    agent_wf.mkdir(parents=True, exist_ok=True)
    for f in sorted(workflows_dir.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        if _has_frontmatter(content):
            (agent_wf / f.name).write_text(content, encoding="utf-8")
        else:
            heading = _extract_first_heading(f)
            (agent_wf / f.name).write_text(
                _add_frontmatter(content, heading), encoding="utf-8"
            )
    print("  ✓ .agent/workflows/")

    # → Cursor + Claude Code（去掉 YAML frontmatter）
    for target_dir, label in [
        (CURSOR_DIR / "commands", ".cursor/commands/"),
        (CLAUDE_DIR / "commands", ".claude/commands/"),
    ]:
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in sorted(workflows_dir.glob("*.md")):
            content = f.read_text(encoding="utf-8")
            stripped = _strip_frontmatter(content) if _has_frontmatter(content) else content
            (target_dir / f.name).write_text(stripped, encoding="utf-8")
        print(f"  ✓ {label}")


def sync_skills():
    """[3/5] canonical/skills/*/ → .agent/skills/ + .claude/skills/"""
    print("[3/5] 同步 Skills...")

    skills_dir = CANONICAL_DIR / "skills"
    if not skills_dir.exists():
        print("  (無 canonical/skills/ 目錄，跳過)")
        return

    for target_dir, label in [
        (AGENT_DIR / "skills", ".agent/skills/"),
        (CLAUDE_DIR / "skills", ".claude/skills/"),
    ]:
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            dest = target_dir / skill_dir.name
            dest.mkdir(parents=True, exist_ok=True)
            for item in skill_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, dest / item.name)
                elif item.is_dir():
                    dest_sub = dest / item.name
                    if dest_sub.exists():
                        shutil.rmtree(dest_sub)
                    shutil.copytree(item, dest_sub)
        print(f"  ✓ {label}")


def sync_global_skills():
    """[4/5] ~/.claude/skills/ → Antigravity + Cursor"""
    print("[4/5] 同步全域 Claude Code Skills 到 Antigravity/Cursor...")

    synced = 0
    if not CLAUDE_GLOBAL_SKILLS.exists():
        print("  ✓ 同步了 0 個全域 skills")
        return

    for skill_dir in sorted(CLAUDE_GLOBAL_SKILLS.iterdir()):
        if not skill_dir.is_dir() or skill_dir.is_symlink():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        # → Antigravity
        ag_dest = AG_GLOBAL_SKILLS / skill_dir.name
        ag_dest.mkdir(parents=True, exist_ok=True)
        for item in skill_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, ag_dest / item.name)
            elif item.is_dir():
                dest_sub = ag_dest / item.name
                if dest_sub.exists():
                    shutil.rmtree(dest_sub)
                shutil.copytree(item, dest_sub)

        # → Cursor（從 SKILL.md 去掉 frontmatter）
        content = skill_md.read_text(encoding="utf-8")
        stripped = _strip_frontmatter(content) if _has_frontmatter(content) else content
        cursor_cmd = CURSOR_DIR / "commands" / f"{skill_dir.name}.md"
        cursor_cmd.parent.mkdir(parents=True, exist_ok=True)
        cursor_cmd.write_text(stripped, encoding="utf-8")

        synced += 1

    print(f"  ✓ 同步了 {synced} 個全域 skills")


def sync_global_commands():
    """[5/5] ~/.claude/commands/ → Antigravity workflows"""
    print("[5/5] 同步全域 Claude Code Commands 到 Antigravity...")

    synced = 0
    if not CLAUDE_GLOBAL_COMMANDS.exists():
        print("  ✓ 同步了 0 個全域 commands")
        return

    AG_GLOBAL_WORKFLOWS.mkdir(parents=True, exist_ok=True)

    for cmd_file in sorted(CLAUDE_GLOBAL_COMMANDS.glob("*.md")):
        content = cmd_file.read_text(encoding="utf-8")
        heading = _extract_first_heading(cmd_file)
        target = AG_GLOBAL_WORKFLOWS / cmd_file.name
        target.write_text(_add_frontmatter(content, heading), encoding="utf-8")
        synced += 1

    print(f"  ✓ 同步了 {synced} 個全域 commands")


def main():
    print("=== Dex Agent OS — 跨平台同步 ===")
    print(f"Root: {ROOT_DIR}")
    print()

    sync_rules()
    sync_workflows()
    sync_skills()
    sync_global_skills()
    sync_global_commands()

    print()
    print("=== 同步完成 ===")
    print()
    print("檔案位置：")
    print(f"  Antigravity: {AGENT_DIR}/ + {AG_GLOBAL_SKILLS.parent}/")
    print(f"  Cursor:      {CURSOR_DIR}/")
    print(f"  Claude Code: {CLAUDE_DIR}/ + CLAUDE.md")
    print()
    print("下次修改 canonical/ 後重新執行 bin/sync 即可。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
