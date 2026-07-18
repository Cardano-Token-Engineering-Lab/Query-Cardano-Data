# Cardano Token Engineering Lab — Query Cardano Data

A Python framework for pulling Cardano native-token on-chain data (asset info, holders, transactions, swaps) into `pandas` DataFrames for systems modeling. Built for Project Catalyst **Milestone: Code Framework for Modeling Data Acquisition**.

[![CI](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/actions/workflows/ci.yml/badge.svg)](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/actions/workflows/ci.yml)

## Milestone requirements → deliverables

| Requirement | Delivered as |
|---|---|
| Framework to pull on-chain token data into Python | [`cardano_token_framework/`](cardano_token_framework/) — [`TokenDataSource`](cardano_token_framework/sources/base.py) interface, [`BlockfrostSource`](cardano_token_framework/sources/blockfrost_source.py), [`KoiosSource`](cardano_token_framework/sources/koios_source.py) |
| Basic token swap transaction type | [`get_swaps()`](cardano_token_framework/sources/blockfrost_source.py) — DEX-address swap classification |
| Stretch: p2p / smart-contract (staking) transactions | Not implemented — scoped as future work in [`docs/indexing_roadmap.md`](docs/indexing_roadmap.md#4-phase-4-stretch-matches-the-milestones-own-stretch-goal-p2p-and-staking-events) |
| Supports all Cardano tokens | Parameterized by policy ID / asset name — [`config.py`](cardano_token_framework/config.py) |
| Inputs: policy ID + asset name, time window | [`TokenIdentifier`, `TimeWindow`](cardano_token_framework/config.py) |
| README explaining usage | This file |
| Example inputs/outputs | [`examples/sample_input.json`](examples/sample_input.json), [`examples/sample_output_swaps.csv`](examples/sample_output_swaps.csv) |
| Supporting docs to run the scripts | [`.env.example`](.env.example), [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Research + plan for a more robust solution (Dolos/Carp/Oura+Scrolls) | [`docs/indexing_roadmap.md`](docs/indexing_roadmap.md) |
| Linting | [`pyproject.toml`](pyproject.toml) (ruff), enforced in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |
| Testing coverage | [`tests/`](tests/) — 100% statement coverage, enforced in CI |
| Docstrings/comments | Every public function in [`cardano_token_framework/`](cardano_token_framework/) |
| Enhanced README (usage + update handling) | This file + [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Code review / assurance process | [`CODE_REVIEW.md`](CODE_REVIEW.md) |
| Automated testing results | [CI Actions tab](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/actions) |
| Example token model using framework output | [`examples/cadcad_basic_model.py`](examples/cadcad_basic_model.py) — basic cadCAD model |
| Feedback loops | [Issues](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/issues), [issue templates](.github/ISSUE_TEMPLATE/) |
| Project progress page | [`PROGRESS.md`](PROGRESS.md) |

## Quickstart

```bash
git clone https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data.git
cd Query-Cardano-Data
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # add your Blockfrost key
```

```bash
python -m cardano_token_framework \
  --policy-id da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24 \
  --asset-name 4c51 \
  info
```

## Usage

```bash
# Asset metadata
python -m cardano_token_framework --policy-id <policy_id> --asset-name <asset_name> info

# Holders
python -m cardano_token_framework --policy-id <policy_id> --asset-name <asset_name> holders

# Transactions in a window
python -m cardano_token_framework --policy-id <policy_id> --asset-name <asset_name> \
  transactions --start 2024-01-01 --end 2024-02-01

# Swaps at a known DEX address
python -m cardano_token_framework --policy-id <policy_id> --asset-name <asset_name> --output swaps.csv \
  swaps --dex-address <dex_address> --start 2024-01-01 --end 2024-02-01
```

Global flags (`--source`, `--policy-id`, `--asset-name`, `--output`) go before the subcommand; subcommand flags go after. Add `--source koios` to use Koios instead of Blockfrost. Full flag reference: `-h` on any command.

As a library:

```python
from cardano_token_framework import BlockfrostSource, TimeWindow, TokenIdentifier

token = TokenIdentifier(policy_id="da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24", asset_name="4c51")
source = BlockfrostSource()
holders_df = source.get_asset_holders(token)
```

See [`examples/README.md`](examples/README.md) for the full worked example, including the cadCAD model.

## Output schemas

`get_swaps`: `tx_hash`, `block_time`, `dex_address`, `direction` (`buy`/`sell`), `quantity`
`get_asset_holders`: `address`, `quantity`
`get_asset_transactions`: `tx_hash`, `block_height`, `block_time`

## Development

```bash
ruff check cardano_token_framework tests examples   # lint
pytest --cov-report=term-missing                     # tests + coverage
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup and update-handling conventions, [`CODE_REVIEW.md`](CODE_REVIEW.md) for the review process, and [`CHANGELOG.md`](CHANGELOG.md) for release history.

## Project layout

```
cardano_token_framework/    config.py, cli.py, sources/ (base + Blockfrost + Koios)
tests/                       100% coverage, mocked API clients
examples/                    sample input/output + cadCAD model
docs/indexing_roadmap.md     plan for Dolos / Carp / Oura+Scrolls
legacy/                      superseded prototype scripts
```

## Limitations

- Swap classification is a net-asset-flow heuristic, not a datum/redeemer decode — see [`docs/indexing_roadmap.md`](docs/indexing_roadmap.md).
- p2p / staking transaction types are not yet implemented (milestone stretch goal) — tracked in [`PROGRESS.md`](PROGRESS.md).

## License

[LICENSE](LICENSE)
