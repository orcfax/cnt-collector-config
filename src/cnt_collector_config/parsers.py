"""Data transformation and parsing functions"""

import logging

try:
    import config
    import dex_config
    import fetchers
except ModuleNotFoundError:
    try:
        from src.cnt_collector_config import config, dex_config, fetchers
    except ModuleNotFoundError:
        from cnt_collector_config import config, dex_config, fetchers

# Set up logging
logger = logging.getLogger(__name__)


class TokenValidationError(Exception):
    """Exception raised when token configuration validation fails."""


def validate_tokens_config(tokens_response: dict) -> None:
    """Validate that each token in the config has all required fields.

    Args:
        tokens_response: The tokens configuration dict with a "tokens" key.

    Raises:
        TokenValidationError: If any token is missing required fields.
    """
    if "tokens" not in tokens_response:
        raise TokenValidationError("Tokens config is missing 'tokens' key")

    tokens = tokens_response["tokens"]
    errors = []

    for ticker, token_info in tokens.items():
        missing_fields = [
            field for field in config.REQUIRED_TOKEN_FIELDS if field not in token_info
        ]
        if missing_fields:
            errors.append(
                f"Token '{ticker}' is missing fields: {', '.join(missing_fields)}"
            )

    if errors:
        raise TokenValidationError("\n".join(errors))


def get_utxo_content(utxo: dict) -> dict:
    """Parse the contents of an UTxO
    Return a dictionary with the amounts of lovelace and tokens in an UTxO
    """
    content = {"amount": utxo["value"]["coins"], "assets": {}}
    # for policy, assets in utxo.output.amount.multi_asset.data.items():
    for asset, amount in utxo["value"]["assets"].items():
        asset_split = asset.split(".")
        policy_id = asset_split[0]
        try:
            asset_name = asset_split[1]
        except IndexError:
            asset_name = ""
        if policy_id not in content["assets"]:
            content["assets"][policy_id] = {}
        if asset_name not in content["assets"][policy_id]:
            content["assets"][policy_id][asset_name] = amount
        else:
            content["assets"][policy_id][asset_name] += amount
    return content


def update_asset(asset: dict, token_info: dict) -> dict:
    """Update asset with the information about the token (ticker, decimals)"""
    updated_asset = asset.copy()
    updated_asset["ticker"] = token_info.get("ticker")
    updated_asset["decimals"] = token_info.get("decimals")
    return updated_asset


def transform_tokens_to_dict(tokens_response: dict) -> tuple[dict, dict]:
    """Transform tokens list into searchable dict by policy_id and asset_name"""
    tokens = tokens_response["tokens"]
    configured_tokens_dict = {}
    for ticker, token_info in tokens.items():
        policy_id = token_info["policy_id"]
        asset_name = token_info["asset_name"]
        decimals = token_info["decimals"]
        if policy_id not in configured_tokens_dict:
            configured_tokens_dict[policy_id] = {}
        configured_tokens_dict[policy_id][asset_name] = {
            "ticker": ticker,
            "decimals": decimals,
        }
    return configured_tokens_dict, tokens


def parse_pairs_utxos(pairs_utxos: dict, all_tokens_info_dict: dict) -> dict:
    """Parse the dictionary containing all the liquidity pools UTxOs
    grouped by source DEX and smart contract address.
    Return a dictionary containing the human-readable UTxOs containing
    the liquidity pools pairs, grouped by source DEX and smart contract address.
    """
    utxos = {}
    for source in pairs_utxos:  # pylint:disable=R1702
        logger.info(source)
        utxos[source] = {}
        for address in pairs_utxos[source]:
            utxos[source][address] = []
            for utxo_content in pairs_utxos[source][address]:
                new_utxo_content = {
                    "amount": utxo_content["amount"],
                    "assets": [],
                }
                configured_asset_found = False
                for policy_id in utxo_content["assets"]:
                    for asset_name in utxo_content["assets"][policy_id]:
                        asset = {
                            "policy_id": policy_id,
                            "asset_name": asset_name,
                            "amount": utxo_content["assets"][policy_id][asset_name],
                        }
                        policy_id_tokens = all_tokens_info_dict.get(policy_id)
                        if policy_id_tokens:
                            policy_id_asset = policy_id_tokens.get(asset_name)
                            if policy_id_asset:
                                updated_asset = update_asset(asset, policy_id_asset)
                                configured_asset_found = True
                            else:
                                updated_asset = asset
                        else:
                            updated_asset = asset
                        new_utxo_content["assets"].append(updated_asset)
                if configured_asset_found:
                    utxos[source][address].append(new_utxo_content)

            # Collect addresses to delete after iteration
            if not utxos[source][address]:
                utxos[source][address] = None

        # Remove empty addresses after iteration
        utxos[source] = {addr: data for addr, data in utxos[source].items() if data}

    return utxos


def is_security_token(source: str, policy_id: str, address: str) -> bool:
    """Parse a token from a pair_info dict and detect if it is the security token"""
    security_token = False
    for item in dex_config.SECURITY_ASSETS:
        if source == item.get("source"):
            policy_ids = []
            for security_asset in item["security_assets"]:
                policy_ids.append(security_asset.get("policy"))
            if policy_id in policy_ids:
                security_token = True
    if not security_token:
        for item in dex_config.ADDRESSES:
            if address == item.get("address"):
                security_token = True
    return security_token


def build_token_info(asset: dict) -> dict:
    """Build token info dictionary from an asset"""
    token_info = {
        "policy_id": asset["policy_id"],
        "asset_name": asset["asset_name"],
        "amount": asset["amount"],
    }
    ticker = asset.get("ticker")
    if ticker:
        token_info["ticker"] = ticker
    decimals = asset.get("decimals")
    if decimals:
        token_info["decimals"] = decimals
    if asset.get("asset_ascii_name"):
        token_info["asset_ascii_name"] = asset.get("asset_ascii_name")
    else:
        try:
            token_info["asset_ascii_name"] = bytes.fromhex(asset["asset_name"]).decode()
        except UnicodeDecodeError:
            pass
    return token_info


def is_ticker_configured(asset: dict, tokens: dict) -> bool:
    """Check if the asset's ticker is properly configured in tokens"""
    ticker = asset.get("ticker")
    if not ticker:
        return False
    if ticker not in tokens:
        return False
    policy_id = tokens[ticker].get("policy_id")
    asset_name = tokens[ticker].get("asset_name")
    if policy_id and asset_name:
        # if the policy_id and asset_name were specified in config.py
        if policy_id == asset["policy_id"] and asset_name == asset["asset_name"]:
            return True
        logger.info(asset)
        logger.info(policy_id)
        logger.info(asset_name)
        return False
    # if the policy_id and asset_name were NOT specified in config.py
    return True


def categorize_token(asset: dict, source: str, address: str) -> str:
    """Categorize a token as security, configured, or other"""
    # If a security token is present in an amount more than 1
    # then it is not considered a security token for that UTxO
    if asset["amount"] == 1:
        if is_security_token(source, asset["policy_id"], address):
            return "security_tokens"
    if asset.get("ticker"):
        return "configured_tokens"
    return "other_tokens"


def process_pair_assets(
    pair_info: dict, tokens: dict, source: str, address: str
) -> tuple[dict, bool]:
    """Process all assets in a pair and return categorized tokens"""
    pair_tokens = {
        "security_tokens": [],
        "configured_tokens": [],
        "other_tokens": [],
    }
    has_configured_ticker = False
    for asset in pair_info["assets"]:
        token_info = build_token_info(asset)
        if is_ticker_configured(asset, tokens):
            has_configured_ticker = True
        category = categorize_token(asset, source, address)
        pair_tokens[category].append(token_info)
    return pair_tokens, has_configured_ticker


def parse_tokens_pairs(
    utxos_by_source_and_address: dict,
    tokens: dict,
) -> list[dict]:
    """Parse tokens pairs information to select the configured tokens"""
    configured_tokens = []
    for source in utxos_by_source_and_address:
        for address in utxos_by_source_and_address[source]:
            for pair_info in utxos_by_source_and_address[source][address]:
                pair_tokens, has_configured_ticker = process_pair_assets(
                    pair_info, tokens, source, address
                )
                if has_configured_ticker:
                    configured_tokens.append(
                        {
                            "source": source,
                            "address": address,
                            "amount": pair_info.get("amount"),
                            "pair_tokens": pair_tokens,
                        }
                    )
    return configured_tokens


def should_skip_pair(other_tokens: list) -> bool:
    """Check if a pair should be skipped based on other_tokens"""
    for token in other_tokens:
        ascii_name = token.get("asset_ascii_name")
        if ascii_name and not ascii_name.endswith("_LQ") and ascii_name != "MINSWAP":
            return True
    return False


def find_matching_pair_in_feeds(
    pair: str, rev_pair: str, cer_feeds: list
) -> str | None:
    """Find if a pair or its reverse exists in cer_feeds"""
    if pair in cer_feeds:
        return pair
    if rev_pair in cer_feeds:
        return rev_pair
    return None


def build_lp_info(liquidity_pool: str, item: dict) -> dict:
    """Build liquidity pool info dictionary"""
    return {"liquidity_pool": liquidity_pool} | item


def extract_valid_tickers(configured_tokens_list: list) -> tuple[int, list]:
    """Extract valid tickers from configured tokens that have both ticker and ascii name"""
    count = 0
    tickers = []
    for token in configured_tokens_list:
        if "ticker" in token and "asset_ascii_name" in token:
            count += 1
            ticker = token.get("ticker")
            if ticker:
                tickers.append(ticker)
    return count, tickers


def process_single_token_pair(item: dict, cer_feeds: list) -> dict | None:
    """Process pairs with exactly one configured token (ADA pairs)"""
    if should_skip_pair(item["pair_tokens"]["other_tokens"]):
        return None
    ticker = item["pair_tokens"]["configured_tokens"][0]["ticker"]
    pair = f"ADA-{ticker}"
    rev_pair = f"{ticker}-ADA"
    matching_pair = find_matching_pair_in_feeds(pair, rev_pair, cer_feeds)
    if matching_pair:
        return build_lp_info(matching_pair, item)
    return None


def process_multi_token_pair(item: dict, cer_feeds: list) -> dict | None:
    """Process pairs with 2-3 configured tokens"""
    configured_tokens_list = item["pair_tokens"]["configured_tokens"]
    count, tickers = extract_valid_tickers(configured_tokens_list)
    if count == 1 and len(tickers) == 1:
        # ADA-<Token> or <Token-ADA> pairs
        pair = f"ADA-{tickers[0]}"
        rev_pair = f"{tickers[0]}-ADA"
    elif count == 2 and tickers:
        # <Token1>-<Token2> pairs
        pair = f"{tickers[0]}-{tickers[1]}"
        rev_pair = f"{tickers[1]}-{tickers[0]}"
    else:
        return None
    matching_pair = find_matching_pair_in_feeds(pair, rev_pair, cer_feeds)
    if matching_pair:
        return build_lp_info(matching_pair, item)
    return None


def parse_configured_tokens(
    configured_tokens: list,
    feeds_location: str,
) -> list:
    """Parse the configured tokens list to select the configured pairs
    First, only ADA-<Token> or <Token>-ADA pairs
    - select the pairs with only one configured token
    - skip the pairs with a not_configured token with ascii name
    """
    configured_pairs = []
    cer_feeds = fetchers.get_cer_feeds(feeds_location)
    logger.info(cer_feeds)
    for item in configured_tokens:
        token_count = len(item["pair_tokens"]["configured_tokens"])
        if token_count == 0:
            continue
        if token_count == 1:
            lp_info = process_single_token_pair(item, cer_feeds)
        elif token_count <= 3:
            lp_info = process_multi_token_pair(item, cer_feeds)
        else:
            lp_info = None
        if lp_info:
            configured_pairs.append(lp_info)
    return configured_pairs
