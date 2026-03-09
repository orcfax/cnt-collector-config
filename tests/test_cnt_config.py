"""Integration tests for cnt-collector-config."""

from src.cnt_collector_config import fetchers, generators, main, parsers, utils


def test_all_modules_importable():
    """Ensure all modules can be imported successfully."""
    assert main
    assert utils
    assert fetchers
    assert parsers
    assert generators


def test_main_function_exists():
    """Ensure the main function exists."""
    assert callable(main.main)


def test_utils_functions_exist():
    """Ensure utils module has expected functions."""
    assert callable(utils.save_txt_file)
    assert callable(utils.save_json_file)
    assert callable(utils.read_json_file)
    assert callable(utils.get_version)
    assert callable(utils.parse_arguments)


def test_fetchers_functions_exist():
    """Ensure fetchers module has expected functions."""
    assert callable(fetchers.kupo_health)
    assert callable(fetchers.get_cer_feeds)
    assert callable(fetchers.fetch_tokens_config)
    assert callable(fetchers.get_assets_by_source_and_address)


def test_parsers_functions_exist():
    """Ensure parsers module has expected functions."""
    assert callable(parsers.get_utxo_content)
    assert callable(parsers.update_asset)
    assert callable(parsers.transform_tokens_to_dict)
    assert callable(parsers.parse_pairs_utxos)
    assert callable(parsers.is_security_token)
    assert callable(parsers.parse_tokens_pairs)
    assert callable(parsers.parse_configured_tokens)


def test_generators_functions_exist():
    """Ensure generators module has expected functions."""
    assert callable(generators.create_config)
