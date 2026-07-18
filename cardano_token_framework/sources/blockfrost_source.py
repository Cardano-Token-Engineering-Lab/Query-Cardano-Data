"""Blockfrost-backed implementation of :class:`TokenDataSource`.

Requires a Blockfrost API key. Set ``BLOCKFROST_API_TOKEN`` in your
environment (or a local ``.env`` file — see ``.env.example``) or pass an
already-constructed :class:`blockfrost.BlockFrostApi` instance directly via
the ``api`` constructor argument (this is how the test suite injects a
mocked client without making real network calls).

Note on rate limits: Blockfrost's free tier is rate-limited per second and
per day. ``get_swaps`` makes one extra API call per candidate transaction
(to fetch UTXO detail), so it is the most rate-limit-sensitive method here.
For large windows, prefer narrowing the time window or upgrading your plan.
"""

from __future__ import annotations

import logging

import pandas as pd
from blockfrost import BlockFrostApi

from cardano_token_framework.config import TimeWindow, TokenIdentifier, get_env_var
from cardano_token_framework.sources.base import TokenDataSource

logger = logging.getLogger(__name__)

_PAGE_SIZE = 100  # Blockfrost's max page size for list endpoints.


class BlockfrostSource(TokenDataSource):
    """Pulls Cardano native-token data via the Blockfrost API."""

    def __init__(self, api: BlockFrostApi | None = None) -> None:
        """Create a source.

        Args:
            api: An already-constructed Blockfrost client. If omitted, one is
                built from the ``BLOCKFROST_API_TOKEN`` environment variable.
        """
        self.api = api or BlockFrostApi(project_id=get_env_var("BLOCKFROST_API_TOKEN"))

    def get_asset_info(self, token: TokenIdentifier) -> pd.DataFrame:
        df = self.api.asset(asset=token.unit, return_type="pandas")
        if "metadata.decimals" not in df.columns:
            df["metadata.decimals"] = 0
        df["metadata.decimals"] = df["metadata.decimals"].fillna(0).astype(int)
        return df

    def get_asset_holders(self, token: TokenIdentifier) -> pd.DataFrame:
        info = self.get_asset_info(token)
        decimals = int(info["metadata.decimals"].iloc[0])

        frames = []
        page = 1
        while True:
            page_df = self.api.asset_addresses(
                asset=token.unit, page=page, return_type="pandas"
            )
            if page_df is None or len(page_df) == 0:
                break
            frames.append(page_df)
            if len(page_df) < _PAGE_SIZE:
                break
            page += 1

        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
            columns=["address", "quantity"]
        )
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce") / (10**decimals)
        return df.sort_values("quantity", ascending=False).reset_index(drop=True)

    def get_asset_transactions(
        self, token: TokenIdentifier, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        frames = []
        page = 1
        while True:
            page_df = self.api.asset_transactions(
                asset=token.unit, page=page, return_type="pandas"
            )
            if page_df is None or len(page_df) == 0:
                break
            frames.append(page_df)
            if len(page_df) < _PAGE_SIZE:
                break
            page += 1

        if not frames:
            return pd.DataFrame(columns=["tx_hash", "block_height", "block_time"])

        df = pd.concat(frames, ignore_index=True)
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
        decimals = int(info["metadata.decimals"].iloc[0])

        tx_df = self.get_asset_transactions(token, window=window)
        records = []

        for _, row in tx_df.iterrows():
            tx_hash = row["tx_hash"]
            try:
                utxos = self.api.transaction_utxos(hash=tx_hash, return_type="pandas")
            except Exception as exc:  # pragma: no cover - network/API errors
                logger.warning("Skipping tx %s: failed to fetch UTXOs (%s)", tx_hash, exc)
                continue

            net_into_dex = self._net_asset_flow_into_dex(utxos, token.unit, dex_set)
            if net_into_dex == 0:
                continue

            direction = "sell" if net_into_dex > 0 else "buy"
            records.append(
                {
                    "tx_hash": tx_hash,
                    "block_time": row["block_time"],
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
    def _net_asset_flow_into_dex(utxos_row: pd.DataFrame, unit: str, dex_set: set) -> int:
        """Compute (asset quantity into DEX outputs) - (asset quantity from DEX inputs).

        A positive result means the trader sent the token to a DEX address
        (i.e. they sold it); a negative result means the token flowed out of
        a DEX address to the trader (i.e. they bought it). Returns 0 if the
        asset did not touch a DEX address in this transaction at all.

        ``utxos_row`` is the single-row DataFrame returned by
        ``BlockFrostApi.transaction_utxos`` for one transaction, which holds
        the nested ``inputs`` and ``outputs`` lists.
        """
        if len(utxos_row) == 0:
            return 0
        inputs = utxos_row.iloc[0].get("inputs", []) or []
        outputs = utxos_row.iloc[0].get("outputs", []) or []

        into_dex = 0
        out_of_dex = 0
        for item, bucket_name in ((inputs, "inputs"), (outputs, "outputs")):
            for utxo in item:
                address = utxo.get("address")
                if address not in dex_set:
                    continue
                for amt in utxo.get("amount", []):
                    if amt.get("unit") != unit:
                        continue
                    qty = int(amt.get("quantity", 0))
                    if bucket_name == "outputs":
                        into_dex += qty
                    else:
                        out_of_dex += qty
        return into_dex - out_of_dex
