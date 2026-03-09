"""Tests for main module."""
# pylint: disable=R0917

import json
from unittest.mock import MagicMock, patch

import pytest

from src.cnt_collector_config import main


class TestMain:
    """Tests for main function."""

    @patch("src.cnt_collector_config.main.utils.parse_arguments")
    @patch("src.cnt_collector_config.main.utils.get_version")
    def test_main_version_flag(self, mock_get_version, mock_parse_args, capsys):
        """Test main exits with version when --version flag is used."""
        mock_args = MagicMock()
        mock_args.version = True
        mock_parse_args.return_value = mock_args
        mock_get_version.return_value = "1.2.3"

        with pytest.raises(SystemExit) as exc_info:
            main.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "1.2.3" in captured.out

    @patch("src.cnt_collector_config.main.utils.parse_arguments")
    def test_main_missing_kupo_url(self, mock_parse_args):
        """Test main exits when Kupo URL is not set."""
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.kupo_url = None
        mock_parse_args.return_value = mock_args

        with pytest.raises(SystemExit) as exc_info:
            main.main()

        assert exc_info.value.code == 1

    @patch("src.cnt_collector_config.main.utils.parse_arguments")
    @patch("src.cnt_collector_config.main.fetchers.kupo_health")
    def test_main_unhealthy_kupo(self, mock_kupo_health, mock_parse_args):
        """Test main exits when Kupo is unhealthy."""
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.kupo_url = "https://kupo.test"
        mock_parse_args.return_value = mock_args
        mock_kupo_health.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            main.main()

        assert exc_info.value.code == 1

    @patch("src.cnt_collector_config.main.utils.parse_arguments")
    @patch("src.cnt_collector_config.main.fetchers.kupo_health")
    @patch("src.cnt_collector_config.main.fetchers.fetch_tokens_config")
    @patch("src.cnt_collector_config.main.parsers.transform_tokens_to_dict")
    @patch("src.cnt_collector_config.main.fetchers.get_assets_by_source_and_address")
    @patch("src.cnt_collector_config.main.parsers.parse_pairs_utxos")
    @patch("src.cnt_collector_config.main.parsers.parse_tokens_pairs")
    @patch("src.cnt_collector_config.main.parsers.parse_configured_tokens")
    @patch("src.cnt_collector_config.main.generators.create_config")
    @patch("src.cnt_collector_config.main.utils.save_txt_file")
    def test_main_successful_execution(  # pylint: disable=too-many-arguments
        self,
        mock_save_txt,
        mock_create_config,
        mock_parse_configured,
        mock_parse_tokens_pairs,
        mock_parse_pairs_utxos,
        mock_get_assets,
        mock_transform_tokens,
        mock_fetch_tokens,
        mock_kupo_health,
        mock_parse_args,
    ):
        """Test successful execution of main function."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.kupo_url = "https://kupo.test"
        mock_args.tokens_location = "file://./tokens.json"
        mock_args.feeds_location = "file://./feeds.json"
        mock_args.config_location = "./output.py"
        mock_parse_args.return_value = mock_args

        mock_kupo_health.return_value = True
        mock_fetch_tokens.return_value = {"tokens": {}}
        mock_transform_tokens.return_value = ({}, {})
        mock_get_assets.return_value = {}
        mock_parse_pairs_utxos.return_value = {}
        mock_parse_tokens_pairs.return_value = []
        mock_parse_configured.return_value = []
        mock_create_config.return_value = [
            {
                "name": "ADA-SNEK",
                "token1_policy": "",
                "token1_name": "lovelace",
                "token1_decimals": 6,
                "token2_policy": "snek_policy",
                "token2_name": "SNEK",
                "token2_decimals": 0,
                "sources": [],
            }
        ]
        mock_save_txt.return_value = True

        # Execute
        main.main()

        # Verify the pipeline was called
        mock_fetch_tokens.assert_called_once()
        mock_transform_tokens.assert_called_once()
        mock_get_assets.assert_called_once()
        mock_parse_pairs_utxos.assert_called_once()
        mock_parse_tokens_pairs.assert_called_once()
        mock_parse_configured.assert_called_once()
        mock_create_config.assert_called_once()
        mock_save_txt.assert_called_once()

    @patch("src.cnt_collector_config.main.utils.parse_arguments")
    @patch("src.cnt_collector_config.main.fetchers.kupo_health")
    @patch("src.cnt_collector_config.main.fetchers.fetch_tokens_config")
    @patch("src.cnt_collector_config.main.parsers.transform_tokens_to_dict")
    @patch("src.cnt_collector_config.main.fetchers.get_assets_by_source_and_address")
    @patch("src.cnt_collector_config.main.parsers.parse_pairs_utxos")
    @patch("src.cnt_collector_config.main.parsers.parse_tokens_pairs")
    @patch("src.cnt_collector_config.main.parsers.parse_configured_tokens")
    @patch("src.cnt_collector_config.main.generators.create_config")
    @patch("src.cnt_collector_config.main.utils.save_txt_file")
    def test_main_output_format(  # pylint: disable=too-many-arguments
        self,
        mock_save_txt,
        mock_create_config,
        mock_parse_configured,
        mock_parse_tokens_pairs,
        mock_parse_pairs_utxos,
        mock_get_assets,
        mock_transform_tokens,
        mock_fetch_tokens,
        mock_kupo_health,
        mock_parse_args,
    ):
        """Test that main creates properly formatted output."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.kupo_url = "https://kupo.test"
        mock_args.tokens_location = "file://./tokens.json"
        mock_args.feeds_location = "file://./feeds.json"
        mock_args.config_location = "./output.py"
        mock_parse_args.return_value = mock_args

        mock_kupo_health.return_value = True
        mock_fetch_tokens.return_value = {"tokens": {}}
        mock_transform_tokens.return_value = ({}, {})
        mock_get_assets.return_value = {}
        mock_parse_pairs_utxos.return_value = {}
        mock_parse_tokens_pairs.return_value = []
        mock_parse_configured.return_value = []
        mock_create_config.return_value = [{"name": "ADA-SNEK", "sources": []}]
        mock_save_txt.return_value = True

        # Execute
        main.main()

        # Check the saved content format
        call_args = mock_save_txt.call_args
        saved_content = call_args[0][0]

        assert '"""DEX Pairs configuration"""' in saved_content
        assert "# pylint: disable = C0302" in saved_content
        assert "# fmt: off" in saved_content
        assert "DEX_PAIRS = " in saved_content

    @patch("src.cnt_collector_config.main.utils.parse_arguments")
    @patch("src.cnt_collector_config.main.fetchers.kupo_health")
    @patch("src.cnt_collector_config.main.fetchers.fetch_tokens_config")
    @patch("src.cnt_collector_config.main.parsers.transform_tokens_to_dict")
    @patch("src.cnt_collector_config.main.fetchers.get_assets_by_source_and_address")
    @patch("src.cnt_collector_config.main.parsers.parse_pairs_utxos")
    @patch("src.cnt_collector_config.main.parsers.parse_tokens_pairs")
    @patch("src.cnt_collector_config.main.parsers.parse_configured_tokens")
    @patch("src.cnt_collector_config.main.generators.create_config")
    @patch("src.cnt_collector_config.main.utils.save_txt_file")
    def test_main_sorts_config_by_name(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        mock_save_txt,
        mock_create_config,
        mock_parse_configured,
        mock_parse_tokens_pairs,
        mock_parse_pairs_utxos,
        mock_get_assets,
        mock_transform_tokens,
        mock_fetch_tokens,
        mock_kupo_health,
        mock_parse_args,
    ):
        """Test that main sorts the config by name."""
        # Setup mocks
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.kupo_url = "https://kupo.test"
        mock_args.tokens_location = "file://./tokens.json"
        mock_args.feeds_location = "file://./feeds.json"
        mock_args.config_location = "./output.py"
        mock_parse_args.return_value = mock_args

        mock_kupo_health.return_value = True
        mock_fetch_tokens.return_value = {"tokens": {}}
        mock_transform_tokens.return_value = ({}, {})
        mock_get_assets.return_value = {}
        mock_parse_pairs_utxos.return_value = {}
        mock_parse_tokens_pairs.return_value = []
        mock_parse_configured.return_value = []

        # Return unsorted config
        mock_create_config.return_value = [
            {"name": "ADA-SNEK", "sources": []},
            {"name": "ADA-MELD", "sources": []},
            {"name": "ADA-COPI", "sources": []},
        ]
        mock_save_txt.return_value = True

        # Execute
        main.main()

        # Check the saved content has sorted pairs
        call_args = mock_save_txt.call_args
        saved_content = call_args[0][0]

        # Parse the JSON from the saved content
        json_start = saved_content.find("DEX_PAIRS = ") + len("DEX_PAIRS = ")
        json_content = saved_content[json_start:].strip()

        pairs = json.loads(json_content)
        names = [pair["name"] for pair in pairs]

        # Should be sorted alphabetically
        assert names == sorted(names)
