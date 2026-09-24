import plotly.graph_objects as go
import streamlit as st

from app.ui.components import chart, header, money
from app.ui.context import get_readout
from app.ui.theme import COLORS
from retaillab.data import VARIANTS
from retaillab.decision import format_roi

r = get_readout()
a, e = r.assumptions, r.economics
header(
    "Question 1",
    "Did the campaign pay for itself?",
    f"{VARIANTS[a.variant]} sent to {e['customers_contacted']:,} customers, measured against a "
    "randomized no-e-mail control over the two-week window.",
)

cols = st.columns(3)
cols[0].metric(
    "Contribution", money(e["contribution"]),
    f"95% CI {money(r.contribution['ci_low'], markdown=True)} to "
    f"{money(r.contribution['ci_high'], markdown=True)}",
    delta_color="off", delta_arrow="off",
)
cols[1].metric(
    "ROI", format_roi(e["roi"]),
    help="Contribution divided by e-mail cost.",
)
cols[2].metric(
    "Gross profit per $1 of e-mail", f"${e['gross_profit'] / e['marketing_cost']:.2f}"
    if e["marketing_cost"] else "n/a",
)

cost_of_goods = e["incremental_revenue"] - e["gross_profit"]
fig = go.Figure(
    go.Waterfall(
        x=["Incremental revenue", "Cost of goods", "Gross profit", "E-mail cost", "Contribution"],
        measure=["absolute", "relative", "total", "relative", "total"],
        y=[e["incremental_revenue"], -cost_of_goods, 0, -e["marketing_cost"], 0],
        text=[
            money(e["incremental_revenue"]), money(-cost_of_goods), money(e["gross_profit"]),
            money(-e["marketing_cost"]), money(e["contribution"]),
        ],
        textposition="outside",
        increasing={"marker": {"color": COLORS["accent"]}},
        decreasing={"marker": {"color": COLORS["danger"]}},
        totals={"marker": {"color": COLORS["ink"]}},
        connector={"line": {"color": COLORS["line"]}},
    )
)
fig.update_yaxes(tickformat="$,.0f")
chart(fig, 380)
st.caption(
    f"Gross margin {a.gross_margin:.1%}, e-mail cost \\${a.contact_cost:.2f} per customer. "
    "Change either in the sidebar. Revenue is a two-week window; lasting effects are not counted."
)
