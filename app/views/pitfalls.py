import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.ui.components import chart, header
from app.ui.context import load_data
from app.ui.theme import COLORS
from retaillab.data import DESIGN, SEGMENT_COLUMNS, campaign_view
from retaillab.estimate import segment_effects, welch_effect
from retaillab.resampling import peeking_false_positive_rate
from retaillab.validity import srm

LOOKS = [1, 2, 3, 5, 10, 20]


@st.cache_data(show_spinner="Simulating 2,000 A/A tests per schedule...")
def peeking_curve() -> list[float]:
    return [peeking_false_positive_rate(looks) for looks in LOOKS]


@st.cache_data(show_spinner="Running 100 placebo shuffles...")
def placebo_slices(shuffles: int = 100, seed: int = 7) -> pd.DataFrame:
    """Shuffle assignment so no true effect exists, then slice by every segment column."""
    data, _ = load_data()
    placebo = campaign_view(data, "any")
    arms = placebo.arm.to_numpy()
    rng = np.random.default_rng(seed)
    raw_hits = {column: 0 for column in SEGMENT_COLUMNS}
    bh_hits = dict(raw_hits)
    any_raw = any_bh = 0
    for _ in range(shuffles):
        placebo["arm"] = rng.permutation(arms)
        found_raw = found_bh = False
        for column in SEGMENT_COLUMNS:
            effects = segment_effects(placebo, column)
            raw, bh = bool((effects.p_value < 0.05).any()), bool(effects.significant.any())
            raw_hits[column] += raw
            bh_hits[column] += bh
            found_raw, found_bh = found_raw or raw, found_bh or bh
        any_raw += found_raw
        any_bh += found_bh
    rows = [
        {
            "Slice": label,
            "False lead, unadjusted": raw_hits[column] / shuffles,
            "False lead, after BH": bh_hits[column] / shuffles,
        }
        for column, label in SEGMENT_COLUMNS.items()
    ]
    rows.append(
        {
            "Slice": "Any of the above",
            "False lead, unadjusted": any_raw / shuffles,
            "False lead, after BH": any_bh / shuffles,
        }
    )
    return pd.DataFrame(rows)


data, _ = load_data()
header(
    "Evidence",
    "What can fool the team?",
    "Three ways a readout goes wrong even when the arithmetic is right.",
)

st.subheader("1. Peeking at a test that has no effect")
rates = peeking_curve()
fig = go.Figure(
    go.Scatter(
        x=LOOKS, y=rates, mode="lines+markers", line={"color": COLORS["danger"]},
        hovertemplate="%{x} looks: %{y:.1%} false wins<extra></extra>",
    )
)
fig.add_hline(
    y=0.05, line_dash="dash", line_color=COLORS["muted"], annotation_text="Promised 5%"
)
fig.update_xaxes(title="Interim looks, stopping at the first p < 0.05", type="log",
                 tickvals=LOOKS)
fig.update_yaxes(title="A/A tests declared winners", tickformat=".0%", rangemode="tozero")
chart(fig, 300)
st.caption(
    f"Checking a test {LOOKS[-2]} times and stopping at the first significant result declares "
    f"a winner {rates[-2]:.0%} of the time when nothing works. Fix the sample size up front, "
    "or use sequential (always-valid) tests. Hillstrom has no timestamps, so this is a "
    "simulation."
)

st.subheader("2. A broken split")
view = campaign_view(data, "any")
treated_non_buyers = view.index[(view.arm == "treatment") & (view.conversion == 0)]
dropped = np.random.default_rng(1).choice(
    treated_non_buyers, int(0.05 * len(treated_non_buyers)), replace=False
)
broken = data.drop(index=dropped)
honest = welch_effect(view, "revenue")
biased = welch_effect(campaign_view(broken, "any"), "revenue")
check = srm(broken, DESIGN)
cols = st.columns(3)
cols[0].metric("True revenue lift", f"{honest['difference'] / honest['control_mean']:+.0%}")
cols[1].metric(
    "Reported after the bug", f"{biased['difference'] / biased['control_mean']:+.0%}",
)
cols[2].metric("SRM check", "FAILED" if check["failed"] else "passed",
               f"p = {check['p_value']:.1e}", delta_color="off")
st.caption(
    "Simulated bug: 5% of e-mailed customers who did not buy go missing from the logs (think "
    "bounced sends silently filtered). The lift inflates, and only the split check catches it."
)

st.subheader("3. Slicing until something is significant")
st.dataframe(
    placebo_slices(),
    hide_index=True,
    column_config={
        "False lead, unadjusted": st.column_config.NumberColumn(format="percent"),
        "False lead, after BH": st.column_config.NumberColumn(format="percent"),
    },
)
st.caption(
    "Assignment is shuffled 100 times, so every true effect is zero. The table shows how often "
    "at least one segment still looks significant. BH correction pulls each slice back toward the 5% target; "
    "slicing four ways and reporting whichever works multiplies the risk again."
)
