# Legacy Scripts

The scripts in `Blockfrost/` and `Koios/` are the original exploratory, token-specific
prototypes used to validate that Blockfrost and Koios could supply the on-chain data
needed for token modeling (developed against the Liqwid LQ token).

They are kept here for historical reference only and are **not** part of the
supported framework. They are not parameterized (policy ID / asset name are
hardcoded), are not covered by tests, and contain at least two known bugs:

- `Blockfrost/token_tx.py` references `df_tx_data` before it is assigned (writes
  the CSV using the wrong variable name inside `get_asset_tx`).
- `Koios/address_info.py` builds a dict comprehension with duplicate keys and
  references an undefined `address_info` variable.

All functionality here has been superseded by the parameterized, tested package in
`cardano_token_framework/`. See the top-level `README.md` for current usage.
