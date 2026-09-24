from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from app.ui.context import get_context
from retaillab.decision import decide
from retaillab.finance import break_even_lift

data, primary, revenue, economics, validity, adjusted = get_context()
st.markdown(
    '<div class="hero"><div class="eyebrow">Retail decision lab</div><h1>RetailLab</h1><p>Marketing says the campaign worked. Sales says revenue is up. Finance asks what it actually earned. RetailLab joins all three and uses randomized experiments to find the answer.</p></div>',
    unsafe_allow_html=True,
)
verdict = decide(
    validity_failed=validity["failed"],
    primary_lift=primary["relative_lift"],
    primary_p=primary["p_value"],
    contribution_low=revenue["ci_low"] * 0.4 - economics["marketing_cost"],
    contribution_high=revenue["ci_high"] * 0.4 - economics["marketing_cost"],
    roi=economics["roi"],
    minimum_roi=0,
    power=min(1, len(data) / 12000),
)
st.markdown(
    f'<div class="verdict"><div class="eyebrow">Recommendation</div><h2>{verdict.label}</h2><p>{" ".join(verdict.reasons)}</p><p><b>Next:</b> {verdict.next_step}</p></div>',
    unsafe_allow_html=True,
)
cols = st.columns(3)
cols[0].metric("Incremental revenue", f"${economics['incremental_revenue']:,.0f}")
cols[1].metric("Contribution", f"${economics['contribution']:,.0f}")
cols[2].metric("Chance of loss", f"{revenue['chance_loss']:.0%}")
st.subheader("How it works")
steps = st.columns(3)
for col, title, body in zip(
    steps,
    ["Randomize", "Join", "Decide"],
    [
        "Customers or stores split at random.",
        "Marketing cost, sales outcomes, and finance margins meet.",
        "Estimate lift, profit, and what to do next.",
    ],
):
    col.markdown(
        f'<div class="step"><b>{title}</b><p class="muted">{body}</p></div>', unsafe_allow_html=True
    )
st.subheader("Break-even and CUPED")
be = break_even_lift(0.18, data[data.arm == "control"].revenue.mean(), 0.4)
st.write(
    f"Break-even lift at the benchmark margin: **{be:.1%}**. Observed lift: **{primary['relative_lift']:.1%}**."
)
if adjusted:
    st.write(
        f"CUPED variance reduction: **{adjusted['variance_reduction']:.1%}**, implying roughly **{adjusted['duration_saving']:.1%}** shorter testing at the same sensitivity."
    )
with st.expander("How we know"):
    st.write(
        "The primary result uses a two-proportion z-test. Revenue uses a bootstrap confidence interval. CUPED uses a pre-period covariate and a treatment-blind theta estimate."
    )
