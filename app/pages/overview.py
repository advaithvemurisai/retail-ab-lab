import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.ui.components import chart, money, verdict_card
from app.ui.context import get_readout, load_data
from app.ui.theme import COLORS
from retaillab.data import ARM_LABELS, VARIANTS

r = get_readout()
a = r.assumptions
data, source = load_data()

st.markdown(
    '<div class="hero"><div class="eyebrow">Retail decision lab</div><h1>RetailLab</h1>'
    "<p>Marketing says the e-mail worked. Sales says revenue is up. Finance asks what it "
    "actually earned. RetailLab prices a randomized e-mail test at the margin and contact "
    "cost you set, then says whether to ship.</p></div>",
    unsafe_allow_html=True,
)
verdict_card(r.verdict, f"{VARIANTS[a.variant]} vs no e-mail")

cols = st.columns(4)
cols[0].metric(
    "Incremental revenue", money(r.economics["incremental_revenue"]),
    help="Treatment minus control revenue per customer, times customers e-mailed "
    "(CUPED-adjusted when the toggle is on).",
)
cols[1].metric(
    "Contribution", money(r.economics["contribution"]),
    f"95% CI {money(r.contribution['ci_low'], markdown=True)} to "
    f"{money(r.contribution['ci_high'], markdown=True)}",
    delta_color="off", delta_arrow="off", help="Incremental gross profit minus e-mail cost.",
)
cols[2].metric(
    "ROI", f"{r.economics['roi']:+.0%}",
    help="Contribution divided by e-mail cost. +100% means each $1 spent returned $2 of "
    "gross profit.",
)
cols[3].metric(
    "Chance of loss", f"{r.contribution['chance_of_loss']:.0%}",
    help="Share of bootstrap draws where contribution is below zero.",
)

st.subheader("Does the lift clear break-even?")
low, high = r.revenue_lift_ci
fig = go.Figure(
    go.Bar(
        x=[r.revenue_lift],
        y=["Observed revenue lift"],
        orientation="h",
        marker_color=COLORS["accent"],
        error_x={
            "type": "data", "symmetric": False, "array": [high - r.revenue_lift],
            "arrayminus": [r.revenue_lift - low], "color": COLORS["ink"],
        },
        hovertemplate="Lift %{x:.1%}<extra></extra>",
    )
)
fig.add_vline(
    x=r.break_even_lift, line_dash="dash", line_color=COLORS["danger"],
    annotation_text=f"Break-even {r.break_even_lift:.0%}", annotation_position="top",
)
fig.update_xaxes(tickformat=".0%", rangemode="tozero")
chart(fig, 180)
st.caption(
    f"Customers who got no e-mail spent \\${r.baseline_revenue:.2f} each on average. "
    f"At {a.gross_margin:.0%} gross margin and \\${a.contact_cost:.2f} per e-mail, revenue "
    f"must rise {r.break_even_lift:.0%} to pay for the send. Conversion moved "
    f"{r.conversion['relative_lift']:+.0%} "
    f"(95% CI {r.conversion['lift_ci_low']:+.0%} to {r.conversion['lift_ci_high']:+.0%})."
)

st.subheader("How it works")
steps = st.columns(3)
for col, title, body in zip(
    steps,
    ["Randomize", "Price", "Decide"],
    [
        "Customers were split at random into no e-mail, men's e-mail, and women's e-mail.",
        "Incremental revenue meets sector gross margin and the cost of each send.",
        "Validity, profit, downside risk, and power feed one rule-based verdict.",
    ],
):
    col.markdown(
        f'<div class="step"><b>{title}</b><p class="muted">{body}</p></div>',
        unsafe_allow_html=True,
    )

with st.expander("How we know"):
    v = r.validity
    st.markdown(
        f"**Split check (SRM).** The design sends one third of customers to each arm. "
        f"Chi-square p = {v['p_value']:.2f}, so the split "
        f"{'**failed**' if v['failed'] else 'matches the design'} (threshold p < 0.001)."
    )
    st.dataframe(
        pd.DataFrame(
            {
                "Arm": [ARM_LABELS[arm] for arm in v["counts"]],
                "Customers": list(v["counts"].values()),
                "Expected": [round(value) for value in v["expected"].values()],
            }
        ),
        hide_index=True,
    )
    st.markdown("**Covariate balance.** Standardized mean differences below 0.1 are balanced.")
    st.dataframe(r.balance, hide_index=True)
    st.markdown(
        "**Methods.** Revenue per customer uses a Welch test, the primary decision metric. "
        "Contribution uncertainty comes from 1,000 bootstrap resamples of the revenue "
        "difference, scaled by customers e-mailed, margin, and cost. Conversion uses a "
        "two-proportion z-test with a delta-method interval. Power is computed for the "
        f"break-even lift at the current sample size ({r.power:.0%}). "
        + (
            f"CUPED is on: past-year spend explains {r.cuped['variance_reduction']:.2%} of "
            "revenue variance here, so it barely changes the estimate."
            if a.use_cuped
            else "CUPED is off."
        )
    )
    if source == "demo":
        st.info("These numbers come from synthetic data, not a published result.")
