import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.ui.components import chart, header
from app.ui.context import get_readout, load_data
from app.ui.theme import COLORS
from retaillab.data import campaign_view
from retaillab.power import power_two_means, required_total_n, weeks_needed
from retaillab.variance import cuped

r = get_readout()
a = r.assumptions
header(
    "Evidence",
    "How long should the next test run?",
    "Size the next test so it can detect the smallest lift that pays for itself. Noise comes "
    "from this experiment's own revenue spread.",
)

left, middle, right = st.columns(3)
target = middle.number_input(
    "Lift to detect (%)", 1.0, 500.0, round(r.planned_lift * 100, 1), step=1.0,
    help="Defaults to the break-even revenue lift at the sidebar margin and cost.",
) / 100
target_power = left.select_slider("Power", [0.7, 0.8, 0.9, 0.95], 0.8)
share = right.select_slider(
    "Share of customers e-mailed", [0.5, 2 / 3, 0.8, 0.9], 0.5,
    format_func=lambda value: f"{value:.0%}",
    help="A bigger holdout costs lost sales; a smaller one needs more customers overall.",
)

view, _ = cuped(campaign_view(load_data()[0], a.variant))
raw_sd = float(view.revenue.std())
cuped_sd = float(view.revenue_cuped.std())
delta = target * r.baseline_revenue
n_raw = required_total_n(delta, raw_sd, share, a.alpha, target_power)
n_cuped = required_total_n(delta, cuped_sd, share, a.alpha, target_power)
n_used = n_cuped if a.use_cuped else n_raw

cols = st.columns(3)
cols[0].metric(
    "Customers needed", f"{n_used:,}", help="Both arms together, CUPED per the sidebar toggle."
)
cols[1].metric("Weeks at current volume", f"{weeks_needed(n_used, a.weekly_customers):.1f}")
cols[2].metric(
    "Weeks saved by CUPED", f"{weeks_needed(n_raw - n_cuped, a.weekly_customers):.2f}",
    help="CUPED cuts required sample by the share of variance past-year spend explains.",
)

weeks = np.linspace(0.25, max(2.0, 2 * weeks_needed(n_raw, a.weekly_customers)), 60)
fig = go.Figure()
for label, spread, color, dash in [
    ("Without CUPED", raw_sd, COLORS["control"], "dash"),
    ("With CUPED", cuped_sd, COLORS["accent"], "solid"),
]:
    power = [
        power_two_means(
            delta, spread, spread, int(w * a.weekly_customers * (1 - share)),
            int(w * a.weekly_customers * share), a.alpha,
        )
        for w in weeks
    ]
    fig.add_scatter(
        x=weeks, y=power, name=label, line={"color": color, "dash": dash},
        hovertemplate="%{x:.1f} weeks: %{y:.0%} power<extra>" + label + "</extra>",
    )
fig.add_hline(y=target_power, line_color=COLORS["danger"], line_dash="dot")
fig.update_layout(showlegend=True, legend={"orientation": "h", "y": 1.12})
fig.update_xaxes(title="Weeks of traffic")
fig.update_yaxes(title="Power", tickformat=".0%", range=[0, 1])
chart(fig, 340)

st.subheader("Why CUPED barely helps here")
st.markdown(
    f"CUPED removes the share of variance a pre-period covariate explains, which is the "
    f"squared correlation. Past-year spend and two-week spend correlate at "
    f"ρ = {r.cuped['correlation']:.3f}, so the reduction is "
    f"{r.cuped['variance_reduction']:.2%}. Most customers buy nothing in the window, and "
    "annual history does not predict who will. A covariate with ρ = 0.5 would cut the "
    "sample by 25%."
)
