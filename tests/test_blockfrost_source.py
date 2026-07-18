import pandas as pd
import pytest

from cardano_token_framework.config import TimeWindow, TokenIdentifier
from cardano_token_framework.sources.blockfrost_source import BlockfrostSource

POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
ASSET_NAME = "4c51"
UNIT = POLICY_ID + ASSET_NAME
DEX_ADDR = "addr1_dex_batcher"
TRADER_ADDR = "addr1_trader"


class FakeBlockFrostApi:
    """Stands in for blockfrost.BlockFrostApi; returns canned pandas data."""

    def __init__(self, tx_pages=None, utxos_by_hash=None, holder_pages=None):
        self.tx_pages = tx_pages or []
        self.utxos_by_hash = utxos_by_hash or {}
        self.holder_pages = holder_pages or []

    def asset(self, asset, return_type):
        assert asset == UNIT
        return pd.DataFrame(
            [{"policy_id": POLICY_ID, "asset_name": ASSET_NAME, "metadata.decimals": 6}]
        )

    def asset_addresses(self, asset, page, return_type):
        idx = page - 1
        if idx < len(self.holder_pages):
            return pd.DataFrame(self.holder_pages[idx])
        return pd.DataFrame(columns=["address", "quantity"])

    def asset_transactions(self, asset, page, return_type):
        idx = page - 1
        if idx < len(self.tx_pages):
            return pd.DataFrame(self.tx_pages[idx])
        return pd.DataFrame(columns=["tx_hash", "block_height", "block_time"])

    def transaction_utxos(self, hash, return_type):
        return pd.DataFrame([self.utxos_by_hash[hash]])


@pytest.fixture
def token():
    return TokenIdentifier(policy_id=POLICY_ID, asset_name=ASSET_NAME)


def test_get_asset_info_fills_missing_decimals(token):
    api = FakeBlockFrostApi()
    source = BlockfrostSource(api=api)
    df = source.get_asset_info(token)
    assert df["metadata.decimals"].iloc[0] == 6


def test_get_asset_holders_decimal_adjusts_and_sorts(token):
    api = FakeBlockFrostApi(
        holder_pages=[
            [
                {"address": "addr_small", "quantity": "1000000"},
                {"address": "addr_big", "quantity": "5000000"},
            ]
        ]
    )
    source = BlockfrostSource(api=api)
    df = source.get_asset_holders(token)
    assert list(df["address"]) == ["addr_big", "addr_small"]
    assert df["quantity"].iloc[0] == pytest.approx(5.0)


def test_get_asset_holders_paginates(token):
    page1 = [{"address": f"addr_{i}", "quantity": "1"} for i in range(100)]
    page2 = [{"address": "addr_last", "quantity": "1"}]
    api = FakeBlockFrostApi(holder_pages=[page1, page2])
    source = BlockfrostSource(api=api)
    df = source.get_asset_holders(token)
    assert len(df) == 101


def test_get_asset_transactions_filters_by_window(token):
    api = FakeBlockFrostApi(
        tx_pages=[
            [
                {"tx_hash": "tx_jan", "block_height": 1, "block_time": 1704067200},  # 2024-01-01
                {"tx_hash": "tx_mar", "block_height": 2, "block_time": 1709251200},  # 2024-03-01
            ]
        ]
    )
    source = BlockfrostSource(api=api)
    window = TimeWindow.from_strings("2024-02-01", "2024-04-01")
    df = source.get_asset_transactions(token, window=window)
    assert list(df["tx_hash"]) == ["tx_mar"]


def test_get_swaps_classifies_sell_when_asset_flows_into_dex(token):
    tx_hash = "tx_sell"
    api = FakeBlockFrostApi(
        tx_pages=[[{"tx_hash": tx_hash, "block_height": 1, "block_time": 1704067200}]],
        utxos_by_hash={
            tx_hash: {
                "inputs": [
                    {"address": TRADER_ADDR, "amount": [{"unit": UNIT, "quantity": "5000000"}]}
                ],
                "outputs": [
                    {"address": DEX_ADDR, "amount": [{"unit": UNIT, "quantity": "5000000"}]}
                ],
            }
        },
    )
    source = BlockfrostSource(api=api)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert len(df) == 1
    assert df.iloc[0]["direction"] == "sell"
    assert df.iloc[0]["quantity"] == pytest.approx(5.0)


def test_get_swaps_classifies_buy_when_asset_flows_out_of_dex(token):
    tx_hash = "tx_buy"
    api = FakeBlockFrostApi(
        tx_pages=[[{"tx_hash": tx_hash, "block_height": 1, "block_time": 1704067200}]],
        utxos_by_hash={
            tx_hash: {
                "inputs": [
                    {"address": DEX_ADDR, "amount": [{"unit": UNIT, "quantity": "2000000"}]}
                ],
                "outputs": [
                    {"address": TRADER_ADDR, "amount": [{"unit": UNIT, "quantity": "2000000"}]}
                ],
            }
        },
    )
    source = BlockfrostSource(api=api)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert len(df) == 1
    assert df.iloc[0]["direction"] == "buy"
    assert df.iloc[0]["quantity"] == pytest.approx(2.0)


def test_get_swaps_ignores_transactions_that_never_touch_dex(token):
    tx_hash = "tx_unrelated"
    api = FakeBlockFrostApi(
        tx_pages=[[{"tx_hash": tx_hash, "block_height": 1, "block_time": 1704067200}]],
        utxos_by_hash={
            tx_hash: {
                "inputs": [
                    {"address": TRADER_ADDR, "amount": [{"unit": UNIT, "quantity": "1000000"}]}
                ],
                "outputs": [
                    {"address": "addr1_other_trader", "amount": [{"unit": UNIT, "quantity": "1000000"}]}
                ],
            }
        },
    )
    source = BlockfrostSource(api=api)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert df.empty


def test_get_swaps_skips_tx_when_utxo_lookup_fails(token):
    tx_hash = "tx_will_fail"

    class FailingApi(FakeBlockFrostApi):
        def transaction_utxos(self, hash, return_type):
            raise RuntimeError("network error")

    api = FailingApi(
        tx_pages=[[{"tx_hash": tx_hash, "block_height": 1, "block_time": 1704067200}]]
    )
    source = BlockfrostSource(api=api)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert df.empty


def test_get_asset_info_when_decimals_column_missing(token):
    class NoDecimalsApi(FakeBlockFrostApi):
        def asset(self, asset, return_type):
            return pd.DataFrame([{"policy_id": POLICY_ID, "asset_name": ASSET_NAME}])

    source = BlockfrostSource(api=NoDecimalsApi())
    df = source.get_asset_info(token)
    assert df["metadata.decimals"].iloc[0] == 0


def test_get_asset_holders_returns_empty_when_no_holders(token):
    api = FakeBlockFrostApi(holder_pages=[])
    source = BlockfrostSource(api=api)
    df = source.get_asset_holders(token)
    assert df.empty


def test_get_asset_transactions_paginates(token):
    page1 = [
        {"tx_hash": f"tx_{i}", "block_height": i, "block_time": 1704067200 + i}
        for i in range(100)
    ]
    page2 = [{"tx_hash": "tx_last", "block_height": 200, "block_time": 1704067300}]
    api = FakeBlockFrostApi(tx_pages=[page1, page2])
    source = BlockfrostSource(api=api)
    df = source.get_asset_transactions(token)
    assert len(df) == 101


def test_get_asset_transactions_returns_empty_when_no_transactions(token):
    api = FakeBlockFrostApi(tx_pages=[])
    source = BlockfrostSource(api=api)
    df = source.get_asset_transactions(token)
    assert df.empty
    assert list(df.columns) == ["tx_hash", "block_height", "block_time"]


def test_net_asset_flow_returns_zero_for_empty_utxos():
    empty = pd.DataFrame(columns=["inputs", "outputs"])
    assert BlockfrostSource._net_asset_flow_into_dex(empty, UNIT, {DEX_ADDR}) == 0


def test_get_swaps_ignores_non_matching_unit_amounts(token):
    tx_hash = "tx_lovelace_only"
    api = FakeBlockFrostApi(
        tx_pages=[[{"tx_hash": tx_hash, "block_height": 1, "block_time": 1704067200}]],
        utxos_by_hash={
            tx_hash: {
                "inputs": [
                    {"address": TRADER_ADDR, "amount": [{"unit": "lovelace", "quantity": "2000000"}]}
                ],
                "outputs": [
                    {"address": DEX_ADDR, "amount": [{"unit": "lovelace", "quantity": "2000000"}]}
                ],
            }
        },
    )
    source = BlockfrostSource(api=api)
    df = source.get_swaps(token, dex_addresses=[DEX_ADDR])
    assert df.empty
