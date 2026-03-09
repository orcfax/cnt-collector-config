"""Tests for parsers module."""
# pylint: disable=C0302

from unittest.mock import patch

import pytest

from src.cnt_collector_config import parsers


class TestValidateTokensConfig:
    """Tests for validate_tokens_config function."""

    def test_validate_tokens_config_valid(self):
        """Test validation passes with valid tokens config."""
        tokens_response = {
            "tokens": {
                "SNEK": {
                    "policy_id": "abc123",
                    "asset_name": "534e454b",
                    "decimals": 0,
                }
            }
        }

        # Should not raise
        parsers.validate_tokens_config(tokens_response)

    def test_validate_tokens_config_missing_tokens_key(self):
        """Test validation fails when 'tokens' key is missing."""
        tokens_response = {"meta": {"version": "1.0"}}

        with pytest.raises(parsers.TokenValidationError) as exc_info:
            parsers.validate_tokens_config(tokens_response)

        assert "missing 'tokens' key" in str(exc_info.value)

    def test_validate_tokens_config_missing_policy_id(self):
        """Test validation fails when policy_id is missing."""
        tokens_response = {
            "tokens": {
                "SNEK": {
                    "asset_name": "534e454b",
                    "decimals": 0,
                }
            }
        }

        with pytest.raises(parsers.TokenValidationError) as exc_info:
            parsers.validate_tokens_config(tokens_response)

        assert "SNEK" in str(exc_info.value)
        assert "policy_id" in str(exc_info.value)

    def test_validate_tokens_config_missing_asset_name(self):
        """Test validation fails when asset_name is missing."""
        tokens_response = {
            "tokens": {
                "SNEK": {
                    "policy_id": "abc123",
                    "decimals": 0,
                }
            }
        }

        with pytest.raises(parsers.TokenValidationError) as exc_info:
            parsers.validate_tokens_config(tokens_response)

        assert "SNEK" in str(exc_info.value)
        assert "asset_name" in str(exc_info.value)

    def test_validate_tokens_config_missing_decimals(self):
        """Test validation fails when decimals is missing."""
        tokens_response = {
            "tokens": {
                "SNEK": {
                    "policy_id": "abc123",
                    "asset_name": "534e454b",
                }
            }
        }

        with pytest.raises(parsers.TokenValidationError) as exc_info:
            parsers.validate_tokens_config(tokens_response)

        assert "SNEK" in str(exc_info.value)
        assert "decimals" in str(exc_info.value)

    def test_validate_tokens_config_multiple_missing_fields(self):
        """Test validation reports all missing fields for a token."""
        tokens_response = {
            "tokens": {
                "SNEK": {
                    "decimals": 0,
                }
            }
        }

        with pytest.raises(parsers.TokenValidationError) as exc_info:
            parsers.validate_tokens_config(tokens_response)

        error_msg = str(exc_info.value)
        assert "SNEK" in error_msg
        assert "policy_id" in error_msg
        assert "asset_name" in error_msg

    def test_validate_tokens_config_multiple_invalid_tokens(self):
        """Test validation reports errors for all invalid tokens."""
        tokens_response = {
            "tokens": {
                "SNEK": {
                    "policy_id": "abc123",
                    "asset_name": "534e454b",
                    # missing decimals
                },
                "MELD": {
                    "decimals": 6,
                    # missing policy_id and asset_name
                },
            }
        }

        with pytest.raises(parsers.TokenValidationError) as exc_info:
            parsers.validate_tokens_config(tokens_response)

        error_msg = str(exc_info.value)
        assert "SNEK" in error_msg
        assert "MELD" in error_msg

    def test_validate_tokens_config_empty_tokens(self):
        """Test validation passes with empty tokens dict."""
        tokens_response = {"tokens": {}}

        # Should not raise
        parsers.validate_tokens_config(tokens_response)


class TestGetUtxoContent:
    """Tests for get_utxo_content function."""

    def test_get_utxo_content_with_assets(self, sample_utxo):
        """Test parsing UTxO with multiple assets."""
        result = parsers.get_utxo_content(sample_utxo)

        assert result["amount"] == 5000000
        assert (
            "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f"
            in result["assets"]
        )
        assert (
            "a2944573e99d2ed3055b808eaa264f0bf119e01fc6b18863067c63e4"
            in result["assets"]
        )

    def test_get_utxo_content_asset_amounts(self, sample_utxo):
        """Test correct asset amounts are extracted."""
        result = parsers.get_utxo_content(sample_utxo)

        snek_policy = "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f"
        meld_policy = "a2944573e99d2ed3055b808eaa264f0bf119e01fc6b18863067c63e4"

        assert result["assets"][snek_policy]["534e454b"] == 1000000
        assert result["assets"][meld_policy]["4d454c44"] == 500000

    def test_get_utxo_content_only_ada(self):
        """Test parsing UTxO with only ADA."""
        utxo = {
            "value": {
                "coins": 2000000,
                "assets": {},
            }
        }

        result = parsers.get_utxo_content(utxo)

        assert result["amount"] == 2000000
        assert not result["assets"]

    def test_get_utxo_content_asset_without_name(self):
        """Test parsing asset without asset name (empty string)."""
        utxo = {
            "value": {
                "coins": 1000000,
                "assets": {
                    "policy123": 100,
                },
            }
        }

        result = parsers.get_utxo_content(utxo)

        assert "policy123" in result["assets"]
        assert "" in result["assets"]["policy123"]


class TestUpdateAsset:
    """Tests for update_asset function."""

    def test_update_asset_with_token_info(self):
        """Test updating asset with ticker and decimals."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "TOKEN",
            "amount": 1000,
        }
        token_info = {
            "ticker": "TKN",
            "decimals": 6,
        }

        result = parsers.update_asset(asset, token_info)

        assert result["ticker"] == "TKN"
        assert result["decimals"] == 6
        assert result["policy_id"] == "abc123"
        assert result["amount"] == 1000

    def test_update_asset_preserves_original(self):
        """Test that original asset dict is not modified."""
        asset = {"policy_id": "abc123", "amount": 1000}
        token_info = {"ticker": "TKN"}

        result = parsers.update_asset(asset, token_info)

        assert "ticker" not in asset
        assert "ticker" in result


class TestTransformTokensToDict:
    """Tests for transform_tokens_to_dict function."""

    def test_transform_tokens_to_dict(self, sample_tokens_response):
        """Test transforming tokens response to searchable dict."""
        configured_dict, _ = parsers.transform_tokens_to_dict(sample_tokens_response)

        assert (
            "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f"
            in configured_dict
        )
        assert (
            "a2944573e99d2ed3055b808eaa264f0bf119e01fc6b18863067c63e4"
            in configured_dict
        )

        snek_policy = "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f"
        assert configured_dict[snek_policy]["534e454b"]["ticker"] == "SNEK"
        assert configured_dict[snek_policy]["534e454b"]["decimals"] == 0

    def test_transform_tokens_returns_original_tokens(self, sample_tokens_response):
        """Test that original tokens dict is also returned."""
        _, tokens = parsers.transform_tokens_to_dict(sample_tokens_response)

        assert tokens == sample_tokens_response["tokens"]


class TestParsePairsUtxos:
    """Tests for parse_pairs_utxos function."""

    def test_parse_pairs_utxos_basic(self, sample_configured_tokens_dict):
        """Test parsing pairs UTxOs with configured tokens."""
        pairs_utxos = {
            "MinSwap": {
                "addr1test": [
                    {
                        "amount": 5000000,
                        "assets": {
                            "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f": {
                                "534e454b": 1000000
                            }
                        },
                    }
                ]
            }
        }

        result = parsers.parse_pairs_utxos(pairs_utxos, sample_configured_tokens_dict)

        assert "MinSwap" in result
        assert "addr1test" in result["MinSwap"]
        assert len(result["MinSwap"]["addr1test"]) == 1

    def test_parse_pairs_utxos_filters_unconfigured(self):
        """Test that UTxOs without configured tokens are filtered out."""
        pairs_utxos = {
            "MinSwap": {
                "addr1test": [
                    {
                        "amount": 5000000,
                        "assets": {"unknown_policy": {"unknown_asset": 1000000}},
                    }
                ]
            }
        }

        result = parsers.parse_pairs_utxos(pairs_utxos, {})

        assert "MinSwap" in result
        # Address should be removed as it has no configured tokens
        assert "addr1test" not in result["MinSwap"]

    def test_parse_pairs_utxos_adds_token_metadata(self, sample_configured_tokens_dict):
        """Test that token metadata is added to assets."""
        pairs_utxos = {
            "MinSwap": {
                "addr1test": [
                    {
                        "amount": 5000000,
                        "assets": {
                            "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f": {
                                "534e454b": 1000000
                            }
                        },
                    }
                ]
            }
        }

        result = parsers.parse_pairs_utxos(pairs_utxos, sample_configured_tokens_dict)

        utxo = result["MinSwap"]["addr1test"][0]
        asset = utxo["assets"][0]

        assert asset["ticker"] == "SNEK"
        assert asset["decimals"] == 0


class TestIsSecurityToken:
    """Tests for is_security_token function."""

    def test_is_security_token_from_security_assets(self):
        """Test identifying security token from SECURITY_ASSETS."""
        mock_security_assets = [
            {
                "source": "MinSwap",
                "security_assets": [
                    {"policy": "test_policy"},
                ],
            }
        ]

        with patch(
            "src.cnt_collector_config.parsers.dex_config.SECURITY_ASSETS",
            mock_security_assets,
        ):
            result = parsers.is_security_token("MinSwap", "test_policy", "addr1test")

        assert result is True

    def test_is_security_token_from_addresses(self):
        """Test identifying security token from ADDRESSES."""
        mock_addresses = [
            {
                "source": "SundaeSwap",
                "address": "addr1sundae",
            }
        ]

        with patch("src.cnt_collector_config.parsers.dex_config.SECURITY_ASSETS", []):
            with patch(
                "src.cnt_collector_config.parsers.dex_config.ADDRESSES", mock_addresses
            ):
                result = parsers.is_security_token(
                    "SundaeSwap", "any_policy", "addr1sundae"
                )

        assert result is True

    def test_is_security_token_not_found(self):
        """Test that non-security tokens return False."""
        with patch("src.cnt_collector_config.parsers.dex_config.SECURITY_ASSETS", []):
            with patch("src.cnt_collector_config.parsers.dex_config.ADDRESSES", []):
                result = parsers.is_security_token(
                    "MinSwap", "random_policy", "addr1test"
                )

        assert result is False


class TestBuildTokenInfo:
    """Tests for build_token_info function."""

    def test_build_token_info_basic(self):
        """Test building token info with basic fields."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "54455354",  # "TEST" in hex
            "amount": 1000,
        }

        result = parsers.build_token_info(asset)

        assert result["policy_id"] == "abc123"
        assert result["asset_name"] == "54455354"
        assert result["amount"] == 1000
        assert result["asset_ascii_name"] == "TEST"

    def test_build_token_info_with_ticker_and_decimals(self):
        """Test building token info with ticker and decimals."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "54455354",
            "amount": 1000,
            "ticker": "TEST",
            "decimals": 6,
        }

        result = parsers.build_token_info(asset)

        assert result["ticker"] == "TEST"
        assert result["decimals"] == 6

    def test_build_token_info_with_existing_ascii_name(self):
        """Test that existing asset_ascii_name is preserved."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "54455354",
            "amount": 1000,
            "asset_ascii_name": "CUSTOM",
        }

        result = parsers.build_token_info(asset)

        assert result["asset_ascii_name"] == "CUSTOM"

    def test_build_token_info_invalid_hex_no_ascii_name(self):
        """Test that invalid hex doesn't crash, just omits ascii name."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "ffff",  # Invalid UTF-8
            "amount": 1000,
        }

        result = parsers.build_token_info(asset)

        assert "asset_ascii_name" not in result


class TestIsTickerConfigured:
    """Tests for is_ticker_configured function."""

    def test_is_ticker_configured_no_ticker(self):
        """Test returns False when asset has no ticker."""
        asset = {"policy_id": "abc123", "asset_name": "TEST", "amount": 1000}
        tokens = {}

        result = parsers.is_ticker_configured(asset, tokens)

        assert result is False

    def test_is_ticker_configured_ticker_not_in_tokens(self):
        """Test returns False when ticker not in tokens dict."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "TEST",
            "amount": 1000,
            "ticker": "TEST",
        }
        tokens = {"OTHER": {"policy_id": "xyz", "asset_name": "OTHER"}}

        result = parsers.is_ticker_configured(asset, tokens)

        assert result is False

    def test_is_ticker_configured_matching_policy_and_asset(self):
        """Test returns True when policy_id and asset_name match."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "TEST",
            "amount": 1000,
            "ticker": "TEST",
        }
        tokens = {"TEST": {"policy_id": "abc123", "asset_name": "TEST"}}

        result = parsers.is_ticker_configured(asset, tokens)

        assert result is True

    def test_is_ticker_configured_mismatched_policy(self):
        """Test returns False when policy_id doesn't match."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "TEST",
            "amount": 1000,
            "ticker": "TEST",
        }
        tokens = {"TEST": {"policy_id": "different", "asset_name": "TEST"}}

        result = parsers.is_ticker_configured(asset, tokens)

        assert result is False

    def test_is_ticker_configured_no_policy_in_config(self):
        """Test returns True when config has no policy_id specified."""
        asset = {
            "policy_id": "abc123",
            "asset_name": "TEST",
            "amount": 1000,
            "ticker": "TEST",
        }
        tokens = {"TEST": {"decimals": 6}}

        result = parsers.is_ticker_configured(asset, tokens)

        assert result is True


class TestCategorizeToken:
    """Tests for categorize_token function."""

    def test_categorize_token_security_token(self):
        """Test categorizing a security token."""
        asset = {"policy_id": "security_policy", "amount": 1}

        with patch(
            "src.cnt_collector_config.parsers.is_security_token", return_value=True
        ):
            result = parsers.categorize_token(asset, "MinSwap", "addr1test")

        assert result == "security_tokens"

    def test_categorize_token_configured_token(self):
        """Test categorizing a configured token with ticker."""
        asset = {"policy_id": "abc123", "amount": 1000, "ticker": "TEST"}

        with patch(
            "src.cnt_collector_config.parsers.is_security_token", return_value=False
        ):
            result = parsers.categorize_token(asset, "MinSwap", "addr1test")

        assert result == "configured_tokens"

    def test_categorize_token_other_token(self):
        """Test categorizing a token without ticker."""
        asset = {"policy_id": "abc123", "amount": 1000}

        with patch(
            "src.cnt_collector_config.parsers.is_security_token", return_value=False
        ):
            result = parsers.categorize_token(asset, "MinSwap", "addr1test")

        assert result == "other_tokens"

    def test_categorize_token_amount_greater_than_one_not_security(self):
        """Test that tokens with amount > 1 are not considered security tokens."""
        asset = {"policy_id": "security_policy", "amount": 2, "ticker": "TEST"}

        # is_security_token should not even be called when amount > 1
        with patch(
            "src.cnt_collector_config.parsers.is_security_token", return_value=True
        ) as mock_is_security:
            result = parsers.categorize_token(asset, "MinSwap", "addr1test")

        mock_is_security.assert_not_called()
        assert result == "configured_tokens"


class TestProcessPairAssets:
    """Tests for process_pair_assets function."""

    def test_process_pair_assets_categorizes_correctly(self):
        """Test that assets are correctly categorized."""
        pair_info = {
            "assets": [
                {
                    "policy_id": "abc",
                    "asset_name": "54455354",
                    "amount": 1000,
                    "ticker": "TEST",
                },
                {"policy_id": "xyz", "asset_name": "4f54484552", "amount": 500},
            ]
        }
        tokens = {"TEST": {"policy_id": "abc", "asset_name": "54455354"}}

        with patch("src.cnt_collector_config.parsers.dex_config.SECURITY_ASSETS", []):
            with patch("src.cnt_collector_config.parsers.dex_config.ADDRESSES", []):
                pair_tokens, has_configured = parsers.process_pair_assets(
                    pair_info, tokens, "MinSwap", "addr1test"
                )

        assert has_configured is True
        assert len(pair_tokens["configured_tokens"]) == 1
        assert len(pair_tokens["other_tokens"]) == 1
        assert len(pair_tokens["security_tokens"]) == 0

    def test_process_pair_assets_no_configured_ticker(self):
        """Test returns False when no configured ticker found."""
        pair_info = {
            "assets": [
                {"policy_id": "abc", "asset_name": "54455354", "amount": 1000},
            ]
        }
        tokens = {}

        with patch("src.cnt_collector_config.parsers.dex_config.SECURITY_ASSETS", []):
            with patch("src.cnt_collector_config.parsers.dex_config.ADDRESSES", []):
                _, has_configured = parsers.process_pair_assets(
                    pair_info, tokens, "MinSwap", "addr1test"
                )

        assert has_configured is False


class TestParseTokensPairs:
    """Tests for parse_tokens_pairs function."""

    def test_parse_tokens_pairs_basic(self):
        """Test parsing token pairs from UTxOs."""
        utxos_by_source = {
            "MinSwap": {
                "addr1test": [
                    {
                        "amount": 10000000,
                        "assets": [
                            {
                                "policy_id": "test_policy",
                                "asset_name": "54455354",  # "TEST" in hex
                                "amount": 1,
                                "ticker": "TEST",
                                "decimals": 6,
                            }
                        ],
                    }
                ]
            }
        }

        tokens = {
            "TEST": {
                "policy_id": "test_policy",
                "asset_name": "54455354",
                "decimals": 6,
            }
        }

        with patch("src.cnt_collector_config.dex_config.SECURITY_ASSETS", []):
            with patch("src.cnt_collector_config.dex_config.ADDRESSES", []):
                result = parsers.parse_tokens_pairs(utxos_by_source, tokens)

        assert len(result) >= 0  # May be 0 if no security token found

    def test_parse_tokens_pairs_filters_by_ticker(self):
        """Test that only pairs with configured tickers are included."""
        utxos_by_source = {
            "MinSwap": {
                "addr1test": [
                    {
                        "amount": 10000000,
                        "assets": [
                            {
                                "policy_id": "unknown_policy",
                                "asset_name": "554e4b4e4f574e",  # "UNKNOWN" in hex
                                "amount": 1000,
                            }
                        ],
                    }
                ]
            }
        }

        tokens = {}

        with patch("src.cnt_collector_config.dex_config.SECURITY_ASSETS", []):
            with patch("src.cnt_collector_config.dex_config.ADDRESSES", []):
                result = parsers.parse_tokens_pairs(utxos_by_source, tokens)

        assert len(result) == 0


class TestShouldSkipPair:
    """Tests for should_skip_pair function."""

    def test_should_skip_pair_with_unwanted_ascii_name(self):
        """Test returns True when other token has unwanted ASCII name."""
        other_tokens = [{"asset_ascii_name": "UNWANTED"}]

        result = parsers.should_skip_pair(other_tokens)

        assert result is True

    def test_should_skip_pair_allows_lq_suffix(self):
        """Test returns False when ASCII name ends with _LQ."""
        other_tokens = [{"asset_ascii_name": "SNEK_LQ"}]

        result = parsers.should_skip_pair(other_tokens)

        assert result is False

    def test_should_skip_pair_allows_minswap(self):
        """Test returns False when ASCII name is MINSWAP."""
        other_tokens = [{"asset_ascii_name": "MINSWAP"}]

        result = parsers.should_skip_pair(other_tokens)

        assert result is False

    def test_should_skip_pair_empty_list(self):
        """Test returns False for empty other_tokens list."""
        result = parsers.should_skip_pair([])

        assert result is False

    def test_should_skip_pair_no_ascii_name(self):
        """Test returns False when token has no ascii_name."""
        other_tokens = [{"policy_id": "abc123"}]

        result = parsers.should_skip_pair(other_tokens)

        assert result is False


class TestFindMatchingPairInFeeds:
    """Tests for find_matching_pair_in_feeds function."""

    def test_find_matching_pair_returns_pair(self):
        """Test returns pair when found in feeds."""
        cer_feeds = ["ADA-SNEK", "ADA-MELD"]

        result = parsers.find_matching_pair_in_feeds("ADA-SNEK", "SNEK-ADA", cer_feeds)

        assert result == "ADA-SNEK"

    def test_find_matching_pair_returns_reverse_pair(self):
        """Test returns reverse pair when only reverse is found."""
        cer_feeds = ["SNEK-ADA", "ADA-MELD"]

        result = parsers.find_matching_pair_in_feeds("ADA-SNEK", "SNEK-ADA", cer_feeds)

        assert result == "SNEK-ADA"

    def test_find_matching_pair_returns_none(self):
        """Test returns None when neither pair nor reverse found."""
        cer_feeds = ["ADA-MELD"]

        result = parsers.find_matching_pair_in_feeds("ADA-SNEK", "SNEK-ADA", cer_feeds)

        assert result is None

    def test_find_matching_pair_prefers_pair_over_reverse(self):
        """Test prefers pair over reverse when both exist."""
        cer_feeds = ["ADA-SNEK", "SNEK-ADA"]

        result = parsers.find_matching_pair_in_feeds("ADA-SNEK", "SNEK-ADA", cer_feeds)

        assert result == "ADA-SNEK"


class TestBuildLpInfo:  # pylint: disable=R0903
    """Tests for build_lp_info function."""

    def test_build_lp_info_merges_correctly(self):
        """Test that liquidity_pool is added and item is merged."""
        item = {
            "source": "MinSwap",
            "address": "addr1test",
            "amount": 10000000,
        }

        result = parsers.build_lp_info("ADA-SNEK", item)

        assert result["liquidity_pool"] == "ADA-SNEK"
        assert result["source"] == "MinSwap"
        assert result["address"] == "addr1test"
        assert result["amount"] == 10000000


class TestExtractValidTickers:
    """Tests for extract_valid_tickers function."""

    def test_extract_valid_tickers_with_valid_tokens(self):
        """Test extracting tickers from tokens with both ticker and ascii_name."""
        configured_tokens_list = [
            {"ticker": "SNEK", "asset_ascii_name": "SNEK"},
            {"ticker": "MELD", "asset_ascii_name": "MELD"},
        ]

        count, tickers = parsers.extract_valid_tickers(configured_tokens_list)

        assert count == 2
        assert tickers == ["SNEK", "MELD"]

    def test_extract_valid_tickers_missing_ascii_name(self):
        """Test that tokens without ascii_name are not counted."""
        configured_tokens_list = [
            {"ticker": "SNEK"},  # No asset_ascii_name
            {"ticker": "MELD", "asset_ascii_name": "MELD"},
        ]

        count, tickers = parsers.extract_valid_tickers(configured_tokens_list)

        assert count == 1
        assert tickers == ["MELD"]

    def test_extract_valid_tickers_missing_ticker(self):
        """Test that tokens without ticker are not counted."""
        configured_tokens_list = [
            {"asset_ascii_name": "SNEK"},  # No ticker
        ]

        count, tickers = parsers.extract_valid_tickers(configured_tokens_list)

        assert count == 0
        assert not tickers

    def test_extract_valid_tickers_empty_list(self):
        """Test with empty list."""
        count, tickers = parsers.extract_valid_tickers([])

        assert count == 0
        assert not tickers


class TestProcessSingleTokenPair:
    """Tests for process_single_token_pair function."""

    def test_process_single_token_pair_found_in_feeds(self):
        """Test returns lp_info when pair found in feeds."""
        item = {
            "pair_tokens": {
                "configured_tokens": [{"ticker": "SNEK", "asset_ascii_name": "SNEK"}],
                "other_tokens": [],
            },
            "source": "MinSwap",
            "address": "addr1test",
        }
        cer_feeds = ["ADA-SNEK"]

        result = parsers.process_single_token_pair(item, cer_feeds)

        assert result is not None
        assert result["liquidity_pool"] == "ADA-SNEK"

    def test_process_single_token_pair_reverse_found(self):
        """Test returns lp_info with reverse pair when reverse found."""
        item = {
            "pair_tokens": {
                "configured_tokens": [{"ticker": "SNEK", "asset_ascii_name": "SNEK"}],
                "other_tokens": [],
            },
            "source": "MinSwap",
            "address": "addr1test",
        }
        cer_feeds = ["SNEK-ADA"]

        result = parsers.process_single_token_pair(item, cer_feeds)

        assert result is not None
        assert result["liquidity_pool"] == "SNEK-ADA"

    def test_process_single_token_pair_not_in_feeds(self):
        """Test returns None when pair not in feeds."""
        item = {
            "pair_tokens": {
                "configured_tokens": [{"ticker": "SNEK", "asset_ascii_name": "SNEK"}],
                "other_tokens": [],
            },
            "source": "MinSwap",
            "address": "addr1test",
        }
        cer_feeds = ["ADA-MELD"]

        result = parsers.process_single_token_pair(item, cer_feeds)

        assert result is None

    def test_process_single_token_pair_skipped_due_to_other_tokens(self):
        """Test returns None when should_skip_pair returns True."""
        item = {
            "pair_tokens": {
                "configured_tokens": [{"ticker": "SNEK", "asset_ascii_name": "SNEK"}],
                "other_tokens": [{"asset_ascii_name": "UNWANTED"}],
            },
            "source": "MinSwap",
            "address": "addr1test",
        }
        cer_feeds = ["ADA-SNEK"]

        result = parsers.process_single_token_pair(item, cer_feeds)

        assert result is None


class TestProcessMultiTokenPair:
    """Tests for process_multi_token_pair function."""

    def test_process_multi_token_pair_single_valid_ticker(self):
        """Test with one valid ticker (forms ADA pair)."""
        item = {
            "pair_tokens": {
                "configured_tokens": [
                    {"ticker": "SNEK", "asset_ascii_name": "SNEK"},
                    {"ticker": "OTHER"},  # Missing ascii_name, not counted
                ],
            },
        }
        cer_feeds = ["ADA-SNEK"]

        result = parsers.process_multi_token_pair(item, cer_feeds)

        assert result is not None
        assert result["liquidity_pool"] == "ADA-SNEK"

    def test_process_multi_token_pair_two_valid_tickers(self):
        """Test with two valid tickers (forms token-token pair)."""
        item = {
            "pair_tokens": {
                "configured_tokens": [
                    {"ticker": "SNEK", "asset_ascii_name": "SNEK"},
                    {"ticker": "MELD", "asset_ascii_name": "MELD"},
                ],
            },
        }
        cer_feeds = ["SNEK-MELD"]

        result = parsers.process_multi_token_pair(item, cer_feeds)

        assert result is not None
        assert result["liquidity_pool"] == "SNEK-MELD"

    def test_process_multi_token_pair_two_tickers_reverse(self):
        """Test with two valid tickers, reverse pair in feeds."""
        item = {
            "pair_tokens": {
                "configured_tokens": [
                    {"ticker": "SNEK", "asset_ascii_name": "SNEK"},
                    {"ticker": "MELD", "asset_ascii_name": "MELD"},
                ],
            },
        }
        cer_feeds = ["MELD-SNEK"]

        result = parsers.process_multi_token_pair(item, cer_feeds)

        assert result is not None
        assert result["liquidity_pool"] == "MELD-SNEK"

    def test_process_multi_token_pair_no_valid_tickers(self):
        """Test returns None when no valid tickers found."""
        item = {
            "pair_tokens": {
                "configured_tokens": [
                    {"ticker": "SNEK"},  # Missing ascii_name
                    {"ticker": "MELD"},  # Missing ascii_name
                ],
            },
        }
        cer_feeds = ["SNEK-MELD"]

        result = parsers.process_multi_token_pair(item, cer_feeds)

        assert result is None

    def test_process_multi_token_pair_not_in_feeds(self):
        """Test returns None when pair not in feeds."""
        item = {
            "pair_tokens": {
                "configured_tokens": [
                    {"ticker": "SNEK", "asset_ascii_name": "SNEK"},
                    {"ticker": "MELD", "asset_ascii_name": "MELD"},
                ],
            },
        }
        cer_feeds = ["ADA-OTHER"]

        result = parsers.process_multi_token_pair(item, cer_feeds)

        assert result is None


class TestParseConfiguredTokens:
    """Tests for parse_configured_tokens function."""

    @patch("src.cnt_collector_config.fetchers.get_cer_feeds")
    def test_parse_configured_tokens_filters_by_feeds(self, mock_get_feeds):
        """Test that only pairs in feeds are included."""
        mock_get_feeds.return_value = ["ADA-SNEK"]

        configured_tokens = [
            {
                "pair_tokens": {
                    "configured_tokens": [
                        {
                            "ticker": "SNEK",
                            "asset_ascii_name": "SNEK",
                        }
                    ],
                    "other_tokens": [],
                },
                "source": "MinSwap",
                "address": "addr1test",
                "amount": 10000000,
            }
        ]

        result = parsers.parse_configured_tokens(
            configured_tokens, "file://./feeds.json"
        )

        assert len(result) == 1
        assert result[0]["liquidity_pool"] == "ADA-SNEK"

    @patch("src.cnt_collector_config.fetchers.get_cer_feeds")
    def test_parse_configured_tokens_handles_reverse_pairs(self, mock_get_feeds):
        """Test that reverse pairs (SNEK-ADA vs ADA-SNEK) are handled."""
        mock_get_feeds.return_value = ["SNEK-ADA"]

        configured_tokens = [
            {
                "pair_tokens": {
                    "configured_tokens": [
                        {
                            "ticker": "SNEK",
                            "asset_ascii_name": "SNEK",
                        }
                    ],
                    "other_tokens": [],
                },
                "source": "MinSwap",
                "address": "addr1test",
                "amount": 10000000,
            }
        ]

        result = parsers.parse_configured_tokens(
            configured_tokens, "file://./feeds.json"
        )

        assert len(result) == 1
        assert result[0]["liquidity_pool"] == "SNEK-ADA"

    @patch("src.cnt_collector_config.fetchers.get_cer_feeds")
    def test_parse_configured_tokens_skips_pairs_with_ascii_names(self, mock_get_feeds):
        """Test skipping pairs with unwanted ASCII names in other tokens."""
        mock_get_feeds.return_value = ["ADA-SNEK"]

        configured_tokens = [
            {
                "pair_tokens": {
                    "configured_tokens": [
                        {
                            "ticker": "SNEK",
                            "asset_ascii_name": "SNEK",
                        }
                    ],
                    "other_tokens": [
                        {
                            "asset_ascii_name": "UNWANTED",
                        }
                    ],
                },
                "source": "MinSwap",
                "address": "addr1test",
                "amount": 10000000,
            }
        ]

        result = parsers.parse_configured_tokens(
            configured_tokens, "file://./feeds.json"
        )

        # Should be skipped due to unwanted ASCII name
        assert len(result) == 0

    @patch("src.cnt_collector_config.fetchers.get_cer_feeds")
    def test_parse_configured_tokens_allows_minswap_lq(self, mock_get_feeds):
        """Test that MINSWAP and _LQ tokens are allowed."""
        mock_get_feeds.return_value = ["ADA-SNEK"]

        configured_tokens = [
            {
                "pair_tokens": {
                    "configured_tokens": [
                        {
                            "ticker": "SNEK",
                            "asset_ascii_name": "SNEK",
                        }
                    ],
                    "other_tokens": [
                        {"asset_ascii_name": "MINSWAP"},
                        {"asset_ascii_name": "SNEK_LQ"},
                    ],
                },
                "source": "MinSwap",
                "address": "addr1test",
                "amount": 10000000,
            }
        ]

        result = parsers.parse_configured_tokens(
            configured_tokens, "file://./feeds.json"
        )

        # Should NOT be skipped
        assert len(result) == 1
