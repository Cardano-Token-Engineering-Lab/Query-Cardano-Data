"""Koios-backed implementation of :class:`TokenDataSource`.

Koios does not require an API key for the public tier (see the project
README for the current state of that policy). This source is built on the
``koios-api`` PyPI package.

Note on schema assumptions: Koios' ``/tx_info`` endpoint returns nested
``inputs``/``outputs`` lists, each with a ``payment_addr.bech32`` address and
an ``asset_list`` of ``{policy_id, asset_name, quantity}`` dicts. That shape
is documented at https://api.koios.rest/#post-/tx_info and is what
``get_swaps`` below assumes; it is covered by a mocked unit test
(``tests/test_koios_source.py``) rather than a live call, since the public
API schema can change independently of this repo.
"""

from __future__ import annotations

import logging

import koios_api as koios
import pandas as pd

from cardano_token_framework.config import TimeWindow, TokenIdentifier
from cardano_token_framework.sources.base import TokenDataSource

logger = logging.getLogger(__name__)


class KoiosSource(TokenDataSource):
    """Pulls Cardano native-token data via the Koios REST API."""

    def __init__(self, client=koios) -> None:
        """Create a source.

        Args:
            client: The ``koios_api`` module (or a drop-in mock exposing the
                same function names) used to make requests. Defaults to the
                real ``koios_api`` module; tests inject a mock here.
        """
        self.client = client

    @staticmethod
    def _asset_ref(token: TokenIdentifier) -> str:
        return f"{token.policy_id}.{token.asset_name}"

    def get_asset_info(self, token: TokenIdentifier) -> pd.DataFrame:
        data = self.client.get_asset_info(self._asset_ref(token))
        df = pd.json_normalize(data)
        if "decimals" not in df.columns and "token_registry_metadata.decimals" in df.columns:
            df["decimals"] = df["token_registry_metadata.decimals"]
        if "decimals" not in df.columns:
            df["decimals"] = 0
        df["decimals"] = df["decimals"].fillna(0).astype(int)
        return df

    def get_asset_holders(self, token: TokenIdentifier) -> pd.DataFrame:
        info = self.get_asset_info(token)
        decimals = int(info["decimals"].iloc[0]) if len(info) else 0

        data = self.client.get_asset_address_list(token.policy_id, token.asset_name)
        df = pd.json_normalize(data)
        if df.empty:
            return pd.DataFrame(columns=["address", "quantity"])

        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce") / (10**decimals)
        return df.sort_values("quantity", ascending=False).reset_index(drop=True)

    def get_asset_transactions(
        self, token: TokenIdentifier, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        data = self.client.get_asset_txs(token.policy_id, token.asset_name, 0, False)
        df = pd.json_normalize(data)
        if df.empty:
            return pd.DataFrame(columns=["tx_hash", "block_height", "block_time"])

        if "block_time" not in df.columns and "tx_timestamp" in df.columns:
            df["block_time"] = df["tx_timestamp"]
        df["block_time"] = pd.to_datetime(df["block_time"], unit="s", utc=True)
        df = df.sort_values("block_time").reset_index(drop=True)

        if window is not None:
            df = df[df["block_time"].apply(window.contains)].reset_index(drop=True)

        return df

    def get_swaps(
        self,
        token: TokenIdentifier,
        dex_addresses: list[str],
        window: TimeWindow | None = None,
    ) -> pd.DataFrame:
        dex_set = set(dex_addresses)
        info = self.get_asset_info(token)
        decimals = int(info["decimals"].iloc[0]) if len(info) else 0

        tx_df = self.get_asset_transactions(token, window=window)
        if tx_df.empty:
            return pd.DataFrame(
                columns=["tx_hash", "block_time", "dex_address", "direction", "quantity"]
            )

        tx_hashes = tx_df["tx_hash"].tolist()
        details = self.client.get_tx_info(tx_hashes)
        block_time_by_hash = dict(
            zip(tx_df["tx_hash"], tx_df["block_time"], strict=True)
        )

        records = []
        for tx in details:
            tx_hash = tx.get("tx_hash")
            net_into_dex = self._net_asset_flow_into_dex(tx, token, dex_set)
            if net_into_dex == 0:
                continue
            direction = "sell" if net_into_dex > 0 else "buy"
            records.append(
                {
                    "tx_hash": tx_hash,
                    "block_time": block_time_by_hash.get(tx_hash),
                    "dex_address": ",".join(sorted(dex_set)),
                    "direction": direction,
                    "quantity": abs(net_into_dex) / (10**decimals),
                }
            )

        return pd.DataFrame(
            records,
            columns=["tx_hash", "block_time", "dex_address", "direction", "quantity"],
        )

    @staticmethod
    def _net_asset_flow_into_dex(tx: dict, token: TokenIdentifier, dex_set: set) -> int:
        """Same heuristic as ``BlockfrostSource._net_asset_flow_into_dex``.

        Positive => token flowed into a DEX address (a sell); negative =>
        token flowed out of a DEX address (a buy); zero => the asset did not
        touch a DEX address in this transaction.
        """
        into_dex = 0
        out_of_dex = 0
        for bucket_name in ("inputs", "outputs"):
            for utxo in tx.get(bucket_name, []) or []:
                address = (utxo.get("payment_addr") or {}).get("bech32")
                if address not in dex_set:
                    continue
                for asset in utxo.get("asset_list", []) or []:
                    if asset.get("policy_id") != token.policy_id:
                        continue
                    if asset.get("asset_name") != token.asset_name:
                        continue
                    qty = int(asset.get("quantity", 0))
                    if bucket_name == "outputs":
                        into_dex += qty
                    else:
                        out_of_dex += qty
        return into_dex - out_of_dex
