import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.ui.components import chart, header
from app.ui.context import get_readout, load_margin_table
from app.ui.theme import COLORS
from retaillab.finance import break_even_lift

r = get_readout()
a = r.assumptions
margins = load_margin_table()
header(
    "Question 5",
    "Would the same lift pay in another sector?",
    "The e-mail's measured revenue lift is held fixed. Only the gross margin changes, so this "
    "shows how much unit economics alone move the decision.",
)

low, high = r.revenue_lift_ci
rows = []
for sector, values in margins["margins"].items():
    margin = values["gross_margin"]
    needed = break_even_lift(a.contact_cost, r.baseline_revenue, margin)
    if low > needed:
        verdict = "Pays"
    elif high < needed:
        verdict = "Doesn't pay"
    else:
        verdict = "Uncertain"
    rows.append(
        {
            "Sector": sector,
            "Gross margin": margin,
            "Break-even lift": needed,
            "Contribution / 10k sends": (
                r.revenue["difference"] * margin - a.contact_cost
            ) * 10_000,
            "Verdict": verdict,
        }
    )
table = pd.DataFrame(rows)

fig = go.Figure(
    go.Bar(
        x=table["Break-even lift"],
        y=table.Sector,
        orientation="h",
        marker_color=COLORS["control"],
        text=[f"{value:.0%}" for value in table["Break-even lift"]],
        textposition="outside",
        hovertemplate="%{y}: break-even %{x:.0%}<extra></extra>",
    )
)
fig.add_vrect(x0=low, x1=high, fillcolor=COLORS["accent"], opacity=0.15, line_width=0)
fig.add_vline(
    x=r.revenue_lift, line_color=COLORS["accent"],
    annotation_text=f"Observed lift {r.revenue_lift:.0%}", annotation_position="top",
)
fig.update_xaxes(tickformat=".0%", title="Revenue lift needed to break even", rangemode="tozero")
chart(fig, 260)
st.dataframe(
    table,
    hide_index=True,
    column_config={
        "Gross margin": st.column_config.NumberColumn(format="percent"),
        "Break-even lift": st.column_config.NumberColumn(format="percent"),
        "Contribution / 10k sends": st.column_config.NumberColumn(format="$%.0f"),
    },
)
st.caption(
    "The shaded band is the 95% interval on the observed lift. A sector pays when the whole band "
    "clears its break-even bar. "
    + (
        f"Margins: Damodaran sector averages for US public companies, {margins['as_of']}. "
        "They are benchmarks, not any one retailer's books."
        if margins["source"] == "damodaran"
        else "Margins are illustrative placeholders until data/raw/margin.xls is downloaded."
    )
)
