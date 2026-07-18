# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - Milestone 2: Code Framework for Modeling Data Acquisition

### Added
- `cardano_token_framework` Python package replacing the original
  token-specific prototype scripts:
  - `TokenIdentifier` / `TimeWindow` input objects (policy ID + asset name,
    and a start/end time window — the milestone's specified inputs).
  - `TokenDataSource` abstract interface implemented by both
    `BlockfrostSource` and `KoiosSource`, covering asset info, holders,
    transactions, and a basic swap-classification heuristic.
  - `python -m cardano_token_framework` CLI with `info`, `holders`,
    `transactions`, and `swaps` subcommands.
- Full test suite (`tests/`) with mocked API clients — 100% statement
  coverage on the package, no live network calls required to run CI.
- `ruff` linting configuration (`pyproject.toml`) and GitHub Actions CI
  (`.github/workflows/ci.yml`) running lint + tests on every push/PR across
  Python 3.10-3.12.
- `examples/` -- sample input JSON, sample output CSV, and
  `cadcad_basic_model.py`, a minimal cadCAD model that consumes the
  framework's swap-volume output as an input signal.
- `docs/indexing_roadmap.md` -- research and phased plan for moving beyond
  Blockfrost/Koios to a more robust indexing backend (Dolos, Carp, or
  Oura+Scrolls).
- `CONTRIBUTING.md`, `CODE_REVIEW.md`, `PROGRESS.md`, issue/PR templates.

### Changed
- Original `Blockfrost/` and `Koios/` scripts moved to `legacy/` (see
  `legacy/README.md`) and are no longer the supported entry point.

### Fixed
- `legacy/Blockfrost/token_tx.py`: `get_asset_tx` wrote `df_tx_data` (a name
  that didn't exist yet at that point in execution) instead of the local
  `df`; fixed in the rewrite by removing the file-level execution-order
  dependency entirely (`BlockfrostSource.get_asset_transactions` returns the
  DataFrame to the caller instead of writing a CSV as a side effect).
- `legacy/Koios/address_info.py`: dict comprehension referenced an undefined
  `address_info` variable and built duplicate dict keys; superseded by
  `KoiosSource.get_swaps`, which is covered by tests.
