"""Tests for bin/sync.py — sync logic."""

import sys
from pathlib import Path

# 讓 sync.py 可以被 import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import sync as sync_mod


class TestStripFrontmatter:
    def test_strips_yaml_frontmatter(self):
        text = '---\ndescription: "Test"\n---\n\n# Content\n\nBody here.\n'
        result = sync_mod._strip_frontmatter(text)
        assert result == "# Content\n\nBody here.\n"

    def test_no_frontmatter_returns_as_is(self):
        text = "# Content\n\nNo frontmatter.\n"
        result = sync_mod._strip_frontmatter(text)
        assert result == text

    def test_incomplete_frontmatter(self):
        text = "---\ndescription: broken\nno closing"
        result = sync_mod._strip_frontmatter(text)
        assert result == text


class TestAddFrontmatter:
    def test_adds_yaml_frontmatter(self):
        result = sync_mod._add_frontmatter("# Content", "My Description")
        assert result.startswith('---\ndescription: "My Description"\n---')
        assert "# Content" in result

    def test_cursor_frontmatter_has_always_apply(self):
        result = sync_mod._add_cursor_frontmatter("# Content", "Test")
        assert "alwaysApply: true" in result


class TestExtractFirstHeading:
    def test_extracts_heading(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# My Heading\n\nBody.\n")
        assert sync_mod._extract_first_heading(f) == "My Heading"

    def test_no_heading_returns_stem(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("No heading here.\n")
        assert sync_mod._extract_first_heading(f) == "test"


class TestExtractDescription:
    def test_extracts_from_frontmatter(self):
        text = '---\ndescription: "Hello World"\n---\n\nContent'
        assert sync_mod._extract_description_from_frontmatter(text) == "Hello World"

    def test_no_frontmatter_returns_empty(self):
        assert sync_mod._extract_description_from_frontmatter("# No FM") == ""


class TestSyncRules:
    def test_copies_to_agent_rules(self, tmp_path, tmp_canonical):
        """canonical/rules/foo.md → .agent/rules/foo.md"""
        sync_mod.ROOT_DIR = tmp_path
        sync_mod.CANONICAL_DIR = tmp_canonical
        sync_mod.AGENT_DIR = tmp_path / ".agent"
        sync_mod.CURSOR_DIR = tmp_path / ".cursor"

        sync_mod.sync_rules()

        assert (tmp_path / ".agent" / "rules" / "00-core.md").exists()
        assert (tmp_path / ".agent" / "rules" / "10-writing.md").exists()

    def test_creates_cursor_mdc_with_frontmatter(self, tmp_path, tmp_canonical):
        """canonical/rules/foo.md → .cursor/rules/foo.mdc（含 YAML frontmatter）"""
        sync_mod.ROOT_DIR = tmp_path
        sync_mod.CANONICAL_DIR = tmp_canonical
        sync_mod.AGENT_DIR = tmp_path / ".agent"
        sync_mod.CURSOR_DIR = tmp_path / ".cursor"

        sync_mod.sync_rules()

        mdc = tmp_path / ".cursor" / "rules" / "00-core.mdc"
        assert mdc.exists()
        content = mdc.read_text()
        assert 'description: "Core Rules"' in content
        assert "alwaysApply: true" in content


class TestSyncWorkflows:
    def test_strips_frontmatter_for_claude(self, tmp_path, tmp_canonical):
        """有 frontmatter 的 workflow → .claude/commands/ 去掉 frontmatter"""
        sync_mod.ROOT_DIR = tmp_path
        sync_mod.CANONICAL_DIR = tmp_canonical
        sync_mod.AGENT_DIR = tmp_path / ".agent"
        sync_mod.CURSOR_DIR = tmp_path / ".cursor"
        sync_mod.CLAUDE_DIR = tmp_path / ".claude"

        sync_mod.sync_workflows()

        claude_cmd = tmp_path / ".claude" / "commands" / "daily-journal.md"
        assert claude_cmd.exists()
        content = claude_cmd.read_text()
        assert "---" not in content
        assert "# Daily Journal" in content

    def test_no_frontmatter_copies_directly(self, tmp_path, tmp_canonical):
        """無 frontmatter 的 workflow → 直接複製"""
        sync_mod.ROOT_DIR = tmp_path
        sync_mod.CANONICAL_DIR = tmp_canonical
        sync_mod.AGENT_DIR = tmp_path / ".agent"
        sync_mod.CURSOR_DIR = tmp_path / ".cursor"
        sync_mod.CLAUDE_DIR = tmp_path / ".claude"

        sync_mod.sync_workflows()

        claude_cmd = tmp_path / ".claude" / "commands" / "topic-create.md"
        assert claude_cmd.exists()
        assert "# Topic Create" in claude_cmd.read_text()

    def test_adds_frontmatter_for_agent(self, tmp_path, tmp_canonical):
        """無 frontmatter 的 workflow → .agent/ 自動加 frontmatter"""
        sync_mod.ROOT_DIR = tmp_path
        sync_mod.CANONICAL_DIR = tmp_canonical
        sync_mod.AGENT_DIR = tmp_path / ".agent"
        sync_mod.CURSOR_DIR = tmp_path / ".cursor"
        sync_mod.CLAUDE_DIR = tmp_path / ".claude"

        sync_mod.sync_workflows()

        agent_wf = tmp_path / ".agent" / "workflows" / "topic-create.md"
        content = agent_wf.read_text()
        assert content.startswith("---")
        assert "Topic Create" in content


class TestSyncIdempotent:
    def test_running_twice_produces_same_result(self, tmp_path, tmp_canonical):
        """跑兩次 sync 結果一致"""
        sync_mod.ROOT_DIR = tmp_path
        sync_mod.CANONICAL_DIR = tmp_canonical
        sync_mod.AGENT_DIR = tmp_path / ".agent"
        sync_mod.CURSOR_DIR = tmp_path / ".cursor"
        sync_mod.CLAUDE_DIR = tmp_path / ".claude"

        sync_mod.sync_rules()
        sync_mod.sync_workflows()
        first_run = {
            str(p.relative_to(tmp_path)): p.read_text()
            for p in tmp_path.rglob("*") if p.is_file()
        }

        sync_mod.sync_rules()
        sync_mod.sync_workflows()
        second_run = {
            str(p.relative_to(tmp_path)): p.read_text()
            for p in tmp_path.rglob("*") if p.is_file()
        }

        assert first_run == second_run
