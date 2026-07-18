# Cardano Token Engineering Lab — Query Cardano Data

A small Python framework for pulling Cardano native-token on-chain data —
asset metadata, holders, transactions, and basic swap activity — into
`pandas` DataFrames, ready to feed into systems models (e.g.
[cadCAD](https://cadcad.org/)). Built for Project Catalyst Milestone 2:
*"Code Framework for Modeling Data Acquisition."*

It supports **any Cardano native token** — pass in a policy ID (and asset
name) and a time window, and pull data from either
[Blockfrost](https://blockfrost.io/) or [Koios](https://koios.rest/) behind
one common interface.

[![CI](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/actions/workflows/ci.yml/badge.svg)](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/actions/workflows/ci.yml)

## Contents

- [Quickstart](#quickstart)
- [What it does](#what-it-does)
- [Usage](#usage)
  - [As a CLI](#as-a-cli)
  - [As a library](#as-a-library)
- [Output schemas](#output-schemas)
- [Choosing a backend](#choosing-a-backend--why-not-dbsync-directly)
- [Examples (incl. the cadCAD model)](#examples)
- [Project layout](#project-layout)
- [Development, testing, and updates](#development-testing-and-updates)
- [Limitations & roadmap](#limitations--roadmap)
- [Feedback](#feedback)

## Quickstart

```bash
git clone https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data.git
cd Query-Cardano-Data
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then put your Blockfrost key in .env
```

```bash
python -m cardano_token_framework \
  --policy-id da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24 \
  --asset-name 4c51 \
  info
```

## What it does

```
                         ┌──────────────────────┐
  policy_id, asset_name  │                      │   pandas.DataFrame
  + time window  ───────▶│  TokenDataSource     │──────────────────▶  your model
  (TokenIdentifier,      │  (Blockfrost/Koios)  │   (info / holders /
   TimeWindow)           │                      │    transactions / swaps)
                         └──────────────────────┘
```

Every data source implements the same interface
(`cardano_token_framework.sources.base.TokenDataSource`), so the rest of
this framework — the CLI, and the cadCAD example in `examples/` — doesn't
care which backend produced the data.

| Method | Returns |
|---|---|
| `get_asset_info(token)` | Asset metadata (decimals, total minted, fingerprint, ...) |
| `get_asset_holders(token)` | Current holder addresses + decimal-adjusted balances |
| `get_asset_transactions(token, window)` | All transactions that moved the asset in a time window |
| `get_swaps(token, dex_addresses, window)` | Basic swap-type transactions at known DEX/batcher addresses, classified `buy`/`sell` |

## Usage

### As a CLI

```bash
# Asset metadata
python -m cardano_token_framework --policy-id <policy_id> --asset-name <asset_name> info

# Current holders
python -m cardano_token_framework --policy-id <policy_id> --asset-name <asset_name> holders

# Transactions in a window
python -m cardano_token_framework --policy-id <policy_id> --asset-name <asset_name> \
  transactions --start 2024-01-01 --end 2024-02-01

# Swap-type transactions at a known DEX address, written to CSV
python -m cardano_token_framework \
  --policy-id da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24 \
  --asset-name 4c51 \
  --output swaps.csv \
  swaps \
  --dex-address addr1zxn9efv2f6w82hagxqtn62ju4m293tqvw0uhmdl64ch8uw6j2c79gy9l76sdg0xwhd7r0c0kna0tycz4y5s6mlenh8pq6s3z70 \
  --start 2024-01-01 --end 2024-02-01
```

Global flags (`--source`, `--policy-id`, `--asset-name`, `--output`) go
**before** the subcommand; subcommand-specific flags (`--start`, `--end`,
`--dex-address`) go after it. Run `python -m cardano_token_framework -h` or
`... <subcommand> -h` for the full flag reference — this README's examples
are kept runnable as-written, but `-h` is always the source of truth.

Add `--source koios` to use Koios instead of Blockfrost (no API key needed
for Koios' current public tier).

### As a library

```python
from cardano_token_framework import BlockfrostSource, TimeWindow, TokenIdentifier

token = TokenIdentifier(
    policy_id="da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24",
    asset_name="4c51",  # "LQ"
)
window = TimeWindow.from_strings("2024-01-01", "2024-02-01")

source = BlockfrostSource()  # reads BLOCKFROST_API_TOKEN from .env
holders_df = source.get_asset_holders(token)
swaps_df = source.get_swaps(
    token,
    dex_addresses=["addr1zxn9efv2f6w82hagxqtn62ju4m293tqvw0uhmdl64ch8uw6j2c79gy9l76sdg0xwhd7r0c0kna0tycz4y5s6mlenh8pq6s3z70"],
    window=window,
)
```

Swap to Koios by importing `KoiosSource` instead — same method calls, same
output schema.

## Output schemas

`get_swaps` (the schema the cadCAD example consumes):

| Column | Type | Notes |
|---|---|---|
| `tx_hash` | str | |
| `block_time` | UTC datetime | |
| `dex_address` | str | The DEX/batcher address(es) checked, comma-joined |
| `direction` | `"buy"` \| `"sell"` | From the non-DEX counterparty's perspective |
| `quantity` | float | Decimal-adjusted token units moved |

`get_asset_holders`: `address` (str), `quantity` (float, decimal-adjusted).

`get_asset_transactions`: `tx_hash` (str), `block_height` (int), `block_time`
(UTC datetime).

See `examples/sample_output_swaps.csv` for a worked (synthetic) example.

## Choosing a backend / why not dbsync directly?

The milestone spec calls for starting with dbsync "or a similar querying
tool." Blockfrost and Koios are both REST layers over indexed Cardano chain
data — Koios in particular runs on its own dbsync-fed infrastructure — so
they satisfy that without requiring every user of this framework to run
and sync their own Postgres instance just to try it out. Running your own
indexer (dbsync, or one of the more robust options below) remains the right
move for production use at scale; see
[`docs/indexing_roadmap.md`](docs/indexing_roadmap.md) for the researched,
phased plan to get there (Dolos, Carp, Oura/Scrolls).

## Examples

See [`examples/`](examples/) for:
- `sample_input.json` — example inputs (policy ID, asset name, time window, DEX address)
- `sample_output_swaps.csv` — example output matching the `get_swaps` schema
- `cadcad_basic_model.py` — **a basic cadCAD model that consumes the framework's
  output**, demonstrating the full path from on-chain data to a running
  systems model:

  ```bash
  python examples/cadcad_basic_model.py
  ```

## Project layout

```
cardano_token_framework/
  config.py                  # TokenIdentifier, TimeWindow, env loading
  sources/
    base.py                  # TokenDataSource abstract interface
    blockfrost_source.py
    koios_source.py
  cli.py                      # python -m cardano_token_framework ...
tests/                        # mirrors the layout above, 100% coverage
examples/                     # sample input/output + the cadCAD demo
docs/
  indexing_roadmap.md         # research + plan for Dolos/Carp/Oura+Scrolls
legacy/                       # superseded prototype scripts (kept for reference)
```

## Development, testing, and updates

```bash
ruff check cardano_token_framework tests examples   # lint
pytest --cov-report=term-missing                     # tests + coverage
```

Both run in CI (`.github/workflows/ci.yml`) on every push/PR across Python
3.10-3.12. See **`CONTRIBUTING.md`** for the full setup/contribution
workflow and **`CODE_REVIEW.md`** for how changes are reviewed and what
"passing CI" actually checks. **`CHANGELOG.md`** records what changed in
each version — update it as part of any PR that changes behavior, and see
`PROGRESS.md` for the milestone-by-milestone status this repo is tracked
against.

## Limitations & roadmap

- **Swap classification is a heuristic** (net asset flow at a known DEX
  address), not a true datum/redeemer decode — see
  `docs/indexing_roadmap.md` for the plan to fix that.
- **p2p transfers and staking/contract-interaction classification** were the
  milestone's stretch goal and are not yet implemented — tracked as future
  work in `PROGRESS.md`, not silently dropped.
- **Blockfrost rate limits** bound how large a `swaps` time window is
  practical on the free tier, since it's one extra API call per candidate
  transaction.

## Feedback

- **Bugs / feature requests:** open a GitHub issue using the templates in
  `.github/ISSUE_TEMPLATE/`.
- **Direction-setting feedback** (which protocols to prioritize, which
  modeling use cases matter most): see the channels listed in `PROGRESS.md`.

## License

See [`LICENSE`](LICENSE).
