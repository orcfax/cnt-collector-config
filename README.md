# CNT (Cardano Native Tokens) Collector Config

Automated configuration generator for tracking Cardano Native Token (CNT) pairs
across multiple DEXes. This tool scans configured DEXes for liquidity pools,
filters by configured token pairs, and generates a config file for
`cnt-collector-node`.

## Supported DEXes

**AMM DEXes:**

- MinSwap (V1, V2)
- SundaeSwap (V1, V3)
- WingRiders (V1, V2)
- Spectrum (removed - low liquidity)
- Splash
- CSwap
- VyFi
- Snek.fun

**Order Book DEXes:**

- MuesliSwap (planned)
- GeniusYield (planned)

## Project Structure

The codebase is organized into focused modules:

- `main.py` - Orchestration and entry point
- `fetchers.py` - API/network interactions (Kupo, feeds, tokens)
- `parsers.py` - Data transformation and parsing logic
- `generators.py` - Configuration file generation
- `utils.py` - File I/O, CLI, and versioning
- `config.py` - Environment and URL configuration
- `dex_config.py` - DEX-specific policies and addresses

## Configuration

### config.py

Key variables to configure:

**`FEEDS_URL`** - URL or file path containing the list of tracked token
pairs (feeds)

**`TOKENS_URL`** - URL or file path containing token metadata
(policy IDs, asset names, decimals)

**`KUPO_URL`** - Kupo instance URL for querying blockchain data
(default: Orcfax internal)

In `TOKENS_URL`, the `policy_id` and `asset_name` must be declared
to avoid external dependencies:

```json
{
  "COPI": {},
  "MELD": {
    "policy_id": "a2944573e99d2ed3055b808eaa264f0bf119e01fc6b18863067c63e4",
    "asset_name": "4d454c44",
    "decimals": 6
  }
}
```

### dex_config.py

DEX-specific policies and smart contract addresses. Two main categories:

**`SECURITY_ASSETS`** - DEXes that use security tokens to identify
liquidity pool UTxOs

- Each pool has a unique or shared policy ID token
- Examples: MinSwap, WingRiders, Splash, CSwap, VyFi, Snek.fun

**`ADDRESSES`** - DEXes with pools at specific smart contract addresses

- UTxOs identified by address rather than security tokens
- Examples: SundaeSwap (V1)

Current configuration includes:

- **MinSwap** (V1 & V2)
- **WingRiders** (V1 & V2)
- **SundaeSwap** (V1 address-based, V3 policy-based)
- **Splash** (7 policy configurations for different pairs)
- **CSwap** (6 policy configurations)
- **VyFi** (5 policy configurations)
- **Snek.fun** (1 policy configuration)

## How It Works

1. **Fetch Configuration** - Reads feeds and token metadata from configured URLs
2. **Query Kupo** - Searches for UTxOs containing DEX security tokens or at DEX addresses
3. **Parse UTxOs** - Extracts token pairs and amounts from liquidity pool UTxOs
4. **Filter Pairs** - Selects pairs matching configured feeds
5. **Generate Config** - Creates `generated_config.py` for cnt-collector-node

## Adding/Removing Liquidity Pools

Add a liquidity pool (LP) if:

- LP has at least 10k ADA locked
- LP has at least 1% of total token liquidity

Remove if the pool no longer meets these criteria.

## Usage

### Basic Usage

From the repository root:

```bash
python -m src.cnt_collector_config.main
```

From the `src/cnt_collector_config` folder:

```bash
python main.py
```

### Command-Line Options

```bash
python -m src.cnt_collector_config.main \
  --kupo-url https://your-kupo-instance.com \
  --feeds-location file://./cer-feeds.json \
  --tokens-location file://./tokens.json \
  --config-location ./generated_config.py \
  --version
```

**Options:**

- `--kupo-url, -k` - Kupo instance URL
- `--feeds-location, -f` - Feeds configuration (URL or file://)
- `--tokens-location, -t` - Tokens configuration (URL or file://)
- `--config-location, -c` - Output file path
- `--version, -v` - Show version

### Execution Time

Runtime: ~2 minutes (depending on number of configured pairs)

**Output:** `generated_config.py` - Use as `pairs.py` in cnt-collector-node

## Developer install

### pip

Set up a virtual environment `venv` and install the local development
requirements as follows:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements/local.txt
```

### tox

#### Run tests (all)

```bash
python -m tox
```

#### Run tests-only

```bash
python -m tox -e py3
```

#### Run linting-only

```bash
python -m tox -e linting
```

### pre-commit

Pre-commit can be used to provide more feedback before committing code. This
reduces the number of commits you might want to make when working on code, it's
also an alternative to running tox manually.

To set up pre-commit, providing `pip install` has been run above:

- `pre-commit install`

This repository contains a default number of pre-commit hooks, but there may be
others suited to different projects. A list of other pre-commit hooks can be
found [here][pre-commit-1].

[pre-commit-1]: https://pre-commit.com/hooks.html

## Packaging

The `Makefile` contains helper functions for packaging and release.

Makefile functions can be reviewed by calling `make` from the root of this
repository:

```make
clean                          Clean the package directory
help                           Print this help message.
package-check                  Check the distribution is valid
package-deps                   Upgrade dependencies for packaging
package-source                 Package the source code
package-upload                 Upload package to pypi
package-upload-test            Upload package to test.pypi
tar-source                     Package repository as tar for easy distribution
```

### pyproject.toml

Packaging consumes the metadata in `pyproject.toml` which helps to describe the
project on the official [pypi.org][pypi-2] repository. Have a look at the
documentation and comments there to help you create a suitably descriptive
metadata file.

### Local packaging

To create a python wheel for testing locally, or distributing to colleagues run:

- `make package-source`

A `tar` and `whl` file will be stored in a `dist/` directory. The `whl` file can
be installed as follows:

- `pip install <your-package>.whl`

### Publishing

Publishing for public use can be achieved with:

- `make package-upload-test` or `make package-upload`

`make-package-upload-test` will upload the package to [test.pypi.org][pypi-1]
which provides a way to look at package metadata and documentation and ensure
that it is correct before uploading to the official [pypi.org][pypi-2]
repository using `make package-upload`.

[pypi-1]: https://test.pypi.org
[pypi-2]: https://pypi.org
