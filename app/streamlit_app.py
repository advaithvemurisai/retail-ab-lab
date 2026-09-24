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
    page_title="RetailLab", page_icon="R", layout="wide", initial_sidebar_state="expanded"
)
inject_theme()
render_sidebar()
pages = {
    "Decision": [
        st.Page("pages/overview.py", title="Overview", default=True),
        st.Page("pages/campaign_roi.py", title="Campaign ROI"),
        st.Page("pages/attribution.py", title="Attributed vs incremental"),
        st.Page("pages/targeting.py", title="Who to send to"),
        st.Page("pages/promotion.py", title="Promotion rollout"),
        st.Page("pages/economics.py", title="Same lift, different economics"),
    ],
    "Evidence": [
        st.Page("pages/planning.py", title="Test planning"),
        st.Page("pages/pitfalls.py", title="Pitfalls lab"),
        st.Page("pages/data_model.py", title="Data model"),
        st.Page("pages/research.py", title="Research"),
    ],
    "Portfolio": [st.Page("pages/case_study.py", title="Case study")],
}
st.navigation(pages).run()
