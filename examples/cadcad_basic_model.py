"""A minimal cadCAD model that consumes ``cardano_token_framework`` output.

This demonstrates the "feed framework output into a systems model" milestone
requirement end-to-end, using ``examples/sample_output_swaps.csv`` (the kind
of DataFrame ``TokenDataSource.get_swaps`` returns) as an exogenous input
signal.

Toy model story: each simulation day, observed swap volume from the real
(or sample) data nudges two state variables:

- ``holder_sentiment``: a bounded [-1, 1] score that drifts toward +1 on
  buy-heavy days and -1 on sell-heavy days. This is a deliberately simple
  stand-in for "is the market net-accumulating or net-distributing the
  token" — a typical first signal token-design researchers want out of a
  systems model.
- ``cumulative_volume``: running total of swap quantity, just to show a
  second, independent state variable evolving off the same input.

This is intentionally small. It is meant as a wiring demo — "here is how
framework output reaches a cadCAD ``state_update_block``" — not a
validated economic model of Liqwid, Indigo, or Minswap.

Run directly:

    python examples/cadcad_basic_model.py

Or import ``run_model()`` from a notebook.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from cadCAD.configuration import Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import ExecutionContext, ExecutionMode, Executor

SAMPLE_CSV = Path(__file__).parent / "sample_output_swaps.csv"


def load_daily_net_signal(csv_path: Path = SAMPLE_CSV) -> pd.Series:
    """Turn raw swap rows into a per-day net signal the model can consume.

    Real usage: replace ``csv_path`` with the output of
    ``BlockfrostSource.get_swaps(...)`` (or ``KoiosSource``), written to CSV
    via the CLI's ``--output`` flag, or passed in-memory if you're scripting
    against the framework directly instead of via the CLI.

    Returns a Series indexed by calendar day with values = (buy volume -
    sell volume) for that day, in decimal-adjusted token units. Positive
    values mean net buying pressure that day, negative means net selling.
    """
    df = pd.read_csv(csv_path, parse_dates=["block_time"])
    df["day"] = df["block_time"].dt.floor("D")
    df["signed_quantity"] = df["quantity"] * df["direction"].map({"buy": 1, "sell": -1})
    daily = df.groupby("day")["signed_quantity"].sum().sort_index()
    return daily


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def make_partial_state_update_blocks(daily_signal: pd.Series) -> list[dict]:
    """Build the cadCAD policy/state-update wiring for this model.

    ``daily_signal`` is captured by closure so the policy function can look
    up "today's" framework-derived signal by timestep, which is the seam
    between framework output and cadCAD's simulation loop.
    """
    days = list(daily_signal.index)

    def p_observe_framework_signal(params, substep, state_history, previous_state):
        """Policy: read this timestep's swap signal from framework output."""
        t = previous_state["timestep"]
        # If we run out of observed data, assume a quiet (zero-flow) day.
        net_volume = float(daily_signal.iloc[t]) if t < len(days) else 0.0
        return {"observed_net_volume": net_volume}

    def s_update_sentiment(params, substep, state_history, previous_state, policy_input):
        net_volume = policy_input["observed_net_volume"]
        # Normalize by a scale parameter so sentiment moves in [-1, 1] steps
        # proportional to, but bounded by, how large the day's net flow was.
        delta = net_volume / params["sentiment_scale"]
        new_sentiment = _clip(previous_state["holder_sentiment"] + delta, -1.0, 1.0)
        return ("holder_sentiment", new_sentiment)

    def s_update_cumulative_volume(params, substep, state_history, previous_state, policy_input):
        new_total = previous_state["cumulative_volume"] + abs(policy_input["observed_net_volume"])
        return ("cumulative_volume", new_total)

    return [
        {
            "policies": {"observe": p_observe_framework_signal},
            "variables": {
                "holder_sentiment": s_update_sentiment,
                "cumulative_volume": s_update_cumulative_volume,
            },
        }
    ]


def run_model(csv_path: Path = SAMPLE_CSV) -> pd.DataFrame:
    """Run the demo simulation and return the resulting cadCAD trajectory."""
    daily_signal = load_daily_net_signal(csv_path)

    genesis_state = {"holder_sentiment": 0.0, "cumulative_volume": 0.0}
    params = {"sentiment_scale": [50_000]}  # token units of net flow to move sentiment by 1.0

    sim_config = config_sim(
        {
            "N": 1,  # one Monte Carlo run; this model has no randomness
            "T": range(len(daily_signal)),
            "M": params,
        }
    )

    # Each call builds a fresh Experiment, so its `.configs` list contains
    # exactly the one model appended below — no shared global state to reset
    # between repeated calls (e.g. re-running this from a notebook).
    experiment = Experiment()
    experiment.append_configs(
        sim_configs=sim_config,
        initial_state=genesis_state,
        partial_state_update_blocks=make_partial_state_update_blocks(daily_signal),
    )

    exec_context = ExecutionContext(ExecutionMode().local_mode)
    executor = Executor(exec_context=exec_context, configs=experiment.configs)
    raw_result, _tensor_field, _sessions = executor.execute()

    return pd.DataFrame(raw_result)


if __name__ == "__main__":
    result_df = run_model()
    # cumulative_volume only accumulates (it's a running total), so the
    # per-timestep change in it is exactly that day's swap volume — useful
    # to see alongside the cumulative figure without re-deriving it by hand.
    result_df["delta_volume"] = result_df["cumulative_volume"].diff().fillna(
        result_df["cumulative_volume"]
    )
    print(
        result_df[
            ["timestep", "holder_sentiment", "cumulative_volume", "delta_volume"]
        ].to_string(index=False)
    )
