# Project Completion Video — Script & Recording Outline

**Target length:** ~5 minutes (guideline, not a hard rule)
**Format:** 720p or 1080p, public YouTube or Vimeo link (no access restrictions), audio commentary in English
**Required elements (per Catalyst spec):** (1) which challenge you entered and why / what you proposed, (2) your progress and how you delivered, (3) challenges faced and how you overcame them, whether you stayed in scope, and whether you hit your milestones/KPIs, (4) implicitly — a live demo of the working solution

This script is written to hit all four in order, with clear "SHOW ON SCREEN" cues so you know what to have open before you hit record.

---

## 0. Before you record — have these open in browser tabs, in this order

1. This project's Catalyst page: `projectcatalyst.io/funds/11/.../cardano-token-engineering-lab-...` (ID #1100073)
2. `github.com/Cardano-Token-Engineering-Lab/Home`
3. `github.com/Cardano-Token-Engineering-Lab/Research` (or wherever the 3 papers ended up — confirm link first)
4. `github.com/Cardano-Token-Engineering-Lab/Query-Cardano-Data`
5. A terminal, in the `Query-Cardano-Data` repo, venv activated
6. The CI Actions tab for `Query-Cardano-Data`, showing a green run

---

## 1. Intro — Challenge & Why (≈45 sec)

**SHOW:** Catalyst project page (#1100073)

> "Hi, I'm Miguel Saldana, and this is the close-out video for the Cardano Token Engineering Lab project, funded through Project Catalyst Fund 11 under the Cardano Use Cases: Concept challenge.
>
> The problem this project set out to solve: Cardano DeFi projects, and the broader ecosystem, didn't have an easy, open way to understand token design patterns, or to pull on-chain token data for the kind of systems modeling that helps catch economic security risks before they become expensive problems. Other ecosystems — Ethereum in particular — have dedicated token engineering research groups. Cardano didn't really have one. That's what this project set out to bootstrap."

---

## 2. What we proposed & delivered (≈90 sec)

**SHOW:** Scroll the Catalyst page down to the milestones table (or narrate over it)

> "The project had three milestones. First, build a public research repository. Second, produce case studies on real Cardano DeFi protocols — specifically one lending protocol, one synthetic-asset protocol, and a third we'd select along the way. Third, build an open-source code framework so anyone could pull the on-chain data needed to actually model these protocols."

**SHOW:** switch to `Home` repo, then `Research` repo

> "Milestone one and two are complete. We published research on Liqwid — Cardano's largest lending protocol — Indigo Protocol, a synthetic-asset platform, and Minswap, Cardano's largest DEX. Each paper covers token design, incentive mechanisms, and — most importantly — economic security analysis: where the real financial risks in each protocol actually sit."

**SHOW:** open one paper PDF briefly, scroll through headings

> "Every paper follows the same structure — background, protocol mechanics, token utility, incentive design, economic security, and recommendations — and every claim is footnoted back to a numbered source list."

---

## 3. Live demo — the code framework (≈2 min)

**SHOW:** switch to `Query-Cardano-Data` repo README, then terminal

> "The final milestone was the code framework. This is `cardano_token_framework` — a Python package that pulls Cardano native-token data — asset info, holders, transaction history, and swap activity — into pandas DataFrames, ready to feed into a model. It works against either Blockfrost or Koios behind the same interface, so switching backends doesn't change your analysis code."

**SHOW:** run this live in the terminal:
```bash
python -m cardano_token_framework --policy-id da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24 --asset-name 4c51 info
```

> "That's a live pull of Liqwid's LQ token metadata straight from the chain."

**SHOW:** run the test suite live:
```bash
pytest --cov-report=term-missing
```

> "The framework has 51 tests and 100% statement coverage, and it's linted and CI-tested on every change — you can see that running in GitHub Actions here."

**SHOW:** switch to the CI Actions tab, show a green run

**SHOW:** run the cadCAD example:
```bash
python examples/cadcad_basic_model.py
```

> "And this is the part that ties it all together — a basic cadCAD systems model that consumes the framework's own swap data as an input signal. This is the actual point of the whole project: on-chain data going straight into a working model."

---

## 4. Challenges, scope, and what's next (≈60 sec)

> "A few honest notes on how this went. The swap-classification logic in the framework is a heuristic right now — it infers buy or sell direction from net token flow at a known DEX address, not a full decode of the transaction's datum and redeemer. That's a real limitation, and it's documented — along with a researched, phased plan for fixing it using more robust indexing infrastructure like Dolos, Carp, or Oura and Scrolls — in the repo's indexing roadmap.
>
> The stretch goal — classifying peer-to-peer transfers and staking interactions separately — didn't make it into this milestone either. It's scoped as future work rather than dropped.
>
> On the partnership side: the milestone called for formalizing a partnership with a Cardano DeFi protocol and an outside token engineering group. That hasn't closed yet. We've left placeholder agreements in the research repo so that work can continue and be tracked transparently once it does.
>
> Overall, we stayed within the original scope of the proposal — three milestones, delivered close to the original timeline, with the two research-heavy tracks fully complete and the code framework now shipped, tested, and documented."

---

## 5. Close (≈15 sec)

> "Everything here is open source under MIT and lives permanently on the Cardano Token Engineering Lab GitHub org — the research papers, the framework, and the roadmap for what comes next. Thanks for watching, and thanks to the Catalyst community for backing this."

---

## Post-recording checklist

- [ ] Upload to YouTube or Vimeo, **public**, no age-gate or unlisted-only restriction
- [ ] Confirm audio is clear and in English throughout
- [ ] Paste the final video URL into `Project_Completion_Report.docx` (the `[INSERT PUBLIC YOUTUBE OR VIMEO LINK]` placeholder) and into the final PoA submission field
- [ ] Re-watch once end-to-end before submitting — confirm all 4 required elements are clearly present
