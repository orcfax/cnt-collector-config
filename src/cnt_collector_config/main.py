"""Calculate the Cardano Native Tokens pairs price from DEX listings

AMM DEXes:
- MinSwap
- SundaeSwap
- WingRiders
- Spectrum

Order Book DEXes:
- MuesliSwap
- GeniusYield

On some AMM DEXes (MinSwap, WingRiders), every liquidity pool UTxO
has a security token attached (the same security token for all pairs).
Those security tokens defined in the `SECURITY_ASSETS` list in the
`dex_config.py` config file.

Other AMM DEXes (SundaeSwap) have a different security token attached to
each liquidity pool UTxO, but all the tokens have the same policy id.

Other AMM DEXes (SundaeSwap, Spectrum) have all the liquidity pools UTxOs
on one or a few smart contract addresses.
The addresses are defined in the `ADDRESSES` list in the `dex_config.py`
config file.
For Spectrum, the security tokens attached to the UTxOs are created
with different policy IDs, hence the UTxOs cannot be identified
by searching for UTxOs containing security tokens created
with a specific policy ID (like for SundaeSwap or others).

"""

import json
import logging
import sys
import time

try:
    from . import fetchers, generators, parsers, utils
except ImportError:
    try:
        from src.cnt_collector_config import fetchers, generators, parsers, utils
    except ModuleNotFoundError:
        from cnt_collector_config import fetchers, generators, parsers, utils

# Set up logging
logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",  # noqa: E501
    datefmt="%Y-%m-%d %H:%M:%S",
    level="INFO",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Format logs using UTC time
logging.Formatter.converter = time.gmtime
logger = logging.getLogger(__name__)


def main() -> None:
    """Primary entry point for this script."""

    args = utils.parse_arguments()

    if args.version:
        print(utils.get_version())
        sys.exit(0)

    # Check if the kupo URL is set
    if not args.kupo_url:
        logger.error(
            "Kupo URL is not set. Please set the KUPO_URL environment variable or provide the Kupo URL using the -k parameter."
        )
        sys.exit(1)

    # Check if Kupo is healthy
    if fetchers.kupo_health(args.kupo_url.rstrip("/")):
        logger.info("Kupo is healthy")
    else:
        logger.info("Kupo is not healthy!")
        sys.exit(1)

    # Fetch and transform tokens
    tokens_raw = fetchers.fetch_tokens_config(args.tokens_location)
    if not tokens_raw:
        logger.error("Unknown URL type: %s", args.tokens_location)
        sys.exit(1)

    # Validate tokens config
    try:
        parsers.validate_tokens_config(tokens_raw)
    except parsers.TokenValidationError as exc:
        logger.error("Invalid tokens configuration:\n%s", exc)
        sys.exit(1)

    configured_tokens_dict, tokens = parsers.transform_tokens_to_dict(tokens_raw)

    # Get all the DEX UTxOs containing security tokens
    assets_by_source_and_address = fetchers.get_assets_by_source_and_address(
        args.kupo_url.rstrip("/")
    )

    # Parse the dictionary containing all the liquidity pools UTxOs
    # to get a list of probably useful UTxOS in a human-readable form
    utxos_by_source_and_address = parsers.parse_pairs_utxos(
        assets_by_source_and_address, configured_tokens_dict
    )

    # parse the probably useful UTxOS in a human-readable form
    # and select the pairs where a configured ticked is found
    configured_tokens_utxos_list = parsers.parse_tokens_pairs(
        utxos_by_source_and_address, tokens
    )

    # parse the pairs with configured tickers to select the configured pairs
    configured_pairs = parsers.parse_configured_tokens(
        configured_tokens_utxos_list, args.feeds_location
    )

    # create the config file from the configured pairs list
    lp_config = generators.create_config(configured_pairs)

    # Sort sources within each item, then sort items by name for deterministic output
    for entry in lp_config:
        entry["sources"] = sorted(entry["sources"], key=lambda s: s["source"])
    lp_config = sorted(lp_config, key=lambda entry: entry["name"])
    lp_config_str = json.dumps(lp_config, indent=2)
    new_pairs_py = (
        '"""DEX Pairs configuration"""\n\n'
        + "# pylint: disable = C0302\n"
        + "# fmt: off\n\n"
        + "DEX_PAIRS = "
        + lp_config_str.strip()
        + "\n"
    )
    utils.save_txt_file(new_pairs_py, args.config_location)


if __name__ == "__main__":
    main()
