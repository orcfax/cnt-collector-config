"""Tests for generators module."""


from src.cnt_collector_config import generators


class TestCreateConfig:
    """Tests for create_config function."""

    def test_create_config_basic(self, sample_pair):
        """Test basic config generation from pairs."""
        pairs = [sample_pair]

        result = generators.create_config(pairs)

        assert len(result) == 1
        assert result[0]["name"] == "ADA-SNEK"

    def test_create_config_includes_token_metadata(self, sample_pair):
        """Test that token metadata is included in config."""
        pairs = [sample_pair]

        result = generators.create_config(pairs)

        config = result[0]
        assert config["token1_policy"] == ""  # ADA
        assert config["token1_name"] == "lovelace"
        assert config["token1_decimals"] == 6
        assert (
            config["token2_policy"]
            == "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f"
        )
        assert config["token2_name"] == "534e454b"
        assert config["token2_decimals"] == 0

    def test_create_config_includes_sources(self, sample_pair):
        """Test that sources are properly structured."""
        pairs = [sample_pair]

        result = generators.create_config(pairs)

        config = result[0]
        assert "sources" in config
        assert isinstance(config["sources"], list)
        assert len(config["sources"]) == 1
        assert config["sources"][0]["source"] == "MinSwap"
        assert config["sources"][0]["address"] == "addr1test"

    def test_create_config_handles_reverse_pair(self):
        """Test creating config for reverse pair (TOKEN-ADA)."""
        pair = {
            "liquidity_pool": "SNEK-ADA",
            "source": "MinSwap",
            "address": "addr1test",
            "amount": 10000000,
            "pair_tokens": {
                "security_tokens": [
                    {
                        "policy_id": "0be55d262b29f564998ff81efe21bdc0022621c12f15af08d0f2ddb1",
                        "asset_name": "",
                        "amount": 1,
                    }
                ],
                "configured_tokens": [
                    {
                        "policy_id": "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f",
                        "asset_name": "534e454b",
                        "ticker": "SNEK",
                        "decimals": 0,
                        "amount": 1000000,
                    }
                ],
                "other_tokens": [],
            },
        }

        result = generators.create_config([pair])

        assert len(result) == 1
        assert result[0]["name"] == "SNEK-ADA"
        # Token1 should be SNEK, Token2 should be ADA
        assert (
            result[0]["token1_policy"]
            == "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f"
        )
        assert result[0]["token2_name"] == "lovelace"

    def test_create_config_merges_same_pair_different_sources(self, sample_pair):
        """Test merging same pair from different DEXes."""
        pair1 = sample_pair.copy()
        pair1["source"] = "MinSwap"

        pair2 = sample_pair.copy()
        pair2["source"] = "SundaeSwap"
        pair2["address"] = "addr1sundae"

        result = generators.create_config([pair1, pair2])

        assert len(result) == 1
        config = result[0]
        assert len(config["sources"]) == 2
        sources = [s["source"] for s in config["sources"]]
        assert "MinSwap" in sources
        assert "SundaeSwap" in sources

    def test_create_config_selects_larger_liquidity(self, sample_pair):
        """Test selecting pool with larger liquidity for same source."""
        pair1 = sample_pair.copy()
        pair1["pair_tokens"]["configured_tokens"][0]["amount"] = 1000000
        pair1["amount"] = 5000000

        pair2 = sample_pair.copy()
        pair2["pair_tokens"]["configured_tokens"][0]["amount"] = 5000000
        pair2["amount"] = 20000000

        result = generators.create_config([pair1, pair2])

        assert len(result) == 1
        # Should select the larger liquidity pool

    def test_create_config_skips_pairs_without_security_token(self):
        """Test that pairs without security tokens are skipped."""
        pair_without_security = {
            "liquidity_pool": "ADA-SNEK",
            "source": "MinSwap",
            "address": "addr1test",
            "amount": 10000000,
            "pair_tokens": {
                "security_tokens": [],  # No security token
                "configured_tokens": [
                    {
                        "policy_id": "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f",
                        "asset_name": "534e454b",
                        "ticker": "SNEK",
                        "decimals": 0,
                        "amount": 1000000,
                    }
                ],
                "other_tokens": [],
            },
        }

        result = generators.create_config([pair_without_security])

        assert len(result) == 0

    def test_create_config_handles_token_token_pairs(self):
        """Test creating config for token-to-token pairs (no ADA)."""
        pair = {
            "liquidity_pool": "SNEK-MELD",
            "source": "MinSwap",
            "address": "addr1test",
            "amount": 10000000,
            "pair_tokens": {
                "security_tokens": [
                    {
                        "policy_id": "0be55d262b29f564998ff81efe21bdc0022621c12f15af08d0f2ddb1",
                        "asset_name": "",
                        "amount": 1,
                    }
                ],
                "configured_tokens": [
                    {
                        "policy_id": "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f",
                        "asset_name": "534e454b",
                        "ticker": "SNEK",
                        "decimals": 0,
                        "amount": 1000000,
                    },
                    {
                        "policy_id": "a2944573e99d2ed3055b808eaa264f0bf119e01fc6b18863067c63e4",
                        "asset_name": "4d454c44",
                        "ticker": "MELD",
                        "decimals": 6,
                        "amount": 500000,
                    },
                ],
                "other_tokens": [],
            },
        }

        result = generators.create_config([pair])

        assert len(result) == 1
        config = result[0]
        assert config["name"] == "SNEK-MELD"
        # Neither token should be lovelace
        assert config["token1_name"] != "lovelace"
        assert config["token2_name"] != "lovelace"

    def test_create_config_multiple_different_pairs(self):
        """Test creating config with multiple different pairs."""
        pair1 = {
            "liquidity_pool": "ADA-SNEK",
            "source": "MinSwap",
            "address": "addr1test1",
            "amount": 10000000,
            "pair_tokens": {
                "security_tokens": [
                    {"policy_id": "sec1", "asset_name": "", "amount": 1}
                ],
                "configured_tokens": [
                    {
                        "policy_id": "snek_policy",
                        "asset_name": "SNEK",
                        "ticker": "SNEK",
                        "decimals": 0,
                        "amount": 1000000,
                    }
                ],
                "other_tokens": [],
            },
        }

        pair2 = {
            "liquidity_pool": "ADA-MELD",
            "source": "MinSwap",
            "address": "addr1test2",
            "amount": 15000000,
            "pair_tokens": {
                "security_tokens": [
                    {"policy_id": "sec2", "asset_name": "", "amount": 1}
                ],
                "configured_tokens": [
                    {
                        "policy_id": "meld_policy",
                        "asset_name": "MELD",
                        "ticker": "MELD",
                        "decimals": 6,
                        "amount": 500000,
                    }
                ],
                "other_tokens": [],
            },
        }

        result = generators.create_config([pair1, pair2])

        assert len(result) == 2
        names = [config["name"] for config in result]
        assert "ADA-SNEK" in names
        assert "ADA-MELD" in names

    def test_create_config_preserves_security_token_info(self, sample_pair):
        """Test that security token policy and name are preserved."""
        pairs = [sample_pair]

        result = generators.create_config(pairs)

        config = result[0]
        source = config["sources"][0]
        assert (
            source["security_token_policy"]
            == "0be55d262b29f564998ff81efe21bdc0022621c12f15af08d0f2ddb1"
        )
        assert source["security_token_name"] == ""

    def test_create_config_handles_missing_decimals(self):
        """Test handling of tokens without decimals specified."""
        pair = {
            "liquidity_pool": "ADA-TOKEN",
            "source": "MinSwap",
            "address": "addr1test",
            "amount": 10000000,
            "pair_tokens": {
                "security_tokens": [
                    {"policy_id": "sec1", "asset_name": "", "amount": 1}
                ],
                "configured_tokens": [
                    {
                        "policy_id": "token_policy",
                        "asset_name": "TOKEN",
                        "ticker": "TOKEN",
                        # No decimals specified
                        "amount": 1000000,
                    }
                ],
                "other_tokens": [],
            },
        }

        result = generators.create_config([pair])

        assert len(result) == 1
        # Should default to 0 for missing decimals
        assert result[0]["token2_decimals"] == 0
