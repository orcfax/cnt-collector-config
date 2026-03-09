"""Shared pytest fixtures for cnt-collector-config tests."""

import pytest


@pytest.fixture
def sample_tokens_response():
    """Sample tokens response from tokens.json."""
    return {
        "tokens": {
            "ADA": {
                "policy_id": "",
                "asset_name": "lovelace",
                "decimals": 6,
            },
            "SNEK": {
                "policy_id": "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f",
                "asset_name": "534e454b",
                "decimals": 0,
            },
            "MELD": {
                "policy_id": "a2944573e99d2ed3055b808eaa264f0bf119e01fc6b18863067c63e4",
                "asset_name": "4d454c44",
                "decimals": 6,
            },
        }
    }


@pytest.fixture
def sample_feeds_response():
    """Sample feeds response from cer-feeds.json."""
    return {
        "feeds": [
            {
                "label": "ADA-SNEK",
                "source": "dex",
            },
            {
                "label": "ADA-MELD",
                "source": "dex",
            },
            {
                "label": "BTC-USD",
                "source": "cex",
            },
        ]
    }


@pytest.fixture
def sample_utxo():
    """Sample UTxO from Kupo."""
    return {
        "transaction_id": "abc123",
        "output_index": 0,
        "address": "addr1test",
        "value": {
            "coins": 5000000,
            "assets": {
                "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f.534e454b": 1000000,
                "a2944573e99d2ed3055b808eaa264f0bf119e01fc6b18863067c63e4.4d454c44": 500000,
            },
        },
    }


@pytest.fixture
def sample_configured_tokens_dict():
    """Sample configured tokens dictionary."""
    return {
        "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f": {
            "534e454b": {
                "ticker": "SNEK",
                "decimals": 0,
            }
        },
        "a2944573e99d2ed3055b808eaa264f0bf119e01fc6b18863067c63e4": {
            "4d454c44": {
                "ticker": "MELD",
                "decimals": 6,
            }
        },
    }


@pytest.fixture
def sample_pair():
    """Sample liquidity pool pair."""
    return {
        "liquidity_pool": "ADA-SNEK",
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
