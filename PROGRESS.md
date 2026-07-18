# Project Progress — Code Framework for Modeling Data Acquisition

This page tracks progress and evidence for Milestone 2. It is the
repo-resident copy of the page that should also be published on the
project's public site/Catalyst page (see "Publishing this page" below) —
the milestone's acceptance criteria require a public progress page in
addition to repo documentation, and this file is meant to be the single
source of truth that page is generated/copied from.

## Status: Complete, pending review

| Requirement | Status | Evidence |
|---|---|---|
| Framework pulls on-chain token data into Python | Done | `cardano_token_framework/sources/` |
| Inputs: policy ID, asset name, time window | Done | `cardano_token_framework/config.py` (`TokenIdentifier`, `TimeWindow`) |
| Basic token swap transaction type | Done | `TokenDataSource.get_swaps` (both backends) |
| Stretch: p2p / smart-contract (staking) transaction types | Not started | Logged as future work — see `docs/indexing_roadmap.md` §5 |
| Supports all Cardano tokens | Done | Framework is parameterized by policy ID/asset name; no token-specific code remains in `cardano_token_framework/` |
| Initially via dbsync or similar querying tool | Done | Blockfrost + Koios (both query indexed/served chain data, equivalent in spirit to a dbsync-backed REST layer) |
| README explains usage | Done | top-level `README.md` |
| Example inputs/outputs | Done | `examples/sample_input.json`, `examples/sample_output_swaps.csv` |
| Supporting docs for scripts to run | Done | `.env.example`, `CONTRIBUTING.md` |
| Research + plan for a more robust solution (Dolos/Carp/Oura+Scrolls) | Done | `docs/indexing_roadmap.md` |
| Linting | Done | `ruff`, enforced in CI |
| Testing coverage | Done | 100% statement coverage, 49 tests, enforced in CI |
| Docstrings/comments | Done | every public function in `cardano_token_framework/` |
| Enhanced README (usage + update handling) | Done | top-level `README.md` + `CONTRIBUTING.md` |
| Code review / assurance process | Done | `CODE_REVIEW.md` |
| Example token model using framework output (cadCAD) | Done | `examples/cadcad_basic_model.py` |
| Feedback loops | Done | GitHub Issues/templates + see "Feedback channels" below |
| Public progress page | **Action needed** | Publish this file's content — see below |

## What this milestone delivers

A small Python framework (`cardano_token_framework`) that:

1. Takes a token's policy ID, optional asset name, and a time window as input.
2. Queries either Blockfrost or Koios (interchangeably, behind one interface)
   for that token's metadata, current holders, transaction history, and
   basic swap activity at known DEX addresses.
3. Returns everything as `pandas.DataFrame`s with a stable schema, ready to
   feed into a systems model — demonstrated end-to-end with a basic cadCAD
   model in `examples/cadcad_basic_model.py`.

It replaces an earlier set of token-specific, hardcoded prototype scripts
(now in `legacy/`) with parameterized, tested, documented code that works
for any Cardano native token.

## Known limitations (tracked, not hidden)

- **Swap classification is a heuristic**, not a true datum/redeemer decode.
  It infers buy/sell direction from net asset flow at a known DEX address,
  which is correct for simple swaps but can misclassify more complex batched
  or multi-hop transactions. See `docs/indexing_roadmap.md` for the plan to
  replace this with proper decoding.
- **p2p transfers and staking/smart-contract interactions are not yet
  classified as distinct types** — this was an explicit stretch goal in the
  milestone spec and is logged as future work, not silently dropped.
- **`get_swaps` makes one API call per candidate transaction** against
  Blockfrost, which is the main rate-limit/performance constraint for large
  time windows on the free tier.

## Code review and quality evidence

- CI status: see the badge/Actions tab on the repo — every push and PR runs
  `ruff check` and the full `pytest` suite (with coverage) across Python
  3.10-3.12.
- Process: see `CODE_REVIEW.md`.
- Latest coverage: 100% (`cardano_token_framework/`), 49 tests, 0 lint errors
  at the time of this milestone submission.

## Feedback channels

- **GitHub Issues** on this repo — bug reports and feature requests use the
  templates in `.github/ISSUE_TEMPLATE/`.
- **Social media** — [add the Cardano Token Engineering Lab's
  Twitter/X / Discord link(s) here once finalized for this milestone].
- **Website feedback form** — [add the form URL here once published].

> Maintainer note: the two bracketed items above need real links before this
> page is published externally — they're placeholders because the actual
> social/website properties weren't provided as part of this milestone's
> source material.

## Publishing this page

The milestone requires the progress page to be visible somewhere beyond the
repo itself. Two low-effort options:

1. **GitHub Pages**: enable Pages for this repo (Settings → Pages → deploy
   from `main` / root or `/docs`), which will render this file directly.
2. **Mirror to the existing project website**: copy the "Status" table and
   "Known limitations" section above into the site whenever they change, and
   link back here for full detail.

Either way, update this file first — it's the source of truth — then sync
the public page from it.
