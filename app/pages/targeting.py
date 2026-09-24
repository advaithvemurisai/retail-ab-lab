import streamlit as st

from app.ui.context import get_context

data, *_ = get_context()
st.markdown(
    '<div class="eyebrow">Question 3</div><h1>Who should receive the next send?</h1>',
    unsafe_allow_html=True,
)
summary = (
    data.groupby("segment")
    .agg(
        audience=("unit_id", "size"), conversion=("conversion", "mean"), revenue=("revenue", "mean")
    )
    .reset_index()
)
summary["profit_per_dollar"] = summary.revenue * 0.4 / 0.18
st.dataframe(summary.sort_values("profit_per_dollar", ascending=False), hide_index=True)
st.caption(
    "Segment ranking is a decision aid. Apply BH correction before treating a segment difference as causal evidence."
)
