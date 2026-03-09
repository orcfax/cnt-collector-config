"""Configuration variables"""
from os import getcwd, getenv, path
from typing import Final

VERSION = "0.9.1"
workdir = getcwd()
base_path = workdir[0 : workdir.find("/src")] if "/src" in workdir else workdir

KUPO_URL: Final[str] = getenv("KUPO_URL", "")
KUPO_TIMEOUT = 120
MAX_PARALLEL_REQUESTS = 5  # Maximum number of parallel requests to Kupo
FEEDS_URL: Final[str] = getenv(
    "FEEDS_URL", "file://" + path.join(base_path, "cer-feeds.json")
)
TOKENS_URL: Final[str] = getenv(
    "TOKENS_URL", "file://" + path.join(base_path, "tokens.json")
)
GENERATED_CONFIG: Final[str] = path.join(
    base_path, getenv("GENERATED_CONFIG", "generated_config.py")
)
REQUIRED_TOKEN_FIELDS: Final[tuple] = ("policy_id", "asset_name", "decimals")
