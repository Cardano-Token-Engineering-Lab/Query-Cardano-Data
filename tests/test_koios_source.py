import pytest

from cardano_token_framework.config import TimeWindow, TokenIdentifier
from cardano_token_framework.sources.koios_source import KoiosSource

POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
ASSET_NAME = "4c51"
DEX_ADDR = "addr1_dex_batcher"
TRADER_ADDR = "addr1_trader"


class FakeKoiosClient:
    """Stands in for the koios_api module; returns canned dict/list data."""

    def __init__(self, tx_list=None, tx_info_by_hash=None, holders=None):
        self.tx_list = tx_list or []
        self.tx_info_by_hash = tx_info_by_hash or {}
        self.holders = holders or []

    def get_asset_info(self, asset_ref):
        return [{"policy_id": POLICY_ID, "asset_name": ASSET_NAME, "decimals": 6}]

    def get_asset_address_list(self, policy_id, asset_name):
        return self.holders

    def get_asset_txs(self, policy_id, asset_name, block_height, history):
        return self.tx_list

    def get_tx_info(self, tx_hashes):
        return [self.tx_info_by_hash[h] for h in tx_hashes if h in self.tx_info_by_hash]


@pytest.fixture
def token():
    return TokenIdentifier(policy_id=POLICY_ID, asset_name=ASSET_NAME)


def test_get_asset_info_returns_decimals(token):
    source = KoiosSource(client=FakeKoiosClient())
    df = source.get_asset_info(token)
    assert df["decimals"].iloc[0] == 6


def test_get_asset_holders_decimal_adjusts_and_sorts(token):
    client = FakeKoiosClient(
        holders=[
            {"address": "addr_small", "quantity": "1000000"},
            {"address": "addr_big", "quantity": "5000000"},
        ]
    )
    source = KoiosSource(client=client)
    df = source.get_asset_holders(token)
    assert list(df["address"]) == ["addr_big", "addr_small"]
    assert df["quantity"].iloc[0] == pytest.approx(5.0)


def test_get_asset_transactions_filters_by_window(token):
    client = FakeKoiosClient(
        tx_list=[
            {"tx_hash": "tx_jan", "block_height": 1, "tx_timestamp": 1704067200},
            {"tx_hash": "tx_mar", "block_height": 2, "tx_timestamp": 1709251200},
        ]
    )
    source = KoiosSource(client=client)
    window = TimeWindow.from_strings("2024-02-01", "2024-04-01")
    df = source.get_asset_transactions(token, window=window)
    assert list(df["tx_hash"]) == ["tx_mar"]


def test_get_swaps_classifies_sell_when_asset_flows_into_dex(token):
    tx_hash = "tx_sell"
    client = FakeKoiosClient(
        tx_list=[{"tx_hash": tx_hash, "block_height": 1, "tx_timestamp": 1704067200}],
        tx_info_by_hash={
            tx_hash: {
                "tx_hash": tx_hash,
                "inputs": [
                    {
                        "payment_addr": {"bech32": TRADER_ADDR},
                        "asset_list": [
                            {"policy_id": POLICY_ID, "asset_name": ASSET_NAME, "quantity": "5000000"}
                        ],
                    }
                ],
                "outputs": [
                    {
                        "payment_addr": {"bech32": DEX_ADDR},
                        "asset_list": [
                            {"policy_id": POLICY_ID, "asset_name": ASSET_NAME, "quantity": "5000000"}
                        ],
                    }
                ],
            }
        },
    )
    source = KoiosSource(client=client)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert len(df) == 1
    assert df.iloc[0]["direction"] == "sell"
    assert df.iloc[0]["quantity"] == pytest.approx(5.0)


def test_get_swaps_classifies_buy_when_asset_flows_out_of_dex(token):
    tx_hash = "tx_buy"
    client = FakeKoiosClient(
        tx_list=[{"tx_hash": tx_hash, "block_height": 1, "tx_timestamp": 1704067200}],
        tx_info_by_hash={
            tx_hash: {
                "tx_hash": tx_hash,
                "inputs": [
                    {
                        "payment_addr": {"bech32": DEX_ADDR},
                        "asset_list": [
                            {"policy_id": POLICY_ID, "asset_name": ASSET_NAME, "quantity": "2000000"}
                        ],
                    }
                ],
                "outputs": [
                    {
                        "payment_addr": {"bech32": TRADER_ADDR},
                        "asset_list": [
                            {"policy_id": POLICY_ID, "asset_name": ASSET_NAME, "quantity": "2000000"}
                        ],
                    }
                ],
            }
        },
    )
    source = KoiosSource(client=client)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert len(df) == 1
    assert df.iloc[0]["direction"] == "buy"
    assert df.iloc[0]["quantity"] == pytest.approx(2.0)


def test_get_swaps_empty_when_no_transactions(token):
    client = FakeKoiosClient(tx_list=[])
    source = KoiosSource(client=client)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert df.empty
    assert list(df.columns) == ["tx_hash", "block_time", "dex_address", "direction", "quantity"]


def test_get_swaps_ignores_other_assets_at_dex_address(token):
    tx_hash = "tx_other_asset"
    client = FakeKoiosClient(
        tx_list=[{"tx_hash": tx_hash, "block_height": 1, "tx_timestamp": 1704067200}],
        tx_info_by_hash={
            tx_hash: {
                "tx_hash": tx_hash,
                "inputs": [{"payment_addr": {"bech32": TRADER_ADDR}, "asset_list": []}],
                "outputs": [
                    {
                        "payment_addr": {"bech32": DEX_ADDR},
                        "asset_list": [
                            {"policy_id": "different_policy", "asset_name": "xx", "quantity": "999"}
                        ],
                    }
                ],
            }
        },
    )
    source = KoiosSource(client=client)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert df.empty


def test_get_asset_info_reads_nested_registry_decimals(token):
    class NestedDecimalsClient(FakeKoiosClient):
        def get_asset_info(self, asset_ref):
            return [{"policy_id": POLICY_ID, "token_registry_metadata.decimals": 6}]

    source = KoiosSource(client=NestedDecimalsClient())
    df = source.get_asset_info(token)
    assert df["decimals"].iloc[0] == 6


def test_get_asset_info_defaults_decimals_to_zero_when_absent(token):
    class NoDecimalsClient(FakeKoiosClient):
        def get_asset_info(self, asset_ref):
            return [{"policy_id": POLICY_ID}]

    source = KoiosSource(client=NoDecimalsClient())
    df = source.get_asset_info(token)
    assert df["decimals"].iloc[0] == 0


def test_get_asset_holders_returns_empty_when_no_holders(token):
    source = KoiosSource(client=FakeKoiosClient(holders=[]))
    df = source.get_asset_holders(token)
    assert df.empty
    assert list(df.columns) == ["address", "quantity"]


def test_get_swaps_ignores_matching_policy_but_different_asset_name(token):
    tx_hash = "tx_different_asset_name"
    client = FakeKoiosClient(
        tx_list=[{"tx_hash": tx_hash, "block_height": 1, "tx_timestamp": 1704067200}],
        tx_info_by_hash={
            tx_hash: {
                "tx_hash": tx_hash,
                "inputs": [{"payment_addr": {"bech32": TRADER_ADDR}, "asset_list": []}],
                "outputs": [
                    {
                        "payment_addr": {"bech32": DEX_ADDR},
                        "asset_list": [
                            {"policy_id": POLICY_ID, "asset_name": "different_asset", "quantity": "999"}
                        ],
                    }
                ],
            }
        },
    )
    source = KoiosSource(client=client)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert df.empty
