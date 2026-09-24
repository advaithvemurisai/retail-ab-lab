from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from app.ui.context import render_sidebar
from app.ui.theme import inject_theme

st.set_page_config(
    page_title="RetailLab", page_icon=":material/storefront:", layout="wide", initial_sidebar_state="expanded"
)
inject_theme()
render_sidebar()
pages = {
    "Decision": [
        st.Page("views/overview.py", title="Overview", default=True),
        st.Page("views/campaign_roi.py", title="Campaign ROI"),
        st.Page("views/attribution.py", title="Attributed vs incremental"),
        st.Page("views/targeting.py", title="Who to send to"),
        st.Page("views/promotion.py", title="Which e-mail"),
        st.Page("views/economics.py", title="Same lift, different economics"),
    ],
    "Evidence": [
        st.Page("views/planning.py", title="Test planning"),
        st.Page("views/pitfalls.py", title="Pitfalls lab"),
        st.Page("views/data_model.py", title="Data model"),
        st.Page("views/research.py", title="Research"),
    ],
    "Portfolio": [st.Page("views/case_study.py", title="Case study")],
}
st.navigation(pages).run()
