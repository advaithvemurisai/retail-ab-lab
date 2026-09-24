import streamlit as st

from app.ui.context import get_context

data, _, _, economics, _, _ = get_context()
st.markdown(
    '<div class="eyebrow">Question 1</div><h1>Did the campaign pay for itself?</h1>',
    unsafe_allow_html=True,
)
st.metric("Contribution", f"${economics['contribution']:,.0f}")
st.metric("ROI", f"{economics['roi']:.1f}x")
st.line_chart(data.groupby("arm")["revenue"].mean())
