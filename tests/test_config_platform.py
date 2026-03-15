"""Tests for scripts/lib/config.py — platform detection."""

from unittest.mock import patch
from pathlib import Path, PurePosixPath, PureWindowsPath
import importlib


def _reload_config(mock_system_return):
    """重新載入 config 模組以套用 mock"""
    import scripts.lib.config as config_mod
    with patch("platform.system", return_value=mock_system_return):
        importlib.reload(config_mod)
    return config_mod


class TestMacPaths:
    @patch("platform.system", return_value="Darwin")
    def test_dayflow_db_points_to_library(self, mock_sys):
        config = _reload_config("Darwin")
        assert config.DAYFLOW_DB is not None
        assert "Library" in str(config.DAYFLOW_DB)
        assert "Application Support" in str(config.DAYFLOW_DB)

    @patch("platform.system", return_value="Darwin")
    def test_apple_podcast_exists_on_mac(self, mock_sys):
        config = _reload_config("Darwin")
        assert config.APPLE_PODCAST_TTML_DIR is not None
        assert "TTML" in str(config.APPLE_PODCAST_TTML_DIR)


class TestWindowsPaths:
    @patch("platform.system", return_value="Windows")
    def test_apple_podcast_none_on_windows(self, mock_sys):
        config = _reload_config("Windows")
        assert config.APPLE_PODCAST_TTML_DIR is None

    @patch("platform.system", return_value="Windows")
    def test_dayflow_uses_appdata_on_windows(self, mock_sys):
        config = _reload_config("Windows")
        assert config.DAYFLOW_DB is not None
        db_str = str(config.DAYFLOW_DB)
        assert "Dayflow" in db_str


class TestLinuxPaths:
    @patch("platform.system", return_value="Linux")
    def test_apple_podcast_none_on_linux(self, mock_sys):
        config = _reload_config("Linux")
        assert config.APPLE_PODCAST_TTML_DIR is None

    @patch("platform.system", return_value="Linux")
    def test_dayflow_none_on_linux(self, mock_sys):
        config = _reload_config("Linux")
        assert config.DAYFLOW_DB is None


class TestClaudeMemoryDir:
    def test_not_hardcoded(self):
        """CLAUDE_MEMORY_DIR 不應包含硬編碼的 -Users-dex-"""
        import scripts.lib.config as config
        # 路徑應根據 ROOT_DIR 動態計算
        assert config.CLAUDE_MEMORY_DIR is not None
        assert config.CLAUDE_MEMORY_DIR.name == "memory"
        assert ".claude" in str(config.CLAUDE_MEMORY_DIR)

    def test_mac_format(self):
        """Mac: ROOT_DIR 的路徑被正確轉換為 Claude 記憶目錄名"""
        import scripts.lib.config as config
        # 直接測試 _compute 函式邏輯：ROOT_DIR 路徑的 / 轉 -
        root_str = str(config.ROOT_DIR)
        expected_encoded = root_str.replace("/", "-")
        assert expected_encoded in str(config.CLAUDE_MEMORY_DIR)


class TestRootDirRelativePaths:
    def test_journal_dir_is_relative_to_root(self):
        """JOURNAL_DIR 應相對於 ROOT_DIR"""
        import scripts.lib.config as config
        assert str(config.JOURNAL_DIR).startswith(str(config.ROOT_DIR))

    def test_insights_dir_is_relative_to_root(self):
        """INSIGHTS_DIR 應相對於 ROOT_DIR"""
        import scripts.lib.config as config
        assert str(config.INSIGHTS_DIR).startswith(str(config.ROOT_DIR))
