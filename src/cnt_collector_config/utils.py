"""Utility functions for file I/O, CLI, and versioning"""

import argparse
import json
import json.decoder
import logging
from importlib.metadata import PackageNotFoundError, version
from typing import Union

try:
    import config
except ModuleNotFoundError:
    try:
        from src.cnt_collector_config import config
    except ModuleNotFoundError:
        from cnt_collector_config import config

# Set up logging
logger = logging.getLogger(__name__)


def save_txt_file(content: Union[dict, list], filename: str) -> bool:
    """Save a dict or a list into a txt file"""
    try:
        with open(filename, "w", encoding="utf8") as txt_file:
            txt_file.write(str(content))
        success = True
    except FileNotFoundError as exc:
        logger.exception(exc)
        success = False
    return success


def save_json_file(content: Union[dict, list], filename: str) -> bool:
    """Save a dict or a list into a json file"""
    try:
        with open(filename, "w", encoding="utf8") as json_file:
            json_file.write(json.dumps(content, indent=2))
        success = True
    except FileNotFoundError as exc:
        logger.exception(exc)
        success = False
    return success


def read_json_file(filename: str) -> dict:
    """Read a json file and return the contents as a dict"""
    try:
        with open(filename, "r", encoding="utf8") as json_file:
            contents = json.loads(json_file.read())
    except FileNotFoundError as exc:
        logger.exception(exc)
        contents = {}
    except json.decoder.JSONDecodeError as exc:
        logger.exception(exc)
        contents = {}
    return contents


def get_version():
    """Return package version to the calling code.

    Version is set to a default value if it isn't picked up by importlib
    as anticipated, i.e. if the code hasn't been installed or isn't
    being run as a package correctly.
    """
    __version__ = config.VERSION
    try:
        __version__ = version("cnt-collector-config")
    except PackageNotFoundError:
        # package is not installed
        pass
    return __version__


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="Orcfax CNT Indexer Config Generator",
        description="A method of indexing CNT prices from Cardano liquidity pools",
        epilog="for more information visit https://orcfax.io/",
    )

    parser.add_argument(
        "--kupo-url",
        "-k",
        help="mainnet kupo url",
        required=False,
        default=config.KUPO_URL,
        type=str,
    )

    parser.add_argument(
        "--feeds-location",
        "-f",
        help="CNT feeds config file location, default: cer-feeds.json",
        required=False,
        default=config.FEEDS_URL,
        type=str,
    )

    parser.add_argument(
        "--tokens-location",
        "-t",
        help="CNT tokens config file location, default: tokens.json",
        required=False,
        default=config.TOKENS_URL,
        type=str,
    )

    parser.add_argument(
        "--config-location",
        "-c",
        help="where to save the new cnt-collector-node config file, default: generated_config.py",
        required=False,
        default=config.GENERATED_CONFIG,
        type=str,
    )

    parser.add_argument(
        "--version",
        "-v",
        help="return script version",
        required=False,
        action="store_true",
    )

    return parser.parse_args()
