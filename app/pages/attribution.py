import plotly.graph_objects as go
import streamlit as st

from app.ui.components import chart, header, money
from app.ui.context import get_readout, load_data
from app.ui.theme import COLORS
from retaillab.data import campaign_view
from retaillab.finance import attributed_incremental

r = get_readout()
data, _ = load_data()
result = attributed_incremental(campaign_view(data, r.assumptions.variant))
header(
    "Question 2",
    "How much revenue was incremental?",
    "A click-through report credits the e-mail with every purchase an e-mailed customer made. "
    "The randomized control shows how much of that would have happened anyway.",
)

cols = st.columns(3)
cols[0].metric("E-mail-attributed revenue", money(result["attributed"]))
cols[1].metric("Incremental revenue", money(result["incremental"]))
cols[2].metric("Would have happened anyway", f"{result['gap_pct']:.0%}")

fig = go.Figure(
    [
        go.Bar(
            name="Would have happened anyway", x=[result["baseline"]], y=["Attributed"],
            orientation="h", marker_color=COLORS["control"],
            text=[money(result["baseline"])], textposition="inside",
        ),
        go.Bar(
            name="Caused by the e-mail", x=[result["incremental"]], y=["Attributed"],
            orientation="h", marker_color=COLORS["accent"],
            text=[money(result["incremental"])], textposition="inside",
        ),
    ]
)
fig.update_layout(barmode="stack")
fig.update_xaxes(tickprefix="$", tickformat=",.0f")
chart(fig, 200)
st.markdown(
    f"Grey is revenue the control group predicts e-mailed customers would have spent "
    f"regardless ({money(result['baseline'], markdown=True)}). Teal is the causal lift "
    f"({money(result['incremental'], markdown=True)}). Budgeting on attributed revenue would "
    f"overstate the e-mail's return by {result['attributed'] / result['incremental']:.1f}x."
    if result["incremental"] > 0
    else "The e-mail produced no measurable incremental revenue."
)
