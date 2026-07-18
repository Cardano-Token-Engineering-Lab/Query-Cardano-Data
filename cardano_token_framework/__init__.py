"""Cardano Token Framework.

A small, source-agnostic framework for pulling Cardano native-token on-chain
data (asset info, holders, transactions, and basic DEX swap activity) into
pandas DataFrames suitable for feeding systems models (e.g., cadCAD).

Supported data sources today: Blockfrost and Koios. Both implement the same
:class:`cardano_token_framework.sources.base.TokenDataSource` interface, so
callers can switch backends without changing analysis code.

See the top-level README.md for usage and docs/indexing_roadmap.md for the
plan to support more robust indexing backends (Dolos, Carp, Oura/Scrolls).
"""

from cardano_token_framework.config import TimeWindow, TokenIdentifier
from cardano_token_framework.sources.blockfrost_source import BlockfrostSource
from cardano_token_framework.sources.koios_source import KoiosSource

__all__ = [
    "TimeWindow",
    "TokenIdentifier",
    "BlockfrostSource",
    "KoiosSource",
]

__version__ = "0.1.0"
