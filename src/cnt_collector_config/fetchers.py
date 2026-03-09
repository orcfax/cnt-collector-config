"""API and network interaction functions"""
# pylint: disable=R0401

import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.exceptions import RequestException

try:
    import config
    import dex_config
    import parsers
    import utils
except ModuleNotFoundError:
    try:
        from src.cnt_collector_config import config, dex_config, parsers, utils
    except ModuleNotFoundError:
        from cnt_collector_config import config, dex_config, parsers, utils

# Set up logging
logger = logging.getLogger(__name__)


def kupo_health(kupo_url: str) -> bool:
    """Check if Kupo is healthy."""
    url = f"{kupo_url}/health"
    logger.info("Checking Kupo health at %s", url)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        latest_checkpoint = next(
            (
                line.split("  ")[1]
                for line in lines
                if line.startswith("kupo_most_recent_checkpoint")
            ),
            None,
        )
        node_tip = next(
            (
                line.split("  ")[1]
                for line in lines
                if line.startswith("kupo_most_recent_node_tip")
            ),
            None,
        )
        if latest_checkpoint and latest_checkpoint == node_tip:
            logger.info("Kupo is healthy")
            return True
        logger.warning("Kupo is not healthy")
    except RequestException as exc:
        logger.error("Failed to check Kupo health")
        logger.exception(exc)
    return False


def get_cer_feeds(feeds_location: str) -> list:
    """Get the Currency Exchange Rate pairs that should be published"""
    cer_feeds = []
    logger.info("Reading the feeds config from %s", feeds_location)
    if feeds_location.startswith("https://"):
        feeds = json.loads(requests.get(feeds_location, timeout=30).text)["feeds"]
    elif feeds_location.startswith("file://"):
        feeds = utils.read_json_file(feeds_location.removeprefix("file://"))["feeds"]
    else:
        logger.error("Unknown URL type: %s", feeds_location)
        sys.exit(1)
    for feed in feeds:
        if feed["source"].lower() == "dex":
            cer_feeds.append(feed["label"])
    return cer_feeds


def fetch_tokens_config(tokens_location: str) -> dict:
    """Fetch tokens config from URL or file"""
    logger.info("Reading the tokens from %s", tokens_location)
    if tokens_location.startswith("https://"):
        return json.loads(requests.get(tokens_location, timeout=30).text)
    if tokens_location.startswith("file://"):
        return utils.read_json_file(tokens_location.removeprefix("file://"))
    return {}


def _fetch_kupo_matches(url: str, source: str, request_type: str) -> dict:
    """Fetch matches from Kupo API (helper for parallel execution).

    Args:
        url: Kupo API URL to fetch
        source: DEX source name
        request_type: Type of request (for logging)

    Returns:
        Dict with source, matches, and metadata
    """
    try:
        logger.info(url)
        resp = requests.get(url, timeout=config.KUPO_TIMEOUT)
        logger.info("Response status code: %s", resp.status_code)
        try:
            matches = json.loads(resp.text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode JSON from %s: %s", url, exc)
            return {
                "source": source,
                "matches": [],
                "success": False,
                "request_type": request_type,
                "error": str(exc),
            }
        logger.info("Matches found for %s: %s", source, len(matches))
        return {
            "source": source,
            "matches": matches,
            "success": True,
            "request_type": request_type,
        }
    except RequestException as exc:
        logger.error("Failed to fetch from %s: %s", url, exc)
        return {
            "source": source,
            "matches": [],
            "success": False,
            "request_type": request_type,
            "error": str(exc),
        }


def get_assets_by_source_and_address(kupo_url: str) -> dict:  # pylint: disable=R0914
    """Parse SECURITY_ASSETS defined in `config.py`
    If "asset" is present, we are only interested in this asset.
    Otherwise, we search for all DEX security tokens created with this policy id.
    Returns all DEX security tokens and all the contents of the containing UTxOs.

    Uses parallel requests (max MAX_PARALLEL_REQUESTS) for improved performance.
    """
    all_assets = {}

    # Prepare all requests to be made
    requests_to_make = []

    # Collect security asset requests
    for item in dex_config.SECURITY_ASSETS:
        source = item["source"]
        for asset in item["security_assets"]:
            sec_policy_id = asset.get("policy")
            sec_asset_name = item.get("asset", "")
            if not sec_asset_name:
                sec_asset = f"{sec_policy_id}.*"
            else:
                sec_asset = f"{sec_policy_id}.{sec_asset_name}"
            url = kupo_url + f"/matches/{sec_asset}?unspent"
            requests_to_make.append((url, source, "security_asset"))

    # Collect address-based requests
    for item in dex_config.ADDRESSES:
        source = item["source"]
        address = item["address"]
        url = kupo_url + f"/matches/{address}?unspent"
        requests_to_make.append((url, source, "address"))

    # Execute requests in parallel
    logger.info(
        "Fetching %s requests with max %s parallel workers",
        len(requests_to_make),
        config.MAX_PARALLEL_REQUESTS,
    )

    with ThreadPoolExecutor(max_workers=config.MAX_PARALLEL_REQUESTS) as executor:
        # Submit all requests
        future_to_request = {
            executor.submit(_fetch_kupo_matches, url, source, req_type): (
                url,
                source,
                req_type,
            )
            for url, source, req_type in requests_to_make
        }

        # Process completed requests
        for future in as_completed(future_to_request):
            result = future.result()
            source = result["source"]
            matches = result["matches"]

            # Initialize source if needed
            if source not in all_assets:
                all_assets[source] = {}

            # Process each match
            for match in matches:
                address = match["address"]
                content = parsers.get_utxo_content(match)

                # Add to results
                if address not in all_assets[source]:
                    all_assets[source][address] = []
                all_assets[source][address].append(content)

    return all_assets
