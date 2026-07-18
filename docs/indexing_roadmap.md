# Indexing Roadmap: Beyond Blockfrost/Koios

Milestone 2 asks for research and a plan toward a more robust solution than
hosted REST APIs — specifically calling out **Dolos** (TxPipe), and a
custom indexing solution via **Carp** (dcSpark) or **Oura/Scrolls** (TxPipe).
This document compares those options against the current Blockfrost/Koios
approach and lays out a phased plan for adopting one.

## 1. Why look beyond Blockfrost/Koios at all?

The current framework (`cardano_token_framework/sources/`) is intentionally
built against hosted REST APIs because that's the fastest path to a working,
parameterized tool — no infrastructure to run, which matched this
milestone's "basic" framing. The tradeoffs that motivate this roadmap:

- **Rate limits.** `get_swaps` makes one extra API call per candidate
  transaction; on Blockfrost's free tier this caps how large a time window
  or how high-volume a token can be analyzed in practice.
- **No control over data freshness or retention.** We depend on the
  provider's indexing cadence and uptime.
- **Heuristic swap detection.** Because we only see UTXO-level
  inputs/outputs (not parsed datums/redeemers), `get_swaps` infers direction
  from net asset flow rather than truly decoding the DEX's swap request.
  Getting this right generally requires either a node-level CBOR
  view (Dolos/dbsync) or a custom indexer with DEX-specific decoding logic
  (Carp/Scrolls), not just a REST wrapper.

## 2. The options

### 2.1 Dolos (TxPipe)

Dolos is a lightweight, Rust-based "data node" — a third category alongside
the traditional block-producer and relay node roles. It connects directly to
the Cardano network over the Ouroboros node-to-node protocol (via Pallas),
following honest upstream peers rather than doing full consensus
validation, which is what lets it run on a small fraction of the resources a
full node needs. It exposes the ledger over multiple protocols (gRPC, REST,
JSON-RPC, Ouroboros) and supports pluggable storage (ledger-only, sliding
window, or full archive).

**Why it matters here:** Dolos is the closest thing to "run dbsync but
lighter" — it's explicitly listed by its own team as something other tools
(dbsync, Ogmios, Carp, Oura) can sit on top of as a data source. For us, it
would mean a self-hosted, low-resource alternative to Blockfrost with no
third-party rate limit, while still giving direct access to UTXO/ledger
state our `TokenDataSource` interface needs.

**Tradeoffs:** it's a node-adjacent piece of infrastructure — there's a
sync time, a storage footprint, and ops overhead (even if small relative to
a full node) that a hosted API doesn't have.

### 2.2 Carp (dcSpark)

Carp is a modular Cardano indexer that syncs chain data into a Postgres
database, positioned as an alternative to `cardano-db-sync`. Its backend is
Rust (built on Oura and the Cardano Multiplatform Library), with a
TypeScript server/client layer. The key design difference from db-sync is
modularity: Carp lets you enable only the indexing "tasks" you actually
need (e.g., just asset mints/burns and UTXO movements, skipping pool
metadata, governance, etc.), which keeps sync time and storage down. It
stores data closer to raw CBOR rather than db-sync's fully-normalized SQL
schema, on the assumption that consumers can parse Cardano binary data
themselves.

**Why it matters here:** a Carp task could be written specifically to
decode DEX swap transactions (Minswap, and others) at the datum/redeemer
level — replacing our net-asset-flow heuristic with an actual decode of
what the trade was. That's the most direct path to fixing the
known-limitation flagged in `PROGRESS.md`.

**Tradeoffs:** initial full sync takes multiple days per Carp's own
documentation, and it requires running and maintaining a Postgres instance.
Carp's task system is the main thing to learn here — most of the value over
a from-scratch indexer is in that existing scaffolding.

### 2.3 Oura + Scrolls (TxPipe)

Oura and Scrolls solve different problems and are often used together:

- **Oura** is a real-time event pipeline: it watches the tip of the chain
  and emits granular events through configurable filter/sink stages — built
  for *reacting* to on-chain patterns (e.g., "alert when this policy ID
  appears in a transaction") rather than for querying history.
- **Scrolls** builds and maintains read-optimized, map-reduce-style
  "collections" (e.g., UTXOs by address, pool metadata by pool ID) by
  crawling the full chain history and then staying caught up at the tip. A
  newer Scrolls effort (still maturing) adds a plugin system so custom
  Map/Reduce logic can be written without forking Scrolls itself, with
  results exposed over an auto-generated GraphQL API.

**Why it matters here:** Oura is the better fit if a future version of this
framework wants a live feed (e.g., "stream new swaps as they happen" rather
than "pull swaps for a historical window"). Scrolls is the better fit for
exactly the kind of derived, query-friendly collection our `get_swaps`
already approximates — a "swaps by policy ID" collection would map directly
onto our existing schema.

**Tradeoffs:** the plugin-based Scrolls work is explicitly flagged by
TxPipe as early/under heavy development, with the API and storage schema
still subject to change — a real near-term adoption risk to track, not
just a footnote.

### 2.4 Comparison at a glance

| | Blockfrost / Koios (current) | Dolos | Carp | Oura + Scrolls |
|---|---|---|---|---|
| Hosting | Third-party (or self-host via RYO/gREST) | Self-hosted, lightweight | Self-hosted, Postgres | Self-hosted |
| Query model | REST, paginated | gRPC/REST/JSON-RPC/Ouroboros | SQL (Postgres) | Event stream (Oura) / KV lookups (Scrolls) |
| True swap decoding | No (heuristic only) | Possible (raw ledger access) | Yes, with a custom task | Yes, with a custom reducer |
| Ops burden | None | Low–medium | Medium (Postgres + multi-day initial sync) | Medium (two services) |
| Best fit for us | Fast historical pulls, current default | Self-hosted REST/gRPC replacement | Custom swap-decoding logic | Live/streaming swap feed |

## 3. Recommended path

This is intentionally staged so each phase delivers value on its own rather
than requiring a single large rewrite:

**Phase 1 (this milestone): done.** Blockfrost/Koios behind the
`TokenDataSource` interface, with the heuristic swap classifier and full
test coverage. This phase's job was to prove the interface and the basic
"policy ID + time window → DataFrame" shape works.

**Phase 2 (next): self-hosted option via Dolos.** Add a `DolosSource`
implementing the same `TokenDataSource` interface, talking to a local Dolos
instance over its gRPC/REST API instead of a third-party host. This removes
the rate-limit ceiling on `get_swaps` and is the lowest-effort step because
it's a drop-in implementation of an interface we already have — no schema
or architecture change needed downstream.

**Phase 3: real swap decoding via a Carp task.** Write a Carp task that
decodes known DEX swap-request/batching contracts (starting with Minswap,
since we already have its swap-batcher address) at the datum/redeemer
level, replacing the net-asset-flow heuristic in `get_swaps` with ground
truth. This directly resolves the swap-classification limitation called out
in `PROGRESS.md`, and would let `get_swaps` report real swap amounts (in
and out) instead of net token flow only.

**Phase 4 (stretch, matches the milestone's own stretch goal): p2p and
staking events.** Once a custom indexer (Carp or Scrolls) is in place, add
reducers/tasks for plain p2p transfers (asset moves between two non-DEX,
non-script addresses) and smart-contract interactions like staking deposits
— extending `TokenDataSource` with `get_transfers` and
`get_contract_interactions` methods following the same pattern as
`get_swaps`.

**Where Oura fits:** independent of the phases above, Oura is the natural
choice *if and when* a live/streaming mode is wanted (e.g., feeding a
running cadCAD simulation or a dashboard in near-real-time instead of a
batch pull). It is not on the critical path for fixing swap-decoding
accuracy, so it's not scheduled into Phases 2–4, but it's worth tracking as
the source for a future `--watch` mode on the CLI.

## 4. What doesn't change

Whichever backend is added, it plugs into the existing
`cardano_token_framework.sources.base.TokenDataSource` interface (see
`CONTRIBUTING.md` §"Project layout"). The CLI, the cadCAD example in
`examples/cadcad_basic_model.py`, and any downstream analysis code are
written against that interface, not against Blockfrost/Koios directly —
that's the whole point of having it. Adding `DolosSource` or a
Carp-task-backed source should not require changing any of those
consumers.

## Sources

- TxPipe, Dolos (GitHub repo and docs): https://github.com/txpipe/dolos , https://docs.txpipe.io/dolos
- TxPipe, Dolos Catalyst Fund 9 proposal: https://projectcatalyst.io/funds/9/developer-ecosystem/dolos-cardano-data-node
- dcSpark, Carp (GitHub repo, docs, and "Carp vs alternatives"): https://github.com/dcSpark/carp , https://dcspark.github.io/carp/docs/intro/ , https://dcspark.github.io/carp/docs/comparison/
- dcSpark, "Carp — New Cardano SQL indexer & replacement for db-sync" (Medium): https://medium.com/dcspark/carp-new-cardano-sql-indexer-replacement-for-db-sync-b990243a329e
- TxPipe, Oura (GitHub repo and docs): https://github.com/txpipe/oura , https://docs.txpipe.io/oura/v3
- TxPipe, Scrolls (GitHub repo): https://github.com/txpipe/scrolls
- TxPipe, Scrolls custom-indexing RFC: https://rfcs.txpipe.io/0006-scrolls-custom-indexing
- TxPipe, Scrolls Catalyst Fund 10 proposal: https://projectcatalyst.io/funds/10/developer-ecosystem-the-evolution/scrolls-develop-and-deploy-custom-graphql-chain-indexes
