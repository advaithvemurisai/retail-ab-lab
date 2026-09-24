import numpy as np
import pandas as pd

from retaillab.decision import decide
from retaillab.demo import demo_email
from retaillab.estimate import benjamini_hochberg, proportion_effect
from retaillab.finance import attributed_incremental, break_even_lift, greedy_allocation
from retaillab.variance import cuped


def test_demo_reproducible_and_schema():
    assert demo_email(100, 7).equals(demo_email(100, 7))
    assert {"unit_id", "arm", "conversion", "revenue", "pre_spend", "segment"}.issubset(
            demo_email().columns
    )


def test_estimator_and_bh():
    data = pd.DataFrame(
        {"arm": ["control"] * 4 + ["treatment"] * 4, "conversion": [0, 0, 1, 0, 1, 1, 1, 0]}
    )
    assert np.isclose(proportion_effect(data)["p_value"], 0.1572992070502805)
    assert benjamini_hochberg([0.01, 0.04, 0.5])["reject"] == [True, False, False]


def test_finance_and_allocation():
    assert break_even_lift(0.2, 1, 0.4) == 0.5
    result = attributed_incremental(demo_email(1000))
    assert result["attributed"] >= result["incremental"]
    rows = pd.DataFrame({"audience": [10, 10], "profit_per_dollar": [2, -1]})
    assert greedy_allocation(rows, 10).send_count.sum() == 10


def test_cuped_and_decision_branches():
    data = demo_email(1000)
    result = cuped(data)
    assert result["variance_reduction"] >= 0
    assert (
        decide(
            validity_failed=True,
            primary_lift=1,
            primary_p=0,
            contribution_low=1,
            contribution_high=2,
        ).label
        == "DON'T TRUST"
    )
    assert (
        decide(
            validity_failed=False,
            primary_lift=0.2,
            primary_p=0.01,
            contribution_low=1,
            contribution_high=2,
            roi=1,
        ).label
        == "SHIP"
    )
    assert (
        decide(
            validity_failed=False,
            primary_lift=0,
            primary_p=0.9,
            contribution_low=1,
            contribution_high=2,
            power=0.9,
        ).label
        == "DON'T SHIP"
    )
