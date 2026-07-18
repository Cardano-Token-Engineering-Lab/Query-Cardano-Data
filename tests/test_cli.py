import pandas as pd
import pytest

from cardano_token_framework import cli

POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"


class FakeSource:
    """A fake TokenDataSource that records calls and returns canned data."""

    last_instance = None

    def __init__(self):
        self.calls = []
        FakeSource.last_instance = self

    def get_asset_info(self, token):
        self.calls.append(("info", token))
        return pd.DataFrame([{"policy_id": token.policy_id}])

    def get_asset_holders(self, token):
        self.calls.append(("holders", token))
        return pd.DataFrame([{"address": "addr1", "quantity": 1.0}])

    def get_asset_transactions(self, token, window=None):
        self.calls.append(("transactions", token, window))
        return pd.DataFrame([{"tx_hash": "abc"}])

    def get_swaps(self, token, dex_addresses, window=None):
        self.calls.append(("swaps", token, dex_addresses, window))
        return pd.DataFrame([{"tx_hash": "abc", "direction": "buy"}])


@pytest.fixture(autouse=True)
def patch_sources(monkeypatch):
    monkeypatch.setitem(cli._SOURCES, "blockfrost", FakeSource)
    monkeypatch.setitem(cli._SOURCES, "koios", FakeSource)


def test_info_command(capsys):
    df = cli.run(["--policy-id", POLICY_ID, "--asset-name", "4c51", "info"])
    assert df.iloc[0]["policy_id"] == POLICY_ID
    assert FakeSource.last_instance.calls[0][0] == "info"


def test_holders_command():
    df = cli.run(["--policy-id", POLICY_ID, "holders"])
    assert list(df.columns) == ["address", "quantity"]


def test_transactions_command_passes_window():
    cli.run(
        [
            "--policy-id", POLICY_ID, "transactions",
            "--start", "2024-01-01", "--end", "2024-02-01",
        ]
    )
    _, _, window = FakeSource.last_instance.calls[0]
    assert window.start is not None
    assert window.end is not None


def test_swaps_command_requires_dex_address():
    with pytest.raises(SystemExit):
        cli.run(["--policy-id", POLICY_ID, "swaps"])


def test_swaps_command_accepts_multiple_dex_addresses():
    df = cli.run(
        [
            "--policy-id", POLICY_ID, "swaps",
            "--dex-address", "addr1_a",
            "--dex-address", "addr1_b",
        ]
    )
    assert df.iloc[0]["direction"] == "buy"
    call = FakeSource.last_instance.calls[0]
    assert call[2] == ["addr1_a", "addr1_b"]


def test_output_writes_csv(tmp_path):
    output_path = tmp_path / "out.csv"
    cli.run(["--policy-id", POLICY_ID, "--output", str(output_path), "info"])
    assert output_path.exists()
    written = pd.read_csv(output_path)
    assert written.iloc[0]["policy_id"] == POLICY_ID
