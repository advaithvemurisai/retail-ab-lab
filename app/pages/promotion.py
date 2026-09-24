import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.ui.components import chart, header, money
from app.ui.context import assumptions, load_data
from app.ui.theme import ARM_COLORS, COLORS
from retaillab.data import ARM_LABELS
from retaillab.estimate import pairwise_arms
from retaillab.variance import cuped

a = assumptions()
data, _ = load_data()
header(
    "Question 4",
    "Which e-mail should roll out?",
    "Men's and women's creatives were tested side by side against no e-mail. Compare all "
    "three with a correction for making three comparisons at once.",
)

frame, _ = cuped(data)
metric = "revenue_cuped" if a.use_cuped else "revenue"
arms = list(ARM_LABELS)
summary = frame.groupby("arm").agg(
    customers=(metric, "size"), conversion=("conversion", "mean"),
    revenue=(metric, "mean"), sd=(metric, "std"),
).reindex(arms)
summary["se"] = summary.sd / np.sqrt(summary.customers)
control = summary.loc["control", "revenue"]
summary["contribution_per_10k"] = np.where(
    summary.index == "control", 0.0,
    ((summary.revenue - control) * a.gross_margin - a.contact_cost) * 10_000,
)
pairs = pairwise_arms(frame, arms, metric, a.alpha)

emails = summary.drop("control")
best, runner_up = emails.contribution_per_10k.sort_values(ascending=False).index[:2]
head_to_head = pairs[pairs.left.isin([best, runner_up]) & pairs.right.isin([best, runner_up])]
decisive = bool(head_to_head.significant.iloc[0])
best_value = summary.loc[best, "contribution_per_10k"]

if best_value <= 0:
    st.error("Neither e-mail earns back its cost at these assumptions. Send neither.")
elif decisive:
    st.success(
        f"**Roll out the {ARM_LABELS[best].lower()}.** It beats the "
        f"{ARM_LABELS[runner_up].lower()} after BH correction and earns "
        f"{money(best_value, markdown=True)} of contribution per 10,000 sends."
    )
else:
    st.warning(
        f"**The {ARM_LABELS[best].lower()} leads, but not decisively.** The gap to the "
        f"{ARM_LABELS[runner_up].lower()} does not survive BH correction. Ship the leader if "
        "a choice is needed now, or extend the head-to-head test."
    )

fig = go.Figure(
    go.Bar(
        x=[ARM_LABELS[arm] for arm in arms],
        y=summary.revenue,
        marker_color=[ARM_COLORS[arm] for arm in arms],
        error_y={"type": "data", "array": 1.96 * summary.se, "color": COLORS["ink"]},
        text=[f"${value:.2f}" for value in summary.revenue],
        textposition="outside",
        hovertemplate="%{x}: %{y:$.2f} per customer<extra></extra>",
    )
)
fig.update_yaxes(title="Revenue per customer, two weeks (95% CI)", tickprefix="$")
chart(fig, 360)

st.dataframe(
    pd.DataFrame(
        {
            "Arm": [ARM_LABELS[arm] for arm in arms],
            "Customers": summary.customers.to_numpy(),
            "Conversion": summary.conversion.to_numpy(),
            "Revenue / customer": summary.revenue.to_numpy(),
            "Contribution / 10k sends": summary.contribution_per_10k.to_numpy(),
        }
    ),
    hide_index=True,
    column_config={
        "Conversion": st.column_config.NumberColumn(format="percent"),
        "Revenue / customer": st.column_config.NumberColumn(format="$%.2f"),
        "Contribution / 10k sends": st.column_config.NumberColumn(format="$%.0f"),
    },
)
st.subheader("Pairwise comparisons")
st.dataframe(
    pairs.assign(
        comparison=[
            f"{ARM_LABELS[right]} vs {ARM_LABELS[left]}"
            for left, right in zip(pairs.left, pairs.right)
        ]
    )[["comparison", "difference", "ci_low", "ci_high", "p_value", "p_adjusted", "significant"]],
    hide_index=True,
    column_config={
        "comparison": "Comparison",
        "difference": st.column_config.NumberColumn("Revenue difference", format="$%.3f"),
        "ci_low": st.column_config.NumberColumn("95% CI low", format="$%.3f"),
        "ci_high": st.column_config.NumberColumn("95% CI high", format="$%.3f"),
        "p_value": st.column_config.NumberColumn("p", format="%.4f"),
        "p_adjusted": st.column_config.NumberColumn("BH-adjusted p", format="%.4f"),
        "significant": "Significant",
    },
)
