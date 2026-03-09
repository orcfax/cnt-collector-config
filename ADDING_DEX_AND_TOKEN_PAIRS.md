# Adding and Removing AMM DEX and Token Pairs

This document describes how to add or remove AMM (Automated Market Maker) DEXes
(Decentralized Exchanges) and token pairs from the CNT (Cardano Native Tokens)
Collector Config project.

## Table of Contents

<!-- TOC via: https://luciopaiva.com/markdown-toc/ -->

- [Overview](#overview)
- [Criteria for Adding/Removing](#criteria-for-addingremoving)
  - [Adding a Liquidity Pool](#adding-a-liquidity-pool)
  - [Removing a Liquidity Pool](#removing-a-liquidity-pool)
  - [Adding a New DEX](#adding-a-new-dex)
  - [Removing a DEX](#removing-a-dex)
- [Adding a New Token Pair](#adding-a-new-token-pair)
  - [Step 1: Add Token Metadata to `tokens.json`](#step-1-add-token-metadata-to-tokensjson)
  - [Step 2: Add Feed Entry to `cer-feeds.json`](#step-2-add-feed-entry-to-cer-feedsjson)
  - [Step 3: Run the Config Generator](#step-3-run-the-config-generator)
- [Adding a New AMM DEX](#adding-a-new-amm-dex)
  - [Approach 1: Security Token-Based DEX](#approach-1-security-token-based-dex)
  - [Approach 2: Address-Based DEX](#approach-2-address-based-dex)
  - [Finding DEX Configuration Values](#finding-dex-configuration-values)
  - [Testing the New DEX](#testing-the-new-dex)
- [Removing Token Pairs or DEXes](#removing-token-pairs-or-dexes)
  - [Removing a Token Pair](#removing-a-token-pair)
  - [Removing a DEX Entry](#removing-a-dex-entry)
- [Configuration Files Reference](#configuration-files-reference)
  - [`tokens.json`](#tokensjson)
  - [`cer-feeds.json`](#cer-feedsjson)
  - [`src/cnt_collector_config/dex_config.py`](#srccnt_collector_configdex_configpy)
  - [`generated_config.py` (Output)](#generated_configpy-output)
- [Troubleshooting](#troubleshooting)
  - [Pool Not Discovered](#pool-not-discovered)
  - [Wrong Token Decimals](#wrong-token-decimals)
  - [DEX Version Changes](#dex-version-changes)
- [Quick Reference](#quick-reference)

---

## Overview

The CNT Collector Config generates liquidity pool configurations by:

1. Querying Kupo for UTxOs at configured DEX addresses/policies
2. Filtering for token pairs defined in `cer-feeds.json`
3. Using token metadata from `tokens.json`
4. Generating `generated_config.py` for use by `cnt-collector-node`

To add new token pairs or DEXes, you need to update the appropriate
configuration files.

---

## Criteria for Adding/Removing

### Adding a Liquidity Pool

A liquidity pool should be added if it meets **both** criteria:

1. **Minimum 10,000 ADA locked** in the pool
2. **At least 1% of total token liquidity** from the token's circulating supply

The amount of ADA locked in a Liquidity Pool can usually be observed on the
DEX's Liquidity Pool details page. The TVL (Total Value Locked) is typically
expressed in ADA, and half of that TVL is ADA (assuming the pair includes ADA,
not two different CNTs).

The total token liquidity (or Circulating Supply) can be checked on a
Blockchain Explorer. The amount of tokens locked in a Liquidity Pool can be
checked on the UTxO representing the Liquidity Pool on-chain. It can also be
calculated from the Liquidity Pool's TVL and the price of the token.

### Removing a Liquidity Pool

Remove a liquidity pool if it no longer meets the criteria above:

- Pool liquidity drops below 10,000 ADA
- Pool holds less than 1% of the token's total liquidity

### Adding a New DEX

Consider adding a new DEX if:

1. The DEX has significant trading volume on Cardano
2. Multiple tracked token pairs have liquidity pools on the DEX
3. The DEX's smart contract architecture is understood (security tokens or
   address-based identification)
4. Pool UTxOs can be reliably identified via Kupo queries

### Removing a DEX

Remove a DEX if:

1. The DEX is deprecated or no longer operational
2. All pools on the DEX fall below liquidity thresholds

---

## Adding a New Token Pair

Adding a new token pair requires updates to two files:

### Step 1: Add Token Metadata to `tokens.json`

Add the token's metadata under the `"tokens"` object:

```json
{
    "tokens": {
        "NEW_TOKEN": {
            "policy_id": "<56-character-hex-policy-id>",
            "asset_name": "<hex-encoded-asset-name>",
            "decimals": 6,
            "total_supply": 1000000000,
        }
    }
}
```

The `total_supply` is optional and should be the real circulating supply
of the token, if this is fixed. For tokens which have regular mints this should
be skipped.

**Required fields:**

| Field | Description |
|---|---|
| `policy_id` | Cardano policy ID (56 hex characters) |
| `asset_name` | Hex-encoded asset name |
| `decimals` | Number of decimal places (0-9) |

**Examples:**

- `policy_id`: `"29d222ce...267170c6"` (56 hex chars)
- `asset_name`: `"4d494e"` (hex for "MIN")
- `decimals`: `6`

**How to find these values:**

- Use a Cardano explorer (CardanoScan, CExplorer) to look up the token
- Policy ID and asset name are visible in the token's on-chain metadata
- Decimals and total_supply can be found in the token's
  CIP-26/CIP-68 metadata or official docs

### Step 2: Add Feed Entry to `cer-feeds.json`

Add the token pair under the `"feeds"` array:

```json
{
    "feeds": [
        {
            "pair": "NEW_TOKEN-ADA",
            "label": "NEW_TOKEN-ADA",
            "interval": 3600,
            "deviation": 2,
            "source": "dex",
            "calculation": "weighted mean",
            "status": "showcase",
            "type": "CER"
        }
    ]
}
```

**Required fields for DEX pairs:**

| Field | Description | Example |
|---|---|---|
| `pair` | Token pair (TICKER1-TICKER2) | `"SNEK-ADA"` |
| `label` | Display label (same as pair) | `"SNEK-ADA"` |
| `interval` | Update interval in seconds | `3600` |
| `deviation` | Price deviation threshold (%) | `2` |
| `source` | Must be `"dex"` | `"dex"` |
| `calculation` | Price calculation method | `"weighted mean"` |
| `status` | Feed status | `"showcase"` |
| `type` | Feed type | `"CER"` |

**Important:** Only feeds with `"source": "dex"` are processed by this tool.

### Step 3: Run the Config Generator

```bash
python -m src.cnt_collector_config.main
```

The tool will automatically discover liquidity pools for the new token pair
across all configured DEXes.

---

## Adding a New AMM DEX

Adding a new DEX requires understanding how its liquidity pools are identified
on-chain. There are two approaches:

### Approach 1: Security Token-Based DEX

Most DEXes use security tokens (NFTs or fungible tokens) to identify their
liquidity pool UTxOs.

**Edit `src/cnt_collector_config/dex_config.py`:**

Add a new entry to the `SECURITY_ASSETS` list:

```python
SECURITY_ASSETS = [
    # ... existing entries ...
    {
        "source": "NewDEX",
        "security_assets": [
            {
                "policy": "<security-token-policy-id>",
                # "asset": "<optional-specific-asset-name>",  # Only if needed
            },
        ],
    },
]
```

**Configuration fields:**

| Field | Required | Description |
|---|---|---|
| `source` | Yes | DEX identifier (used in output config) |
| `security_assets` | Yes | List of security token configs |
| `policy` | Yes | Policy ID of the security token |
| `asset` | No | Asset name (if policy has multiple uses) |

**Examples from existing DEXes:**

```python
# Simple: Single policy, no asset filter
{
    "source": "MinSwap",
    "security_assets": [
        {"policy": "0be55d262b29f564998ff81efe21bdc0022621c12f15af08d0f2ddb1"},
    ],
},

# With asset filter: Same policy, specific asset name
{
    "source": "WingRiders",
    "security_assets": [
        {
            "policy": "026a18d04a0c642759bb3d83b12e3344894e5c1c7b2aeb1a2113a570",
            "asset": "4c",  # Hex for "L"
        },
    ],
},

# Multiple policies: Different policies for different pairs
{
    "source": "Splash",
    "security_assets": [
        # ADA-USDM
        {"policy": "7a3b08bf74ac6283edf40087f4b53e9b01b0d46a59fee3dd417fda9d"},
        # STRIKE-ADA
        {"policy": "e73e65176c6bd31dbc878e317e852c826a534fb949d279a463ecbd18"},
        # ... more policies ...
    ],
},
```

#### Finding Security Tokens for Splash DEX

The security token policy and asset name can be extracted from a Splash
liquidity pool URL. For example, the ADA-USDM pool:

```text
https://app.splash.trade/liquidity/<policy>.<asset_name>
https://app.splash.trade/liquidity/7a3b08bf74ac6283edf40087f4b53e9b01b0d46a59fee3dd417fda9d.0014df105553444d5f4144415f4e4654
```

The URL uses a dot (`.`) as delimiter between the two parts:

- **Policy:** `7a3b08bf74ac6283edf40087f4b53e9b01b0d46a59fee3dd417fda9d`
- **Asset name:** `0014df105553444d5f4144415f4e4654`

> **Tip:** Check the policy on CardanoScan. If only one asset exists under
> that policy, the policy ID alone is enough to uniquely identify the pool
> UTxO — no `asset` filter is needed in `dex_config.py`.

#### Finding Security Tokens for CSwap DEX

CSwap pool URLs follow the same pattern but **concatenate** the policy and
asset name without a delimiter:

```text
https://cswap.trade/pools/<policy><asset_name>
```

For example, the IAG-ADA pool:

```text
https://cswap.trade/pools/a00d48eff61d8cfd86b5795d0b15015b84a33f139f22e7c8e3005c34432d4c503a20414441207820494147
```

Since Cardano policy IDs are always 56 hex characters, split the URL path at
character 56 to separate the policy from the asset name:

- **Policy:** `a00d48eff61d8cfd86b5795d0b15015b84a33f139f22e7c8e3005c34`
- **Asset name:** `432d4c503a20414441207820494147`

### Approach 2: Address-Based DEX

Some DEXes (like SundaeSwap V1) identify pools by smart contract address rather
than security tokens.

**Edit `src/cnt_collector_config/dex_config.py`:**

Add a new entry to the `ADDRESSES` list:

```python
ADDRESSES = [
    # ... existing entries ...
    {
        "source": "NewDEX",
        "address": "addr1...",
    },
]
```

**Configuration fields:**

| Field     | Required | Description                                 |
|-----------|----------|---------------------------------------------|
| `source`  | Yes      | DEX identifier name (used in output config) |
| `address` | Yes      | Smart contract address for the DEX pools    |

**Example:**

```python
{
    "source": "SundaeSwap",
    "address": "addr1w9qzpelu9hn45pefc0xr4ac4kdxeswq7pndul2vuj59u8tqaxdznu",
},
```

### Finding DEX Configuration Values

To configure a new DEX, you need to identify:

1. **Security token policy IDs** or **smart contract addresses**
2. **How pool UTxOs are structured** (which assets they hold)

Methods to find this information:

1. **DEX Documentation** - Check official docs for smart contract details
2. **Cardano Explorers** - Examine known pool UTxOs on CardanoScan/CExplorer
3. **DEX Aggregators** - DexHunter, TapTools often list pool addresses
4. **Open Source Code** - Many DEXes publish their contract code on GitHub

### Testing the New DEX

After adding the configuration:

```bash
# Run the config generator
python -m src.cnt_collector_config.main

# Check the output for new DEX entries
grep "NewDEX" generated_config.py
```

Verify that:

- Pools are discovered for existing token pairs
- The `source` field correctly identifies the DEX
- Token amounts and addresses are valid

---

## Removing Token Pairs or DEXes

### Removing a Token Pair

1. **Remove from `cer-feeds.json`** - Delete the feed entry for the pair
2. **Optionally remove from `tokens.json`** - Only if the token is not used by
   any other pairs

The next config generation will exclude the removed pair.

### Removing a DEX Entry

**Edit `src/cnt_collector_config/dex_config.py`:**

1. Remove the entry from `SECURITY_ASSETS` or `ADDRESSES`
2. Add a comment noting why it was removed (for historical reference)

Example (from existing code):

```python
# Spectrum (removed - low liquidity)
```

---

## Configuration Files Reference

### `tokens.json`

Token metadata file containing policy IDs, asset names, and decimals.

**Location:** Project root

**Structure:**

```json
{
    "meta": {
        "description": "active Orcfax tokens",
        "version": "YYYY.MM.DD.NNNN"
    },
    "tokens": {
        "TICKER": {
            "policy_id": "56-char-hex",
            "asset_name": "hex-encoded-name",
            "decimals": 6
        }
    }
}
```

### `cer-feeds.json`

Feed configuration defining which token pairs to track.

**Location:** Project root

**Structure:**

```json
{
    "meta": {
        "description": "active Orcfax CER feeds (mainnet)",
        "version": "YYYY.MM.DD.NNNN"
    },
    "feeds": [
        {
            "pair": "TOKEN-ADA",
            "label": "TOKEN-ADA",
            "interval": 3600,
            "deviation": 2,
            "source": "dex",
            "calculation": "weighted mean",
            "status": "showcase",
            "type": "CER"
        }
    ]
}
```

### `src/cnt_collector_config/dex_config.py`

DEX-specific configuration for identifying liquidity pools.

**Location:** `src/cnt_collector_config/`

**Structure:**

```python
SECURITY_ASSETS = [
    {
        "source": "DEXName",
        "security_assets": [
            {"policy": "policy-id", "asset": "optional-asset-name"},
        ],
    },
]

ADDRESSES = [
    {
        "source": "DEXName",
        "address": "addr1...",
    },
]
```

### `generated_config.py` (Output)

Auto-generated configuration file for `cnt-collector-node`.

**Location:** Configured via `--config-location` (default: `generated_config.py`)

**Structure:**

```python
DEX_PAIRS = [
    {
        "name": "TOKEN-ADA",
        "token1_policy": "policy-id",
        "token1_name": "asset-name-hex",
        "token1_decimals": 6,
        "token2_policy": "",
        "token2_name": "lovelace",
        "token2_decimals": 6,
        "sources": [
            {
                "source": "MinSwap",
                "address": "addr1...",
                "security_token_policy": "policy-id",
                "security_token_name": "asset-name-hex"
            }
        ]
    }
]
```

---

## Troubleshooting

### Pool Not Discovered

- Verify the DEX policy/address is correctly configured in `dex_config.py`
- Check that the token pair exists in both `tokens.json` and `cer-feeds.json`
- Ensure `"source": "dex"` is set in the feed entry
- Verify the pool meets minimum liquidity requirements (10k ADA)

### Wrong Token Decimals

- Update `decimals` in `tokens.json`
- Re-run the config generator

### DEX Version Changes

When a DEX upgrades (e.g., MinSwap V1 to V2):

1. Add new version as separate entry in `dex_config.py`
2. Keep old version if pools still have liquidity
3. Remove old version once all liquidity migrates

---

## Quick Reference

| Task                    | Files to Update                          |
|-------------------------|------------------------------------------|
| Add token pair          | `tokens.json`, `cer-feeds.json`          |
| Add new DEX             | `dex_config.py`                          |
| Remove token pair       | `cer-feeds.json` (optionally `tokens.json`) |
| Remove DEX              | `dex_config.py`                          |
| Change token decimals   | `tokens.json`                            |
| Add DEX version         | `dex_config.py` (new entry)              |
