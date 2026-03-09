"""Tests for fetchers module."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.cnt_collector_config import fetchers


class TestKupoHealth:
    """Tests for kupo_health function."""

    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_kupo_health_healthy(self, mock_get):
        """Test Kupo health check when healthy."""
        mock_response = MagicMock()
        mock_response.text = """
kupo_most_recent_checkpoint  1234567
kupo_most_recent_node_tip  1234567
other_metric  100
"""
        mock_get.return_value = mock_response

        result = fetchers.kupo_health("https://kupo.test")

        assert result is True
        mock_get.assert_called_once_with("https://kupo.test/health", timeout=30)

    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_kupo_health_not_synced(self, mock_get):
        """Test Kupo health check when not fully synced."""
        mock_response = MagicMock()
        mock_response.text = """
kupo_most_recent_checkpoint  1234567
kupo_most_recent_node_tip  1234600
"""
        mock_get.return_value = mock_response

        result = fetchers.kupo_health("https://kupo.test")

        assert result is False

    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_kupo_health_request_exception(self, mock_get):
        """Test Kupo health check with request exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = fetchers.kupo_health("https://kupo.test")

        assert result is False

    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_kupo_health_missing_metrics(self, mock_get):
        """Test Kupo health check with missing metrics."""
        mock_response = MagicMock()
        mock_response.text = "some other output"
        mock_get.return_value = mock_response

        result = fetchers.kupo_health("https://kupo.test")

        assert result is False


class TestGetCerFeeds:
    """Tests for get_cer_feeds function."""

    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_get_cer_feeds_from_url(self, mock_get, sample_feeds_response):
        """Test fetching feeds from HTTPS URL."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_feeds_response)
        mock_get.return_value = mock_response

        result = fetchers.get_cer_feeds("https://example.com/feeds.json")

        assert result == ["ADA-SNEK", "ADA-MELD"]
        assert "BTC-USD" not in result  # CEX feed should be filtered out

    @patch("src.cnt_collector_config.utils.read_json_file")
    def test_get_cer_feeds_from_file(self, mock_read, sample_feeds_response):
        """Test fetching feeds from file."""
        mock_read.return_value = sample_feeds_response

        result = fetchers.get_cer_feeds("file:///path/to/feeds.json")

        assert result == ["ADA-SNEK", "ADA-MELD"]
        mock_read.assert_called_once_with("/path/to/feeds.json")

    def test_get_cer_feeds_invalid_url_type(self):
        """Test error handling for invalid URL type."""
        with pytest.raises(SystemExit):
            fetchers.get_cer_feeds("ftp://invalid.com/feeds.json")


class TestFetchTokensConfig:
    """Tests for fetch_tokens_config function."""

    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_fetch_tokens_config_from_url(self, mock_get, sample_tokens_response):
        """Test fetching tokens config from HTTPS URL."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(sample_tokens_response)
        mock_get.return_value = mock_response

        result = fetchers.fetch_tokens_config("https://example.com/tokens.json")

        assert result == sample_tokens_response
        mock_get.assert_called_once_with("https://example.com/tokens.json", timeout=30)

    @patch("src.cnt_collector_config.utils.read_json_file")
    def test_fetch_tokens_config_from_file(self, mock_read, sample_tokens_response):
        """Test fetching tokens config from file."""
        mock_read.return_value = sample_tokens_response

        result = fetchers.fetch_tokens_config("file:///path/to/tokens.json")

        assert result == sample_tokens_response
        mock_read.assert_called_once_with("/path/to/tokens.json")

    def test_fetch_tokens_config_invalid_url_type(self):
        """Test error handling for invalid URL type."""
        assert fetchers.fetch_tokens_config("ftp://invalid.com/tokens.json") == {}


class TestFetchKupoMatches:
    """Tests for _fetch_kupo_matches helper function."""

    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_fetch_kupo_matches_success(self, mock_get):
        """Test successful fetch from Kupo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps([{"test": "data"}])
        mock_get.return_value = mock_response

        result = fetchers._fetch_kupo_matches(  # pylint: disable=protected-access
            "https://kupo.test/matches/test", "TestDEX", "security_asset"
        )

        assert result["success"] is True
        assert result["source"] == "TestDEX"
        assert len(result["matches"]) == 1
        assert result["request_type"] == "security_asset"

    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_fetch_kupo_matches_failure(self, mock_get):
        """Test failed fetch from Kupo."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = fetchers._fetch_kupo_matches(  # pylint: disable=protected-access
            "https://kupo.test/matches/test", "TestDEX", "security_asset"
        )

        assert result["success"] is False
        assert result["source"] == "TestDEX"
        assert result["matches"] == []
        assert "error" in result


class TestGetAssetsBySourceAndAddress:
    """Tests for get_assets_by_source_and_address function."""

    @patch("src.cnt_collector_config.parsers.get_utxo_content")
    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_get_assets_by_source_and_address_with_security_assets(
        self, mock_get, mock_get_content
    ):
        """Test fetching assets using security tokens."""
        # Mock Kupo response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            [
                {
                    "address": "addr1test",
                    "value": {"coins": 5000000, "assets": {}},
                }
            ]
        )
        mock_get.return_value = mock_response

        # Mock UTxO content parser
        mock_get_content.return_value = {
            "amount": 5000000,
            "assets": {},
        }

        with patch("src.cnt_collector_config.dex_config.SECURITY_ASSETS", []):
            with patch("src.cnt_collector_config.dex_config.ADDRESSES", []):
                result = fetchers.get_assets_by_source_and_address("https://kupo.test")

        assert isinstance(result, dict)

    @patch("src.cnt_collector_config.parsers.get_utxo_content")
    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_get_assets_by_source_and_address_groups_by_source(
        self, mock_get, mock_get_content
    ):
        """Test that results are grouped by source DEX."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps([])
        mock_get.return_value = mock_response

        mock_get_content.return_value = {"amount": 5000000, "assets": {}}

        mock_security_assets = [
            {
                "source": "MinSwap",
                "security_assets": [
                    {"policy": "test_policy_1"},
                ],
            },
            {
                "source": "WingRiders",
                "security_assets": [
                    {"policy": "test_policy_2", "asset": "4c"},
                ],
            },
        ]

        with patch(
            "src.cnt_collector_config.dex_config.SECURITY_ASSETS",
            mock_security_assets,
        ):
            with patch("src.cnt_collector_config.dex_config.ADDRESSES", []):
                result = fetchers.get_assets_by_source_and_address("https://kupo.test")

        assert "MinSwap" in result
        assert "WingRiders" in result

    @patch("src.cnt_collector_config.parsers.get_utxo_content")
    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_get_assets_by_address(self, mock_get, mock_get_content):
        """Test fetching assets by address."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            [
                {
                    "address": "addr1sundaeswap",
                    "value": {"coins": 10000000, "assets": {}},
                }
            ]
        )
        mock_get.return_value = mock_response

        mock_get_content.return_value = {
            "amount": 10000000,
            "assets": {},
        }

        mock_addresses = [
            {
                "source": "SundaeSwap",
                "address": "addr1sundaeswap",
            }
        ]

        with patch("src.cnt_collector_config.dex_config.SECURITY_ASSETS", []):
            with patch("src.cnt_collector_config.dex_config.ADDRESSES", mock_addresses):
                result = fetchers.get_assets_by_source_and_address("https://kupo.test")

        assert "SundaeSwap" in result
        assert "addr1sundaeswap" in result["SundaeSwap"]

    @patch("src.cnt_collector_config.parsers.get_utxo_content")
    @patch("src.cnt_collector_config.fetchers.requests.get")
    def test_get_assets_parallel_execution(self, mock_get, mock_get_content):
        """Test that parallel execution is used with configured max workers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps([])
        mock_get.return_value = mock_response

        mock_get_content.return_value = {"amount": 0, "assets": {}}

        # Create multiple security assets to trigger parallel execution
        mock_security_assets = [
            {
                "source": f"DEX{i}",
                "security_assets": [{"policy": f"policy{i}"}],
            }
            for i in range(10)
        ]

        with patch(
            "src.cnt_collector_config.dex_config.SECURITY_ASSETS",
            mock_security_assets,
        ):
            with patch("src.cnt_collector_config.dex_config.ADDRESSES", []):
                with patch("src.cnt_collector_config.config.MAX_PARALLEL_REQUESTS", 5):
                    result = fetchers.get_assets_by_source_and_address(
                        "https://kupo.test"
                    )

        # Verify all sources were processed
        assert len(result) == 10
        # Verify requests were made
        assert mock_get.call_count == 10
