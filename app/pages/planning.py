import streamlit as st

from app.ui.context import get_context
from retaillab.resampling import aa_false_positive_rate

data, *_ = get_context()
st.markdown(
    '<div class="eyebrow">Evidence</div><h1>How long should the next test run?</h1>',
    unsafe_allow_html=True,
)
st.metric("A/A false positive rate with peeking", f"{aa_false_positive_rate():.1%}")
st.line_chart(data.groupby("arm")["conversion"].mean())
