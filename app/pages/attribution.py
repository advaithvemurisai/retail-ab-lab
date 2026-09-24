import streamlit as st

from app.ui.context import get_context
from retaillab.finance import attributed_incremental

data, *_ = get_context()
result = attributed_incremental(data)
st.markdown(
    '<div class="eyebrow">Question 2</div><h1>How much revenue was incremental?</h1>',
    unsafe_allow_html=True,
)
st.bar_chart(
    {"Attributed revenue": [result["attributed"]], "Incremental revenue": [result["incremental"]]}
)
st.write(
    f"**{result['gap_pct']:.0%}** of treatment revenue would have happened anyway, based on the randomized control."
)
