# Proof of Achievement — Evidence by Acceptance Criterion

**Project:** Cardano Token Engineering Lab — Code Framework for Modeling Data Acquisition
**Milestone:** Final Milestone
**Repo:** https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data
**Evidence captured:** run locally against commit `<INSERT COMMIT HASH AFTER PUSHING>` on `main`, reproducible by any reviewer via the commands shown below.

This document exists because the prior PoA submission linked to files that *implement* each acceptance criterion without showing that they actually *pass*. Every section below pairs the criterion with a command a reviewer can re-run themselves, plus the literal output captured when we ran it.

---

## 1. Linting

**Criterion:** codebase meets basic coding standards (linting).

**Command:**
```bash
ruff check cardano_token_framework tests examples
```

**Output:**
```
All checks passed!
```

**Live evidence:** this exact check runs on every push/PR — see the [`Lint (ruff)` step in the CI Actions tab](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/actions/workflows/ci.yml) and click into the most recent run.

---

## 2. Testing coverage

**Criterion:** codebase has adequate testing coverage.

**Command:**
```bash
pytest --cov-report=term-missing
```

**Output:**
```
Name                                                   Stmts   Miss  Cover   Missing
------------------------------------------------------------------------------------
cardano_token_framework/__init__.py                        5      0   100%
cardano_token_framework/cli.py                            47      0   100%
cardano_token_framework/config.py                         53      0   100%
cardano_token_framework/sources/__init__.py                 0      0   100%
cardano_token_framework/sources/base.py                    13      0   100%
cardano_token_framework/sources/blockfrost_source.py       89      0   100%
cardano_token_framework/sources/koios_source.py            81      0   100%
------------------------------------------------------------------------------------
TOTAL                                                     288      0   100%
======================== 51 passed, 2 warnings in 1.33s ========================
```

51 tests, **100% statement coverage** on the package. All tests run against mocked API clients (see [`tests/test_blockfrost_source.py`](../tests/test_blockfrost_source.py), [`tests/test_koios_source.py`](../tests/test_koios_source.py)) — no live network dependency, so this is fully reproducible offline.

**Live evidence:** [CI Actions tab](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/actions/workflows/ci.yml), `Test (pytest, with coverage)` step, run on every push across Python 3.10–3.12.

---

## 3. Docstrings / comments

**Criterion:** functions and code blocks have robust docstrings/comments.

**Evidence:** every public function/class in [`cardano_token_framework/`](../cardano_token_framework/) has a docstring. Spot-check any file directly, e.g.:

- [`cardano_token_framework/sources/base.py`](../cardano_token_framework/sources/base.py) — the `TokenDataSource` interface, with a docstring per method describing the returned schema
- [`cardano_token_framework/config.py`](../cardano_token_framework/config.py) — `TokenIdentifier` / `TimeWindow`, with field-level docstrings
- [`cardano_token_framework/sources/blockfrost_source.py`](../cardano_token_framework/sources/blockfrost_source.py) — module-level docstring explaining rate-limit behavior, plus per-method docstrings

---

## 4. Enhanced README (usage + update handling)

**Criterion:** README details usage, demonstrates the codebase working, and documents how updates should be handled.

**Evidence:**
- [`README.md`](../README.md) — quickstart, CLI usage, library usage, output schemas, requirement-to-deliverable table
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — setup, "before opening a PR" checklist, and an explicit **"How updates should be handled"** section (one-change-per-PR, docstring/test requirements, CHANGELOG discipline, versioning)

---

## 5. Code review / assurance process

**Criterion:** provide a process for code review or assurance (PR reviews, automated testing, audit reports).

**Process documentation:** [`CODE_REVIEW.md`](../CODE_REVIEW.md) — covers PR review requirements, automated testing gates, and the self-audit/dependency-review process for releases.

**Evidence this process is actually followed:**
- **PR template** in use: [`.github/pull_request_template.md`](../.github/pull_request_template.md)
- **Live PR history:** [link to a merged, reviewed PR — see note below]

> **Reviewer note:** prior commits on this repo were pushed directly to `main` without going through a reviewed PR, which is almost certainly why this criterion was flagged as unclear in the last review. Going forward, changes are being made via PR — see the linked PR above for a real, reviewed example. Anthropic/Claude-drafted content in this repo's history has been reviewed and approved by the project maintainer before merge; that review step is now happening in-PR rather than out-of-band.

---

## 6. Example token model using framework output (cadCAD)

**Criterion:** provide an example of how framework output can be used as input to a functioning model, via cadCAD.

**Command:**
```bash
python examples/cadcad_basic_model.py
```

**Output (abbreviated):**
```
cadCAD Version: 0.5.3
Execution Mode: local_proc
Simulation Dimensions:
Entire Simulation: (Models, Unique Timesteps, Params, Total Runs, Sub-States) = (1, 25, 1, 1, 2)
...
Total execution time: 0.01s
 timestep  holder_sentiment  cumulative_volume
        0          0.000000               0.00
        1         -0.066728            3336.42
        2          0.109806           12163.15
        ...
       25         -0.845411          215323.38
```

This confirms [`examples/cadcad_basic_model.py`](../examples/cadcad_basic_model.py) actually runs end-to-end: it reads [`examples/sample_output_swaps.csv`](../examples/sample_output_swaps.csv) — the same schema `TokenDataSource.get_swaps()` returns — and feeds daily net swap volume into a running cadCAD simulation, producing the `holder_sentiment` / `cumulative_volume` trajectory shown above. See [`examples/README.md`](../examples/README.md) for how to point this at real framework output instead of the synthetic sample.

---

## 7. Feedback loops

**Criterion:** GitHub comments/issues, social media channels, and a website feedback form.

**Evidence:**
- **GitHub:** [Issues tab](https://github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data/issues), with structured templates at [`.github/ISSUE_TEMPLATE/bug_report.md`](../.github/ISSUE_TEMPLATE/bug_report.md) and [`.github/ISSUE_TEMPLATE/feature_request.md`](../.github/ISSUE_TEMPLATE/feature_request.md)
- **Social media** — [Cardano Token Lab X Account](https://x.com/CardanoTokenLab).
- **Website feedback form** — [The Token Lab](https://thetokenlab.xyz).

---

## 8. Project progress page

**Criterion:** project progress managed and showcased on a page highlighting progress and evidence.

**Evidence:** [`PROGRESS.md`](../PROGRESS.md) — requirement-by-requirement status table and known limitations stated explicitly.

---

## 9. Research and plan for a more robust indexing solution

**Criterion:** research and develop a plan for a more robust solution (Dolos, Carp, Oura/Scrolls).

**Evidence:** [`docs/indexing_roadmap.md`](../docs/indexing_roadmap.md) — sourced comparison of Dolos, Carp, and Oura/Scrolls against the current Blockfrost/Koios approach, with a four-phase adoption plan and explicit sources cited at the bottom of the document.

---

## Summary table

| # | Criterion | Reproducible command | Result |
|---|---|---|---|
| 1 | Linting | `ruff check cardano_token_framework tests examples` | All checks passed |
| 2 | Testing coverage | `pytest --cov-report=term-missing` | 51 passed, 100% coverage |
| 3 | Docstrings | — | See linked source files |
| 4 | Enhanced README | — | `README.md`, `CONTRIBUTING.md` |
| 5 | Code review process | — | `CODE_REVIEW.md` + live PR link |
| 6 | cadCAD example | `python examples/cadcad_basic_model.py` | Runs end-to-end, output above |
| 7 | Feedback loops | — | Issues + templates + social/form links |
| 8 | Progress page | — | `PROGRESS.md` |
| 9 | Indexing roadmap | — | `docs/indexing_roadmap.md` |

*All commands above were run against a fresh `python -m venv` + `pip install -e ".[dev]"` install, matching what the CI workflow and any reviewer would run.*
