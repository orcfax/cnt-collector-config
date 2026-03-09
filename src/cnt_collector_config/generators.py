"""Configuration generation functions"""

import logging

# Set up logging
logger = logging.getLogger(__name__)


def create_config(pairs: list) -> list:  # pylint:disable=R0801, R0912, R0914, R0915
    """Create the config file from the configured pairs list"""
    lp_config_dict = {}
    no_security_token_list = []
    for pair in pairs:
        try:
            lp_name = pair["liquidity_pool"]
            source = pair["source"]
            address = pair["address"]
            amount = pair["amount"]
            security_token_policy = pair["pair_tokens"]["security_tokens"][0][
                "policy_id"
            ]
            security_token_name = pair["pair_tokens"]["security_tokens"][0][
                "asset_name"
            ]
            token1_policy = None
            token1_name = None
            token1_decimals = None
            token1_amount = None
            token2_policy = None
            token2_name = None
            token2_decimals = None
            token2_amount = None
            tickers = lp_name.split("-")
            token1_ticker = tickers[0]
            token2_ticker = tickers[1]
        except IndexError:
            no_security_token_list.append(pair)
            continue
        if token1_ticker == "ADA":
            token1_policy = ""
            token1_name = "lovelace"
            token1_decimals = 6
            token1_amount = amount
        if token2_ticker == "ADA":
            token2_policy = ""
            token2_name = "lovelace"
            token2_decimals = 6
            token2_amount = amount
        for item in pair["pair_tokens"]["configured_tokens"]:
            if item["ticker"] == token1_ticker:
                token1_policy = item["policy_id"]
                token1_name = item["asset_name"]
                token1_decimals = item.get("decimals", 0)
                token1_amount = item["amount"]
            elif item["ticker"] == token2_ticker:
                token2_policy = item["policy_id"]
                token2_name = item["asset_name"]
                token2_decimals = item.get("decimals", 0)
                token2_amount = item["amount"]
        if lp_name not in lp_config_dict:
            lp_config_dict[lp_name] = {
                "name": lp_name,
                "token1_policy": token1_policy,
                "token1_name": token1_name,
                "token1_decimals": token1_decimals,
                "token2_policy": token2_policy,
                "token2_name": token2_name,
                "token2_decimals": token2_decimals,
                "sources": {
                    source: {
                        "source": source,
                        "address": address,
                        "security_token_policy": security_token_policy,
                        "security_token_name": security_token_name,
                        "token1_amount": token1_amount,
                        "token2_amount": token2_amount,
                    }
                },
            }
            continue
        if source not in lp_config_dict[lp_name]["sources"]:
            lp_config_dict[lp_name]["sources"][source] = {
                "source": source,
                "address": address,
                "security_token_policy": security_token_policy,
                "security_token_name": security_token_name,
                "token1_amount": token1_amount,
                "token2_amount": token2_amount,
            }
            continue
        try:
            # pylint: disable=too-many-boolean-expressions
            if (
                token1_amount
                > lp_config_dict[lp_name]["sources"][source]["token1_amount"]
                and token2_amount
                > lp_config_dict[lp_name]["sources"][source]["token2_amount"]
            ) or (
                token1_name == "lovelace"
                and token1_amount
                > lp_config_dict[lp_name]["sources"][source]["token1_amount"]
                or token2_name == "lovelace"
                and token2_amount
                > lp_config_dict[lp_name]["sources"][source]["token2_amount"]
            ):
                lp_config_dict[lp_name]["sources"][source] = {
                    "source": source,
                    "address": address,
                    "security_token_policy": security_token_policy,
                    "security_token_name": security_token_name,
                    "token1_amount": token1_amount,
                    "token2_amount": token2_amount,
                }
        except TypeError as exc:
            logger.exception(exc)
            logger.info(token1_amount)
            logger.info(lp_config_dict[lp_name]["sources"][source]["token1_amount"])
            logger.info(token2_amount)
            logger.info(lp_config_dict[lp_name]["sources"][source]["token2_amount"])
    lp_config = []
    for item in lp_config_dict.values():
        item_sources = []
        for item_source in item["sources"]:
            item_sources.append(
                {
                    "source": item["sources"][item_source]["source"],
                    "address": item["sources"][item_source]["address"],
                    "security_token_policy": item["sources"][item_source][
                        "security_token_policy"
                    ],
                    "security_token_name": item["sources"][item_source][
                        "security_token_name"
                    ],
                }
            )
        item["sources"] = item_sources
        lp_config.append(item)

    logger.warning(
        "Number of UTxOs without a security token: %s", len(no_security_token_list)
    )
    return lp_config
