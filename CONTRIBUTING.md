# Contributing

## Setup

```bash
git clone https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data.git
cd Query-Cardano-Data
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env               # then fill in BLOCKFROST_API_TOKEN
```

## Before opening a pull request

```bash
ruff check cardano_token_framework tests examples   # lint
pytest --cov-report=term-missing            # tests + coverage
```

Both run automatically in CI on every PR (see `.github/workflows/ci.yml`), but
running them locally first saves a review round-trip.

## Project layout

```
cardano_token_framework/
  config.py            # TokenIdentifier, TimeWindow, env loading
  sources/
    base.py             # TokenDataSource abstract interface
    blockfrost_source.py
    koios_source.py
  cli.py                # python -m cardano_token_framework ...
tests/                  # mirrors the package layout above
examples/                # sample input/output + the cadCAD demo model
docs/                    # indexing roadmap and other design docs
legacy/                  # superseded prototype scripts, kept for reference
```

## How updates should be handled

1. **One logical change per PR.** Framework changes, new data sources, and
   model/example changes should be separate PRs where practical — it keeps
   review focused and the changelog meaningful.
2. **Every new public function gets a docstring** (Google-style, matching the
   existing modules) and at least one test. If you're fixing a bug, add a
   regression test that fails without your fix.
3. **If you touch `TokenDataSource`** (the abstract interface in
   `sources/base.py`), update *both* `BlockfrostSource` and `KoiosSource` to
   match, and update `docs/indexing_roadmap.md` if it changes what a future
   backend (Dolos/Carp/Oura+Scrolls) would need to implement.
4. **Update the README** if you change CLI flags, add a command, or change
   output schema — the README's usage examples should always be runnable
   as-written against the current code.
5. **Record the change in `CHANGELOG.md`** under "Unreleased" (Keep a
   Changelog format). This is what `PROGRESS.md` and the public project page
   get updated from.
6. **Tag a release** (and update `__version__` in
   `cardano_token_framework/__init__.py`) only from `main`, after CI is green.

## Code review

See `CODE_REVIEW.md` for the review/approval process and what reviewers check.

## Reporting bugs / requesting features

Use the GitHub issue templates (`.github/ISSUE_TEMPLATE/`). For broader
direction-setting feedback (which protocols to support next, which modeling
use case to prioritize), also see the feedback channels listed in the
top-level README.
