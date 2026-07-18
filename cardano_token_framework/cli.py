"""Command-line interface for the Cardano Token Framework.

Examples:
    Fetch asset info::

        python -m cardano_token_framework info \\
            --policy-id da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24 \\
            --asset-name 4c51

    Fetch swap-type transactions for a window, writing to CSV::

        python -m cardano_token_framework \\
            --policy-id da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24 \\
            --asset-name 4c51 \\
            --source blockfrost --output swaps.csv \\
            swaps \\
            --dex-address addr1zxn9efv2f6w82hagxqtn62ju4m293tqvw0uhmdl64ch8uw6j2c79gy9l76sdg0xwhd7r0c0kna0tycz4y5s6mlenh8pq6s3z70 \\
            --start 2024-01-01 --end 2024-02-01
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from cardano_token_framework.config import TimeWindow, TokenIdentifier
from cardano_token_framework.sources.base import TokenDataSource
from cardano_token_framework.sources.blockfrost_source import BlockfrostSource
from cardano_token_framework.sources.koios_source import KoiosSource

_SOURCES = {
    "blockfrost": BlockfrostSource,
    "koios": KoiosSource,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cardano_token_framework",
        description="Pull Cardano native-token on-chain data into CSV/DataFrames.",
    )
    parser.add_argument(
        "--source",
        choices=sorted(_SOURCES),
        default="blockfrost",
        help="Which backend to query (default: blockfrost).",
    )
    parser.add_argument(
        "--policy-id", required=True, help="56-character hex policy ID."
    )
    parser.add_argument(
        "--asset-name", default="", help="Hex-encoded asset name (omit for ADA)."
    )
    parser.add_argument(
        "--output", default=None, help="Optional CSV path to write results to."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("info", help="Fetch asset metadata.")
    subparsers.add_parser("holders", help="Fetch current holder addresses/balances.")

    tx_parser = subparsers.add_parser("transactions", help="Fetch asset transactions.")
    tx_parser.add_argument("--start", default=None, help="ISO date/datetime, inclusive.")
    tx_parser.add_argument("--end", default=None, help="ISO date/datetime, exclusive.")

    swap_parser = subparsers.add_parser(
        "swaps", help="Fetch basic swap-type transactions at known DEX addresses."
    )
    swap_parser.add_argument(
        "--dex-address",
        action="append",
        required=True,
        dest="dex_addresses",
        help="A known DEX/batcher address to check for swap activity. "
        "May be passed multiple times.",
    )
    swap_parser.add_argument("--start", default=None, help="ISO date/datetime, inclusive.")
    swap_parser.add_argument("--end", default=None, help="ISO date/datetime, exclusive.")

    return parser


def run(argv: list[str] | None = None) -> pd.DataFrame:
    """Parse CLI args, run the requested command, and return the resulting DataFrame.

    Also writes to ``--output`` (if given) and prints a preview to stdout.
    Exposed as a function (rather than only a ``__main__`` block) so it is
    directly testable and importable from notebooks.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    source_cls = _SOURCES[args.source]
    source: TokenDataSource = source_cls()
    token = TokenIdentifier(policy_id=args.policy_id, asset_name=args.asset_name)

    if args.command == "info":
        df = source.get_asset_info(token)
    elif args.command == "holders":
        df = source.get_asset_holders(token)
    elif args.command == "transactions":
        window = TimeWindow.from_strings(args.start, args.end)
        df = source.get_asset_transactions(token, window=window)
    elif args.command == "swaps":
        window = TimeWindow.from_strings(args.start, args.end)
        df = source.get_swaps(token, args.dex_addresses, window=window)
    else:  # pragma: no cover - argparse prevents this
        raise ValueError(f"Unknown command: {args.command}")

    print(df.head(20).to_string())
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"\nWrote {len(df)} rows to {args.output}")

    return df


def main() -> None:  # pragma: no cover - thin wrapper around run()
    try:
        run(sys.argv[1:])
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
