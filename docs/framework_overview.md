# `cardano_token_framework` — Feature Overview

A source-agnostic Python framework for pulling Cardano native-token on-chain
data into `pandas` DataFrames, so the same analysis or systems-modeling code
works no matter which backend served the data. This page walks through every
feature the package exposes. For install/quickstart instructions, see the
top-level [`README.md`](../README.md); for the plan to move beyond
Blockfrost/Koios, see [`indexing_roadmap.md`](indexing_roadmap.md).

## Contents

- [Package layout](#package-layout)
- [Inputs: `TokenIdentifier` and `TimeWindow`](#inputs-tokenidentifier-and-timewindow)
- [The `TokenDataSource` interface](#the-tokendatasource-interface)
  - [`get_asset_info`](#get_asset_info)
  - [`get_asset_holders`](#get_asset_holders)
  - [`get_asset_transactions`](#get_asset_transactions)
  - [`get_swaps`](#get_swaps)
- [Backends](#backends)
  - [`BlockfrostSource`](#blockfrostsource)
  - [`KoiosSource`](#koiossource)
- [Environment / configuration](#environment--configuration)
- [Command-line interface](#command-line-interface)
- [Using it as a library](#using-it-as-a-library)
- [Known limitations](#known-limitations)

## Package layout

```
cardano_token_framework/
  __init__.py          # public exports: TokenIdentifier, TimeWindow, BlockfrostSource, KoiosSource
  __main__.py           # `python -m cardano_token_framework` entry point
  cli.py                 # argparse-based CLI, built on the same public API
  config.py              # TokenIdentifier, TimeWindow, get_env_var
  sources/
    base.py              # TokenDataSource abstract interface (the contract every backend implements)
    blockfrost_source.py # Blockfrost-backed implementation
    koios_source.py       # Koios-backed implementation
```

Everything downstream — the CLI and the [cadCAD example](../examples/cadcad_basic_model.py)
— is written against the `TokenDataSource` interface, not against a specific
backend. That's what makes swapping `--source blockfrost` for
`--source koios` a one-flag change rather than a rewrite.

## Inputs: `TokenIdentifier` and `TimeWindow`

Every method in the framework takes one or both of these two plain,
frozen dataclasses (`cardano_token_framework/config.py`).

### `TokenIdentifier`

Identifies a single Cardano native asset by policy ID and (optionally)
asset name.

```python
from cardano_token_framework import TokenIdentifier

token = TokenIdentifier(
    policy_id="da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24",
    asset_name="4c51",  # hex-encoded; omit for ADA-only contexts
)
```

| Field | Type | Notes |
|---|---|---|
| `policy_id` | `str` | Required. Must be exactly 56 hex characters — validated in `__post_init__`, raises `ValueError` otherwise. |
| `asset_name` | `str` | Optional, hex-encoded. Defaults to `""`. |
| `display_name` | `str \| None` | Optional. If omitted, it's derived automatically: `asset_name` is decoded as UTF-8 if possible, otherwise the hex string is used as-is, and if `asset_name` is empty the first 8 characters of `policy_id` are used. Used only for display/labeling — not sent to any API. |

`token.unit` returns `policy_id + asset_name` concatenated, the identifier
format most Cardano APIs (including Blockfrost) expect for a single asset.

### `TimeWindow`

A UTC time window used to bound a data extraction. Every field is
optional — an unbounded window (`TimeWindow()`) means "everything."

```python
from cardano_token_framework import TimeWindow

window = TimeWindow.from_strings(start="2024-01-01", end="2024-02-01")
```

| Field | Type | Notes |
|---|---|---|
| `start` | `datetime \| None` | Inclusive lower bound. Naive datetimes are coerced to UTC automatically. |
| `end` | `datetime \| None` | Exclusive upper bound. Same UTC coercion. |

- `TimeWindow.from_strings(start=None, end=None)` — convenience constructor
  that parses ISO-8601 date/datetime strings (what the CLI's `--start`/`--end`
  flags accept), e.g. `"2024-01-01"` or a full ISO datetime.
- `window.contains(when)` — returns `True` if `when` falls in `[start, end)`.
  This is what every backend uses internally to filter transaction results.
- Construction raises `ValueError` if `start > end`.

## The `TokenDataSource` interface

`cardano_token_framework/sources/base.py` defines the abstract contract
(`ABC`) every backend implements. Four methods, each returning a
`pandas.DataFrame` with a stable, documented schema regardless of backend:

### `get_asset_info`

```python
source.get_asset_info(token: TokenIdentifier) -> pd.DataFrame
```

Single-row DataFrame describing the asset: policy ID, asset name,
fingerprint, total quantity minted (base units), and decimals. Both
backends normalize the decimals field to a plain `int` column even when
the underlying API omits it (defaulting to `0`).

### `get_asset_holders`

```python
source.get_asset_holders(token: TokenIdentifier) -> pd.DataFrame
```

Columns: `address`, `quantity`. Current holder addresses and their
decimal-adjusted balances (raw on-chain quantity divided by
`10 ** decimals`), sorted largest-holder-first. Both backends paginate
through the full result set automatically before returning.

### `get_asset_transactions`

```python
source.get_asset_transactions(token: TokenIdentifier, window: TimeWindow | None = None) -> pd.DataFrame
```

Columns: `tx_hash`, `block_height`, `block_time` (UTC `datetime`). Every
transaction that moved the asset, sorted chronologically, optionally
filtered to `window`. Filtering happens client-side against the returned
`block_time` — both backends pull the full history and then apply
`window.contains()`, rather than pushing the filter to the API.

### `get_swaps`

```python
source.get_swaps(token: TokenIdentifier, dex_addresses: list[str], window: TimeWindow | None = None) -> pd.DataFrame
```

Columns: `tx_hash`, `block_time`, `dex_address`, `direction`
(`"buy"` or `"sell"`), `quantity` (decimal-adjusted units of `token`
moved). Basic swap-type transaction detection at one or more known
DEX/batcher addresses.

**How classification works (same heuristic in both backends):** for each
candidate transaction, sum the asset quantity flowing into `dex_addresses`
via transaction outputs, and subtract the quantity flowing out via
transaction inputs. A positive net flow means the token moved *into* a DEX
address — classified `"sell"` (from the non-DEX counterparty's
perspective). A negative net flow means the token moved *out of* a DEX
address — classified `"buy"`. A net flow of zero (the asset never touched
`dex_addresses` in that transaction) means the transaction is dropped
entirely.

This is a **heuristic based on net asset flow, not a datum/redeemer
decode** — it's correct for simple swaps but can misclassify complex
batched or multi-hop transactions. See
[`indexing_roadmap.md`](indexing_roadmap.md) for the plan to replace it
with ground-truth decoding.

## Backends

### `BlockfrostSource`

`cardano_token_framework/sources/blockfrost_source.py`, built on the
official `blockfrost` Python SDK.

```python
from cardano_token_framework import BlockfrostSource

source = BlockfrostSource()                 # reads BLOCKFROST_API_TOKEN from env/.env
# or, e.g. for tests / a pre-built client:
source = BlockfrostSource(api=my_blockfrost_client)
```

- Requires an API key (`BLOCKFROST_API_TOKEN`) — see
  [Environment / configuration](#environment--configuration).
- Paginates list endpoints (`asset_addresses`, `asset_transactions`) in
  pages of 100, Blockfrost's max page size.
- `get_swaps` makes **one extra API call per candidate transaction**
  (`transaction_utxos`, to inspect input/output addresses) — this is the
  main rate-limit/performance constraint on Blockfrost's free tier for
  large time windows. A transaction that fails to fetch is logged and
  skipped rather than aborting the whole run.

### `KoiosSource`

`cardano_token_framework/sources/koios_source.py`, built on the
`koios-api` PyPI package.

```python
from cardano_token_framework.sources.koios_source import KoiosSource

source = KoiosSource()                # uses the real koios_api module
# or inject a mock/alternate client (used by the test suite):
source = KoiosSource(client=my_mock_client)
```

- Does **not** require an API key on Koios' public tier (as of this
  writing — see the top-level README for the current policy).
- `get_swaps` fetches transaction detail for all candidate hashes in a
  single `get_tx_info` batch call, rather than one call per transaction
  like the Blockfrost backend — a meaningful throughput difference for
  large windows.
- Relies on the documented `/tx_info` response shape (`inputs`/`outputs`
  with `payment_addr.bech32` and an `asset_list` of
  `{policy_id, asset_name, quantity}`), covered by a mocked unit test
  rather than a live call since Koios' public schema can evolve
  independently of this repo.

Both backends implement `TokenDataSource`, so they're interchangeable
anywhere the interface is used — swap one for the other via `--source` on
the CLI, or by constructing the other class directly as a library.

## Environment / configuration

`cardano_token_framework/config.py` provides `get_env_var(name)`, used
internally by `BlockfrostSource` to load `BLOCKFROST_API_TOKEN`. It calls
`dotenv.load_dotenv()` first, so a local `.env` file (copied from
[`.env.example`](../.env.example)) is picked up automatically, and raises a
clear `OSError` — pointing back at `.env.example` — if a required variable
is missing.

## Command-line interface

`cardano_token_framework/cli.py`, exposed via
`python -m cardano_token_framework`. Global flags precede the subcommand;
subcommand-specific flags follow it.

| Flag | Scope | Notes |
|---|---|---|
| `--source {blockfrost,koios}` | global | Default `blockfrost`. |
| `--policy-id` | global | Required. |
| `--asset-name` | global | Optional, hex-encoded. |
| `--output` | global | Optional CSV path; if given, results are also written to disk. |

Subcommands, each mapping directly to one `TokenDataSource` method:

- `info` — `get_asset_info`
- `holders` — `get_asset_holders`
- `transactions --start ... --end ...` — `get_asset_transactions`
- `swaps --dex-address ... [--dex-address ...] --start ... --end ...` —
  `get_swaps`. `--dex-address` may be repeated to check multiple DEX
  addresses in one call.

Every invocation prints the first 20 rows of the resulting DataFrame to
stdout (`df.head(20).to_string()`), and writes the full result to
`--output` if given. The whole thing is also importable as
`cardano_token_framework.cli.run(argv)`, which returns the DataFrame
directly — useful for testing or scripting without shelling out.

## Using it as a library

Nothing about the framework requires the CLI — every piece above is a
plain importable class/function:

```python
from cardano_token_framework import BlockfrostSource, TimeWindow, TokenIdentifier

token = TokenIdentifier(
    policy_id="da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24",
    asset_name="4c51",
)
source = BlockfrostSource()

info_df = source.get_asset_info(token)
holders_df = source.get_asset_holders(token)

window = TimeWindow.from_strings("2024-01-01", "2024-02-01")
tx_df = source.get_asset_transactions(token, window=window)
swaps_df = source.get_swaps(token, dex_addresses=["addr1..."], window=window)
```

Because every method returns a plain `pandas.DataFrame` with a stable
schema, the output plugs directly into further analysis or a systems
model — see [`examples/cadcad_basic_model.py`](../examples/cadcad_basic_model.py)
for a worked example feeding `get_swaps` output into a running cadCAD
simulation.

## Known limitations

- **Swap classification is a heuristic** (net asset flow at known DEX
  addresses), not a true datum/redeemer decode. See
  [`indexing_roadmap.md`](indexing_roadmap.md) for the plan to fix this.
- **p2p transfers and staking/smart-contract interaction types** are not
  yet classified as distinct transaction types — an explicit stretch goal,
  tracked as future work rather than silently dropped.
- **`get_swaps` on `BlockfrostSource` makes one API call per candidate
  transaction**, the main rate-limit/performance constraint for large time
  windows on Blockfrost's free tier. `KoiosSource` batches this into one
  call instead.
