# Examples

| File | What it is |
|---|---|
| `sample_input.json` | An example of the framework's two required inputs (policy ID + asset name, and a time window), plus the DEX address(es) needed for `swaps`, shown both as a JSON description and as the equivalent CLI command. |
| `sample_output_swaps.csv` | **Synthetic** example output matching the exact schema `TokenDataSource.get_swaps` returns (`tx_hash`, `block_time`, `dex_address`, `direction`, `quantity`). Generated with a fixed random seed for illustration — it is not real historical Minswap trade data. |
| `cadcad_basic_model.py` | A minimal cadCAD model that reads `sample_output_swaps.csv` and uses daily net swap volume as an input signal to two toy state variables. Demonstrates the full path from framework output to a running systems model. |

## Running the cadCAD example

```bash
pip install -e ".[dev]"   # installs cadCAD along with everything else
python examples/cadcad_basic_model.py
```

This prints the simulation trajectory (`timestep`, `holder_sentiment`,
`cumulative_volume`) to stdout. To use it with real data instead of the
synthetic sample:

```bash
python -m cardano_token_framework \
  --policy-id <policy_id> --asset-name <asset_name> \
  --output my_swaps.csv \
  swaps --dex-address <dex_address> --start 2024-01-01 --end 2024-02-01
```

```python
from examples.cadcad_basic_model import run_model
result = run_model(csv_path="my_swaps.csv")
```

## Regenerating the sample CSV

`sample_output_swaps.csv` was generated with:

```python
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
# ... see git history of this file / ask in an issue if you need the exact script
```

If you change the schema of `get_swaps`, regenerate this file so the example
stays in sync — see `CONTRIBUTING.md`.
