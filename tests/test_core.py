from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.power import NormalIndPower

from retaillab.analysis import Assumptions, analyze
from retaillab.data import COLUMNS, DESIGN, campaign_view, demo_email, load_hillstrom
from retaillab.decision import decide
from retaillab.estimate import (
    benjamini_hochberg,
    bootstrap_difference,
    pairwise_arms,
    proportion_effect,
    segment_effects,
    welch_effect,
)
from retaillab.finance import (
    attributed_incremental,
    benchmark_margins,
    break_even_lift,
    contribution_distribution,
    greedy_allocation,
    load_margins,
    pnl,
)
from retaillab.power import power_two_means, required_total_n
from retaillab.resampling import peeking_false_positive_rate
from retaillab.validity import srm
from retaillab.variance import cuped
from retaillab.warehouse import build_warehouse

RAW = Path(__file__).parents[1] / "data" / "raw"
DEMO = demo_email()


def test_demo_reproducible_and_schema():
    assert demo_email(500, 7).equals(demo_email(500, 7))
    assert list(DEMO.columns) == COLUMNS
    assert set(DEMO.arm) == set(DESIGN)


def test_load_hillstrom_maps_three_arms(tmp_path):
    path = tmp_path / "hillstrom.csv"
    pd.DataFrame(
        {
            "recency": [1, 2, 3], "history_segment": ["1) $0 - $100"] * 3,
            "history": [10.0, 20.0, 30.0], "mens": [1, 0, 1], "womens": [0, 1, 1],
            "zip_code": ["Urban"] * 3, "newbie": [0, 1, 0], "channel": ["Web"] * 3,
            "segment": ["No E-Mail", "Mens E-Mail", "Womens E-Mail"],
            "visit": [0, 1, 1], "conversion": [0, 0, 1], "spend": [0.0, 0.0, 50.0],
        }
    ).to_csv(path, index=False)
    frame = load_hillstrom(path)
    assert list(frame.arm) == ["control", "mens", "womens"]
    assert list(frame.columns) == COLUMNS
    assert frame.revenue.tolist() == [0.0, 0.0, 50.0]


def test_campaign_view_pools_or_selects():
    pooled = campaign_view(DEMO, "any")
    assert len(pooled) == len(DEMO)
    assert set(pooled.arm) == {"control", "treatment"}
    assert len(campaign_view(DEMO, "mens")) == (DEMO.arm != "womens").sum()
    with pytest.raises(ValueError):
        campaign_view(DEMO, "sms")


def test_srm_uses_the_designed_split():
    # Pooling two e-mail arms gives a 1:2 split by design. That must pass the design check
    # and fail a naive 50/50 check (the original bug).
    frame = pd.DataFrame({"arm": ["control"] * 1000 + ["mens"] * 1000 + ["womens"] * 1000})
    assert not srm(frame, DESIGN)["failed"]
    pooled = campaign_view(frame.assign(unit_id=0), "any")
    assert srm(pooled, {"control": 0.5, "treatment": 0.5})["failed"]
    assert not srm(pooled, {"control": 1 / 3, "treatment": 2 / 3})["failed"]


def test_estimators():
    data = pd.DataFrame(
        {"arm": ["control"] * 4 + ["treatment"] * 4, "conversion": [0, 0, 1, 0, 1, 1, 1, 0]}
    )
    result = proportion_effect(data)
    assert np.isclose(result["p_value"], 0.1572992070502805)
    assert result["lift_ci_low"] < result["relative_lift"] < result["lift_ci_high"]
    view = campaign_view(DEMO, "mens")
    effect = welch_effect(view)
    assert effect["ci_low"] < effect["difference"] < effect["ci_high"]
    draws = bootstrap_difference(view, draws=300)
    assert len(draws) == 300
    assert abs(draws.mean() - effect["difference"]) < effect["se"]


def test_benjamini_hochberg():
    assert benjamini_hochberg([0.01, 0.04, 0.5])["reject"] == [True, False, False]
    assert np.allclose(benjamini_hochberg([0.01, 0.02, 0.03])["adjusted_p_values"], 0.03)
    assert benjamini_hochberg([]) == {"adjusted_p_values": [], "reject": []}


def test_pairwise_and_segments_are_corrected():
    pairs = pairwise_arms(DEMO, list(DESIGN))
    assert len(pairs) == 3
    assert (pairs.p_adjusted >= pairs.p_value).all()
    segments = segment_effects(campaign_view(DEMO), "channel")
    assert set(segments.segment) == {"Web", "Phone", "Multichannel"}
    assert {"p_adjusted", "significant"}.issubset(segments.columns)


def test_finance():
    assert break_even_lift(0.2, 1, 0.4) == 0.5
    assert break_even_lift(0.2, 0, 0.4) == np.inf
    economics = pnl(campaign_view(DEMO), 0.5, 0.1)
    assert np.isclose(
        economics["contribution"], economics["gross_profit"] - economics["marketing_cost"]
    )
    result = attributed_incremental(campaign_view(DEMO))
    assert result["attributed"] >= result["incremental"]
    assert np.isclose(result["baseline"] + result["incremental"], result["attributed"])


def test_contribution_interval_scales_to_the_campaign():
    # Regression: the per-customer interval was once compared to whole-campaign cost.
    draws = np.full(100, 0.5)
    result = contribution_distribution(draws, 1000, 0.4, 0.1)
    assert np.isclose(result["ci_low"], 100) and np.isclose(result["ci_high"], 100)
    assert result["chance_of_loss"] == 0


def test_greedy_allocation():
    rows = pd.DataFrame(
        {"audience": [10, 10, 10], "profit_per_dollar": [2, 1, -1],
         "significant": [False, True, True]}
    )
    assert greedy_allocation(rows, 15).send_count.tolist() == [10, 5, 0]
    assert greedy_allocation(rows, 100).send_count.sum() == 20
    assert greedy_allocation(rows, 100, require_significant=True).send_count.sum() == 10


def test_placeholder_margins_are_labelled():
    margins = load_margins(force_demo=True)
    assert margins["source"] == "placeholder"
    assert set(margins["margins"]) == {"Apparel", "Retail (Grocery and Food)", "Restaurant/Dining"}


@pytest.mark.skipif(not (RAW / "margin.xls").exists(), reason="Damodaran workbook not downloaded")
def test_damodaran_workbook():
    margins = benchmark_margins(RAW / "margin.xls")
    assert margins["as_of"] != "undated"
    assert all(0 < row["gross_margin"] < 1 for row in margins["margins"].values())


def test_cuped_reduction_matches_correlation():
    rng = np.random.default_rng(0)
    x = rng.normal(size=20_000)
    frame = pd.DataFrame(
        {"arm": rng.choice(["control", "treatment"], 20_000), "pre_spend": x,
         "revenue": 0.6 * x + 0.8 * rng.normal(size=20_000)}
    )
    adjusted, stats = cuped(frame)
    assert abs(stats["variance_reduction"] - stats["correlation"] ** 2) < 0.01
    assert adjusted.revenue_cuped.var() < frame.revenue.var()


def test_power_matches_statsmodels():
    ours = power_two_means(0.1, 1, 1, 1000, 1000)
    reference = NormalIndPower().power(0.1, 1000, 0.05, ratio=1)
    assert abs(ours - reference) < 0.01
    n = required_total_n(0.1, 1, 0.5)
    assert abs(power_two_means(0.1, 1, 1, n // 2, n // 2) - 0.8) < 0.01
    assert required_total_n(0.1, 1, 2 / 3) > n


def test_peeking_inflates_false_positives():
    assert 0.035 < peeking_false_positive_rate(1, simulations=2000) < 0.065
    assert peeking_false_positive_rate(10, simulations=2000) > 0.15


def test_decision_branches():
    base = {"validity_failed": False, "contribution_low": 1, "contribution_high": 2}
    assert decide(**{**base, "validity_failed": True}, primary_lift=1, primary_p=0).label == (
        "DON'T TRUST"
    )
    assert decide(**base, primary_lift=-0.2, primary_p=0.01).label == "DON'T SHIP"
    assert decide(
        validity_failed=False, primary_lift=0.1, primary_p=0.5, contribution_low=-5,
        contribution_high=-1,
    ).label == "DON'T SHIP"
    assert decide(**base, primary_lift=0.2, primary_p=0.01, segment_harm=True).label == (
        "DON'T SHIP"
    )
    assert decide(**base, primary_lift=0.2, primary_p=0.01, roi=1).label == "SHIP"
    risky = decide(**base, primary_lift=0.2, primary_p=0.01, roi=0.3, chance_of_loss=0.2)
    assert risky.label == "SHIP" and "20% chance" in risky.reasons[-1]
    below_hurdle = decide(**base, primary_lift=0.2, primary_p=0.01, roi=0.1, minimum_roi=0.5)
    assert below_hurdle.label == "DON'T SHIP" and "misses" in below_hurdle.reasons[1]
    assert decide(**base, primary_lift=0, primary_p=0.9, power=0.9).label == "DON'T SHIP"
    waiting = decide(**base, primary_lift=0, primary_p=0.9, power=0.4, additional_weeks=3)
    assert waiting.label == "KEEP TESTING" and waiting.additional_weeks == 3


def test_analyze_demo_end_to_end():
    readout = analyze(DEMO, Assumptions(gross_margin=0.5))
    assert not readout.validity["failed"]
    assert readout.verdict.label == "SHIP"
    assert readout.contribution["ci_low"] < readout.economics["contribution"]
    assert readout.economics["contribution"] < readout.contribution["ci_high"]
    assert 0 < readout.power <= 1


def test_analyze_reacts_to_economics_and_broken_splits():
    expensive = analyze(DEMO, Assumptions(gross_margin=0.5, contact_cost=2.0))
    assert expensive.verdict.label == "DON'T SHIP"
    treated = DEMO.index[DEMO.arm != "control"]
    broken = DEMO.drop(index=treated[: len(treated) // 10])
    assert analyze(broken, Assumptions()).verdict.label == "DON'T TRUST"


def test_warehouse_pnl_matches_python():
    margins = load_margins(force_demo=True)
    connection = build_warehouse(":memory:", DEMO, margins, 0.18)
    sql = connection.execute(
        "SELECT contribution FROM mart_pnl WHERE arm = 'mens' AND sector = 'Apparel'"
    ).fetchone()[0]
    python = pnl(campaign_view(DEMO, "mens"), margins["margins"]["Apparel"]["gross_margin"], 0.18)
    assert np.isclose(sql, python["contribution"])


@pytest.mark.skipif(not (RAW / "hillstrom.csv").exists(), reason="Hillstrom not downloaded")
def test_hillstrom_readout_is_trusted():
    # Regression: a 50/50 SRM check flagged Hillstrom's 1:1:1 design as broken.
    readout = analyze(load_hillstrom(RAW / "hillstrom.csv"), Assumptions(gross_margin=0.5))
    assert not readout.validity["failed"]
    assert readout.verdict.label != "DON'T TRUST"
