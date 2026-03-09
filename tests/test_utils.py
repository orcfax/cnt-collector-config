"""Tests for utils module."""

import json
from unittest.mock import patch

from src.cnt_collector_config import utils


class TestSaveTxtFile:
    """Tests for save_txt_file function."""

    def test_save_txt_file_success(self, tmp_path):
        """Test successful text file save."""
        test_file = tmp_path / "test.txt"
        content = "Test content"

        result = utils.save_txt_file(content, str(test_file))

        assert result is True
        assert test_file.read_text() == content

    def test_save_txt_file_dict_content(self, tmp_path):
        """Test saving dict as text file."""
        test_file = tmp_path / "test.txt"
        content = {"key": "value"}

        result = utils.save_txt_file(content, str(test_file))

        assert result is True
        assert "key" in test_file.read_text()

    def test_save_txt_file_not_found_error(self):
        """Test handling of FileNotFoundError."""
        invalid_path = "/nonexistent/path/test.txt"
        content = "Test content"

        result = utils.save_txt_file(content, invalid_path)

        assert result is False


class TestSaveJsonFile:
    """Tests for save_json_file function."""

    def test_save_json_file_success(self, tmp_path):
        """Test successful JSON file save."""
        test_file = tmp_path / "test.json"
        content = {"key": "value", "number": 42}

        result = utils.save_json_file(content, str(test_file))

        assert result is True
        saved_data = json.loads(test_file.read_text())
        assert saved_data == content

    def test_save_json_file_list_content(self, tmp_path):
        """Test saving list as JSON file."""
        test_file = tmp_path / "test.json"
        content = [1, 2, 3, 4, 5]

        result = utils.save_json_file(content, str(test_file))

        assert result is True
        saved_data = json.loads(test_file.read_text())
        assert saved_data == content

    def test_save_json_file_not_found_error(self):
        """Test handling of FileNotFoundError."""
        invalid_path = "/nonexistent/path/test.json"
        content = {"key": "value"}

        result = utils.save_json_file(content, invalid_path)

        assert result is False


class TestReadJsonFile:
    """Tests for read_json_file function."""

    def test_read_json_file_success(self, tmp_path):
        """Test successful JSON file read."""
        test_file = tmp_path / "test.json"
        content = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(content))

        result = utils.read_json_file(str(test_file))

        assert result == content

    def test_read_json_file_not_found(self):
        """Test reading non-existent file returns empty dict."""
        result = utils.read_json_file("/nonexistent/file.json")

        assert result == {}

    def test_read_json_file_invalid_json(self, tmp_path):
        """Test reading invalid JSON returns empty dict."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json {")

        result = utils.read_json_file(str(test_file))

        assert result == {}


class TestGetVersion:
    """Tests for get_version function."""

    def test_get_version_returns_string(self):
        """Test that get_version returns a version string."""
        version = utils.get_version()

        assert isinstance(version, str)
        assert len(version) > 0

    @patch("src.cnt_collector_config.utils.version")
    def test_get_version_from_package(self, mock_version):
        """Test getting version from installed package."""
        mock_version.return_value = "1.2.3"

        version = utils.get_version()

        assert version == "1.2.3"

    @patch("src.cnt_collector_config.utils.version")
    def test_get_version_package_not_found(self, mock_version):
        """Test fallback to config version when package not installed."""
        # pylint: disable=import-outside-toplevel
        from importlib.metadata import PackageNotFoundError

        mock_version.side_effect = PackageNotFoundError

        version = utils.get_version()

        # Should return the version from config
        assert isinstance(version, str)


class TestParseArguments:
    """Tests for parse_arguments function."""

    def test_parse_arguments_defaults(self):
        """Test parsing arguments with defaults."""
        with patch("sys.argv", ["prog"]):
            args = utils.parse_arguments()

        assert hasattr(args, "kupo_url")
        assert hasattr(args, "feeds_location")
        assert hasattr(args, "tokens_location")
        assert hasattr(args, "config_location")
        assert hasattr(args, "version")

    def test_parse_arguments_custom_values(self):
        """Test parsing arguments with custom values."""
        test_args = [
            "prog",
            "--kupo-url",
            "https://custom-kupo.com",
            "--feeds-location",
            "file://./feeds.json",
            "--tokens-location",
            "file://./tokens.json",
            "--config-location",
            "./output.py",
        ]

        with patch("sys.argv", test_args):
            args = utils.parse_arguments()

        assert args.kupo_url == "https://custom-kupo.com"
        assert args.feeds_location == "file://./feeds.json"
        assert args.tokens_location == "file://./tokens.json"
        assert args.config_location == "./output.py"

    def test_parse_arguments_version_flag(self):
        """Test version flag is parsed correctly."""
        with patch("sys.argv", ["prog", "--version"]):
            args = utils.parse_arguments()

        assert args.version is True

    def test_parse_arguments_short_flags(self):
        """Test short flag versions."""
        test_args = [
            "prog",
            "-k",
            "https://kupo.test",
            "-f",
            "file://./feeds.json",
            "-t",
            "file://./tokens.json",
            "-c",
            "./out.py",
            "-v",
        ]

        with patch("sys.argv", test_args):
            args = utils.parse_arguments()

        assert args.kupo_url == "https://kupo.test"
        assert args.feeds_location == "file://./feeds.json"
        assert args.tokens_location == "file://./tokens.json"
        assert args.config_location == "./out.py"
        assert args.version is True
