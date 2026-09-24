import streamlit as st

from app.ui.context import get_context

data, *_ = get_context()
st.markdown(
    '<div class="eyebrow">Question 4</div><h1>Which promotion should roll out?</h1>',
    unsafe_allow_html=True,
)
st.info(
    "Demo mode shows the customer campaign. The store-level warehouse path aggregates by store and applies design-effect corrections."
)
st.dataframe(
    data.groupby("arm").agg(units=("unit_id", "count"), sales=("revenue", "sum")),
    use_container_width=True,
)
