# Code Review & Quality Assurance Process

This is the evidence-of-completion process referenced in Milestone 2: how
changes to this repository are reviewed, tested, and (periodically) audited.

## 1. Pull Request Reviews

- All changes land via pull request — no direct pushes to `main`.
- Every PR uses the template at `.github/pull_request_template.md`, which
  requires the author to confirm lint/tests pass locally and to describe how
  the change was tested.
- At least one maintainer reviews and approves before merge. Reviewers check:
  - Does the change match the `TokenDataSource` interface contract (if it
    touches a data source)?
  - Are new/changed functions documented with docstrings?
  - Is there test coverage for the new behavior, including at least one
    failure-path test (bad input, empty API response, etc.)?
  - Does the README/docs update match the code change?
- Small, low-risk PRs (typo fixes, doc-only changes) may be merged with a
  single approval; anything touching `sources/` or `cli.py` gets a second
  look from whoever knows that backend best.

## 2. Automated Testing Results

- `.github/workflows/ci.yml` runs on every push and PR, across Python
  3.10–3.12:
  - `ruff check` — linting (style, unused imports, common bug patterns)
  - `pytest --cov-report=xml --cov-report=term-missing` — full test suite
    with coverage reported in the PR's checks tab and uploaded as a build
    artifact
- CI must be green before merge. The coverage report is not currently gated
  at a hard threshold, but a PR that visibly *drops* coverage on touched
  files is flagged in review.
- All API-dependent tests (Blockfrost, Koios) run against mocked clients
  (see `tests/test_blockfrost_source.py`, `tests/test_koios_source.py`) so CI
  results are deterministic and don't depend on third-party API uptime or
  rate limits.

## 3. Code Audits

- This is a small, community research-tooling repo, not a smart contract or
  funds-custody system, so it does not currently warrant a paid third-party
  security audit. The bar instead is:
  - **Self-audit on every release**: before tagging a version, a maintainer
    re-reads the diff since the last tag end-to-end (not just the most
    recent PRs in isolation) and re-runs lint + full test suite locally.
  - **Dependency review**: `pip list --outdated` is checked before each
    release; security advisories for `blockfrost-python`, `koios-api`,
    `pandas`, and `requests` are reviewed via GitHub's Dependabot alerts
    (enabled on this repo).
  - If/when this framework grows into something that handles funds or feeds
    decisions with financial consequences (e.g. is wired directly into an
    automated trading or treasury system), a third-party audit should be
    commissioned before that integration ships — flagged here so it isn't
    forgotten.

## Severity triage for bug reports

| Severity | Example | Response |
|---|---|---|
| Critical | Silent data corruption (e.g. wrong swap direction/quantity) | Fix + regression test merged ASAP; note in CHANGELOG under a "Fixed" entry with explicit description |
| High | A backend method throws on valid input | Fix within the current milestone cycle |
| Medium | Missing edge-case handling, confusing error message | Triaged into backlog, addressed opportunistically |
| Low | Style, docs typos, minor DX improvements | "Good first issue" candidates |
