"""Tests for bin/agent.py — CLI routing."""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENT_PY = ROOT_DIR / "bin" / "agent.py"


def test_help_prints_usage():
    """help 指令應印出使用說明"""
    result = subprocess.run(
        [sys.executable, str(AGENT_PY), "help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "Dex Agent OS" in result.stdout
    assert "journal" in result.stdout


def test_help_flag():
    """--help flag 也應印出使用說明"""
    result = subprocess.run(
        [sys.executable, str(AGENT_PY), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "Dex Agent OS" in result.stdout


def test_unknown_command_exits_1():
    """未知指令應 exit 1"""
    result = subprocess.run(
        [sys.executable, str(AGENT_PY), "nonexistent-command"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "Unknown command" in result.stdout


def test_no_args_shows_help():
    """無參數應顯示 help"""
    result = subprocess.run(
        [sys.executable, str(AGENT_PY)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "Dex Agent OS" in result.stdout


def test_commands_dict_matches_bash_original():
    """確認 COMMANDS dict 涵蓋所有原始 bash 版本的指令"""
    # 從 agent.py 匯入 COMMANDS
    import importlib.util
    spec = importlib.util.spec_from_file_location("agent_cli", str(AGENT_PY))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    expected_commands = {
        "journal", "dayflow", "extract", "collect-threads", "extract-style",
        "topic-create", "topic-to-thread", "topic-to-fb", "topic-to-blog",
        "topic-to-short-video", "film-review", "youtube-add", "learning-note",
        "readwise-sync", "rss-sync", "anybox-sync", "gmail-sync",
        "daily-digest", "podcast-add", "podcast-digest",
        "weekly-review", "weekly-newsletter",
        "project-status", "meeting-notes", "consultation-notes",
        "classroom-sync", "fireflies-sync",
    }
    assert set(mod.COMMANDS.keys()) == expected_commands
