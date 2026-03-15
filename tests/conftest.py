"""Shared test fixtures for Dex Agent OS tests."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_canonical(tmp_path):
    """建立一個模擬的 canonical/ 結構"""
    canonical = tmp_path / "canonical"

    # rules
    rules = canonical / "rules"
    rules.mkdir(parents=True)
    (rules / "00-core.md").write_text("# Core Rules\n\nSome rules here.\n")
    (rules / "10-writing.md").write_text("# Writing Style\n\nStyle guide.\n")

    # workflows
    workflows = canonical / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "daily-journal.md").write_text(
        "---\ndescription: \"Daily Journal\"\n---\n\n# Daily Journal\n\nWorkflow content.\n"
    )
    (workflows / "topic-create.md").write_text("# Topic Create\n\nNo frontmatter workflow.\n")

    # skills
    skills = canonical / "skills" / "my-skill"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text(
        "---\ndescription: \"My Skill\"\n---\n\n# My Skill\n\nSkill content.\n"
    )

    return canonical


@pytest.fixture
def tmp_targets(tmp_path):
    """建立模擬的目標目錄"""
    return {
        "agent": tmp_path / ".agent",
        "cursor": tmp_path / ".cursor",
        "claude": tmp_path / ".claude",
    }
