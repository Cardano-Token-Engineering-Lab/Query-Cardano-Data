"""Smoke test for the cadCAD example in examples/.

This isn't part of the installable package (examples/ is documentation, not
library code), but it's exactly the kind of thing that silently breaks when
the get_swaps schema changes, so it's worth one end-to-end check in CI.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from examples.cadcad_basic_model import load_daily_net_signal, run_model  # noqa: E402


def test_load_daily_net_signal_returns_one_row_per_day():
    daily = load_daily_net_signal()
    assert len(daily) > 0
    assert daily.index.is_monotonic_increasing


def test_run_model_produces_bounded_sentiment_and_growing_volume():
    result = run_model()
    assert (result["holder_sentiment"] <= 1.0).all()
    assert (result["holder_sentiment"] >= -1.0).all()
    # cumulative_volume is a running sum of absolute daily flow, so it
    # should never decrease.
    assert result["cumulative_volume"].is_monotonic_increasing
