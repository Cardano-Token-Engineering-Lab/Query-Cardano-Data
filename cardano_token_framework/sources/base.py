"""Abstract interface that every data source backend implements.

Defining this interface up front is what makes the framework "source
agnostic": analysis code (and the cadCAD example in examples/) is written
against :class:`TokenDataSource` rather than against Blockfrost or Koios
directly, so a new backend (e.g. a future Dolos- or dbsync-backed source,
see docs/indexing_roadmap.md) can be dropped in without touching downstream
code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from cardano_token_framework.config import TimeWindow, TokenIdentifier


class TokenDataSource(ABC):
    """Common interface for pulling Cardano native-token data.

    Every method returns a :class:`pandas.DataFrame` with a stable, documented
    schema (see each method's docstring) regardless of which backend is used,
    so downstream analysis and modeling code does not need to know which
    source produced the data.
    """

    @abstractmethod
    def get_asset_info(self, token: TokenIdentifier) -> pd.DataFrame:
        """Return a single-row DataFrame describing the asset.

        Expected columns include at least: ``policy_id``, ``asset_name``,
        ``fingerprint``, ``quantity`` (total minted, in base units), and
        ``decimals``.
        """

    @abstractmethod
    def get_asset_holders(self, token: TokenIdentifier) -> pd.DataFrame:
        """Return current holder addresses and balances for the asset.

        Expected columns: ``address``, ``quantity`` (decimal-adjusted units).
        """

    @abstractmethod
    def get_asset_transactions(
        self, token: TokenIdentifier, window: TimeWindow | None = None
    ) -> pd.DataFrame:
        """Return all transactions that moved the asset, optionally filtered.

        Expected columns: ``tx_hash``, ``block_time`` (UTC ``datetime``),
        ``block_height``.
        """

    @abstractmethod
    def get_swaps(
        self,
        token: TokenIdentifier,
        dex_addresses: list[str],
        window: TimeWindow | None = None,
    ) -> pd.DataFrame:
        """Return basic swap-type transactions for the asset at known DEX addresses.

        This is a heuristic, not a full datum/redeemer decode (see
        docs/indexing_roadmap.md for the plan to do that properly). A
        transaction is classified as a swap if it moves the asset into or
        out of one of ``dex_addresses``. Expected columns: ``tx_hash``,
        ``block_time``, ``dex_address``, ``direction`` (``"buy"`` or
        ``"sell"`` from the perspective of the non-DEX counterparty),
        ``quantity`` (decimal-adjusted units of ``token`` moved).
        """
