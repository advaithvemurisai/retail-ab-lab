import plotly.graph_objects as go
import streamlit as st

from app.ui.components import chart, header, money
from app.ui.context import get_readout, load_data
from app.ui.theme import COLORS
from retaillab.data import SEGMENT_COLUMNS, campaign_view
from retaillab.estimate import segment_effects
from retaillab.finance import greedy_allocation
from retaillab.variance import cuped

r = get_readout()
a = r.assumptions
data, _ = load_data()
header(
    "Question 3",
    "Who should receive the next send?",
    "Rank segments by the profit the e-mail caused in each one, not by how much they "
    "already spend. Then fill the send budget from the top.",
)

left, middle, right = st.columns(3)
by = left.selectbox("Segment by", list(SEGMENT_COLUMNS), format_func=SEGMENT_COLUMNS.get)
cap = middle.number_input(
    "Send budget (customers)", 0, len(data), len(data), step=1_000,
    help="Defaults to the whole file, so the plan simply skips unprofitable segments.",
)
require_significant = right.toggle(
    "Only BH-significant segments", False,
    help="Send only where the lift survives Benjamini-Hochberg correction across segments.",
)

view, _ = cuped(campaign_view(data, a.variant))
metric = "revenue_cuped" if a.use_cuped else "revenue"
rows = segment_effects(view, by, metric, a.alpha)
rows["audience"] = rows.segment.map(data.groupby(by, observed=True).size()).astype(int)
rows["profit_per_send"] = rows.difference * a.gross_margin - a.contact_cost
rows["profit_low"] = rows.ci_low * a.gross_margin - a.contact_cost
rows["profit_high"] = rows.ci_high * a.gross_margin - a.contact_cost
rows["profit_per_dollar"] = (
    rows.profit_per_send / a.contact_cost if a.contact_cost else rows.profit_per_send
)
plan = greedy_allocation(rows, int(cap), require_significant)

planned = float((plan.send_count * plan.profit_per_send).sum())
everyone = float((plan.audience * plan.profit_per_send).sum())
cols = st.columns(3)
cols[0].metric("Customers to e-mail", f"{int(plan.send_count.sum()):,}")
cols[1].metric("Expected contribution", money(planned))
cols[2].metric(
    "vs e-mailing everyone", money(planned - everyone, signed=True),
    help=f"E-mailing all {int(plan.audience.sum()):,} customers: {money(everyone)}.",
)

ordered = plan.sort_values("profit_per_send")
fig = go.Figure(
    go.Scatter(
        x=ordered.profit_per_send,
        y=ordered.segment.astype(str),
        mode="markers",
        marker={
            "size": 12,
            "color": [COLORS["accent"] if s else COLORS["control"] for s in ordered.selected],
        },
        error_x={
            "type": "data", "symmetric": False,
            "array": ordered.profit_high - ordered.profit_per_send,
            "arrayminus": ordered.profit_per_send - ordered.profit_low,
            "color": COLORS["muted"],
        },
        hovertemplate="%{y}: %{x:$.2f} per send<extra></extra>",
    )
)
fig.add_vline(x=0, line_color=COLORS["danger"], line_dash="dash")
fig.update_xaxes(title="Incremental contribution per e-mail (95% CI)", tickformat="$,.2~f")
chart(fig, 60 + 45 * len(ordered))

st.dataframe(
    plan[
        ["segment", "audience", "difference", "profit_per_send", "p_value", "p_adjusted",
         "significant", "send_count"]
    ],
    hide_index=True,
    column_config={
        "segment": SEGMENT_COLUMNS[by],
        "audience": st.column_config.NumberColumn("Customers", format="%d"),
        "difference": st.column_config.NumberColumn("Revenue lift / customer", format="dollar"),
        "profit_per_send": st.column_config.NumberColumn("Contribution / send", format="dollar"),
        "p_value": st.column_config.NumberColumn("p", format="%.3f"),
        "p_adjusted": st.column_config.NumberColumn("BH-adjusted p", format="%.3f"),
        "significant": "Significant",
        "send_count": st.column_config.NumberColumn("Send", format="%d"),
    },
)
st.caption(
    "Segment estimates are noisier than the overall result. Point estimates drive the plan; "
    "turn on the BH filter to act only on segment differences that survive correction."
)
