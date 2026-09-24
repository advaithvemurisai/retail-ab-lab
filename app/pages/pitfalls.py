import streamlit as st

from retaillab.resampling import aa_false_positive_rate

st.markdown(
    '<div class="eyebrow">Evidence</div><h1>What can fool the team?</h1>', unsafe_allow_html=True
)
st.write(
    "Peeking inflates false wins. Broken splits invalidate estimates. Segment slicing needs correction. CUPED helps only when the covariate predicts the outcome."
)
st.metric("Peeking A/A false positive rate", f"{aa_false_positive_rate():.1%}")
